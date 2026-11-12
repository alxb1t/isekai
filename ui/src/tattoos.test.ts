import { expect } from 'vitest'
import { spec } from './test/spec'
import {
  card,
  controlsWait,
  defaultTone,
  differs,
  greyOf,
  inkSize,
  refusalField,
  scaleOf,
  uploadName,
  whiteState,
} from './tattoos'
import type { Pair, Stage1, Tattoo } from './types'

const DIGEST = 'a1b2c3d4e5f6'

function tattoo(over: Partial<Tattoo>): Tattoo {
  return {
    name: 'bow',
    kind: 'image',
    size: [800, 600],
    kept: '2026-11-12T09:30:00.000000Z',
    outlined: false,
    downscaled_from: null,
    cut_from: null,
    ...over,
  }
}

const FLOOR = 6

const stage = (count: number, flag = false): Stage1 => ({
  pairs: Array.from({ length: count }, (_, n): Pair => [[n, 0], [n, 1]]),
  not_on_photo: flag,
})

spec('ui:picker:the-cards-show-the-state-and-the-source', () => {
  const upload = card(tattoo({ outlined: true }), DIGEST, undefined, FLOOR)
  expect(upload).toEqual({
    state: 'outlined',
    source: 'kept 2026-11-12',
    choosable: true,
    reason: null,
    stage: null,
    offers: true,
    opens: 'photo',
  })
  const cut = card(tattoo({ kind: 'cut', cut_from: DIGEST }), DIGEST, undefined, FLOOR)
  expect(cut.state).toBe('not outlined')
  expect(cut.source).toBe(`from photograph ${DIGEST}`)
  // The size an upload came with, when it was scaled down.
  const scaled = card(tattoo({ downscaled_from: [5000, 3000] }), DIGEST, undefined, FLOOR)
  expect(scaled.source).toBe('kept 2026-11-12 · downscaled from 5000×3000')
})

spec('ui:picker:a-card-is-ready-for-this-photograph', () => {
  const upload = card(tattoo({ outlined: true }), DIGEST, stage(6), FLOOR)
  const cut = card(tattoo({ kind: 'cut', cut_from: DIGEST, outlined: true }), DIGEST, undefined, FLOOR)

  expect(upload.state).toBe('ready for this photograph')
  expect(upload.stage).toBe('stage 1 · 6 pairs')
  expect(cut.state).toBe('ready for this photograph')
  // Short of the floor, an upload is outlined and no more; flagged, it is ready.
  expect(card(tattoo({ outlined: true }), DIGEST, stage(5), FLOOR).state).toBe('outlined')
  expect(card(tattoo({ outlined: true }), DIGEST, stage(5), FLOOR).stage).toBe('stage 1 · 5 pairs')
  const flagged = card(tattoo({ outlined: true }), DIGEST, stage(0, true), FLOOR)
  expect(flagged.state).toBe('ready for this photograph')
  expect(flagged.stage).toBe('not on this photo')
  // Not outlined is never ready, and a cut of another photograph is not either.
  expect(card(tattoo({ outlined: false }), DIGEST, stage(9), FLOOR).state).toBe('not outlined')
  const other = card(tattoo({ kind: 'cut', cut_from: 'ffffffffffff', outlined: true }), DIGEST, undefined, FLOOR)
  expect(other.state).toBe('outlined')
  expect(card(tattoo({ outlined: true }), DIGEST, stage(1), FLOOR).stage).toBe('stage 1 · 1 pair')
})

spec('ui:picker:a-card-opens-the-step-its-state-asks', () => {
  expect(card(tattoo({ outlined: false }), DIGEST, undefined, FLOOR).opens).toBe('outline')
  expect(card(tattoo({ outlined: true }), DIGEST, stage(2), FLOOR).opens).toBe('photo')
  expect(card(tattoo({ outlined: true }), DIGEST, stage(6), FLOOR).opens).toBe('render')
  expect(card(tattoo({ outlined: true }), DIGEST, stage(0, true), FLOOR).opens).toBe('render')
  expect(
    card(tattoo({ kind: 'cut', cut_from: DIGEST, outlined: true }), DIGEST, undefined, FLOOR).opens,
  ).toBe('render')
})

