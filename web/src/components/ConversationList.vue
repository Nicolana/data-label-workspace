<template>
    <div class="conversation-list">
      <div class="list-header">
        <h3><el-icon><ChatLineRound /></el-icon> 对话列表</h3>
        <div class="list-actions">
          <el-button type="primary" size="small" @click="$emit('create')" :icon="Plus">新增对话</el-button>
          <el-button 
            type="success" 
            size="small" 
            @click="exportSelected"
            :disabled="selectedIds.length === 0"
            :icon="Download"
          >
            批量导出 <span v-if="selectedIds.length > 0">({{ selectedIds.length }})</span>
          </el-button>
        </div>
      </div>
      
      <div class="list-toolbar">
        <el-checkbox 
          v-model="selectAll" 
          @change="handleSelectAll" 
          :disabled="conversations.length === 0"
        >
          全选
        </el-checkbox>
        <el-button 
          type="text" 
          size="small" 
          @click="clearSelection"
          :disabled="selectedIds.length === 0"
        >
          清除选择
        </el-button>
      </div>
      
      <el-scrollbar height="calc(100vh - 155px)">
        <div class="conversation-items">
          <div 
            v-for="conversation in localConversations" 
            :key="conversation.id"
            class="conversation-item"
            :class="{ 'conversation-selected': isSelected(conversation.id) }"
            @click="handleItemClick(conversation)"
          >
            <div class="conversation-checkbox">
              <el-checkbox 
                v-model="conversation.selected" 
                @change="updateSelection" 
                @click.stop
              ></el-checkbox>
            </div>
            <div class="conversation-info" @click.stop="$emit('select', conversation.id)">
              <div class="conversation-title">
                <el-icon><Document /></el-icon>
                {{ conversation.title }}
              </div>
              <div class="conversation-meta">
                <el-tag size="small" effect="plain">{{ conversation.message_count }}条消息</el-tag>
                <el-tag 
                  size="small" 
                  :type="conversation.token_count > 4000 ? 'danger' : 'success'"
                  effect="plain"
                >
                  {{ conversation.token_count }} tokens
                </el-tag>
              </div>
            </div>
            <div class="conversation-actions">
              <el-tooltip content="导出对话" placement="top">
                <el-button 
                  type="success" 
                  size="small" 
                  @click.stop="$emit('export', conversation.id)"
                  :icon="Download"
                  circle
                ></el-button>
              </el-tooltip>
              <el-tooltip content="删除对话" placement="top">
                <el-button 
                  type="danger" 
                  size="small" 
                  @click.stop="$emit('delete', conversation.id)"
                  :icon="Delete"
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
  import { ref, watch, computed } from 'vue'
  import { Document, ChatLineRound, Delete, Download, Plus } from '@element-plus/icons-vue'
  import { encoding_for_model } from 'tiktoken'
  
  export default {
    props: {
      conversations: {
        type: Array,
        required: true
      }
    },
    emits: ['select', 'create', 'delete', 'export', 'batch-export'],
    setup(props, { emit }) {
      // 保存本地会话列表副本，带有选中状态
      const localConversations = ref([])
      const selectAll = ref(false)
         
      // 计算选中的ID列表
      const selectedIds = computed(() => {
        return localConversations.value
          .filter(conv => conv.selected)
          .map(conv => conv.id)
      })


   
      
      // 检查特定ID是否被选中
      const isSelected = (id) => {
        return selectedIds.value.includes(id)
      }
      
      // 全选/取消全选
      const handleSelectAll = (val) => {
        localConversations.value.forEach(conv => {
          conv.selected = val
        })
      }
      
      // 清除选择
      const clearSelection = () => {
        localConversations.value.forEach(conv => {
          conv.selected = false
        })
        selectAll.value = false
      }
      
      // 更新选择状态
      const updateSelection = () => {
        if (localConversations.value.length === 0) {
          selectAll.value = false
          return
        }
        
        const allSelected = localConversations.value.every(conv => conv.selected)
        selectAll.value = allSelected
      }
      
      // 点击整个项目时切换选择
      const handleItemClick = (conversation) => {
        conversation.selected = !conversation.selected
        updateSelection()
      }
      
      // 导出选中的对话
      const exportSelected = () => {
        if (selectedIds.value.length > 0) {
          emit('batch-export', selectedIds.value)
        }
      }
      
      const getMessagesCount = (conversation) => {
        return conversation.messages ? conversation.messages.length : 0
      }

      // 计算 token 数量
      const getTokenCount = (conversation) => {
        if (!conversation.messages) return 0
        
        const enc = encoding_for_model('gpt-3.5-turbo')
        let totalTokens = 0
        
        conversation.messages.forEach(message => {
          // 计算消息内容的 tokens
          totalTokens += enc.encode(message.content).length
          
          // 计算角色名称的 tokens
          totalTokens += enc.encode(message.role).length
          
          // 添加一些系统消息的 tokens
          if (message.role === 'system') {
            totalTokens += 4
          } else if (message.role === 'user') {
            totalTokens += 4
          } else if (message.role === 'assistant') {
            totalTokens += 4
          }
        })
        
        return totalTokens
      }

      // 监听会话列表变化，创建本地副本
      watch(() => props.conversations, (newVal) => {
        // 保持以前的选中状态
        const previousSelectedIds = selectedIds.value
        
        localConversations.value = newVal.map(conv => {
          // 检查之前是否选中过
          const wasSelected = previousSelectedIds.includes(conv.id)
          return {
            ...conv,
            selected: wasSelected
          }
        })
        
        // 更新全选状态
        updateSelection()
      }, { immediate: true, deep: true })
      
      return {
        localConversations,
        selectAll,
        selectedIds,
        isSelected,
        handleSelectAll,
        clearSelection,
        updateSelection,
        handleItemClick,
        exportSelected,
        getMessagesCount,
        getTokenCount,
        Document,
        ChatLineRound,
        Delete,
        Download,
        Plus
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
    margin-bottom: 10px;
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
  .list-actions {
    display: flex;
    gap: 8px;
  }
  .list-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 15px 10px;
    margin-bottom: 5px;
  }
  .conversation-items {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 5px;
  }
  .conversation-item {
    display: flex;
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
  .conversation-selected {
    background-color: #ecf5ff;
    border-color: #b3d8ff;
  }
  .conversation-checkbox {
    margin-right: 10px;
  }
  .conversation-info {
    flex: 1;
    overflow: hidden;
    cursor: pointer;
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
    display: flex;
    gap: 8px;
  }
  .conversation-actions {
    display: flex;
    gap: 5px;
    margin-left: 10px;
    opacity: 0.5;
    transition: opacity 0.2s;
  }
  .conversation-item:hover .conversation-actions {
    opacity: 1;
  }
  </style>