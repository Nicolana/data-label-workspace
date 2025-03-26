<template>
    <div class="conversation-list">
      <div class="list-header">
        <h3>对话列表</h3>
        <el-button type="primary" size="small" @click="$emit('create')">新增对话</el-button>
      </div>
      <el-scrollbar height="calc(100vh - 120px)">
        <el-menu>
          <el-menu-item 
            v-for="conversation in conversations" 
            :key="conversation.id"
            @click="$emit('select', conversation.id)"
          >
            <span>{{ conversation.title }}</span>
            <template #title>
              <span>{{ conversation.title }}</span>
              <el-button 
                type="danger" 
                size="small" 
                @click.stop="$emit('delete', conversation.id)"
                class="delete-btn"
              >
                删除
              </el-button>
            </template>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      conversations: {
        type: Array,
        required: true
      }
    },
    emits: ['select', 'create', 'delete']
  }
  </script>
  
  <style>
  .conversation-list {
    height: 100%;
  }
  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  .delete-btn {
    margin-left: 10px;
  }
  </style>