import request from './request'

export const indexApi = {
  // 创建索引
  createIndex(data) {
    return request.post('/indices', data)
  },

  // 获取索引列表
  getIndices() {
    return request.get('/indices')
  },

  // 获取单个索引
  getIndex(id) {
    return request.get(`/indices/${id}`)
  },

  // 删除索引
  deleteIndex(id) {
    return request.delete(`/indices/${id}`)
  },

  // 重建索引
  rebuildIndex(id) {
    return request.post(`/indices/${id}/rebuild`)
  },

  // 添加文档
  createDocument(indexId, data) {
    return request.post(`/indices/${indexId}/documents`, data)
  },

  // 获取文档列表
  getDocuments(indexId) {
    return request.get(`/indices/${indexId}/documents`)
  },

  // 删除文档
  deleteDocument(indexId, documentId) {
    return request.delete(`/indices/${indexId}/documents/${documentId}`)
  },

  // 召回测试
  testRecall(indexId, data) {
    return request({
      url: `/indices/${indexId}/recall-test`,
      method: 'post',
      data: {
        ...data,
        index_id: indexId
      }
    })
  },

  // 文件上传
  uploadFile(indexId, file, config, metadata = {}) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('config_json', JSON.stringify(config))
    formData.append('metadata_json', JSON.stringify(metadata))
    
    return request({
      url: `/indices/${indexId}/upload-file`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 批量上传
  batchUpload(indexId, files, config, metadata = {}) {
    const formData = new FormData()
    
    // 添加多个文件
    files.forEach(file => {
      formData.append('files', file)
    })
    
    formData.append('config_json', JSON.stringify(config))
    formData.append('metadata_json', JSON.stringify(metadata))
    
    return request({
      url: `/indices/${indexId}/batch-upload`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 索引本地代码仓库
  indexRepository(indexId, repoPath, config, metadata = {}, recursive = true) {
    return request({
      url: `/indices/${indexId}/index-repository`,
      method: 'post',
      data: {
        repo_path: repoPath,
        chunking_config: config,
        recursive: recursive,
        metadata: metadata
      }
    })
  }
} 