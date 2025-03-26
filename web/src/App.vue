<template>
  <div class="app-container">
    <el-container>
      <el-header>
        <h1>对话微调数据管理平台</h1>
      </el-header>
      <el-container>
        <el-aside width="300px">
          <ConversationList 
            :conversations="conversations" 
            @select="handleSelectConversation"
            @create="showCreateDialog"
            @delete="handleDeleteConversation"
          />
        </el-aside>
        <el-main>
          <ConversationDetail 
            v-if="selectedConversation" 
            :conversation="selectedConversation" 
            @save="handleSaveConversation"
            @export="handleExportConversation"
          />
          <div v-else class="empty-placeholder">
            <el-empty description="请选择或创建一个对话" />
          </div>
        </el-main>
      </el-container>
    </el-container>
    
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="50%">
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
import ConversationList from './components/ConversationList.vue'
import ConversationDetail from './components/ConversationDetail.vue'
import ConversationForm from './components/ConversationForm.vue'

export default {
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
      }
    }

    const handleSelectConversation = async (id) => {
      try {
        const response = await axios.get(`${API_URL}/conversations/${id}`)
        selectedConversation.value = response.data
      } catch (error) {
        console.error('Error fetching conversation:', error)
      }
    }

    const showCreateDialog = () => {
      dialogTitle.value = '创建新对话'
      editingConversation.value = {
        title: '',
        messages: [
          { role: 'system', content: '' },
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
        } else {
          await axios.post(`${API_URL}/conversations`, formData)
        }
        dialogVisible.value = false
        fetchConversations()
        if (isEditing.value && selectedConversation.value && selectedConversation.value.id === formData.id) {
          handleSelectConversation(formData.id)
        }
      } catch (error) {
        console.error('Error saving conversation:', error)
      }
    }

    const handleSaveConversation = (conversation) => {
      showEditDialog(conversation)
    }

    const handleDeleteConversation = async (id) => {
      try {
        await axios.delete(`${API_URL}/conversations/${id}`)
        if (selectedConversation.value && selectedConversation.value.id === id) {
          selectedConversation.value = null
        }
        fetchConversations()
      } catch (error) {
        console.error('Error deleting conversation:', error)
      }
    }

    const handleExportConversation = async (id) => {
      try {
        const response = await axios.get(`${API_URL}/conversations/${id}/export`)
        const data = response.data
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `conversation_${id}.json`
        a.click()
        URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Error exporting conversation:', error)
      }
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
      handleExportConversation
    }
  }
}
</script>

<style>
.app-container {
  height: 100vh;
}
.el-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
}
.el-aside {
  background-color: #f5f7fa;
  padding: 20px;
}
.empty-placeholder {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>