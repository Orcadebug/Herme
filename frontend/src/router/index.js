import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import SportsProcessView from '../views/SportsProcessView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/sports/:workspaceId',
    name: 'SportsProcess',
    component: SportsProcessView,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
