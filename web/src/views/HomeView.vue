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
    
    <ConversationDetail 
      v-if="selectedConversation" 
      :conversation="selectedConversation" 
      @save="handleSaveConversation"
      @export="handleExportConversation"
    />
    <div v-else class="empty-placeholder">
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

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import ConversationList from '../components/ConversationList.vue'
import ConversationDetail from '../components/ConversationDetail.vue'
import ConversationForm from '../components/ConversationForm.vue'

export default {
  name: 'HomeView',
  components: {
    ConversationList,
    ConversationDetail,
    ConversationForm
  },
  setup() {
    const conversations = ref([])
    const selectedConversation = ref(null)
    const dialogVisible = ref(false)
    const dialogTitle = ref('')
    const editingConversation = ref(null)
    const isEditing = ref(false)

    const API_URL = 'http://localhost:8000'

    const fetchConversations = async () => {
      try {
        const response = await axios.get(`${API_URL}/conversations`)
        conversations.value = response.data
      } catch (error) {
        console.error('Error fetching conversations:', error)
        ElMessage.error('获取对话列表失败')
      }
    }

    const handleSelectConversation = async (id) => {
      try {
        const response = await axios.get(`${API_URL}/conversations/${id}`)
        selectedConversation.value = response.data
      } catch (error) {
        console.error('Error fetching conversation:', error)
        ElMessage.error('获取对话详情失败')
      }
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

    const showEditDialog = (conversation) => {
      dialogTitle.value = '编辑对话'
      editingConversation.value = JSON.parse(JSON.stringify(conversation))
      isEditing.value = true
      dialogVisible.value = true
    }

    const handleFormSubmit = async (formData) => {
      try {
        if (isEditing.value) {
          await axios.put(`${API_URL}/conversations/${formData.id}`, formData)
          ElMessage.success('对话已更新')
        } else {
          await axios.post(`${API_URL}/conversations`, formData)
          ElMessage.success('对话已创建')
        }
        dialogVisible.value = false
        fetchConversations()
        if (isEditing.value && selectedConversation.value && selectedConversation.value.id === formData.id) {
          handleSelectConversation(formData.id)
        }
      } catch (error) {
        console.error('Error saving conversation:', error)
        ElMessage.error('保存对话失败')
      }
    }

    const handleSaveConversation = (conversation) => {
      showEditDialog(conversation)
    }

    const handleDeleteConversation = async (id) => {
      try {
        await ElMessageBox.confirm('确定要删除这个对话吗？此操作不可恢复', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await axios.delete(`${API_URL}/conversations/${id}`)
        if (selectedConversation.value && selectedConversation.value.id === id) {
          selectedConversation.value = null
        }
        ElMessage.success('对话已删除')
        fetchConversations()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Error deleting conversation:', error)
          ElMessage.error('删除对话失败')
        }
      }
    }

    const handleExportConversation = async (id) => {
      try {
        const response = await axios.get(`${API_URL}/conversations/${id}/export`)
        const data = response.data
        const jsonlContent = JSON.stringify(data)
        downloadAsFile(jsonlContent, `conversation_${id}.jsonl`)
        ElMessage.success('对话已导出')
      } catch (error) {
        console.error('Error exporting conversation:', error)
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
          axios.get(`${API_URL}/conversations/${id}/export`)
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
        const response = await axios.post(`${API_URL}/conversations/${conversationId}/copy`)
        await fetchConversations()
        ElMessage.success('对话复制成功')
      } catch (error) {
        console.error('复制对话失败:', error)
        ElMessage.error('复制对话失败')
      }
    }

    const handleGenerateSuccess = async (conversation) => {
      await fetchConversations()
      selectedConversation.value = conversation
    }

    onMounted(() => {
      fetchConversations()
    })

    return {
      conversations,
      selectedConversation,
      dialogVisible,
      dialogTitle,
      editingConversation,
      handleSelectConversation,
      showCreateDialog,
      handleFormSubmit,
      handleSaveConversation,
      handleDeleteConversation,
      handleExportConversation,
      handleBatchExportSelected,
      handleCopyConversation,
      handleGenerateSuccess
    }
  }
}
</script>

<style scoped>
.empty-placeholder {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style> 