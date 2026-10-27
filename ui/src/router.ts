import { createRouter, createWebHistory } from 'vue-router'
import Billing from './views/Billing.vue'
import Home from './views/Home.vue'
import Compare from './views/Compare.vue'
import Hub from './views/Hub.vue'
import RenderLarge from './views/RenderLarge.vue'
import Renders from './views/Renders.vue'
import Review from './views/Review.vue'
import ReviewHead from './views/ReviewHead.vue'

/* Every screen has a URL naming its collection and its run (design spec §4). The
   server answers any of them with the shell, so a reload lands where it was.
   Navigation goes by name, so the router encodes every parameter. */
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: Home },
    { path: '/c/:collection/hub', name: 'hub', component: Hub, props: true },
    { path: '/c/:collection/review', name: 'review-head', component: ReviewHead, props: true },
    { path: '/c/:collection/review/:digest/:flow', name: 'review', component: Review, props: true },
    { path: '/c/:collection/renders', name: 'renders', component: Renders, props: true },
    {
      path: '/c/:collection/renders/:digest/:flow/:version/:seed',
      name: 'render',
      component: RenderLarge,
      props: true,
    },
    {
      path: '/c/:collection/renders/:digest/:flow/:version/:seed/compare/photo',
      name: 'compare-photo',
      component: Compare,
      props: true,
    },
    {
      path: '/c/:collection/renders/:digest/:flow/:version/:seed/compare/:withFlow/:withVersion/:withSeed',
      name: 'compare',
      component: Compare,
      props: true,
    },
    { path: '/billing', name: 'billing', component: Billing },
    { path: '/:rest(.*)*', redirect: '/' },
  ],
})
