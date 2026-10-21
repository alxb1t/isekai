import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Hub from './views/Hub.vue'
import Review from './views/Review.vue'

/* Every screen has a URL naming its batch and its run (design spec §4). The
   server answers any of them with the shell, so a reload lands where it was.
   Navigation goes by name, so the router encodes every parameter. */
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/b/:batch/hub', name: 'hub', component: Hub, props: true },
    { path: '/b/:batch/review/:digest/:flow', name: 'review', component: Review, props: true },
    { path: '/:rest(.*)*', redirect: '/' },
  ],
})
