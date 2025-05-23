<template>
  <el-dialog
    v-model="dialogVisible"
    title="批量导入对话"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-upload
      class="upload-demo"
      drag
      action="#"
      :auto-upload="false"
      :on-change="handleFileChange"
      :limit="1"
      accept=".json,.jsonl"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          请上传 JSON 或 JSONL 格式的对话数据文件
        </div>
      </template>
    </el-upload>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleImport" :loading="importing">
          导入
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { conversationApi } from '../api/conversation'

export default {
  components: {
    UploadFilled
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true
    }
  },
  emits: ['update:modelValue', 'success'],
  setup(props, { emit }) {
    const dialogVisible = ref(props.modelValue)
    const importing = ref(false)
    const fileList = ref([])

    const handleFileChange = (file) => {
      fileList.value = [file]
    }

    const parseJsonl = (text) => {
      return text.split('\n')
        .filter(line => line.trim())
        .map(line => JSON.parse(line))
    }

    const handleImport = async () => {
      if (fileList.value.length === 0) {
        ElMessage.warning('请选择要导入的文件')
        return
      }

      const file = fileList.value[0]
      if (!file.raw) {
        ElMessage.error('文件读取失败')
        return
      }

      importing.value = true
      try {
        const text = await file.raw.text()
        let data
        
        // 根据文件扩展名判断格式
        if (file.name.endsWith('.jsonl')) {
          data = parseJsonl(text)
        } else {
          data = JSON.parse(text)
          if (!Array.isArray(data)) {
            data = [data] // 单个对象转换为数组
          }
        }
        
        // 验证每条数据的必要字段
        data.forEach((item, index) => {
          if (!Array.isArray(item)) {
            throw new Error(`第 ${index + 1} 条数据格式错误：必须是数组格式`)
          }
          item.forEach((message, msgIndex) => {
            if (!message.role || !message.content) {
              throw new Error(`第 ${index + 1} 条数据的第 ${msgIndex + 1} 条消息格式错误：缺少 role 或 content 字段`)
            }
          })
        })

        // 批量创建对话
        const response = await conversationApi.batchCreateConversations(data)
        if (response.code === 200) {
          emit('success', response.data)
          dialogVisible.value = false
          ElMessage.success('导入成功')
        } else {
          ElMessage.error(response.message || '导入失败')
        }
      } catch (error) {
        ElMessage.error(error.message || '导入失败')
      } finally {
        importing.value = false
      }
    }

    return {
      dialogVisible,
      importing,
      fileList,
      handleFileChange,
      handleImport
    }
  },
  watch: {
    modelValue(val) {
      this.dialogVisible = val
    },
    dialogVisible(val) {
      this.$emit('update:modelValue', val)
    }
  }
}
</script>

<style scoped>
.upload-demo {
  text-align: center;
}
.el-upload__tip {
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}
</style>