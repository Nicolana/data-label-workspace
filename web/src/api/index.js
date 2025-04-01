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

  // 添加文档
  addDocument(indexId, data) {
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

  testRecall: (indexId, params) => {
    return request({
      url: `/indices/${indexId}/recall-test`,
      method: 'post',
      data: params
    })
  }
} 