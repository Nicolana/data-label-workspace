import request from './request'

export const chatConversationApi = {
  // 创建聊天对话
  createChatConversation(data) {
    return request.post('/chat-conversations', data)
  },

  // 获取聊天对话列表
  getChatConversations() {
    return request.get('/chat-conversations')
  },

  // 获取单个聊天对话
  getChatConversation(id) {
    return request.get(`/chat-conversations/${id}`)
  },

  // 删除聊天对话
  deleteChatConversation(id) {
    return request.delete(`/chat-conversations/${id}`)
  },

  // 更新聊天对话标题
  updateChatConversationTitle(id, title) {
    return request.put(`/chat-conversations/${id}/title`, { title })
  }
}
