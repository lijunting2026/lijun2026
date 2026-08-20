<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { subjectApi, knowledgeApi } from "@/api"
import type { Subject, KnowledgePoint } from "@/types"
import { ElMessage, ElMessageBox } from "element-plus"
import { Plus, Edit, Delete } from "@element-plus/icons-vue"

const subjects = ref<Subject[]>([])
const selectedSubjectId = ref("")
const treeData = ref<any[]>([])
const flatList = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref("")
const form = ref({ name: "", description: "", parent_id: "" as string | undefined })
const parentName = ref("")

async function loadSubjects() {
  const r = await subjectApi.list()
  subjects.value = r.data as any
  if (subjects.value.length > 0 && !selectedSubjectId.value) {
    selectedSubjectId.value = subjects.value[0].id
    loadKnowledgePoints()
  }
}

async function loadKnowledgePoints() {
  if (!selectedSubjectId.value) return
  loading.value = true
  try {
    const [treeRes, flatRes] = await Promise.all([
      knowledgeApi.getTree(selectedSubjectId.value),
      knowledgeApi.list(selectedSubjectId.value),
    ])
    treeData.value = treeRes.data
    flatList.value = flatRes.data
  } catch {
    ElMessage.error("加载知识点失败")
  } finally {
    loading.value = false
  }
}

function openCreate(parentId?: string) {
  editingId.value = ""
  form.value = { name: "", description: "", parent_id: parentId }
  const parent = flatList.value.find((k: any) => k.id === parentId)
  parentName.value = parent ? parent.name : "（顶层）"
  dialogVisible.value = true
}

function openEdit(kp: any) {
  editingId.value = kp.id
  form.value = { name: kp.name, description: kp.description, parent_id: kp.parent_id }
  const parent = flatList.value.find((k: any) => k.id === kp.parent_id)
  parentName.value = parent ? parent.name : "（顶层）"
  dialogVisible.value = true
}

async function save() {
  if (!form.value.name) {
    ElMessage.error("请输入知识点名称")
    return
  }
  try {
    if (editingId.value) {
      await knowledgeApi.update(editingId.value, form.value)
      ElMessage.success("更新成功")
    } else {
      await knowledgeApi.create({
        subject_id: selectedSubjectId.value,
        name: form.value.name,
        description: form.value.description,
        parent_id: form.value.parent_id,
      })
      ElMessage.success("创建成功")
    }
    dialogVisible.value = false
    await loadKnowledgePoints()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || "操作失败")
  }
}

async function remove(id: string, name: string) {
  await ElMessageBox.confirm(`确定删除知识点「${name}」及其下级知识点？`)
  await knowledgeApi.delete(id)
  ElMessage.success("已删除")
  await loadKnowledgePoints()
}

function renderTree(nodes: any[], level = 0): any[] {
  const result: any[] = []
  for (const node of nodes) {
    result.push({ ...node, _level: level })
    if (node.children?.length) {
      result.push(...renderTree(node.children, level + 1))
    }
  }
  return result
}

const flatTree = computed(() => renderTree(treeData.value))

onMounted(loadSubjects)
</script>

<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
          <span style="font-weight: 600">知识点库管理</span>
          <div style="display: flex; gap: 8px">
            <el-select
              v-model="selectedSubjectId"
              placeholder="选择科目"
              style="width: 180px"
              @change="loadKnowledgePoints"
            >
              <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
            <el-button type="primary" :icon="Plus" @click="openCreate()" :disabled="!selectedSubjectId">
              添加知识点
            </el-button>
          </div>
        </div>
      </template>

      <el-alert title="知识点按科目分类，可设置层级结构（上级→下级），用于考试命题细目表和知识点分析" type="info" show-icon :closable="false" style="margin-bottom: 12px" />

      <el-table :data="flatTree" v-loading="loading" stripe empty-text="暂无知识点，请先添加">
        <el-table-column label="知识点名称" min-width="300">
          <template #default="{ row }">
            <div :style="{ paddingLeft: row._level * 24 + 'px', display: 'flex', alignItems: 'center', gap: '6px' }">
              <el-icon v-if="row.children?.length" :size="16" color="#E6A23C"><FolderOpened /></el-icon>
              <el-icon v-else :size="14" color="#409EFF"><Document /></el-icon>
              <span :style="{ fontWeight: row._level === 0 ? 600 : 400 }">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :icon="Plus" @click="openCreate(row.id)">添加下级</el-button>
            <el-button size="small" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :icon="Delete" @click="remove(row.id, row.name)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑知识点' : '添加知识点'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="上级知识点">
          <el-input :model-value="parentName" disabled />
        </el-form-item>
        <el-form-item label="知识点名称">
          <el-input v-model="form.name" placeholder="如：函数定义域" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="可选描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
