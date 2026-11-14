import { expect } from 'vitest'
import { held, none } from './pairs'
import { type Placement, bakeState, fitted, summary } from './review'
import { spec } from './test/spec'
import type { Outline, Pair, TattooLimits } from './types'

const LIMITS = {
  floor_stage1: 6,
  floor_stage2: 8,
  floor_direct: 6,
  photo_depth: 1.6,
  image_depth: 1.0,
} as TattooLimits

const outline = (over: Partial<Outline> = {}): Outline => ({
  points: Array.from({ length: 36 }, (_, n): [number, number] => [n, n]),
  closed: true,
  white: 1,
  neutral: true,
  depth: 1.6,
  ...over,
})

const pairs = (count: number): Pair[] =>
  Array.from({ length: count }, (_, n): Pair => [[n, 0], [n, 1]])

const cut = (over: Partial<Placement> = {}): Placement => ({
  tattoo: { name: 'bow', kind: 'cut', kept: '2026-11-12T09:30:00.000000Z', outline: outline() },
  mode: 'cut',
  photograph: 'meadow_02',
  automatic: 119,
  seed: '42',
  edit: null,
  first: [],
  second: pairs(8),
  limb: null,
  exclusions: [],
  limits: LIMITS,
  ...over,
})

const upload = (tone: Partial<Outline>, over: Partial<Placement> = {}): Placement =>
  cut({
    tattoo: {
      name: 'bow',
      kind: 'image',
      kept: '2026-11-12T09:30:00.000000Z',
      outline: outline({ neutral: false, depth: 1, ...tone }),
    },
    mode: 'two-stage',
    first: pairs(6),
    ...over,
  })

spec('ui:review:the-tattoo-row-names-the-source-and-the-white-point', () => {
  expect(summary(cut()).tattoo).toBe(
    'bow · cut from meadow_02 · outline 36 points · white 119 · neutral · depth 1.6',
  )
  // A white set by hand is the scale on the automatic grey, as the outline step shows it.
  expect(summary(cut({ tattoo: { ...cut().tattoo, outline: outline({ white: 0.9 }) } })).tattoo).toContain(
    'white 107',
  )
  // Until the preview answers there is no grey to name.
  expect(summary(cut({ automatic: null })).tattoo).not.toContain('white')
})

spec('ui:review:an-uploads-default-tone-is-left-out', () => {
  const plain = summary(upload({})).tattoo
  expect(plain).toBe('bow · kept 2026-11-12 · outline 36 points · white 119')
  expect(plain).not.toMatch(/neutral|depth/)

  expect(summary(upload({ depth: 1.4 })).tattoo).toBe(
    'bow · kept 2026-11-12 · outline 36 points · white 119 · depth 1.4',
  )
  expect(summary(upload({ neutral: true })).tattoo).toContain('neutral · depth 1')
})

spec('ui:review:the-summary-lists-the-pairs-of-the-mode', () => {
  expect(summary(upload({})).stages).toEqual([
    'stage 1 · tattoo ↔ photograph · 6 pairs',
    'stage 2 · photograph ↔ render · 8 pairs',
  ])
  expect(summary(upload({}, { mode: 'direct', first: [], second: pairs(6) })).stages).toEqual([
    'tattoo ↔ render · 6 pairs',
  ])
  expect(summary(cut()).stages).toEqual(['stage 2 · photograph ↔ render · 8 pairs'])
  expect(summary(cut({ second: pairs(1) })).stages).toEqual(['stage 2 · photograph ↔ render · 1 pair'])

  const square = [[0, 0], [9, 0], [9, 9]] as [number, number][]
  const placed = summary(cut({ limb: square, exclusions: [square.slice(0, 3), square.slice(0, 3)] }))
  expect(placed.outlines).toEqual([
    'limb · 3 points · keeps',
    'exclusion 1 · 3 points · removes',
    'exclusion 2 · 3 points · removes',
  ])
  expect(summary(cut()).outlines).toEqual(['no limb or exclusion'])
  expect(summary(cut()).image).toBe('seed 42')
  expect(summary(cut({ edit: 3 })).image).toBe('edit 3 · seed 42')
})

spec('ui:review:the-crops-are-fitted-to-their-columns', () => {
  const render = { width: 1100, height: 600 }

  expect(fitted({ x: 250, y: 275, width: 100, height: 50 }, render)).toEqual({
    aspectRatio: '100 / 50',
    backgroundSize: '1100%',
    backgroundPosition: '25% 50%',
  })

  // An axis the box fills has nothing left to offset by, and places at 0%.
  expect(fitted({ x: 0, y: 100, width: 1100, height: 200 }, render)).toEqual({
    aspectRatio: '1100 / 200',
    backgroundSize: '100%',
    backgroundPosition: '0% 25%',
  })
})

spec('ui:review:bake-waits-for-a-stage-and-then-queues', () => {
  const state = (over: Partial<Parameters<typeof bakeState>[0]> = {}) =>
    bakeState({
      mode: 'cut',
      first: none,
      second: held(pairs(5)),
      limits: LIMITS,
      asking: false,
      edit: null,
      refusal: null,
      ...over,
    })

  expect(state()).toEqual({ phase: 'waiting', text: 'stage 2 · 8 pairs needed · 5 placed', enabled: false })
  expect(state({ second: held(pairs(8)) })).toEqual({ phase: 'ready', text: '', enabled: true })
  expect(state({ second: held(pairs(8)), asking: true })).toMatchObject({ phase: 'baking', enabled: false })
  expect(state({ second: held(pairs(8)), edit: 3 })).toEqual({
    phase: 'queued',
    text: 'queued · edit 3 · next render session',
    enabled: false,
  })
  // A refusal is shown and the bake may be asked again.
  expect(state({ second: held(pairs(8)), refusal: 'the render is gone' })).toEqual({
    phase: 'refused',
    text: 'the render is gone',
    enabled: true,
  })

  // Stage 1 of a two-stage tattoo is named first; a direct tattoo has its own floor.
  expect(state({ mode: 'two-stage', first: held(pairs(4)), second: held(pairs(8)) }).text).toBe(
    'stage 1 · 6 pairs needed · 4 placed',
  )
  expect(state({ mode: 'direct', second: held(pairs(5)) }).text).toBe('tattoo ↔ render · 6 pairs needed · 5 placed')
  expect(state({ mode: 'direct', second: held(pairs(6)) }).phase).toBe('ready')
})
