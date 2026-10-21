import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Compare from './views/Compare.vue'
import Hub from './views/Hub.vue'
import RenderLarge from './views/RenderLarge.vue'
import Renders from './views/Renders.vue'
import Review from './views/Review.vue'
import Session from './views/Session.vue'

/* Every screen has a URL naming its batch and its run (design spec §4). The
   server answers any of them with the shell, so a reload lands where it was.
   Navigation goes by name, so the router encodes every parameter. */
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/b/:batch/hub', name: 'hub', component: Hub, props: true },
    { path: '/b/:batch/review/:digest/:flow', name: 'review', component: Review, props: true },
    { path: '/b/:batch/renders', name: 'renders', component: Renders, props: true },
    {
      path: '/b/:batch/renders/:digest/:flow/:version/:seed',
      name: 'render',
      component: RenderLarge,
      props: true,
    },
    {
      path: '/b/:batch/renders/:digest/:flow/:version/:seed/compare',
      name: 'compare',
      component: Compare,
      props: true,
    },
    { path: '/session', name: 'session', component: Session },
    { path: '/:rest(.*)*', redirect: '/' },
  ],
})
