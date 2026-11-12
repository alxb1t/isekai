import { createMemoryHistory, createRouter } from 'vue-router'
import { expect } from 'vitest'
import { forward, held, none } from './pairs'
import { routes } from './routes'
import { circled, floorOf, forwardOf, modeOf, shortStep, skipped, startStep, stepsOf } from './stages'
import { spec } from './test/spec'
import type { Pair, Stage1, Tattoo, TattooLimits } from './types'

const LIMITS = {
  floor_stage1: 6,
  floor_stage2: 8,
  floor_direct: 6,
} as TattooLimits

const tattoo = (over: Partial<Tattoo>): Tattoo => ({
  name: 'bow',
  kind: 'image',
  size: [800, 600],
  kept: '2026-11-12T09:30:00.000000Z',
  outlined: true,
  downscaled_from: null,
  cut_from: null,
  ...over,
})

const pairs = (count: number): Pair[] =>
  Array.from({ length: count }, (_, n): Pair => [[n, 0], [n, 1]])

const state = (count: number, flag = false): Stage1 => ({ pairs: pairs(count), not_on_photo: flag })

/* A step with its circled number, as the stepper draws it. */
const marked = (mode: Parameters<typeof stepsOf>[0]) =>
  stepsOf(mode).map(({ step, number }) => `${circled(number)} ${step}`)

spec('ui:stages:the-stepper-lists-the-steps-of-the-mode', () => {
  expect(marked('two-stage')).toEqual(['① tattoo', '② outline', '③ photo', '④ render', '⑤ review'])
  expect(marked('direct')).toEqual(['① tattoo', '② outline', '③ render', '⑤ review'])
  expect(marked('cut')).toEqual(['① tattoo', '② outline', '④ render', '⑤ review'])
  // A number names one screen: the photograph stage is 3 and the render after it is 4.
  expect(stepsOf('two-stage').map((one) => one.label)).toContain('photograph ↔ render')
  expect(stepsOf('direct').map((one) => one.label)).toContain('tattoo ↔ render')
})

spec('ui:stages:forward-goes-to-the-stage-of-the-mode', () => {
  const closed = { closed: true, points: 24 }

  expect(forwardOf('two-stage', closed)).toEqual({ step: 'photo', wait: null })
  expect(forwardOf('direct', closed)).toEqual({ step: 'render', wait: null })
  expect(forwardOf('cut', closed)).toEqual({ step: 'render', wait: null })
})

spec('ui:stages:forward-waits-for-a-closed-outline', () => {
  expect(forwardOf('two-stage', { closed: false, points: 27 })).toEqual({
    step: null,
    wait: 'outline open · 27 points',
  })
  expect(forwardOf('cut', { closed: false, points: 1 }).wait).toBe('outline open · 1 point')
  expect(forwardOf('cut', { closed: false, points: 0 }).wait).toBe('outline open · 0 points')
})

spec('ui:direct:the-flag-skips-stage-1', () => {
  const flagged = modeOf('image', true)

  expect(flagged).toBe('direct')
  expect(stepsOf(flagged).map((one) => one.step)).not.toContain('photo')
  expect(modeOf('image', false)).toBe('two-stage')
  expect(modeOf('cut', false)).toBe('cut')
  // A cut keeps its mode whatever its flag says.
  expect(modeOf('cut', true)).toBe('cut')
})

spec('ui:direct:the-direct-stage-has-its-own-floor', () => {
  const five = held(pairs(5))

  expect(floorOf('direct', 'render', LIMITS)).toBe(6)
  expect(forward(five, floorOf('direct', 'render', LIMITS))).toBe('6 pairs needed · 5 placed')
  expect(forward(none, floorOf('two-stage', 'photo', LIMITS))).toBe('6 pairs needed · 0 placed')
  expect(floorOf('two-stage', 'render', LIMITS)).toBe(8)
  expect(floorOf('cut', 'render', LIMITS)).toBe(8)
})

spec('ui:picker:a-card-opens-the-step-its-state-asks', () => {
  expect(startStep(tattoo({ outlined: false }), undefined, 6)).toBe('outline')
  expect(startStep(tattoo({}), undefined, 6)).toBe('photo')
  expect(startStep(tattoo({}), state(5), 6)).toBe('photo')
  expect(startStep(tattoo({}), state(6), 6)).toBe('render')
  // A flagged upload and a cut have no stage 1.
  expect(startStep(tattoo({}), state(0, true), 6)).toBe('render')
  expect(startStep(tattoo({ kind: 'cut', cut_from: 'a1b2c3d4e5f6' }), undefined, 6)).toBe('render')
  expect(startStep(tattoo({ kind: 'cut', outlined: false }), undefined, 6)).toBe('outline')
})

spec('ui:place-route:a-skipped-step-redirects-to-the-step-in-its-place', async () => {
  expect(skipped('cut', 'photo')).toBe('render')
  expect(skipped('direct', 'photo')).toBe('render')
  expect(skipped('two-stage', 'photo')).toBe('photo')
  expect(skipped('cut', 'render')).toBe('render')
  expect(skipped('direct', 'outline')).toBe('outline')
  // The review before the stages' floors goes to the earliest stage short of its floor.
  expect(skipped('two-stage', 'review', 'photo')).toBe('photo')
  expect(skipped('cut', 'review', 'render')).toBe('render')
  expect(skipped('cut', 'review')).toBe('review')
  expect(shortStep('two-stage', { first: 5, second: 0 }, LIMITS)).toBe('photo')
  expect(shortStep('two-stage', { first: 6, second: 7 }, LIMITS)).toBe('render')
  expect(shortStep('two-stage', { first: 6, second: 8 }, LIMITS)).toBeNull()
  expect(shortStep('direct', { first: 0, second: 5 }, LIMITS)).toBe('render')
  expect(shortStep('direct', { first: 0, second: 6 }, LIMITS)).toBeNull()
  expect(shortStep('cut', { first: 0, second: 7 }, LIMITS)).toBe('render')

  // The route knows the steps; the screen replaces it with the step the read mode takes.
  const router = createRouter({ history: createMemoryHistory(), routes })
  const base = '/c/wedding/renders/a1b2c3d4e5f6/summon-anime-wai/v2/41/place'
  await router.push(`${base}/photo/arm`)
  expect(router.currentRoute.value.name).toBe('place')
  expect(router.currentRoute.value.params.step).toBe('photo')
  const asked = router.currentRoute.value.params
  await router.replace({
    name: 'place',
    params: { ...asked, step: skipped('cut', asked.step as 'photo') },
  })
  expect(router.currentRoute.value.path).toBe(`${base}/render/arm`)
})
