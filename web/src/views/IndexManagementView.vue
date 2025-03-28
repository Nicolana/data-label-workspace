<template>
  <div class="index-management">
    <div class="page-header">
      <h2>索引管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleCreateIndex">
          <el-icon><Plus /></el-icon>创建索引
        </el-button>
        <el-button type="success" @click="handleBatchImport">
          <el-icon><Upload /></el-icon>批量导入
        </el-button>
      </div>
    </div>

    <!-- 索引列表 -->
    <el-table :data="indexList" style="width: 100%">
      <el-table-column prop="name" label="索引名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="document_count" label="文档数量" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250">
        <template #default="{ row }">
          <el-button-group>
            <el-button type="primary" size="small" @click="handleViewDocuments(row)">
              查看文档
            </el-button>
            <el-button type="success" size="small" @click="handleAddDocuments(row)">
              添加文档
            </el-button>
            <el-button type="warning" size="small" @click="handleRebuildIndex(row)">
              重建索引
            </el-button>
            <el-button type="danger" size="small" @click="handleDeleteIndex(row)">
              删除
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建索引对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建索引" width="500px">
      <el-form :model="indexForm" label-width="100px">
        <el-form-item label="索引名称">
          <el-input v-model="indexForm.name" placeholder="请输入索引名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="indexForm.description" type="textarea" placeholder="请输入索引描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCreateIndex">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加文档对话框 -->
    <el-dialog v-model="addDocDialogVisible" title="添加文档" width="600px">
      <el-form :model="documentForm" label-width="100px">
        <el-form-item label="文档内容">
          <el-input v-model="documentForm.content" type="textarea" :rows="6" placeholder="请输入文档内容" />
        </el-form-item>
        <el-form-item label="元数据">
          <el-input v-model="documentForm.metadata" type="textarea" :rows="3" placeholder="请输入JSON格式的元数据" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDocDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitAddDocument">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 查看文档对话框 -->
    <el-dialog v-model="viewDocDialogVisible" title="文档列表" width="800px">
      <el-table :data="documents" style="width: 100%">
        <el-table-column prop="content" label="内容" show-overflow-tooltip />
        <el-table-column prop="metadata" label="元数据" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="handleDeleteDocument(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload } from '@element-plus/icons-vue'
import axios from 'axios'

// 状态
const indexList = ref([])
const createDialogVisible = ref(false)
const addDocDialogVisible = ref(false)
const viewDocDialogVisible = ref(false)
const documents = ref([])
const currentIndex = ref(null)

const indexForm = ref({
  name: '',
  description: ''
})

const documentForm = ref({
  content: '',
  metadata: ''
})

// 获取索引列表
const fetchIndexList = async () => {
  try {
    const response = await axios.get('/api/indices')
    indexList.value = response.data
  } catch (error) {
    ElMessage.error('获取索引列表失败')
  }
}

// 创建索引
const handleCreateIndex = () => {
  indexForm.value = {
    name: '',
    description: ''
  }
  createDialogVisible.value = true
}

const submitCreateIndex = async () => {
  try {
    await axios.post('/api/indices', indexForm.value)
    ElMessage.success('索引创建成功')
    createDialogVisible.value = false
    await fetchIndexList()
  } catch (error) {
    ElMessage.error('索引创建失败')
  }
}

// 添加文档
const handleAddDocuments = (index) => {
  currentIndex.value = index
  documentForm.value = {
    content: '',
    metadata: ''
  }
  addDocDialogVisible.value = true
}

const submitAddDocument = async () => {
  try {
    let metadata = {}
    try {
      metadata = JSON.parse(documentForm.value.metadata)
    } catch (e) {
      metadata = {}
    }

    await axios.post(`/api/indices/${currentIndex.value.id}/documents`, {
      content: documentForm.value.content,
      metadata
    })
    ElMessage.success('文档添加成功')
    addDocDialogVisible.value = false
  } catch (error) {
    ElMessage.error('文档添加失败')
  }
}

// 查看文档
const handleViewDocuments = async (index) => {
  currentIndex.value = index
  try {
    const response = await axios.get(`/api/indices/${index.id}/documents`)
    documents.value = response.data
    viewDocDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取文档列表失败')
  }
}

// 删除文档
const handleDeleteDocument = async (document) => {
  try {
    await ElMessageBox.confirm('确定要删除这个文档吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await axios.delete(`/api/indices/${currentIndex.value.id}/documents/${document.id}`)
    ElMessage.success('文档删除成功')
    await handleViewDocuments(currentIndex.value)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('文档删除失败')
    }
  }
}

// 重建索引
const handleRebuildIndex = async (index) => {
  try {
    await ElMessageBox.confirm('确定要重建索引吗？这可能需要一些时间。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await axios.post(`/api/indices/${index.id}/rebuild`)
    ElMessage.success('索引重建成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('索引重建失败')
    }
  }
}

// 删除索引
const handleDeleteIndex = async (index) => {
  try {
    await ElMessageBox.confirm('确定要删除这个索引吗？此操作不可恢复。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await axios.delete(`/api/indices/${index.id}`)
    ElMessage.success('索引删除成功')
    await fetchIndexList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('索引删除失败')
    }
  }
}

// 批量导入
const handleBatchImport = () => {
  // TODO: 实现批量导入功能
  ElMessage.info('批量导入功能开发中')
}

// 格式化时间
const formatTime = (time) => {
  return new Date(time).toLocaleString()
}

onMounted(() => {
  fetchIndexList()
})
</script>

<style scoped>
.index-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 12px;
}
</style> 