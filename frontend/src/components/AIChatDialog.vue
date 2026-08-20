<script setup lang="ts">
import { ref, watch } from "vue"
import { ElMessage } from "element-plus"

const props = defineProps<{
  visible: boolean
  contextType?: string
  contextId?: string
  contextLabel?: string
}>()

const emit = defineEmits(["update:visible"])

const messages = ref<Array<{ role: string; content: string }>>([
      { role: "ai", content: `你好！当前正在查看"${props.contextLabel}"。我可以帮你深入分析这些数据、优化报告内容，或者回答你的任何问题。` }
])
const inputMessage = ref("")
const sending = ref(false)
const chatRef = ref<HTMLElement | null>(null)
const sessionId = ref("")

function close() {
  emit("update:visible", false)
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
}

function renderMessage(text: string): string {
  // First escape HTML to prevent XSS, then apply safe formatting
  return escapeHtml(text)
    .replace(/\n/g, "<br/>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
}

async function send() {
  if (!inputMessage.value.trim()) return
  const msg = inputMessage.value.trim()
  messages.value.push({ role: "user", content: msg })
  inputMessage.value = ""
  sending.value = true

  try {
    const token = localStorage.getItem("token") || ""
    const res = await fetch("/api/v1/analysis/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token},
      body: JSON.stringify({
        message: msg,
        context_type: props.contextType || "general",
        context_id: props.contextId || null,
        session_id: sessionId.value || null,
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || "请求失败")
    messages.value.push({ role: "ai", content: data.response })
    if (data.session_id) { sessionId.value = data.session_id }
  } catch (err: any) {
    messages.value.push({ role: "ai", content: "抱歉，我暂时无法回答这个问题。请稍后再试。" })
    ElMessage.error("AI 响应失败: " + (err.message || ""))
  } finally {
    sending.value = false
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

// Reset when opened with new context
watch(() => props.visible, (val) => {
  if (val && props.contextLabel) {
    sessionId.value = ""
    messages.value = [
      { role: "ai", content: `你好！当前正在查看"${props.contextLabel}"。我可以帮你深入分析这些数据、优化报告内容，或者回答你的任何问题。` }
    ]
  }
})
</script>

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="(v: boolean) => emit('update:visible', v)"
    title="AI 分析助手"
    width="560px"
    :close-on-click-modal="false"
    class="ai-chat-dialog"
    top="5vh"
  >
    <div class="chat-container">
      <div class="chat-messages" ref="chatRef">
        <div v-for="(m, i) in messages" :key="i" :class="['message', m.role === 'ai' ? 'ai' : 'user']">
          <div class="message-avatar">{{ m.role === "ai" ? "🤖" : "👤" }}</div>
          <div class="message-bubble">
            <div class="message-text" v-html="renderMessage(m.content)"></div>
          </div>
        </div>
        <div v-if="sending" class="message ai">
          <div class="message-avatar">🤖</div>
          <div class="message-bubble">
            <div class="message-text thinking">思考中...</div>
          </div>
        </div>
      </div>
      <div class="chat-input">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入你的问题... (Enter 发送, Shift+Enter 换行)"
          :disabled="sending"
          @keydown="handleKeydown"
        />
        <div style="display: flex; justify-content: flex-end; margin-top: 8px; gap: 8px">
          <el-button size="small" @click="close">关闭</el-button>
          <el-button type="primary" size="small" :loading="sending" @click="send">发送</el-button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 480px;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 12px;
}
.message {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.message.user {
  flex-direction: row-reverse;
}
.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  background: #f0f2f5;
}
.message-bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.6;
}
.message.ai .message-bubble {
  background: #fff;
  border: 1px solid #e4e7ed;
  color: #303133;
}
.message.user .message-bubble {
  background: #409eff;
  color: #fff;
}
.message-text :deep(strong) {
  color: inherit;
}
.thinking {
  color: #909399;
  font-style: italic;
}
</style>

