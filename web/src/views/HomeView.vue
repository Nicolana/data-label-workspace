<template>
  <div>
    <ConversationList 
      :conversations="conversations" 
      @select="handleSelectConversation"
      @create="showCreateDialog"
      @delete="handleDeleteConversation"
      @export="handleExportConversation"
      @batch-export="handleBatchExportSelected"
      @copy="handleCopyConversation"
      @generate-success="handleGenerateSuccess"
    />
    
    <div class="empty-placeholder">
      <el-empty 
        description="请选择或创建一个对话" 
        :image-size="200"
      >
        <el-button type="primary" @click="showCreateDialog">创建新对话</el-button>
      </el-empty>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="70%">
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import ConversationList from '../components/ConversationList.vue'
import ConversationForm from '../components/ConversationForm.vue'
import { conversationApi } from '../api/conversation'
const router = useRouter()
const conversations = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('')
const editingConversation = ref(null)
const isEditing = ref(false)

const fetchConversations = async () => {
  try {
    const response = await conversationApi.getConversations()
    conversations.value = response.data;
  } catch (error) {
    console.error('获取对话列表失败:', error)
    ElMessage.error('获取对话列表失败')
  }
}

const handleSelectConversation = (id) => {
  router.push(`/conversation/${id}`)
}

const showCreateDialog = () => {
  dialogTitle.value = '创建新对话'
  editingConversation.value = {
    title: '',
    messages: [
      { role: 'system', content: '你是Spotter Gmesh项目的一个前端开发辅助，你会接收用户给出的任务，来帮助他完成代码编写' },
      { role: 'user', content: '' },
      { role: 'assistant', content: '' }
    ]
  }
  isEditing.value = false
  dialogVisible.value = true
}

const handleFormSubmit = async (formData) => {
  try {
    if (isEditing.value) {
      await conversationApi.updateConversation(formData.id, formData)
      ElMessage.success('对话已更新')
    } else {
      await conversationApi.createConversation(formData)
      ElMessage.success('对话已创建')
    }
    dialogVisible.value = false
    await fetchConversations()
  } catch (error) {
    console.error('保存对话失败:', error)
    ElMessage.error('保存对话失败')
  }
}

const handleDeleteConversation = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？此操作不可恢复', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await conversationApi.deleteConversation(id)
    ElMessage.success('对话已删除')
    await fetchConversations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除对话失败:', error)
      ElMessage.error('删除对话失败')
    }
  }
}

const handleExportConversation = async (id) => {
  try {
    const response = await conversationApi.getConversation(id)
    const data = response.data
    const jsonlContent = JSON.stringify(data)
    downloadAsFile(jsonlContent, `conversation_${id}.jsonl`)
    ElMessage.success('对话已导出')
  } catch (error) {
    console.error('导出对话失败:', error)
    ElMessage.error('导出对话失败')
  }
}

const handleBatchExportSelected = async (ids) => {
  if (!ids || ids.length === 0) {
    ElMessage.warning('请至少选择一个对话')
    return
  }
  
  try {
    await exportMultipleConversations(ids)
  } catch (error) {
    console.error('批量导出失败:', error)
    ElMessage.error('批量导出失败')
  }
}

const exportMultipleConversations = async (ids) => {
  try {
    ElMessage.info({
      message: '正在准备导出数据...',
      duration: 0
    })
    
    const exportPromises = ids.map(id => 
      conversationApi.getConversation(id)
    )
    
    const responses = await Promise.all(exportPromises)
    const allData = responses.map(response => response.data)
    
    const jsonlContent = allData.map(data => JSON.stringify(data)).join('\n')
    downloadAsFile(jsonlContent, `conversations_batch_${new Date().getTime()}.jsonl`)
    
    ElMessage.closeAll()
    ElMessage.success(`成功导出 ${ids.length} 个对话`)
  } catch (error) {
    ElMessage.closeAll()
    throw error
  }
}

const downloadAsFile = (content, filename) => {
  const blob = new Blob([content], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const handleCopyConversation = async (conversationId) => {
  try {
    await conversationApi.copyConversation(conversationId)
    await fetchConversations()
    ElMessage.success('对话复制成功')
  } catch (error) {
    console.error('复制对话失败:', error)
    ElMessage.error('复制对话失败')
  }
}

const handleGenerateSuccess = async (conversation) => {
  await fetchConversations()
  router.push(`/conversation/${conversation.id}`)
}

onMounted(() => {
  fetchConversations()
})
</script>

<style scoped>
.empty-placeholder {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style> 