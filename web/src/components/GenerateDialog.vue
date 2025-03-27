<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="使用 DeepSeek 生成对话"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form :model="form" label-width="100px">
      <el-form-item label="系统提示词">
        <el-input
          v-model="form.system_prompt"
          type="textarea"
          :rows="3"
          placeholder="可选，用于设置 AI 的行为和角色"
        />
      </el-form-item>
      <el-form-item label="用户提示词">
        <el-input
          v-model="form.prompt"
          type="textarea"
          :rows="4"
          placeholder="请输入您想要 AI 回答的问题或指令"
        />
      </el-form-item>
      <el-form-item label="最大长度">
        <el-input-number
          v-model="form.max_tokens"
          :min="100"
          :max="10000"
          :step="100"
          placeholder="最大生成 token 数量"
        />
      </el-form-item>
      <el-form-item label="温度">
        <el-slider
          v-model="form.temperature"
          :min="0"
          :max="2"
          :step="0.1"
          :format-tooltip="value => value.toFixed(1)"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          生成对话
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import { ref, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

export default {
  props: {
    modelValue: {
      type: Boolean,
      required: true
    }
  },
  emits: ['update:modelValue', 'success'],
  setup(props, { emit }) {
    const loading = ref(false)
    const form = ref({
      system_prompt: '你是Spotter Gmesh项目的一个前端开发辅助，你会接收用户给出的任务，来帮助他完成代码编写',
      prompt: '',
      max_tokens: 4000,
      temperature: 0.7
    })

    const handleClose = () => {
      emit('update:modelValue', false)
      form.value = {
        system_prompt: '',
        prompt: '',
        max_tokens: 1000,
        temperature: 0.7
      }
    }

    const handleSubmit = async () => {
      if (!form.value.prompt.trim()) {
        ElMessage.warning('请输入用户提示词')
        return
      }

      loading.value = true
      try {
        const response = await axios.post('http://localhost:8000/generate', form.value)
        ElMessage.success('对话生成成功')
        emit('success', response.data)
        handleClose()
      } catch (error) {
        console.error('生成对话失败:', error)
        ElMessage.error(error.response?.data?.detail || '生成对话失败')
      } finally {
        loading.value = false
      }
    }

    return {
      loading,
      form,
      handleClose,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style> 