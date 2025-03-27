<template>
  <div class="chat-container">
    <!-- 左侧聊天列表 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" @click="handleNewChat">
          <el-icon><Plus /></el-icon>
          新对话
        </el-button>
      </div>
      <div class="chat-list">
        <div
          v-for="chat in chatList"
          :key="chat.id"
          class="chat-item"
          :class="{ active: currentConversationId === chat.id }"
          @click="handleSelectChat(chat.id)"
        >
          <div class="chat-item-content">
            <el-icon><ChatDotRound /></el-icon>
            <span class="chat-title">{{ chat.title }}</span>
          </div>
          <div class="chat-item-actions">
            <el-button
              type="text"
              @click.stop="handleDeleteChat(chat.id)"
              :disabled="currentConversationId === chat.id"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="chat-main">
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0 && !isLoading" class="empty-message">
          <el-empty description="开始新的对话" />
        </div>
        <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
          <div class="message-content">
            <MdPreview :modelValue="message.content" />
          </div>
          <div class="message-time">{{ formatTime(message.created_at) }}</div>
        </div>
        <div v-if="isLoading" class="message assistant">
          <div class="message-content">
            <MdPreview :modelValue="currentResponse" />
          </div>
        </div>
      </div>
      <div class="input-container">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="3"
          placeholder="输入消息..."
          @keydown.enter.prevent="handleSend"
          :disabled="isLoading || !currentConversationId"
        />
        <el-button 
          type="primary" 
          @click="handleSend" 
          :loading="isLoading"
          :disabled="!userInput.trim() || isLoading || !currentConversationId"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { MdPreview } from 'md-editor-v3'
import { Plus, ChatDotRound, Delete } from '@element-plus/icons-vue'
import 'md-editor-v3/lib/preview.css'

export default {
  name: 'ChatView',
  components: {
    MdPreview,
    Plus,
    ChatDotRound,
    Delete
  },
  setup() {
    const messages = ref([])
    const userInput = ref('')
    const isLoading = ref(false)
    const currentResponse = ref('')
    const messagesContainer = ref(null)
    const currentConversationId = ref(null)
    const chatList = ref([])
    const API_URL = 'http://localhost:8000'

    // 获取聊天列表
    const fetchChatList = async () => {
      try {
        const response = await axios.get(`${API_URL}/conversations`)
        chatList.value = response.data
      } catch (error) {
        console.error('获取聊天列表失败:', error)
        ElMessage.error('获取聊天列表失败')
      }
    }

    // 创建新对话
    const handleNewChat = async () => {
      try {
        const response = await axios.post(`${API_URL}/conversations`, {
          title: `新对话 ${new Date().toLocaleString()}`,
          messages: []
        })
        currentConversationId.value = response.data.id
        await fetchChatList()
        messages.value = []
      } catch (error) {
        console.error('创建对话失败:', error)
        ElMessage.error('创建对话失败')
      }
    }

    // 选择对话
    const handleSelectChat = async (id) => {
      currentConversationId.value = id
      await fetchMessages(id)
    }

    // 删除对话
    const handleDeleteChat = async (id) => {
      try {
        await ElMessageBox.confirm('确定要删除这个对话吗？此操作不可恢复', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await axios.delete(`${API_URL}/conversations/${id}`)
        if (currentConversationId.value === id) {
          currentConversationId.value = null
          messages.value = []
        }
        await fetchChatList()
        ElMessage.success('对话已删除')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除对话失败:', error)
          ElMessage.error('删除对话失败')
        }
      }
    }

    // 获取历史消息
    const fetchMessages = async (conversationId) => {
      try {
        const response = await axios.get(`${API_URL}/chat-messages/${conversationId}`)
        messages.value = response.data
      } catch (error) {
        console.error('获取消息失败:', error)
        ElMessage.error('获取消息失败')
      }
    }

    // 发送消息
    const handleSend = async () => {
      if (!userInput.value.trim() || isLoading.value || !currentConversationId.value) return

      const content = userInput.value.trim()
      userInput.value = ''
      isLoading.value = true
      currentResponse.value = ''

      try {
        // 保存用户消息
        await axios.post(`${API_URL}/chat-messages`, {
          conversation_id: currentConversationId.value,
          role: 'user',
          content: content
        })

        // 获取历史消息
        const historyResponse = await axios.get(`${API_URL}/chat-messages/${currentConversationId.value}`)
        const history = historyResponse.data.map(msg => ({
          role: msg.role,
          content: msg.content
        }))

        // 调用 AI 接口
        const response = await fetch(`${API_URL}/complete`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            messages: history
          })
        })

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let assistantMessage = ''

        while (true) {
          const { value, done } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = JSON.parse(line.slice(6))
              if (data.content) {
                assistantMessage += data.content
                currentResponse.value = assistantMessage
                await nextTick()
                scrollToBottom()
              } else if (data.error) {
                throw new Error(data.error)
              }
            }
          }
        }

        // 保存 AI 回复
        await axios.post(`${API_URL}/chat-messages`, {
          conversation_id: currentConversationId.value,
          role: 'assistant',
          content: assistantMessage
        })

        // 更新消息列表
        await fetchMessages(currentConversationId.value)
        currentResponse.value = ''
      } catch (error) {
        console.error('发送消息失败:', error)
        ElMessage.error('发送消息失败')
      } finally {
        isLoading.value = false
      }
    }

    // 格式化时间
    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleString()
    }

    // 滚动到底部
    const scrollToBottom = () => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }

    onMounted(async () => {
      await fetchChatList()
    })

    return {
      messages,
      userInput,
      isLoading,
      currentResponse,
      messagesContainer,
      chatList,
      currentConversationId,
      handleNewChat,
      handleSelectChat,
      handleDeleteChat,
      handleSend,
      formatTime,
      scrollToBottom
    }
  }
}
</script>

<style scoped>
.chat-container {
  height: 100%;
  display: flex;
  background-color: #f5f7fa;
}

.chat-sidebar {
  width: 300px;
  background-color: white;
  border-right: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #dcdfe6;
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
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 4px;
}

.chat-item:hover {
  background-color: #f5f7fa;
}

.chat-item.active {
  background-color: #ecf5ff;
  color: #409EFF;
}

.chat-item-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  overflow: hidden;
}

.chat-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-item-actions {
  opacity: 0;
  transition: opacity 0.2s;
}

.chat-item:hover .chat-item-actions {
  opacity: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.empty-message {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.message {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 8px;
  position: relative;
}

.message.user {
  align-self: flex-end;
  background-color: #409EFF;
  color: white;
}

.message.assistant {
  align-self: flex-start;
  background-color: white;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.message-content {
  margin-bottom: 4px;
}

.message-time {
  font-size: 12px;
  color: #909399;
  text-align: right;
}

.input-container {
  padding: 20px;
  background-color: white;
  border-top: 1px solid #dcdfe6;
  display: flex;
  gap: 10px;
}

.input-container .el-input {
  flex: 1;
}

.input-container .el-button {
  align-self: flex-end;
}
</style> 