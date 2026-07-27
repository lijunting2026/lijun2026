<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { schoolApi } from "@/api"
import type { Grade, ClassInfo } from "@/types"
import { ElMessage, ElMessageBox } from "element-plus"

const grades = ref<Grade[]>([])
const allClasses = ref<ClassInfo[]>([])
const loading = ref(false)
const gradeDialog = ref(false)
const classDialog = ref(false)
const gradeForm = ref({ name: "", sort_order: 0 })
const classForm = ref({ name: "", grade_id: "" })
const editingGradeId = ref("")
const editingClassId = ref("")

// Build tree data
interface TreeNode {
  id: string
  label: string
  type: "grade" | "class"
  children?: TreeNode[]
  raw?: any
  student_count?: number
  grade_id?: string
}
const treeData = computed<TreeNode[]>(() => {
  return grades.value.map((g) => ({
    id: g.id,
    label: g.name + " (年级)",
    type: "grade" as const,
    raw: g,
    children: allClasses.value
      .filter((c) => c.grade_id === g.id)
      .map((c) => ({
        id: c.id,
        label: c.name + (c.student_count != null ? " (" + c.student_count + "人)" : ""),
        type: "class" as const,
        raw: c,
        student_count: c.student_count,
        grade_id: c.grade_id,
      })),
  }))
})

async function loadGrades() {
  loading.value = true
  try {
    const res = await schoolApi.listGrades()
    grades.value = res.data
  } catch {
    ElMessage.error("加载年级失败")
  } finally {
    loading.value = false
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

function openCreateGrade() {
  editingGradeId.value = ""
  gradeForm.value = { name: "", sort_order: 0 }
  gradeDialog.value = true
}

function openEditGrade(row: Grade) {
  editingGradeId.value = row.id
  gradeForm.value = { name: row.name, sort_order: row.sort_order }
  gradeDialog.value = true
}

async function saveGrade() {
  try {
    if (editingGradeId.value) {
      await schoolApi.updateGrade(editingGradeId.value, gradeForm.value)
      ElMessage.success("修改成功")
    } else {
      await schoolApi.createGrade(gradeForm.value)
      ElMessage.success("添加成功")
    }
    gradeDialog.value = false
    gradeForm.value = { name: "", sort_order: 0 }
    await loadGrades()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || "操作失败")
  }
}

async function deleteGrade(id: string) {
  try {
    await ElMessageBox.confirm("确定删除该年级，删除后下属班级也将被删除")
    await schoolApi.deleteGrade(id)
    ElMessage.success("已删除")
    await Promise.all([loadGrades(), loadAllClasses()])
  } catch (err: any) {
    if (err !== "cancel") {
      ElMessage.error(err.response?.data?.detail || err.message || "删除失败")
    }
  }
}

function openCreateClass(gradeId?: string) {
  editingClassId.value = ""
  classForm.value = { name: "", grade_id: gradeId || "" }
  classDialog.value = true
}

function openEditClass(row: ClassInfo) {
  editingClassId.value = row.id
  classForm.value = { name: row.name, grade_id: row.grade_id }
  classDialog.value = true
}

async function saveClass() {
  try {
    if (editingClassId.value) {
      await schoolApi.updateClass(editingClassId.value, classForm.value)
      ElMessage.success("修改成功")
    } else {
      await schoolApi.createClass(classForm.value)
      ElMessage.success("添加成功")
    }
    classDialog.value = false
    classForm.value = { name: "", grade_id: "" }
    await loadAllClasses()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || "操作失败")
  }
}

async function deleteClass(id: string) {
  try {
    await ElMessageBox.confirm("确定删除该班级？")
    await schoolApi.deleteClass(id)
    ElMessage.success("已删除")
    await loadAllClasses()
  } catch (err: any) {
    if (err !== "cancel") {
      ElMessage.error(err.response?.data?.detail || err.message || "删除失败")
    }
  }
}

onMounted(() => {
  loadGrades()
  loadAllClasses()
})
</script>

<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span style="font-weight: 600">年级与班级</span>
          <div style="display: flex; gap: 8px">
            <el-button type="primary" size="small" @click="openCreateGrade">添加年级</el-button>
          </div>
        </div>
      </template>
      <el-alert
        title="点击年级节点可展开查看下属班级，悬浮节点可进行操作"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 12px"
      />
      <el-tree
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
              <el-icon v-else :size="16" color="#409EFF"><Document /></el-icon>
              <span :style="{ fontWeight: data.type === 'grade' ? 600 : 400 }">{{ data.label }}</span>
            </div>
            <div style="display: flex; gap: 4px" @click.stop>
              <template v-if="data.type === 'grade'">
                <el-button size="small" text type="primary" @click="openCreateClass(data.id)">
                  <el-icon><Plus /></el-icon>添加班级
                </el-button>
                <el-button size="small" text @click="openEditGrade(data.raw)">编辑</el-button>
                <el-button size="small" text type="danger" @click="deleteGrade(data.id)">删除</el-button>
              </template>
              <template v-else>
                <el-button size="small" text @click="openEditClass(data.raw)">编辑</el-button>
                <el-button size="small" text type="danger" @click="deleteClass(data.id)">删除</el-button>
              </template>
            </div>
          </div>
        </template>
      </el-tree>
      <el-empty v-if="!loading && treeData.length === 0" description="暂无数据，请添加年级" />
    </el-card>

    <el-dialog v-model="gradeDialog" :title="editingGradeId ? '编辑年级' : '添加年级'" width="400px">
      <el-form :model="gradeForm" label-width="80px">
        <el-form-item label="年级名称">
          <el-input v-model="gradeForm.name" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="gradeForm.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="gradeDialog = false">取消</el-button>
        <el-button type="primary" @click="saveGrade">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="classDialog" :title="editingClassId ? '编辑班级' : '添加班级'" width="400px">
      <el-form :model="classForm" label-width="80px">
        <el-form-item label="班级名称">
          <el-input v-model="classForm.name" />
        </el-form-item>
        <el-form-item label="所属年级">
          <el-select v-model="classForm.grade_id" filterable>
            <el-option v-for="g in grades" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="classDialog = false">取消</el-button>
        <el-button type="primary" @click="saveClass">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
