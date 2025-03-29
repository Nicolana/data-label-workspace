<template>
  <div class="app-container">
    <el-container>
      <el-header class="app-header">
        <div class="app-logo">
          <el-icon size="24"><ChatSquare /></el-icon>
          <h1>对话微调数据管理平台</h1>
        </div>
        <el-menu
          mode="horizontal"
          :router="true"
          class="app-menu"
          :ellipsis="false"
          background-color="#409EFF"
          text-color="#fff"
          active-text-color="#fff"
        >
          <el-menu-item index="/">对话管理</el-menu-item>
          <el-menu-item index="/chat">
            <el-icon><ChatDotRound /></el-icon>
            <span>AI 助手</span>
          </el-menu-item>
          <el-menu-item index="/indices">
            <el-icon><Files /></el-icon>
            <span>索引管理</span>
          </el-menu-item>
        </el-menu>
      </el-header>
      <el-container class="main-container">
        <el-main class="app-main">
          <transition name="slide-fade">
            <router-view></router-view>
          </transition>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { ChatSquare, ChatDotRound, Files } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { conversationApi } from '../api/conversation'

export default {
  name: 'DefaultLayout',
  components: {
    ChatSquare,
    ChatDotRound,
    Files
  },
  props: {
    showSidebar: {
      type: Boolean,
      default: true
    }
  },
  setup() {
    const API_URL = 'http://localhost:8000'

    const handleBatchExport = async () => {
      try {
        await ElMessageBox.confirm('确定要导出所有对话吗？', '批量导出', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        })
        
        const response = await conversationApi.getConversations()
        const conversations = response.data
        
        if (conversations.length === 0) {
          ElMessage.warning('没有可导出的对话')
          return
        }
        
        const ids = conversations.map(conv => conv.id)
        await exportMultipleConversations(ids)
      } catch (error) {
        if (error !== 'cancel') {
          console.error('批量导出失败:', error)
          ElMessage.error('批量导出失败')
        }
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

    return {
      handleBatchExport
    }
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  background-color: #f5f7fa;
}

.app-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.app-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-logo h1 {
  font-size: 20px;
  margin: 0;
}

.app-menu {
  border-bottom: none;
  margin-left: auto;
}

.app-menu :deep(.el-menu-item) {
  height: 60px;
  line-height: 60px;
  color: #fff;
}

.app-menu :deep(.el-menu-item.is-active) {
  background-color: rgba(255, 255, 255, 0.1);
}

.app-menu :deep(.el-menu-item:not(.is-active):hover) {
  background-color: rgba(255, 255, 255, 0.1);
}

.main-container {
  height: calc(100vh - 60px);
  overflow: hidden;
}

.app-aside {
  background-color: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  border-right: none;
}

.app-main {
  background-color: #ffffff;
  border-radius: 4px;
  padding: 0;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

/* 过渡效果 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from, .slide-fade-leave-to {
  transform: translateX(10px);
  opacity: 0;
}
</style> 