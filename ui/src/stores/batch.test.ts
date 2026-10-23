import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import type { RenderOffer } from '../types'
import { useBatchStore } from './batch'

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
  const store = useBatchStore()
  store.open('b')
  const older = store.check()
  const newer = store.check()

  answers[1]({ disabled: null, images: 2, refused: null })
  await newer
  answers[0]({ disabled: null, images: 5, refused: null })
  await older

  expect(store.offer.images).toBe(2)
})
