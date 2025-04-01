<template>
  <div class="index-management">
    <!-- 左侧索引列表和管理 -->
    <div class="index-sidebar">
      <div class="sidebar-header">
        <h2>索引管理</h2>
        <div class="header-actions">
          <el-button type="primary" size="small" @click="handleCreateIndex">
            <el-icon><Plus /></el-icon>创建索引
          </el-button>
          <el-button type="success" size="small" @click="handleBatchImport">
            <el-icon><Upload /></el-icon>批量导入
          </el-button>
        </div>
      </div>

      <!-- 索引列表 -->
      <div class="index-list">
        <el-card v-for="item in indexList" :key="item.id" class="index-card" 
                 :class="{ 'is-active': currentIndex && currentIndex.id === item.id }"
                 @click="selectIndex(item)">
          <div class="index-card-header">
            <h3>{{ item.name }}</h3>
            <div class="index-actions">
              <el-dropdown trigger="click" @command="handleIndexCommand($event, item)">
                <el-button type="primary" size="small" circle>
                  <el-icon><More /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="rebuild">重建索引</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除索引</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          <div class="index-card-content">
            <p class="description">{{ item.description || '无描述' }}</p>
            <div class="index-meta">
              <span class="doc-count">{{ item.document_count }} 文档</span>
              <span class="create-time">{{ formatTime(item.created_at, true) }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 右侧内容区 -->
    <div class="index-content">
      <div v-if="!currentIndex" class="empty-content">
        <el-empty description="请选择左侧索引以查看内容和进行测试" />
      </div>
      <template v-else>
        <div class="content-header">
          <h2>{{ currentIndex.name }}</h2>
          <div class="content-actions">
            <el-button type="primary" size="small" @click="handleAddDocuments(currentIndex)">
              <el-icon><Plus /></el-icon>添加文档
            </el-button>
          </div>
        </div>

        <!-- 内容标签页 -->
        <el-tabs v-model="activeTab" class="index-tabs">
          <el-tab-pane label="文档管理" name="documents">
            <!-- 文档列表 -->
            <el-table :data="documents" style="width: 100%">
              <el-table-column prop="content" label="内容" show-overflow-tooltip />
              <el-table-column prop="metadata" label="元数据" show-overflow-tooltip />
              <el-table-column prop="created_at" label="创建时间" width="180">
                <template #default="{ row }">
                  {{ formatTime(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="{ row }">
                  <el-button type="danger" size="small" @click="handleDeleteDocument(row)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          
          <el-tab-pane label="召回测试" name="recall">
            <div class="recall-container">
              <div class="chat-history">
                <div v-if="chatHistory.length === 0" class="empty-chat">
                  <p>在下方输入框输入查询内容，测试索引召回效果</p>
                </div>
                <div v-else class="chat-messages">
                  <div v-for="(message, index) in chatHistory" :key="index" class="chat-message"
                       :class="{ 'user-message': message.isUser, 'system-message': !message.isUser }">
                    <div class="message-content">
                      <div class="message-header">
                        <strong>{{ message.isUser ? '查询' : '召回结果' }}</strong>
                        <span class="message-time">{{ formatTime(message.time, true) }}</span>
                      </div>
                      <div v-if="message.isUser" class="user-query">
                        {{ message.content }}
                      </div>
                      <div v-else class="recall-results">
                        <div v-for="(result, rIndex) in message.results" :key="rIndex" class="recall-result">
                          <div class="result-score">{{ (result.score * 100).toFixed(2) }}%</div>
                          <div class="result-content">{{ result.content }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="chat-input">
                <el-input
                  v-model="recallQuery"
                  type="textarea"
                  :rows="3"
                  placeholder="输入查询内容测试索引召回效果"
                  @keyup.ctrl.enter="submitRecallQuery"
                />
                <div class="input-actions">
                  <span class="hint">按 Ctrl+Enter 发送</span>
                  <el-button type="primary" @click="submitRecallQuery">测试召回</el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </template>
    </div>

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
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, More } from '@element-plus/icons-vue'
import { indexApi } from '../api/index'

// 状态
const indexList = ref([])
const createDialogVisible = ref(false)
const addDocDialogVisible = ref(false)
const documents = ref([])
const currentIndex = ref(null)
const activeTab = ref('documents')
const recallQuery = ref('')
const chatHistory = ref([])

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
    const response = await indexApi.getIndices()
    indexList.value = response.data
  } catch (error) {
    ElMessage.error('获取索引列表失败')
  }
}

// 选择索引
const selectIndex = async (index) => {
  currentIndex.value = index
  // 加载索引文档
  await fetchDocuments(index.id)
}

// 获取索引文档
const fetchDocuments = async (indexId) => {
  try {
    const response = await indexApi.getDocuments(indexId)
    documents.value = response.data
  } catch (error) {
    ElMessage.error('获取文档列表失败')
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
    await indexApi.createIndex(indexForm.value)
    ElMessage.success('索引创建成功')
    createDialogVisible.value = false
    await fetchIndexList()
  } catch (error) {
    ElMessage.error('索引创建失败')
  }
}

// 索引下拉菜单操作
const handleIndexCommand = async (command, index) => {
  switch (command) {
    case 'rebuild':
      await handleRebuildIndex(index)
      break
    case 'delete':
      await handleDeleteIndex(index)
      break
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

    await indexApi.createDocument(currentIndex.value.id, {
      content: documentForm.value.content,
      metadata
    })
    ElMessage.success('文档添加成功')
    addDocDialogVisible.value = false
    await fetchDocuments(currentIndex.value.id)
  } catch (error) {
    ElMessage.error('文档添加失败')
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
    
    await indexApi.deleteDocument(currentIndex.value.id, document.id)
    ElMessage.success('文档删除成功')
    await fetchDocuments(currentIndex.value.id)
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
    
    await indexApi.rebuildIndex(index.id)
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
    
    await indexApi.deleteIndex(index.id)
    ElMessage.success('索引删除成功')
    
    // 如果删除的是当前选中的索引，清空当前索引
    if (currentIndex.value && currentIndex.value.id === index.id) {
      currentIndex.value = null
    }
    
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
const formatTime = (time, short = false) => {
  if (short) {
    return new Date(time).toLocaleString('zh-CN', { 
      month: 'numeric', 
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric'
    })
  }
  return new Date(time).toLocaleString()
}

// 提交召回测试查询
const submitRecallQuery = async () => {
  if (!recallQuery.value.trim()) {
    ElMessage.warning('请输入查询内容')
    return
  }
  
  if (!currentIndex.value) {
    ElMessage.warning('请先选择索引')
    return
  }
  
  // 添加用户查询到历史记录
  chatHistory.value.push({
    isUser: true,
    content: recallQuery.value,
    time: new Date()
  })
  
  try {
    const response = await indexApi.testRecall(currentIndex.value.id, {
      query: recallQuery.value,
      top_k: 5
    })
    
    // 添加响应结果到历史记录
    chatHistory.value.push({
      isUser: false,
      results: response.data,
      time: new Date()
    })
    
    // 清空输入框
    recallQuery.value = ''
    
    // 自动切换到召回测试标签
    activeTab.value = 'recall'
  } catch (error) {
    ElMessage.error('召回测试失败')
  }
}

// 当索引变更时重置聊天历史
watch(currentIndex, () => {
  chatHistory.value = []
})

onMounted(() => {
  fetchIndexList()
})
</script>

<style scoped>
.index-management {
  display: flex;
  height: calc(100vh - 64px); /* 减去顶部导航栏高度 */
  overflow: hidden;
}

/* 左侧索引列表样式 */
.index-sidebar {
  width: 380px;
  border-right: 1px solid #e0e0e0;
  background-color: #f8f9fa;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
  background-color: #fff;
}

.sidebar-header h2 {
  margin: 0 0 12px 0;
  font-size: 18px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.index-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.index-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.index-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.index-card.is-active {
  border-left: 4px solid var(--el-color-primary);
}

.index-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.index-card-header h3 {
  margin: 0;
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.index-card-content {
  display: flex;
  flex-direction: column;
}

.description {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.index-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

/* 右侧内容区样式 */
.index-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #fff;
}

.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.content-header {
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.content-header h2 {
  margin: 0;
  font-size: 18px;
}

.content-actions {
  display: flex;
  gap: 8px;
}

.index-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.el-tabs__content) {
  flex: 1;
  overflow: auto;
  padding: 16px;
  height: 100%;
}

:deep(.el-tabs__nav) {
  margin-left: 16px;
}

/* 召回测试样式 */
.recall-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #f9f9f9;
  margin-bottom: 16px;
}

.empty-chat {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-message {
  display: flex;
  flex-direction: column;
  max-width: 85%;
}

.user-message {
  align-self: flex-end;
}

.system-message {
  align-self: flex-start;
}

.message-content {
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.user-message .message-content {
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
}

.system-message .message-content {
  background-color: #fff;
  border: 1px solid #e0e0e0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.message-time {
  color: #999;
}

.user-query {
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

.recall-results {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recall-result {
  display: flex;
  padding: 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
  gap: 12px;
}

.result-score {
  font-weight: bold;
  color: var(--el-color-primary);
  width: 60px;
  flex-shrink: 0;
}

.result-content {
  flex: 1;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-input {
  margin-top: auto;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.hint {
  font-size: 12px;
  color: #999;
}
</style> 