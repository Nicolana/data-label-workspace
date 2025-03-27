<template>
  <div class="chat-container">
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
        <div class="message-avatar">
          <el-avatar :size="40" :icon="message.role === 'user' ? User : ChatDotRound" />
        </div>
        <div class="message-content">
          <div class="message-text" v-html="formatMarkdown(message.content)"></div>
          <div class="message-time">{{ formatTime(message.timestamp) }}</div>
        </div>
      </div>
      <div v-if="isGenerating" class="message assistant">
        <div class="message-avatar">
          <el-avatar :size="40" :icon="ChatDotRound" />
        </div>
        <div class="message-content">
          <div class="message-text" v-html="formatMarkdown(generatedContent)"></div>
          <div class="message-time">正在输入...</div>
        </div>
      </div>
    </div>
    
    <div class="chat-input">
      <el-input
        v-model="userInput"
        type="textarea"
        :rows="3"
        placeholder="输入消息，按 Enter 发送，Shift + Enter 换行"
        @keydown.enter.prevent="handleEnter"
        :disabled="isGenerating"
        ref="inputRef"
      />
      <el-button 
        type="primary" 
        @click="sendMessage" 
        :loading="isGenerating"
        :disabled="!userInput.trim() || isGenerating"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { User, ChatDotRound } from '@element-plus/icons-vue'
import { marked } from 'marked'
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
  name: 'ChatView',
  components: {
    User,
    ChatDotRound
  },
  setup() {
    const messages = ref([])
    const userInput = ref('')
    const isGenerating = ref(false)
    const generatedContent = ref('')
    const messagesContainer = ref(null)
    const inputRef = ref(null)

    const formatMarkdown = (content) => {
      return marked(content)
    }

    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString()
    }

    const scrollToBottom = async () => {
      await nextTick()
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }

    const handleEnter = (event) => {
      if (event.shiftKey) {
        return
      }
      sendMessage()
    }

    const sendMessage = async () => {
      if (!userInput.value.trim() || isGenerating.value) return

      const userMessage = {
        role: 'user',
        content: userInput.value,
        timestamp: new Date().toISOString()
      }
      messages.value.push(userMessage)
      const currentInput = userInput.value
      userInput.value = ''
      isGenerating.value = true
      generatedContent.value = ''

      try {
        const response = await fetch('http://localhost:8000/generate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            prompt: currentInput,
            system_prompt: '你是一个专业的AI助手，请用简洁专业的语言回答用户的问题。',
            max_tokens: 4000,
            temperature: 0.7,
            stream: true
          })
        })

        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') {
                messages.value.push({
                  role: 'assistant',
                  content: generatedContent.value,
                  timestamp: new Date().toISOString()
                })
                isGenerating.value = false
                break
              }

              try {
                const parsed = JSON.parse(data)
                if (parsed.error) {
                  throw new Error(parsed.error)
                }
                if (parsed.content) {
                  generatedContent.value += parsed.content
                  await scrollToBottom()
                }
              } catch (e) {
                console.error('解析响应失败:', e)
                ElMessage.error('生成失败')
                isGenerating.value = false
                break
              }
            }
          }
        }
      } catch (error) {
        console.error('发送消息失败:', error)
        ElMessage.error(error.message || '发送失败')
        isGenerating.value = false
      }
    }

    onMounted(() => {
      inputRef.value?.focus()
    })

    return {
      messages,
      userInput,
      isGenerating,
      generatedContent,
      messagesContainer,
      inputRef,
      formatMarkdown,
      formatTime,
      handleEnter,
      sendMessage
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-content {
  background-color: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.message.user .message-content {
  background-color: #409eff;
  color: white;
}

.message-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.message-text :deep(p) {
  margin: 0;
}

.message-text :deep(code) {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}

.message.user .message-text :deep(code) {
  background-color: rgba(255, 255, 255, 0.2);
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  text-align: right;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.chat-input {
  padding: 20px;
  background-color: white;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-input :deep(.el-textarea__inner) {
  resize: none;
  padding: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.chat-input .el-button {
  height: 40px;
  padding: 0 20px;
}
</style> 