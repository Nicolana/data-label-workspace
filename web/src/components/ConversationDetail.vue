<template>
    <div class="conversation-detail">
      <div class="detail-header">
        <h2>{{ conversation.title }}</h2>
        <div class="action-buttons">
          <el-button type="primary" @click="$emit('save', conversation)">编辑</el-button>
          <el-button type="success" @click="$emit('export', conversation.id)">导出JSONL</el-button>
        </div>
      </div>
      
      <div class="message-container">
        <div v-for="(message, index) in conversation.messages" :key="index" class="message-item">
          <div class="message-role">{{ getRoleName(message.role) }}</div>
          <div class="message-content" v-html="message.content"></div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      conversation: {
        type: Object,
        required: true
      }
    },
    emits: ['save', 'export'],
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
  }
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  .message-container {
    border: 1px solid #ebeef5;
    border-radius: 4px;
    overflow: hidden;
  }
  .message-item {
    border-bottom: 1px solid #ebeef5;
    padding: 15px;
  }
  .message-item:last-child {
    border-bottom: none;
  }
  .message-role {
    font-weight: bold;
    margin-bottom: 8px;
    color: #409EFF;
  }
  .message-content {
    line-height: 1.6;
  }
  /* 为 Quill 内容添加样式 */
  .message-content .ql-editor {
    padding: 0;
  }
  .message-content blockquote {
    border-left: 4px solid #ccc;
    margin-bottom: 5px;
    margin-top: 5px;
    padding-left: 16px;
  }
  .message-content pre {
    background-color: #f0f0f0;
    border-radius: 3px;
    padding: 8px;
    overflow-x: auto;
  }
  .message-content code {
    background-color: #f0f0f0;
    border-radius: 3px;
    padding: 2px 4px;
    font-family: monospace;
  }
  </style>