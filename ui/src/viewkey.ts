import type { RouteLocationRaw } from 'vue-router'

/* What the shell keys its screen by, which screens keep the Hub's tab lit, and where
   a render's *Place a tattoo* goes. Plain functions, so a test reads them in node. */

/** The screens the Hub's tab stays lit on: the Hub, and what opens from it — the large
    view, a bake's, Compare and the placement screen. */
export const HUB_SCREENS = ['hub', 'render', 'bake', 'compare', 'compare-photo', 'place']

/** What `viewKey` reads of a route. */
export interface Viewed {
  name?: string | symbol | null
  path: string
  params: Record<string, string | string[]>
}

const STEP = /\/place\/(?:tattoo|outline|photo|render|review)(?:\/[^/]*)?$/

/** Return the key a screen is mounted under, so a new key mounts it again. A review is
    one per collection and flow; the placement screen is one per render, whatever its
    step or tattoo. e.g. `/c/a/renders/d/f/v1/7/place/outline/bow` -> `/c/a/renders/d/f/v1/7` */
export function viewKey(route: Viewed): string {
  if (route.name === 'review') return `${String(route.params.collection)}/${String(route.params.flow)}`
  if (route.name === 'place') return route.path.replace(STEP, '')
  return route.path
}

/** What `offerTo` reads of a render's address. */
export interface Offered {
  collection: string
  digest: string
  flow: string
  version: string
  seed: string
}

/** Return the placement screen's first step on a render, where its button and `⇧P` go. */
export function offerTo(place: Offered): RouteLocationRaw {
  const { collection, digest, flow, version, seed } = place
  return { name: 'place', params: { collection, digest, flow, version, seed, step: 'tattoo' } }
}
