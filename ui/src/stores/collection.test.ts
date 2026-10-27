import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import type { RenderOffer } from '../types'
import { kept } from '../grid'
import { useCollectionStore } from './collection'

/* Each offer request waits on its own answer, released in whatever order a test chooses. */
let answers: ((offer: RenderOffer) => void)[]

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

  answers[1]({ disabled: null, images: 2, refused: null })
  await newer
  answers[0]({ disabled: null, images: 5, refused: null })
  await older

  expect(store.offer.images).toBe(2)
})

spec('ui:renders:a-grid-keeps-its-focus', () => {
  const store = useCollectionStore()
  const name = (one: string) => one
  store.open('b')
  expect(kept(['a', 'b', 'c'], name, store.focus.renders)).toBe('a')
  store.focus.renders = 'b'
  store.open('b')
  expect(kept(['a', 'b', 'c'], name, store.focus.renders)).toBe('b')
  // A spot gone since is the first; another collection starts from the first.
  expect(kept(['a', 'c'], name, store.focus.renders)).toBe('a')
  store.open('c')
  expect(store.focus).toEqual({ hub: null, renders: null })
})
