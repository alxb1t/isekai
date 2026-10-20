import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Hub from './views/Hub.vue'
import Review from './views/Review.vue'

/* Every screen has a URL naming its batch and its run (design spec §4). The
   server answers any of them with the shell, so a reload lands where it was. */
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/b/:batch/hub', component: Hub, props: true },
    { path: '/b/:batch/review/:digest/:flow', component: Review, props: true },
    { path: '/:rest(.*)*', redirect: '/' },
  ],
})
