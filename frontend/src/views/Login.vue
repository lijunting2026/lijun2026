<script setup lang="ts">
import { ref, watch } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores"
import { ElMessage, ElDialog, ElForm, ElFormItem, ElInput, ElButton } from "element-plus"
import { User, Lock } from "@element-plus/icons-vue"

const router = useRouter()
const auth = useAuthStore()

const form = ref({ username: "admin", password: "" })
const loading = ref(false)

// Force password change dialog
const showChangePwd = ref(false)
const pwdForm = ref({ old_password: "", new_password: "", confirm_password: "" })
const pwdLoading = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    if (auth.needsPasswordChange) {
      showChangePwd.value = true
    } else {
      ElMessage.success("登录成功")
      router.push("/dashboard")
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || "登录失败")
  } finally {
    loading.value = false
  }
}

async function handleChangePassword() {
  if (pwdForm.value.new_password !== pwdForm.value.confirm_password) {
    ElMessage.error("两次输入的新密码不一致")
    return
  }
  if (pwdForm.value.new_password.length < 8) {
    ElMessage.error("新密码至少8位")
    return
  }
  pwdLoading.value = true
  try {
    await auth.changePassword(pwdForm.value.old_password, pwdForm.value.new_password)
    ElMessage.success("密码修改成功")
    showChangePwd.value = false
    router.push("/dashboard")
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || "密码修改失败")
  } finally {
    pwdLoading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="login-title">考试质量分析系统</h2>
      <p class="login-subtitle">请登录您的账户</p>
      <el-form :model="form" @keyup.enter="handleLogin" label-width="0">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" style="width: 100%" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-tip">首次登录请使用 admin / Admin@ChangeMe2026，系统将要求修改密码</div>
    </div>

    <!-- Force Password Change Dialog -->
    <el-dialog v-model="showChangePwd" title="首次登录 - 请修改密码" width="420px" :close-on-click-modal="false" :show-close="false">
      <el-form :model="pwdForm" label-width="80px">
        <el-form-item label="原密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" :loading="pwdLoading" @click="handleChangePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}
.login-title {
  text-align: center;
  margin: 0 0 4px;
  font-size: 24px;
  color: #303133;
}
.login-subtitle {
  text-align: center;
  margin: 0 0 24px;
  color: #909399;
  font-size: 14px;
}
.login-tip {
  text-align: center;
  color: #c0c4cc;
  font-size: 12px;
}
</style>