<template>
  <div class="chat-container">
    <!-- 左侧聊天列表 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" @click="handleNewChat">
          <el-icon><Plus /></el-icon>新建对话
        </el-button>
      </div>
      <div class="chat-list">
        <div
          v-for="chat in chatList"
          :key="chat.id"
          class="chat-item"
          :class="{ active: currentChat?.id === chat.id }"
          @click="handleSelectChat(chat)"
        >
          <div class="chat-item-content">
            <el-icon><ChatDotRound /></el-icon>
            <span class="chat-title">{{ chat.title }}</span>
          </div>
          <div class="chat-item-actions">
            <el-tooltip content="保存为训练数据" placement="top">
              <el-button
                type="text"
                size="small"
                :icon="DocumentAdd"
                class="chat-item-action-button"
                @click.stop="handleSaveAsTraining(chat)"
              >
              </el-button>
            </el-tooltip>
            <el-button
              type="text"
              size="small"
              :icon="Delete"
              class="chat-item-action-button"
              @click.stop="handleDeleteChat(chat)"
            >
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="chat-main">
      <template v-if="currentChat">
        <!-- 消息列表 -->
        <div class="message-list" ref="messageList">
          <div
            v-for="message in messages"
            :key="message.id"
            class="message-item"
            :class="message.role"
          >
            <div class="message-avatar">
              <el-avatar :size="40">
                {{ message.role === 'user' ? 'U' : 'AI' }}
              </el-avatar>
            </div>
            <div class="message-content">
              <div class="message-role">{{ message.role === 'user' ? '用户' : 'AI' }}</div>
              <div class="message-text">
                <MdPreview :modelValue="message.content" />
              </div>
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="input-wrapper">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="输入消息，按 Enter 发送，Shift + Enter 换行"
              @keydown.enter.prevent="handleSendMessage"
              :disabled="isLoading"
            />
            <el-button
              type="primary"
              :icon="isLoading ? 'Loading' : 'Send'"
              :loading="isLoading"
              @click="handleSendMessage"
              :disabled="!inputMessage.trim() || isLoading"
            >
              发送
            </el-button>
          </div>
        </div>
      </template>
      <div v-else class="empty-state">
        <el-empty description="请选择或创建一个对话" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ChatDotRound, Delete, DocumentAdd } from '@element-plus/icons-vue'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'
import axios from 'axios'

// 状态
const chatList = ref([])
const currentChat = ref(null)
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messageList = ref(null)

// 获取聊天列表
const fetchChatList = async () => {
  try {
    const response = await axios.get('/api/chat-conversations')
    chatList.value = response.data
  } catch (error) {
    ElMessage.error('获取聊天列表失败')
  }
}

// 获取消息列表
const fetchMessages = async (conversationId) => {
  try {
    const response = await axios.get(`/api/chat-messages/${conversationId}`)
    messages.value = response.data
    await nextTick()
    scrollToBottom()
  } catch (error) {
    ElMessage.error('获取消息列表失败')
  }
}

// 创建新对话
const handleNewChat = async () => {
  try {
    const response = await axios.post('/api/chat-conversations', {
      title: `新对话 ${new Date().toLocaleString()}`
    })
    chatList.value.unshift(response.data)
    currentChat.value = response.data
    messages.value = []
  } catch (error) {
    ElMessage.error('创建对话失败')
  }
}

// 选择对话
const handleSelectChat = async (chat) => {
  currentChat.value = chat
  await fetchMessages(chat.id)
}

// 删除对话
const handleDeleteChat = async (chat) => {
  try {
    await axios.delete(`/api/chat-conversations/${chat.id}`)
    chatList.value = chatList.value.filter(c => c.id !== chat.id)
    if (currentChat.value?.id === chat.id) {
      currentChat.value = null
      messages.value = []
    }
    ElMessage.success('删除成功')
  } catch (error) {
    ElMessage.error('删除对话失败')
  }
}

// 保存为训练数据对话
const handleSaveAsTraining = async (chat) => {
  try {
    // 获取完整的对话消息
    const response = await axios.get(`/api/chat-messages/${chat.id}`)
    const messages = response.data

    // 创建训练数据对话
    await axios.post('/api/conversations', {
      title: `训练数据 - ${chat.title}`,
      messages: messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))
    })

    ElMessage.success('已保存为训练数据对话')
  } catch (error) {
    console.error('保存训练数据失败:', error)
    ElMessage.error('保存训练数据失败')
  }
}

const handleSendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const message = inputMessage.value.trim()
  inputMessage.value = ''
  isLoading.value = true

  try {
    // 添加用户消息
    const userMessage = {
      conversation_id: currentChat.value.id,
      role: 'user',
      content: message
    }

    // 添加用户消息
    await axios.post('/api/chat-messages', userMessage)


    messages.value.push({
      ...userMessage,
      created_at: new Date().toISOString()
    })

    // 调用 AI 接口
    const response = await fetch('/api/complete', {
      method: 'POST',
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: messages.value.map(msg => ({
          role: msg.role,
          content: msg.content
        }))
      })
    })

    if (!response.body) {
      throw new Error('服务器未返回流式响应')
    }

    // ✅ 正确获取流式数据
    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    let aiResponse = ''
    let assistantMessage = null

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value, { stream: true })
      console.log("text = ", text)

      const lines = text.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.content) {
              aiResponse += data.content

              // ✅ 确保只有一条 `assistant` 消息，而不是每次都 `push`
              if (!assistantMessage) {
                assistantMessage = {
                  conversation_id: currentChat.value.id,
                  role: 'assistant',
                  content: '',
                  created_at: new Date().toISOString()
                }
                messages.value.push(assistantMessage)
              }

              assistantMessage.content = aiResponse
              await nextTick()
              scrollToBottom()
            }
          } catch (err) {
            console.warn("解析 JSON 失败: ", line, err)
          }
        }
      }
    }

    await axios.post('/api/chat-messages', assistantMessage)
  } catch (error) {
    console.error('流式读取失败: ', error)
    ElMessage.error('发送消息失败')
  } finally {
    isLoading.value = false
  }
}


// 滚动到底部
const scrollToBottom = () => {
  if (messageList.value) {
    messageList.value.scrollTop = messageList.value.scrollHeight
  }
}

// 格式化时间
const formatTime = (time) => {
  return new Date(time).toLocaleString()
}

// 初始化
onMounted(() => {
  fetchChatList()
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 60px);
  background-color: #f5f5f5;
}

.chat-sidebar {
  width: 300px;
  background-color: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.chat-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.chat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.chat-item:hover {
  background-color: #f5f5f5;
}

.chat-item.active {
  background-color: #ecf5ff;
}

.chat-item-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  overflow: hidden;
}

.chat-title {
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-item-actions {
  opacity: 0;
  transition: opacity 0.3s;
  display: flex;
  align-items: center;
  gap: 4px;
}


.chat-item-action-button {
  margin-left: 0!important;
  padding: 0!important;
}

.chat-item:hover .chat-item-actions {
  opacity: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #fff;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message-item {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 80%;
  background-color: #fff;
  padding: 12px 16px;
  border-radius: 8px;
  position: relative;
  box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
}


.message-role {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.message-text {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  text-align: right;
}

.input-area {
  padding: 20px;
  border-top: 1px solid #e0e0e0;
  background-color: #fff;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #f5f5f5;
}
</style> 