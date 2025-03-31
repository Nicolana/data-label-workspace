import request from './request'

export const conversationApi = {
  // 创建对话
  createConversation(data) {
    return request.post('/conversations', data)
  },

  // 获取对话列表
  getConversations() {
    return request.get('/conversations')
  },

  // 获取单个对话
  getConversation(id) {
    return request.get(`/conversations/${id}`)
  },

  // 删除对话
  deleteConversation(id) {
    return request.delete(`/conversations/${id}`)
  },

  // 复制对话
  copyConversation(id) {
    return request.post(`/conversations/${id}/copy`)
  },
} 

