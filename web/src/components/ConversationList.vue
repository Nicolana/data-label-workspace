<template>
    <div class="conversation-list">
      <div class="list-header">
        <h3><el-icon><ChatLineRound /></el-icon> 对话列表</h3>
        <el-button type="primary" size="small" @click="$emit('create')" icon="Plus">新增对话</el-button>
      </div>
      <el-scrollbar height="calc(100vh - 120px)">
        <div class="conversation-items">
          <div 
            v-for="conversation in conversations" 
            :key="conversation.id"
            class="conversation-item"
            @click="$emit('select', conversation.id)"
          >
            <div class="conversation-info">
              <div class="conversation-title">
                <el-icon><Document /></el-icon>
                {{ conversation.title }}
              </div>
              <div class="conversation-meta">
                <el-tag size="small" effect="plain">{{ getMessagesCount(conversation) }}条消息</el-tag>
              </div>
            </div>
            <div class="conversation-actions">
              <el-tooltip content="删除对话" placement="top">
                <el-button 
                  type="danger" 
                  size="small" 
                  @click.stop="$emit('delete', conversation.id)"
                  icon="Delete"
                  circle
                ></el-button>
              </el-tooltip>
            </div>
          </div>
        </div>
      </el-scrollbar>
    </div>
  </template>
  
  <script>
  import { Document, ChatLineRound } from '@element-plus/icons-vue'
  
  export default {
    props: {
      conversations: {
        type: Array,
        required: true
      }
    },
    emits: ['select', 'create', 'delete'],
    setup() {
      const getMessagesCount = (conversation) => {
        return conversation.messages ? conversation.messages.length : 0
      }
      
      return {
        getMessagesCount,
        Document,
        ChatLineRound
      }
    }
  }
  </script>
  
  <style>
  .conversation-list {
    height: 100%;
    border-right: 1px solid #ebeef5;
  }
  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid #ebeef5;
  }
  .list-header h3 {
    margin: 0;
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 16px;
    color: #303133;
  }
  .conversation-items {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 5px;
  }
  .conversation-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    border-radius: 8px;
    background-color: #fff;
    border: 1px solid #ebeef5;
    transition: all 0.3s;
    cursor: pointer;
  }
  .conversation-item:hover {
    background-color: #f5f7fa;
    transform: translateY(-2px);
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  }
  .conversation-info {
    flex: 1;
    overflow: hidden;
  }
  .conversation-title {
    display: flex;
    align-items: center;
    gap: 5px;
    font-weight: 500;
    margin-bottom: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .conversation-meta {
    font-size: 12px;
    color: #909399;
  }
  .conversation-actions {
    margin-left: 10px;
    opacity: 0.5;
    transition: opacity 0.2s;
  }
  .conversation-item:hover .conversation-actions {
    opacity: 1;
  }
  </style>