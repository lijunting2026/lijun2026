<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { studentApi, schoolApi } from "@/api"
import type { Student, ClassInfo, Grade, TransferResponse } from "@/types"
import { ElMessage, ElMessageBox } from "element-plus"
import { downloadBlob } from "@/utils/download"

const grades = ref<Grade[]>([])
const allClasses = ref<ClassInfo[]>([])
const allStudents = ref<Student[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const transferDialogVisible = ref(false)
const transferring = ref(false)

const form = ref({ student_no: "", name: "", gender: "未知", class_id: "" })
const editingId = ref("")
const dialogTitle = ref("添加学生")
const importText = ref("")
const uploadFile = ref<File | null>(null)
const importing = ref(false)

// 转班相关
const transferStudent = ref<Student | null>(null)
const transferForm = ref({ target_class_id: "", migrate_scores: false })

interface TreeNode {
  id: string
  label: string
  type: "grade" | "class" | "student"
  children?: TreeNode[]
  raw?: any
  student_count?: number
  grade_id?: string
  class_id?: string
}

const treeRef = ref()
function expandAll() {
  const tree = treeRef.value as any
  if (!tree?.store?.nodesMap) return
  tree.store.nodesMap.forEach((node: any) => {
    if (node.childNodes && node.childNodes.length > 0) {
      node.expand()
    }
  })
}
function collapseAll() {
  const tree = treeRef.value as any
  if (!tree?.store?.nodesMap) return
  tree.store.nodesMap.forEach((node: any) => {
    if (node.childNodes && node.childNodes.length > 0) {
      node.collapse()
    }
  })
}

const treeData = computed<TreeNode[]>(() => {
  return grades.value.map((g) => ({
    id: "grade-" + g.id,
    label: g.name,
    type: "grade" as const,
    raw: g,
    children: allClasses.value
      .filter((c) => c.grade_id === g.id)
      .map((c) => {
        const studentsInClass = allStudents.value.filter((s) => s.class_id === c.id)
        return {
          id: "class-" + c.id,
          label: c.name + " (" + c.student_count + "人)",
          type: "class" as const,
          raw: c,
          student_count: c.student_count,
          grade_id: c.grade_id,
          children: studentsInClass.length > 0
            ? studentsInClass.map((s) => ({
                id: "student-" + s.id,
                label: s.student_no + " - " + s.name,
                type: "student" as const,
                raw: s,
                class_id: s.class_id,
              }))
            : undefined,
        }
      }),
  }))
})

async function loadGrades() {
  try {
    const res = await schoolApi.listGrades()
    grades.value = res.data
  } catch {
    ElMessage.error("加载年级失败")
  }
}

async function loadAllClasses() {
  try {
    const res = await schoolApi.listClasses()
    allClasses.value = res.data
  } catch {
    // ignore
  }
}

async function loadAllStudents() {
  loading.value = true
  try {
    const res = await studentApi.list({ limit: 10000 })
    allStudents.value = res.data.items
  } finally {
    loading.value = false
  }
}

function openCreate(classId?: string) {
  form.value = { student_no: "", name: "", gender: "未知", class_id: classId || "" }
  editingId.value = ""
  dialogTitle.value = "添加学生"
  dialogVisible.value = true
}

function editStudent(row: Student) {
  editingId.value = row.id
  form.value = {
    student_no: row.student_no,
    name: row.name,
    gender: row.gender || "未知",
    class_id: row.class_id,
  }
  dialogTitle.value = "编辑学生"
  dialogVisible.value = true
}

// 打开转班对话框
function openTransfer(student: Student) {
  transferStudent.value = student
  transferForm.value = {
    target_class_id: "",
    migrate_scores: false,
  }
  transferDialogVisible.value = true
}

// 执行转班
async function handleTransfer() {
  if (!transferStudent.value || !transferForm.value.target_class_id) {
    ElMessage.warning("请选择目标班级")
    return
  }
  if (transferForm.value.target_class_id === transferStudent.value.class_id) {
    ElMessage.warning("目标班级与原班级相同")
    return
  }
  transferring.value = true
  try {
    const res = await studentApi.transfer(transferStudent.value.id, {
      target_class_id: transferForm.value.target_class_id,
      migrate_scores: transferForm.value.migrate_scores,
    })
    const data: TransferResponse = res.data
    ElMessage.success(
      `${data.student_name} 已从 ${data.original_class_name} 转入 ${data.target_class_name}` +
        (data.migrated_score_count > 0
          ? `，已同步迁移 ${data.migrated_score_count} 条成绩`
          : "")
    )
    transferDialogVisible.value = false
    transferStudent.value = null
    await Promise.all([loadAllStudents(), loadAllClasses()])
  } catch (err: unknown) {
    ElMessage.error(err.response?.data?.detail || err.message || "转班失败")
  } finally {
    transferring.value = false
  }
}

async function save() {
  try {
    if (editingId.value) {
      const res = await studentApi.update(editingId.value, form.value)
      // 如果班级发生变化（通过 update_student 的自动迁移），提示用户
      const respData = res.data as any
      if (respData._migrated_score_count !== undefined) {
        ElMessage.success(
          `修改成功，同时迁移了 ${respData._migrated_score_count} 条成绩记录到新班级`
        )
      } else {
        ElMessage.success("修改成功")
      }
    } else {
      await studentApi.create(form.value)
      ElMessage.success("添加成功")
    }
    editingId.value = ""
    dialogVisible.value = false
    await Promise.all([loadAllStudents(), loadAllClasses()])
  } catch (err: unknown) {
    ElMessage.error(err.response?.data?.detail || err.message || "操作失败")
  }
}

async function remove(id: string) {
  try {
    await ElMessageBox.confirm("确定删除该学生？")
    await studentApi.delete(id)
    ElMessage.success("已删除")
    await Promise.all([loadAllStudents(), loadAllClasses()])
  } catch (err: unknown) {
    if (err !== "cancel") {
      ElMessage.error(err.response?.data?.detail || err.message || "删除失败")
    }
  }
}

function openImport(classId?: string) {
  form.value.class_id = classId || ""
  importText.value = ""
  uploadFile.value = null
  importDialogVisible.value = true
}

async function downloadTemplate() {
  try {
    const token = localStorage.getItem("token") || ""
    const res = await fetch("/api/v1/students/export-template", {
      headers: { Authorization: "Bearer " + token },
    })
    if (!res.ok) {
      const err = await res.json()
      ElMessage.error(err.detail || "导出失败")
      return
    }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "学生导入模板.xlsx"
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success("模板已下载")
  } catch {
    ElMessage.error("下载模板失败")
  }
}

async function handleExcelImport() {
  if (!uploadFile.value || !form.value.class_id) {
    ElMessage.warning("请选择班级和文件")
    return
  }
  importing.value = true
  try {
    const formData = new FormData()
    formData.append("class_id", form.value.class_id)
    formData.append("file", uploadFile.value)
    const token = localStorage.getItem("token") || ""
    const res = await fetch("/api/v1/students/import-excel", {
      method: "POST",
      headers: { Authorization: "Bearer " + token },
      body: formData,
    })
    const data = await res.json()
    if (!res.ok) {
      ElMessage.error(data.detail || "导入失败")
      return
    }
    ElMessage.success(data.message)
    importDialogVisible.value = false
    await Promise.all([loadAllStudents(), loadAllClasses()])
  } catch {
    ElMessage.error("导入失败")
  } finally {
    importing.value = false
  }
}

function handleFileChange(file: any) {
  uploadFile.value = file.raw
}

async function handleImport() {
  const lines = importText.value
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
  if (lines.length === 0) {
    ElMessage.warning("请输入学生数据")
    return
  }
  const students = lines.map((line) => {
    const parts = line.split(/[,，\t]/).map((s) => s.trim())
    return {
      student_no: parts[0],
      name: parts[1] || "",
      gender: parts[2] || "未知",
      class_id: form.value.class_id,
    }
  })
  importing.value = true
  try {
    const res = await studentApi.importBatch({ students })
    ElMessage.success(res.data.message)
    importDialogVisible.value = false
    await Promise.all([loadAllStudents(), loadAllClasses()])
  } catch (err: unknown) {
    ElMessage.error(err.response?.data?.detail || err.message || "导入失败")
  } finally {
    importing.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadGrades(), loadAllClasses(), loadAllStudents()])
})
</script>

