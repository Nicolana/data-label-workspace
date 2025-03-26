<template>
    <el-form :model="formData" label-width="80px" ref="formRef">
      <el-form-item label="标题" prop="title" :rules="[{ required: true, message: '请输入标题' }]">
        <el-input v-model="formData.title" placeholder="请输入对话标题"></el-input>
      </el-form-item>
      
      <el-form-item 
        v-for="(message, index) in formData.messages" 
        :key="index"
        :label="getRoleName(message.role)"
      >
        <QuillEditor 
          v-model:content="message.content" 
          :toolbar="toolbarOptions"
          :readOnly="message.role !== 'system' && message.role !== 'user' && message.role !== 'assistant'"
          theme="snow"
          contentType="html"
          style="height: 200px; margin-bottom: 30px; width: 100%;"
        />
        <el-button 
          v-if="index > 0" 
          type="danger" 
          size="small" 
          @click="removeMessage(index)"
          style="margin-top: 10px;"
        >
          删除此消息
        </el-button>
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="addMessage('user')">添加用户消息</el-button>
        <el-button type="primary" @click="addMessage('assistant')">添加助手消息</el-button>
      </el-form-item>
    </el-form>
  </template>
  
  <script>
  import { ref, watch, nextTick } from 'vue'
  
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
      
      // 定义 Quill 编辑器的工具栏选项
      const toolbarOptions = [
        ['bold', 'italic', 'underline', 'strike'],
        ['blockquote', 'code-block'],
        [{ 'header': 1 }, { 'header': 2 }],
        [{ 'list': 'ordered' }, { 'list': 'bullet' }],
        [{ 'script': 'sub' }, { 'script': 'super' }],
        [{ 'indent': '-1' }, { 'indent': '+1' }],
        [{ 'direction': 'rtl' }],
        [{ 'size': ['small', false, 'large', 'huge'] }],
        [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
        [{ 'color': [] }, { 'background': [] }],
        [{ 'font': [] }],
        [{ 'align': [] }],
        ['clean'],
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
        addMessage,
        removeMessage,
        submit,
        toolbarOptions
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
  /* 确保编辑器的容器有足够空间 */
  .ql-container {
    min-height: 150px;
  }
  </style>