spec(['ui:picker:not-on-this-photo-is-offered-on-an-upload-alone', 'ui:direct:a-cut-does-not-offer-the-flag'], () => {
  expect(card(tattoo({}), DIGEST, undefined, FLOOR).offers).toBe(true)
  expect(card(tattoo({ kind: 'cut', cut_from: DIGEST }), DIGEST, undefined, FLOOR).offers).toBe(false)
  expect(card(tattoo({ kind: 'cut', cut_from: 'ffffffffffff' }), DIGEST, undefined, FLOOR).offers).toBe(false)
})

spec('ui:picker:an-uploads-name-starts-as-the-files-stem', () => {
  expect(uploadName('IMG_5521.heic')).toBe('IMG_5521')
  expect(uploadName('a.b.png')).toBe('a.b')
  expect(uploadName('plain')).toBe('plain')
  expect(uploadName('.hidden')).toBe('.hidden')
})

spec('ui:picker:a-cut-of-another-photograph-cannot-be-chosen', () => {
  const other = card(tattoo({ kind: 'cut', cut_from: 'ffffffffffff' }), DIGEST, undefined, FLOOR)
  expect(other.choosable).toBe(false)
  expect(other.reason).toContain('ffffffffffff')
  expect(card(tattoo({ kind: 'cut', cut_from: DIGEST }), DIGEST, undefined, FLOOR).choosable).toBe(true)
  // An upload serves every render.
  expect(card(tattoo({}), 'ffffffffffff', undefined, FLOOR).choosable).toBe(true)
})

spec('ui:picker:a-refusal-shows-its-fix', () => {
  expect(refusalField('bow is kept; choose another name')).toBe('name')
  expect(refusalField("'.x' is not a folder name: it starts with a dot; choose another name")).toBe('name')
  expect(refusalField('photo.heic still carries exif; clean it as an import does, then keep it')).toBe('file')
})

spec('ui:outline-step:the-white-grey-converts-to-a-scale-and-back', () => {
  expect(scaleOf(180, 200)).toBeCloseTo(0.9, 9)
  expect(greyOf(200, scaleOf(180, 200))).toBe(180)
  expect(greyOf(201, 0.5)).toBe(101)
  // The grey is held to 1..255, so a scale is never zero, and no automatic grey divides by zero.
  expect(scaleOf(0, 200)).toBeGreaterThan(0)
  expect(scaleOf(900, 200)).toBeCloseTo(255 / 200, 9)
  expect(scaleOf(10, 0)).toBe(1)
})

spec('ui:outline-step:a-scale-of-one-is-automatic', () => {
  expect(whiteState(1)).toBe('auto')
  expect(whiteState(0.9)).toBe('set by hand')
  expect(whiteState(scaleOf(200, 200))).toBe('auto')
})

spec('ui:outline-step:reset-appears-when-the-tone-differs', () => {
  const limits = { photo_depth: 1.6, image_depth: 1.0 }
  const cut = defaultTone('cut', limits)
  expect(cut).toEqual({ neutral: true, depth: 1.6 })
  expect(defaultTone('image', limits)).toEqual({ neutral: false, depth: 1.0 })
  expect(differs(cut, cut)).toBe(false)
  expect(differs({ neutral: true, depth: 1.4 }, cut)).toBe(true)
  expect(differs({ neutral: false, depth: 1.6 }, cut)).toBe(true)
})

spec('ui:outline-step:the-controls-wait-for-a-closed-outline', () => {
  expect(controlsWait({ closed: false })).toBe('outline open')
  expect(controlsWait({ closed: true })).toBeNull()
})

spec('ui:outline-step:the-size-of-the-cuts-ink-is-the-outlines-box', () => {
  expect(inkSize({ width: 412.4, height: 300.6 })).toBe('412×301')
  expect(inkSize(null)).toBeNull()
})

spec('ui:outline-step:uploading-instead-keeps-the-cut', () => {
  expect(uploadName('scan.png', 'bow')).toBe('bow_closeup')
})