<template>
  <div>
    <el-card shadow="hover">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span style="font-weight: 600">学生管理</span>
          <div>
            <el-button size="small" @click="expandAll">展开全部</el-button>
            <el-button size="small" @click="collapseAll">折叠全部</el-button>
          </div>
        </div>
      </template>
      <el-alert
        title="展开班级节点查看下属学生，悬停节点可进行操作"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 12px"
      />
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="{ children: 'children', label: 'label' }"
        node-key="id"
        default-expand-all
        :expand-on-click-node="false"
        v-loading="loading"
      >
        <template #default="{ node, data }">
          <div style="display: flex; align-items: center; justify-content: space-between; flex: 1; padding-right: 8px">
            <div style="display: flex; align-items: center; gap: 8px">
              <el-icon v-if="data.type === 'grade'" :size="18" color="#E6A23C"><FolderOpened /></el-icon>
              <el-icon v-else-if="data.type === 'class'" :size="16" color="#409EFF"><Folder /></el-icon>
              <el-icon v-else :size="14" color="#67C23A"><User /></el-icon>
              <span :style="{ fontWeight: data.type === 'grade' ? 600 : data.type === 'class' ? 500 : 400 }">{{ data.label }}</span>
            </div>
            <div style="display: flex; gap: 4px" @click.stop>
              <template v-if="data.type === 'class'">
                <el-button size="small" text type="primary" @click="openCreate(data.raw.id)">
                  <el-icon><Plus /></el-icon>添加学生
                </el-button>
                <el-button size="small" text @click="openImport(data.raw.id)">
                  <el-icon><Upload /></el-icon>导入
                </el-button>
              </template>
              <template v-else-if="data.type === 'student'">
                <el-button size="small" text @click="editStudent(data.raw)">编辑</el-button>
                <el-button size="small" text type="warning" @click="openTransfer(data.raw)">转班</el-button>
                <el-button size="small" text type="danger" @click="remove(data.raw.id)">删除</el-button>
              </template>
            </div>
          </div>
        </template>
      </el-tree>
      <el-empty v-if="!loading && treeData.length === 0" description="暂无数据，请先添加年级和班级" />
    </el-card>

    <!-- 编辑/添加学生对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="学号">
          <el-input v-model="form.student_no" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="form.gender">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
            <el-option label="未知" value="未知" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="form.class_id" filterable>
            <el-option v-for="c in allClasses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">确定</el-button>
      </template>
    </el-dialog>

    <!-- 转班对话框 -->
    <el-dialog v-model="transferDialogVisible" title="学生转班" width="480px">
      <template v-if="transferStudent">
        <el-alert
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 16px"
        >
          <template #title>
            将 <strong>{{ transferStudent.name }}</strong>（{{ transferStudent.student_no }}）从
            <strong>{{ transferStudent.class_name }}</strong> 转到：
          </template>
        </el-alert>
        <el-form :model="transferForm" label-width="120px">
          <el-form-item label="目标班级">
            <el-select v-model="transferForm.target_class_id" filterable placeholder="请选择目标班级" style="width: 100%">
              <el-option
                v-for="c in allClasses"
                :key="c.id"
                :label="c.name + (c.grade_name ? ' (' + c.grade_name + ')' : '')"
                :value="c.id"
                :disabled="c.id === transferStudent.class_id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="成绩迁移">
            <el-switch
              v-model="transferForm.migrate_scores"
              active-text="同步迁移已有成绩到新班级"
              inactive-text="保留成绩在原班级"
            />
          </el-form-item>
        </el-form>
        <div v-if="transferForm.migrate_scores" style="background: #f0f9eb; padding: 10px 14px; border-radius: 6px; font-size: 13px; color: #67c23a; margin-bottom: 8px">
          该学生的所有历史成绩将归属到新班级，班级统计数据将自动更新。
        </div>
        <div v-else style="background: #fdf6ec; padding: 10px 14px; border-radius: 6px; font-size: 13px; color: #e6a23c; margin-bottom: 8px">
          历史成绩保留在原班级，仅新录入的成绩归属新班级。班级统计数据可能不一致。
        </div>
      </template>
      <template #footer>
        <el-button @click="transferDialogVisible = false">取消</el-button>
        <el-button type="warning" :loading="transferring" @click="handleTransfer">
          确认转班
        </el-button>
      </template>
    </el-dialog>

    <!-- 导入对话框 -->
    <el-dialog v-model="importDialogVisible" title="批量导入学生" width="550px">
      <div style="margin-bottom: 12px">
        <el-select v-model="form.class_id" placeholder="选择目标班级" filterable style="width: 100%">
          <el-option v-for="c in allClasses" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </div>
      <div style="margin-bottom: 12px">
        <el-button size="small" @click="downloadTemplate">下载Excel模板</el-button>
        <span style="color: #909399; margin-left: 8px; font-size: 13px">或直接输入文本</span>
      </div>
      <el-upload
        :auto-upload="false"
        :show-file-list="true"
        accept=".xlsx,.xls"
        :on-change="handleFileChange"
        style="margin-bottom: 12px"
      >
        <el-button size="small" type="primary">选择Excel文件</el-button>
      </el-upload>
      <el-divider />
      <p style="color: #909399; margin-bottom: 8px">每行一个学生，格式：学号,姓名,性别（性别可省略）</p>
      <el-input v-model="importText" type="textarea" :rows="6" placeholder="2024001,张三,男" />
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" :disabled="!form.class_id" @click="handleImport">文本导入</el-button>
        <el-button type="success" :loading="importing" :disabled="!form.class_id || !uploadFile" @click="handleExcelImport">Excel导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>
