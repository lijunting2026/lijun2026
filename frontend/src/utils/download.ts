import { ElMessage } from "element-plus"

export async function downloadBlob(url: string, filename: string) {
  const token = localStorage.getItem("token") || ""
  const res = await fetch(url, { headers: { Authorization: "Bearer " + token } })
  if (!res.ok) { ElMessage.error("导出失败"); return }
  const blob = await res.blob()
  const link = document.createElement("a"); link.href = URL.createObjectURL(blob)
  link.download = filename; link.click()
  URL.revokeObjectURL(link.href)
  ElMessage.success("导出成功")
}