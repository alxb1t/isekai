import { createMemoryHistory, createRouter } from 'vue-router'
import { expect } from 'vitest'
import { routes } from './routes'
import { spec } from './test/spec'
import { HUB_SCREENS, offerTo, viewKey } from './viewkey'

const RENDER = {
  collection: 'wedding',
  digest: 'a1b2c3d4e5f6',
  flow: 'summon-anime-wai',
  version: 'v2',
  seed: '41',
}
const BASE = '/c/wedding/renders/a1b2c3d4e5f6/summon-anime-wai/v2/41'

const made = () => createRouter({ history: createMemoryHistory(), routes })

spec('ui:place-route:a-step-change-keeps-the-screen-mounted', async () => {
  const router = made()
  await router.push(offerTo(RENDER))
  const first = viewKey(router.currentRoute.value)

  await router.push({ name: 'place', params: { ...RENDER, step: 'outline', name: 'bow' } })
  expect(router.currentRoute.value.path).toBe(`${BASE}/place/outline/bow`)
  expect(viewKey(router.currentRoute.value)).toBe(first)

  await router.push({ name: 'place', params: { ...RENDER, step: 'outline', name: 'arm' } })
  expect(viewKey(router.currentRoute.value)).toBe(first)

  // Another render is another screen, and the other screens keep the keys they had.
  await router.push(offerTo({ ...RENDER, seed: '42' }))
  expect(viewKey(router.currentRoute.value)).not.toBe(first)
  expect(viewKey({ name: 'review', path: '/c/a/review/d/f', params: { collection: 'a', flow: 'f' } })).toBe('a/f')
  expect(viewKey({ name: 'hub', path: '/c/a/hub', params: { collection: 'a' } })).toBe('/c/a/hub')

  // The Hub stays lit on the placement screen.
  expect(HUB_SCREENS).toContain('place')
  expect(HUB_SCREENS).toContain('bake')
})

spec('ui:place-route:an-unknown-step-redirects-to-the-first', async () => {
  const router = made()
  for (const path of [`${BASE}/place/dye`, `${BASE}/place/dye/bow`, `${BASE}/place`]) {
    await router.push(path)
    expect(router.currentRoute.value.name).toBe('place')
    expect(router.currentRoute.value.path).toBe(`${BASE}/place/tattoo`)
  }
})

spec('ui:place-route:the-route-does-not-collide-with-compare', () => {
  const router = made()
  expect(router.resolve(`${BASE}/compare/photo`).name).toBe('compare-photo')
  expect(router.resolve(`${BASE}/compare/summon-anime-wai/v1/41`).name).toBe('compare')
  expect(router.resolve(`${BASE}/place/tattoo`).name).toBe('place')
  expect(router.resolve(`${BASE}/place/outline/bow`).params.name).toBe('bow')
  // The stages are steps of the same route, each with the tattoo's name.
  for (const step of ['photo', 'render']) {
    const resolved = router.resolve(`${BASE}/place/${step}/bow`)
    expect(resolved.name).toBe('place')
    expect(resolved.params).toMatchObject({ step, name: 'bow' })
  }
  expect(router.resolve(BASE).name).toBe('render')
})
