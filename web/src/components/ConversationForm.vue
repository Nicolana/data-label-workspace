<template>
    <el-form :model="formData" label-width="100px" ref="formRef">
      <el-form-item label="标题" prop="title" :rules="[{ required: true, message: '请输入标题' }]">
        <el-input v-model="formData.title" placeholder="请输入对话标题" clearable></el-input>
      </el-form-item>
      
      <div v-for="(message, index) in formData.messages" :key="index" class="message-card">
        <el-divider content-position="left">
          <el-tag :type="getTagType(message.role)" size="large" effect="plain">{{ getRoleName(message.role) }}</el-tag>
        </el-divider>
        
        <MdEditor 
          v-model="message.content" 
          :toolbars="toolbars"
          :preview="message.role !== 'system' && message.role !== 'user' && message.role !== 'assistant'"
          previewTheme="vuepress"
          :tabWidth="2"
          height="200px"
          style="margin-bottom: 20px; width: 100%; border-radius: 4px;"
        />
        
        <div class="message-actions" v-if="index > 0">
          <el-tooltip content="删除此消息" placement="top">
            <el-button 
              type="danger" 
              size="small" 
              @click="removeMessage(index)"
              :icon="Delete"
              circle
            ></el-button>
          </el-tooltip>
        </div>
      </div>
      
      <div class="form-actions">
        <el-button-group>
          <el-button type="primary" @click="addMessage('user')" :icon="User">添加用户消息</el-button>
          <el-button type="success" @click="addMessage('assistant')" :icon="ChatDotRound">添加助手消息</el-button>
        </el-button-group>
      </div>
    </el-form>
  </template>
  
  <script>
  import { ref, watch } from 'vue'
  import { Delete, User, ChatDotRound } from '@element-plus/icons-vue'
  
  export default {
    props: {
      conversation: {
        type: Object,
        required: true
      }
    },
    emits: ['submit'],
    setup(props, { emit }) {
      const formData = ref(JSON.parse(JSON.stringify(props.conversation)))
      const formRef = ref(null)
      
      // 定义 Markdown 编辑器的工具栏选项
      const toolbars = [
        'bold',
        'italic',
        'strikethrough',
        'heading',
        'quote',
        'code',
        'link',
        'image',
        'table',
        'list',
        'ordered-list',
        'hr',
        'undo',
        'redo',
        'preview'
      ]
  
      watch(() => props.conversation, (newVal) => {
        formData.value = JSON.parse(JSON.stringify(newVal))
      }, { deep: true })
  
      const getRoleName = (role) => {
        const roleNames = {
          system: '系统消息',
          user: '用户消息',
          assistant: '助手消息'
        }
        return roleNames[role] || role
      }
      
      const getTagType = (role) => {
        const tagTypes = {
          system: 'info',
          user: 'warning',
          assistant: 'success'
        }
        return tagTypes[role] || 'info'
      }
  
      const addMessage = (role) => {
        formData.value.messages.push({
          role: role,
          content: ''
        })
      }
  
      const removeMessage = (index) => {
        // 不再需要特殊处理，直接移除消息
        formData.value.messages.splice(index, 1)
      }
  
      const submit = () => {
        formRef.value.validate((valid) => {
          if (valid) {
            emit('submit', formData.value)
          }
        })
      }
  
      return {
        formData,
        formRef,
        getRoleName,
        getTagType,
        addMessage,
        removeMessage,
        submit,
        toolbars,
        Delete,
        User,
        ChatDotRound
      }
    },
    methods: {
      submit() {
        this.$refs.formRef.validate((valid) => {
          if (valid) {
            this.$emit('submit', this.formData)
          }
        })
      }
    }
  }
  </script>
  
  <style>
  .message-card {
    margin-bottom: 20px;
    position: relative;
    padding: 0 10px;
    border-radius: 8px;
    background-color: #f7f9fc;
    border-left: 4px solid #e6e8eb;
    transition: all 0.3s;
  }
  .message-card:hover {
    border-left-color: #409eff;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  }
  .message-actions {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 10;
  }
  .form-actions {
    display: flex;
    justify-content: center;
    margin-top: 20px;
  }
  
  /* 覆盖md-editor样式 */
  .md-editor {
    border-radius: 4px;
  }
  .md-editor-toolbar {
    border-radius: 4px 4px 0 0;
    background-color: #f9f9f9;
  }
  </style>