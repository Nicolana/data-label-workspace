<template>
  <div class="conversation-detail-view">
    <div class="detail-header">
      <div class="header-left">
        <el-button @click="$router.push('/')" :icon="ArrowLeft">返回</el-button>
        <h2>
          <el-icon><Document /></el-icon>
          {{ conversation.title }}
        </h2>
      </div>
      <div class="action-buttons">
        <el-button type="primary" @click="handleEdit" :icon="EditPen">编辑</el-button>
        <el-button type="success" @click="handleExport" :icon="Download">导出JSONL</el-button>
        <el-button type="danger" @click="handleDelete" :icon="Delete">删除</el-button>
      </div>
    </div>
    
    <el-scrollbar height="calc(100vh - 180px)" class="message-scrollbar">
      <div class="message-container">
        <div v-for="(message, index) in conversation.messages" :key="index" 
             :class="['message-item', getMessageClass(message.role)]">
          <div class="message-header">
            <el-avatar :size="32" :icon="getAvatarIcon(message.role)" :class="getRoleColorClass(message.role)"></el-avatar>
            <div class="message-role">{{ getRoleName(message.role) }}</div>
          </div>
          <div class="message-bubble">
            <div class="message-content">
              <MdPreview :modelValue="message.content" previewTheme="vuepress" :codeFoldable="false" />
            </div>
          </div>
        </div>
      </div>
    </el-scrollbar>

    <!-- 编辑对话框 -->
    <el-dialog v-model="dialogVisible" title="编辑对话" width="70%">
      <ConversationForm 
        ref="conversationForm"
        :conversation="editingConversation"
        @submit="handleFormSubmit"
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="$refs.conversationForm.submit()">
            确认
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, User, Service, ChatDotRound, EditPen, Download, Delete, ArrowLeft } from '@element-plus/icons-vue'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'
import ConversationForm from '../components/ConversationForm.vue'
import { conversationApi } from '../api/conversation'

const route = useRoute()
const router = useRouter()
const conversation = ref({})
const dialogVisible = ref(false)
const editingConversation = ref(null)

// 获取对话详情
const fetchConversation = async () => {
  try {
    const response = await conversationApi.getConversation(route.params.id)
    conversation.value = response.data
    console.log("conversation = ", conversation.value)
  } catch (error) {
    console.error('获取对话详情失败:', error)
    ElMessage.error('获取对话详情失败')
    router.push('/')
  }
}

// 编辑对话
const handleEdit = () => {
  editingConversation.value = JSON.parse(JSON.stringify(conversation.value))
  dialogVisible.value = true
}

// 导出对话
const handleExport = async () => {
  try {
    const response = await conversationApi.getConversation(route.params.id)
    const data = response.data
    const jsonlContent = JSON.stringify(data)
    downloadAsFile(jsonlContent, `conversation_${route.params.id}.jsonl`)
    ElMessage.success('对话已导出')
  } catch (error) {
    console.error('导出对话失败:', error)
    ElMessage.error('导出对话失败')
  }
}

// 删除对话
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？此操作不可恢复', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await conversationApi.deleteConversation(route.params.id)
    ElMessage.success('对话已删除')
    router.push('/')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除对话失败:', error)
      ElMessage.error('删除对话失败')
    }
  }
}

// 表单提交
const handleFormSubmit = async (formData) => {
  try {
    await conversationApi.updateConversation(formData.id, formData)
    ElMessage.success('对话已更新')
    dialogVisible.value = false
    await fetchConversation()
  } catch (error) {
    console.error('保存对话失败:', error)
    ElMessage.error('保存对话失败')
  }
}

// 下载文件
const downloadAsFile = (content, filename) => {
  const blob = new Blob([content], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// 消息样式相关方法
const getMessageClass = (role) => {
  return role === 'assistant' ? 'message-assistant' : 'message-other'
}

const getAvatarIcon = (role) => {
  switch (role) {
    case 'system': return Service
    case 'user': return User
    case 'assistant': return ChatDotRound
    default: return User
  }
}

const getRoleColorClass = (role) => {
  switch (role) {
    case 'system': return 'avatar-system'
    case 'user': return 'avatar-user'
    case 'assistant': return 'avatar-assistant'
    default: return 'avatar-user'
  }
}

const getRoleName = (role) => {
  const roleNames = {
    system: '系统',
    user: '用户',
    assistant: '助手'
  }
  return roleNames[role] || role
}

onMounted(() => {
  fetchConversation()
})
</script>

<style scoped>
.conversation-detail-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.detail-header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: #303133;
}

.message-scrollbar {
  flex: 1;
}

.message-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px 0;
}

.message-item {
  display: flex;
  flex-direction: column;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.message-role {
  font-weight: bold;
  font-size: 14px;
}

.message-bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message-content {
  line-height: 1.6;
  word-break: break-word;
}

/* 角色颜色 */
.avatar-system {
  background-color: #909399 !important;
}
.avatar-user {
  background-color: #e6a23c !important;
}
.avatar-assistant {
  background-color: #67c23a !important;
}

/* 消息气泡样式 */
.message-other .message-bubble {
  align-self: flex-start;
  background-color: #fff;
  border: 1px solid #ebeef5;
}
.message-assistant .message-bubble {
  align-self: flex-end;
  background-color: #fff;
  /* border: 1px solid #d9ecff; */
}
.message-assistant {
  align-items: flex-end;
}
.message-other {
  align-items: flex-start;
}
</style> 