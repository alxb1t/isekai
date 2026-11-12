import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import type { RenderOffer } from '../types'
import { kept } from '../grid'
import { useCollectionStore } from './collection'

/* Each offer request waits on its own answer, released in whatever order a test chooses. */
let answers: ((offer: RenderOffer) => void)[]

/* An offer holding nothing. */
const held: RenderOffer = {
  disabled: null,
  images: 0,
  others: 0,
  bakes: 0,
  other_bakes: 0,
  refused: null,
}

beforeEach(() => {
  setActivePinia(createPinia())
  answers = []
  vi.stubGlobal(
    'fetch',
    () =>
      new Promise((resolve) =>
        answers.push((offer) => resolve({ ok: true, json: async () => offer })),
      ),
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
})

spec('ui:render:a-stale-offer-is-dropped', async () => {
  const store = useCollectionStore()
  store.open('b')
  const older = store.check()
  const newer = store.check()

  answers[1]({ ...held, images: 2 })
  await newer
  answers[0]({ ...held, images: 5 })
  await older

  expect(store.offer.images).toBe(2)
})

spec('ui:render:a-bar-counts-a-bake-alone', async () => {
  const store = useCollectionStore()
  store.open('b')
  const read = store.check()
  answers[0]({ ...held, other_bakes: 1 })
  await read

  expect(store.offer.other_bakes).toBe(1)
  store.openDialog()
  expect(store.dialog).toBe(true)

  store.dialog = false
  const empty = store.check()
  answers[1](held)
  await empty
  store.openDialog()
  expect(store.dialog).toBe(false)
})

spec('ui:hub:the-hub-keeps-its-focus', () => {
  const store = useCollectionStore()
  const name = (one: string) => one
  store.open('b')
  expect(kept(['a', 'b', 'c'], name, store.focus.hub)).toBe('a')
  store.focus.hub = 'b'
  store.open('b')
  expect(kept(['a', 'b', 'c'], name, store.focus.hub)).toBe('b')
  // A spot gone since is the first; another collection starts from the first.
  expect(kept(['a', 'c'], name, store.focus.hub)).toBe('a')
  store.open('c')
  expect(store.focus).toEqual({ hub: null })
})
