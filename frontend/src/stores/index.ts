import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { authApi } from "@/api"
import type { UserInfo } from "@/types"

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("token") || "")
  const user = ref<UserInfo | null>(JSON.parse(localStorage.getItem("user") || "null"))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === "admin")
  const displayName = computed(() => user.value?.display_name || "")

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem("token", res.data.access_token)
    localStorage.setItem("user", JSON.stringify(res.data.user))
  }

  function logout() {
    token.value = ""
    user.value = null
    localStorage.removeItem("token")
    localStorage.removeItem("user")
  }

  return { token, user, isLoggedIn, isAdmin, displayName, login, logout }
})
