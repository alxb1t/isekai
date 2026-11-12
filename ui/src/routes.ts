import type { RouteRecordRaw } from 'vue-router'
import Billing from './views/Billing.vue'
import Compare from './views/Compare.vue'
import Home from './views/Home.vue'
import Hub from './views/Hub.vue'
import Place from './views/Place.vue'
import RenderLarge from './views/RenderLarge.vue'
import Review from './views/Review.vue'
import ReviewHead from './views/ReviewHead.vue'

/* Every screen has a URL naming its collection and its run (design spec §4). The
   server answers any of them with the shell, so a reload lands where it was.
   Navigation goes by name, so the router encodes every parameter. The table lives
   here, apart from `router.ts`, so a test builds a router on a memory history. */
const RENDER = '/c/:collection/renders/:digest/:flow/:version/:seed'

export const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: Home },
  { path: '/c/:collection/hub', name: 'hub', component: Hub, props: true },
  { path: '/c/:collection/review', name: 'review-head', component: ReviewHead, props: true },
  { path: '/c/:collection/review/:digest/:flow', name: 'review', component: Review, props: true },
  { path: RENDER, name: 'render', component: RenderLarge, props: true },
  { path: `${RENDER}/edit/:k`, name: 'bake', component: RenderLarge, props: true },
  { path: `${RENDER}/compare/photo`, name: 'compare-photo', component: Compare, props: true },
  {
    path: `${RENDER}/compare/:withFlow/:withVersion/:withSeed`,
    name: 'compare',
    component: Compare,
    props: true,
  },
  {
    path: `${RENDER}/place/:step(tattoo|outline|photo|render|review)/:name?`,
    name: 'place',
    component: Place,
    props: true,
  },
  {
    path: `${RENDER}/place/:other(.*)*`,
    redirect: (to) => {
      const { other: _other, ...render } = to.params
      return { name: 'place', params: { ...render, step: 'tattoo' } }
    },
  },
  { path: '/billing', name: 'billing', component: Billing },
  { path: '/:rest(.*)*', redirect: '/' },
]
