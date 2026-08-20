<script setup lang="ts">
import { ref, onMounted } from "vue"
import { authApi, userApi } from "@/api"
import type { UserInfo } from "@/types"
import { ElMessage, ElMessageBox, ElTag, ElButton, ElDialog, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElTable, ElTableColumn, ElCard, ElSwitch } from "element-plus"

const users = ref<UserInfo[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref("")
const form = ref({ username: "", display_name: "", password: "", role: "teacher" })

async function loadUsers() {
  loading.value = true
  try {
    const res = await userApi.list()
    users.value = res.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = ""
  form.value = { username: "", display_name: "", password: "", role: "teacher" }
  dialogVisible.value = true
}

function openEdit(row: Record<string, any>) {
  editingId.value = row.id
  form.value = { username: row.username, display_name: row.display_name, password: "", role: row.role }
  dialogVisible.value = true
}

async function save() {
  if (editingId.value) {
    const data: any = { username: form.value.username, display_name: form.value.display_name, role: form.value.role }
    if (form.value.password) data.password = form.value.password
    await userApi.update(editingId.value, data)
    ElMessage.success("更新成功")
  } else {
    await authApi.register({ username: form.value.username, password: form.value.password, display_name: form.value.display_name, role: form.value.role })
    ElMessage.success("添加成功")
  }
  dialogVisible.value = false
  await loadUsers()
}

async function remove(id: string) {
  await ElMessageBox.confirm("确定删除该用户？")
  await userApi.delete(id)
  ElMessage.success("已删除")
  await loadUsers()
}

function getRoleTag(role: string) {
  return role === "admin" ? "danger" : role === "teacher" ? "warning" : "info"
}

function formatDate(d: string) { return d ? d.slice(0, 10) + ' ' + d.slice(11, 19) : '-' }

async function toggleActive(row: UserInfo) {
  await userApi.update(row.id, { is_active: !row.is_active })
  ElMessage.success(row.is_active ? '已禁用' : '已启用')
  await loadUsers()
}

onMounted(loadUsers)
</script>

<template>
  <div>
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span style="font-weight: 600">用户管理</span>
          <el-button type="primary" @click="openCreate">添加用户</el-button>
        </div>
      </template>
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="display_name" label="显示名称" width="150" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleTag(row.role)" size="small">
              {{ row.role === "admin" ? "管理员" : row.role === "teacher" ? "教师" : "学生" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? "启用" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="首次修改密码" width="100">
          <template #default="{ row }">
            <el-tag :type="row.needs_password_change ? 'warning' : 'success'" size="small">
              {{ row.needs_password_change ? "待修改" : "已修改" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑用户' : '添加用户'" width="450px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="form.display_name" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" :placeholder="editingId ? '留空则不修改' : '必填'" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role">
            <el-option label="管理员" value="admin" />
            <el-option label="教师" value="teacher" />
            <el-option label="学生" value="student" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>


