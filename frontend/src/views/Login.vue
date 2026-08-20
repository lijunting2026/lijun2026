<script setup lang="ts">
import { ref, computed } from "vue"
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

// Password strength calculation
function calcStrength(pwd: string): { strength: string; color: string; text: string } {
  if (!pwd) return { strength: "", color: "", text: "" }
  if (pwd.length < 8) return { strength: "weak", color: "#F56C6C", text: "太短" }
  let score = 0
  if (/[A-Z]/.test(pwd)) score++
  if (/[a-z]/.test(pwd)) score++
  if (/\d/.test(pwd)) score++
  if (/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/;'`~]/.test(pwd)) score++
  if (score <= 1) return { strength: "weak", color: "#F56C6C", text: "弱" }
  if (score <= 2) return { strength: "medium", color: "#E6A23C", text: "中" }
  return { strength: "strong", color: "#67C23A", text: "强" }
}

const pwdStrength = computed(() => calcStrength(pwdForm.value.new_password))

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
  const s = calcStrength(pwdForm.value.new_password)
  if (!s.strength || s.strength === "weak") {
    ElMessage.error("密码强度太弱，需包含大写字母、小写字母、数字和特殊字符")
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
          <div v-if="pwdStrength.text" style="margin-top: 4px; display: flex; align-items: center; gap: 6px;">
            <div style="flex: 1; height: 4px; background: #eee; border-radius: 2px; overflow: hidden;">
              <div :style="`width: ${pwdStrength.strength === 'weak' ? '33%' : pwdStrength.strength === 'medium' ? '66%' : '100%'}; height: 100%; background: ${pwdStrength.color}; border-radius: 2px; transition: all 0.3s;`"></div>
            </div>
            <span :style="{ color: pwdStrength.color, fontSize: '12px', fontWeight: 600 }">{{ pwdStrength.text }}</span>
          </div>
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
