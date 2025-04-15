<template>
    <div class="conversation-list">
      <div class="list-header-wrapper">
        <div class="list-header">
          <div class="list-actions">
            <el-button type="primary" size="small" @click="$emit('create')" :icon="Plus">新增对话</el-button>
            <el-button 
              type="warning" 
              size="small" 
              @click="showGenerateDialog"
              :icon="MagicStick"
            >
              生成对话
            </el-button>
            <el-button 
              type="success" 
              size="small" 
              @click="exportSelected"
              :disabled="selectedIds.length === 0"
              :icon="Download"
            >
              批量导出 <span v-if="selectedIds.length > 0">({{ selectedIds.length }})</span>
            </el-button>
            <el-button 
              type="info" 
              size="small" 
              @click="showImportDialog"
              :icon="Upload"
            >
              批量导入
            </el-button>
          </div>
        </div>
        <div class="list-stats">
          <el-tag size="small" effect="plain" type="info">
            共 {{ conversations.length }} 条对话
          </el-tag>
          <el-tag 
            size="small" 
            effect="plain" 
            type="warning"
            v-if="selectedIds.length > 0"
          >
            已选择 {{ selectedIds.length }} 条
          </el-tag>
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
      </div>
      
      <el-scrollbar height="calc(100vh - 138px - 60px)">
        <el-table
          :data="localConversations"
          style="width: 100%"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column label="序号" width="60">
            <template #default="scope">
              {{ scope.$index + 1 }}
            </template>
          </el-table-column>
          <el-table-column prop="id" label="ID" width="180" />
          <el-table-column label="消息列表" min-width="400">
            <template #default="{ row }">
              <el-table
                :data="row.messages || []"
                style="width: 100%"
                size="small"
              >
                <el-table-column prop="role" label="角色" width="100">
                  <template #default="{ row: message }">
                    <el-tag :type="getRoleTagType(message.role)" size="small">
                      {{ message.role }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="content" label="内容" show-overflow-tooltip />
              </el-table>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button-group>
                <el-tooltip content="复制对话" placement="top">
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="$emit('copy', row.id)"
                    :icon="CopyDocument"
                    circle
                  ></el-button>
                </el-tooltip>
                <el-tooltip content="编辑对话" placement="top">
                  <el-button 
                    type="warning" 
                    size="small" 
                    @click="$emit('edit', row.id)"
                    :icon="Edit"
                    circle
                  ></el-button>
                </el-tooltip>
                <el-tooltip content="导出对话" placement="top">
                  <el-button 
                    type="success" 
                    size="small" 
                    @click="$emit('export', row.id)"
                    :icon="Download"
                    circle
                  ></el-button>
                </el-tooltip>
                <el-tooltip content="删除对话" placement="top">
                  <el-button 
                    type="danger" 
                    size="small" 
                    @click="$emit('delete', row.id)"
                    :icon="Delete"
                    circle
                  ></el-button>
                </el-tooltip>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
      </el-scrollbar>
      <GenerateDialog
        v-model="generateDialogVisible"
        @success="handleGenerateSuccess"
      />
      <ImportDialog
        v-model="importDialogVisible"
        @success="handleImportSuccess"
      />
    </div>
</template>

<script>
import { ref, watch, computed } from 'vue'
import { Document, ChatLineRound, Delete, Download, Plus, CopyDocument, MagicStick, Upload } from '@element-plus/icons-vue'
import GenerateDialog from './GenerateDialog.vue'
import ImportDialog from './ImportDialog.vue'

export default {
  components: {
    GenerateDialog,
    ImportDialog
  },
  props: {
    conversations: {
      type: Array,
      required: true
    }
  },
  emits: ['select', 'create', 'delete', 'export', 'batch-export', 'copy', 'generate-success', 'import-success'],
  setup(props, { emit }) {
    const localConversations = ref([])
    const selectAll = ref(false)
    const generateDialogVisible = ref(false)
    const importDialogVisible = ref(false)
    const selectedRows = ref([])
    
    // 计算选中的ID列表
    const selectedIds = computed(() => {
      return selectedRows.value.map(row => row.id)
    })
    
    // 处理表格选择变化
    const handleSelectionChange = (selection) => {
      selectedRows.value = selection
      selectAll.value = selection.length === props.conversations.length
    }
    
    // 全选/取消全选
    const handleSelectAll = (val) => {
      const table = document.querySelector('.el-table')
      if (table) {
        const checkboxes = table.querySelectorAll('.el-checkbox')
        checkboxes.forEach(checkbox => {
          if (val) {
            checkbox.classList.add('is-checked')
          } else {
            checkbox.classList.remove('is-checked')
          }
        })
      }
    }
    
    // 清除选择
    const clearSelection = () => {
      selectedRows.value = []
      selectAll.value = false
      const table = document.querySelector('.el-table')
      if (table) {
        const checkboxes = table.querySelectorAll('.el-checkbox')
        checkboxes.forEach(checkbox => {
          checkbox.classList.remove('is-checked')
        })
      }
    }
    
    // 获取角色标签类型
    const getRoleTagType = (role) => {
      switch (role) {
        case 'system':
          return 'info'
        case 'user':
          return 'primary'
        case 'assistant':
          return 'success'
        default:
          return ''
      }
    }
    
    // 导出选中的对话
    const exportSelected = () => {
      if (selectedIds.value.length > 0) {
        emit('batch-export', selectedIds.value)
      }
    }

    const showGenerateDialog = () => {
      generateDialogVisible.value = true
    }

    const handleGenerateSuccess = (conversation) => {
      emit('generate-success', conversation)
    }

    const showImportDialog = () => {
      importDialogVisible.value = true
    }

    const handleImportSuccess = (data) => {
      emit('import-success', data)
    }

    // 监听会话列表变化，创建本地副本
    watch(() => props.conversations, (newVal) => {
      localConversations.value = newVal.map(conv => ({
        ...conv,
        messages: conv.messages || []
      }))
    }, { immediate: true, deep: true })
    
    return {
      localConversations,
      selectAll,
      selectedIds,
      handleSelectAll,
      clearSelection,
      exportSelected,
      getRoleTagType,
      generateDialogVisible,
      showGenerateDialog,
      handleGenerateSuccess,
      handleSelectionChange,
      importDialogVisible,
      showImportDialog,
      handleImportSuccess,
      Document,
      ChatLineRound,
      Delete,
      Download,
      Plus,
      CopyDocument,
      MagicStick,
      Upload,
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
  margin-bottom: 10px;
  padding: 10px 15px;
  border-bottom: 1px solid #ebeef5;
}
.list-stats {
  display: flex;
  gap: 8px;
  padding: 0 15px;
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
.list-header-wrapper {
  background-color: #fff;
  padding: 8px 0;
  position: sticky;
  top: 0;
  z-index: 100;
}

.el-table {
  --el-table-border-color: #ebeef5;
  --el-table-header-bg-color: #f5f7fa;
}

.el-table .el-table__inner-wrapper {
  border-radius: 4px;
}

.el-table .el-table__cell {
  padding: 8px 0;
}

.el-button-group {
  display: flex;
  gap: 4px;
}
</style>