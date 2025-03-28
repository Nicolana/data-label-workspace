import { createRouter, createWebHistory } from 'vue-router'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import HomeView from '../views/HomeView.vue'
import ChatView from '../views/ChatView.vue'
import ConversationDetailView from '../views/ConversationDetailView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: DefaultLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: HomeView
        }
      ]
    },
    {
      path: '/chat',
      component: DefaultLayout,
      children: [
        {
          path: '',
          name: 'chat',
          component: ChatView
        }
      ]
    },
    {
      path: '/conversation/:id',
      component: DefaultLayout,
      children: [
        {
          path: '',
          name: 'conversation-detail',
          component: ConversationDetailView
        }
      ]
    }
  ]
})

export default router 