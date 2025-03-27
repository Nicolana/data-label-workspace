<template>
  <div class="chat-container">
    <div class="messages-container" ref="messagesContainer">
      <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
        <div class="message-content">
          <MdEditor v-model="message.content" :preview-only="true" />
        </div>
        <div class="message-time">{{ formatTime(message.created_at) }}</div>
      </div>
      <div v-if="isLoading" class="message assistant">
        <div class="message-content">
          <MdEditor v-model="currentResponse" :preview-only="true" />
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
        :disabled="isLoading"
      />
      <el-button 
        type="primary" 
        @click="handleSend" 
        :loading="isLoading"
        :disabled="!userInput.trim() || isLoading"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'ChatView',
  setup() {
    const messages = ref([])
    const userInput = ref('')
    const isLoading = ref(false)
    const currentResponse = ref('')
    const messagesContainer = ref(null)
    const currentConversationId = ref(null)
    const API_URL = 'http://localhost:8000'

    // 创建新对话
    const createConversation = async () => {
      try {
        const response = await axios.post(`${API_URL}/conversations`, {
          title: `新对话 ${new Date().toLocaleString()}`,
          messages: []
        })
        currentConversationId.value = response.data.id
        return response.data.id
      } catch (error) {
        console.error('创建对话失败:', error)
        ElMessage.error('创建对话失败')
        throw error
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
      if (!userInput.value.trim() || isLoading.value) return

      const content = userInput.value.trim()
      userInput.value = ''
      isLoading.value = true
      currentResponse.value = ''

      try {
        // 如果没有对话，创建一个新对话
        if (!currentConversationId.value) {
          await createConversation()
        }

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
      // 创建新对话
      await createConversation()
    })

    return {
      messages,
      userInput,
      isLoading,
      currentResponse,
      messagesContainer,
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
  flex-direction: column;
  background-color: #f5f7fa;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
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