<template>
    <div class="conversation-detail">
      <div class="detail-header">
        <h2>
          <el-icon><Document /></el-icon>
          {{ conversation.title }}
        </h2>
        <div class="action-buttons">
          <el-button type="primary" @click="$emit('save', conversation)" :icon="EditPen">编辑</el-button>
          <el-button type="success" @click="$emit('export', conversation.id)" :icon="Download">导出JSONL</el-button>
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
                <MdPreview :modelValue="message.content" :previewTheme="'vuepress'" />
              </div>
            </div>
          </div>
        </div>
      </el-scrollbar>
    </div>
  </template>
  
  <script>
  import { Document, User, Service, ChatDotRound, EditPen, Download } from '@element-plus/icons-vue'
  import { MdPreview } from 'md-editor-v3'
  
  export default {
    components: {
      MdPreview
    },
    props: {
      conversation: {
        type: Object,
        required: true
      }
    },
    emits: ['save', 'export'],
    setup() {
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
      
      return {
        getMessageClass,
        getAvatarIcon,
        getRoleColorClass,
        Document,
        EditPen,
        Download
      }
    },
    methods: {
      getRoleName(role) {
        const roleNames = {
          system: '系统',
          user: '用户',
          assistant: '助手'
        }
        return roleNames[role] || role
      }
    }
  }
  </script>
  
  <style>
  .conversation-detail {
    padding: 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #ebeef5;
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
    white-space: pre-wrap;
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
    background-color: #f2f6fc;
    border: 1px solid #ebeef5;
  }
  .message-assistant .message-bubble {
    align-self: flex-end;
    background-color: #ecf5ff;
    border: 1px solid #d9ecff;
  }
  .message-assistant {
    align-items: flex-end;
  }
  .message-other {
    align-items: flex-start;
  }
  
  /* 自定义 Markdown 预览样式 */
  .message-content .md-editor-preview {
    padding: 0 !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }
  
  .message-content .md-editor-preview-wrapper {
    padding: 0 !important;
  }
  
  .message-content pre {
    margin: 8px 0;
    padding: 12px;
    background-color: #f6f8fa;
    border-radius: 6px;
    overflow-x: auto;
  }
  
  .message-content blockquote {
    padding-left: 1em;
    border-left: 4px solid #b3d8ff;
    color: #666;
    margin: 1em 0;
  }
  
  /* 移除不必要的边距 */
  .md-preview {
    margin: 0 !important;
  }
  </style>