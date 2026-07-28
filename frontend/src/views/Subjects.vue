<script setup lang="ts">
import { ref, onMounted } from "vue"
import { subjectApi } from "@/api"
import type { Subject } from "@/types"
import { ElMessage, ElMessageBox } from "element-plus"

const subjects = ref<Subject[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref("")
const form = ref({ name: "", full_score: 100, sort_order: 0 })

async function loadSubjects() {
  loading.value = true
  try {
    const res = await subjectApi.list()
    subjects.value = res.data as any
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = ""
  form.value = { name: "", full_score: 100, sort_order: 0 }
  dialogVisible.value = true
}

function openEdit(row: Subject) {
  editingId.value = row.id
  form.value = { name: row.name, full_score: row.full_score, sort_order: row.sort_order }
  dialogVisible.value = true
}

async function save() {
  try {
    if (editingId.value) {
      await subjectApi.update(editingId.value, form.value)
      ElMessage.success("更新成功")
    } else {
      await subjectApi.create(form.value)
      ElMessage.success("添加成功")
    }
    dialogVisible.value = false
    await loadSubjects()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || "操作失败")
  }
}

async function remove(id: string) {
  try {
    await ElMessageBox.confirm("确定删除该科目？")
    await subjectApi.delete(id)
    ElMessage.success("已删除")
    await loadSubjects()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.detail || err.message || "删除失败")
    }
  }
}

onMounted(loadSubjects)
</script>

<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>科目管理</span>
          <el-button type="primary" size="small" @click="openCreate">添加科目</el-button>
        </div>
      </template>
      <el-table :data="subjects" v-loading="loading" stripe>
        <el-table-column prop="name" label="科目名称" />
        <el-table-column prop="full_score" label="满分" width="100" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑科目' : '添加科目'" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="科目名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="满分">
          <el-input-number v-model="form.full_score" :min="1" :max="300" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

