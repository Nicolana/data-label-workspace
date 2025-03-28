import { createRouter, createWebHistory } from 'vue-router'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import HomeView from '../views/HomeView.vue'
import ChatView from '../views/ChatView.vue'
import ConversationDetailView from '../views/ConversationDetailView.vue'
import IndexManagementView from '../views/IndexManagementView.vue'

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
        },
        {
          path: 'chat',
          name: 'chat',
          component: ChatView,
          props: { showSidebar: false }
        },
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
    },
    {
      path: '/indices',
      component: DefaultLayout,
      children: [
        {
          path: '',
          name: 'indices',
          component: IndexManagementView
        }
      ]
    }
  ]
})

export default router 