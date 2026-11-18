import { effectScope } from 'vue'
import { afterEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import type { Outline } from '../types'
import { useCutInk } from './useCutInk'

const closed: Outline = {
  points: [
    [0, 0],
    [10, 0],
    [10, 10],
  ],
  closed: true,
  white: 0.5,
  neutral: false,
  depth: 0,
}

/** A card whose ink view the case answers by hand, ignoring the signal as a late abort does. */
function card() {
  let answer: () => void = () => undefined
  const ink = () =>
    new Promise<{ image: Blob }>((resolve) => {
      answer = () => resolve({ image: new Blob(['ink']) })
    })
  const scope = effectScope()
  const read = scope.run(() => useCutInk({ outline: () => Promise.resolve(closed), ink }))!
  return { scope, read, answer: () => answer() }
}

const afterTheOutline = () => new Promise<void>((resolve) => setTimeout(resolve, 0))

afterEach(() => vi.restoreAllMocks())

spec('ui:picker:a-crop-that-lands-after-leaving-is-dropped', async () => {
  const made = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:ink')
  const revoked = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined)

  // The card is left before the ink view answers: no object URL is made for it.
  const left = card()
  const first = left.read.load()
  await afterTheOutline()
  left.scope.stop()
  left.answer()
  await first
  expect(made).not.toHaveBeenCalled()
  expect(left.read.ink.value).toBeNull()
  expect(revoked).not.toHaveBeenCalled()

  // The card stays: the answer is shown, and the URL is released when the card is left.
  const kept = card()
  const second = kept.read.load()
  await afterTheOutline()
  kept.answer()
  await second
  expect(made).toHaveBeenCalledTimes(1)
  expect(kept.read.ink.value).toBe('blob:ink')
  expect(revoked).not.toHaveBeenCalled()
  kept.scope.stop()
  expect(revoked).toHaveBeenCalledWith('blob:ink')
})
