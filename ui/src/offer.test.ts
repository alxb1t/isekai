import { createMemoryHistory, createRouter } from 'vue-router'
import { expect } from 'vitest'
import { routes } from './routes'
import { spec } from './test/spec'
import large from './views/RenderLarge.vue?raw'
import { offerTo } from './viewkey'

/* Every screen's and component's source, as the page draws them. */
const SOURCES = import.meta.glob<string>(['./*.vue', './views/*.vue', './components/*.vue'], {
  query: '?raw',
  import: 'default',
  eager: true,
})

const RENDER = {
  collection: 'wedding',
  digest: 'a1b2c3d4e5f6',
  flow: 'summon-anime-wai',
  version: 'v2',
  seed: '41',
}

spec('ui:place-offer:the-button-opens-the-picker', () => {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const there = router.resolve(offerTo(RENDER))
  expect(there.name).toBe('place')
  expect(there.params.step).toBe('tattoo')
  expect(there.path).toBe('/c/wedding/renders/a1b2c3d4e5f6/summon-anime-wai/v2/41/place/tattoo')
  // The button and the command go to that location.
  expect(large).toContain('<RouterLink class="btn btn-secondary" :to="offerTo(props)" data-place')
  expect(large).toContain('router.push(offerTo(props))')
})

spec('ui:place-offer:the-command-is-declared-once', () => {
  expect(large).toContain("id: 'place',\n    keys: [shifted('KeyP')],")
  const taking = Object.entries(SOURCES).flatMap(([file, source]) =>
    source.split('\n').filter((line) => /shifted\('KeyP'\)|code: 'KeyP', shift: true/.test(line)).map(() => file),
  )
  expect(taking).toEqual(['./views/RenderLarge.vue'])
})
