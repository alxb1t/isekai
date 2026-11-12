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
import type { Tattoo } from './types'

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

spec('ui:picker:the-cards-show-the-state-and-the-source', () => {
  const upload = card(tattoo({ outlined: true }), DIGEST)
  expect(upload).toEqual({
    state: 'outlined',
    source: 'kept 2026-11-12',
    choosable: true,
    reason: null,
  })
  const cut = card(tattoo({ kind: 'cut', cut_from: DIGEST }), DIGEST)
  expect(cut.state).toBe('not outlined')
  expect(cut.source).toBe(`from photograph ${DIGEST}`)
  // The size an upload came with, when it was scaled down.
  const scaled = card(tattoo({ downscaled_from: [5000, 3000] }), DIGEST)
  expect(scaled.source).toBe('kept 2026-11-12 · downscaled from 5000×3000')
})

spec('ui:picker:an-uploads-name-starts-as-the-files-stem', () => {
  expect(uploadName('IMG_5521.heic')).toBe('IMG_5521')
  expect(uploadName('a.b.png')).toBe('a.b')
  expect(uploadName('plain')).toBe('plain')
  expect(uploadName('.hidden')).toBe('.hidden')
})

spec('ui:picker:a-cut-of-another-photograph-cannot-be-chosen', () => {
  const other = card(tattoo({ kind: 'cut', cut_from: 'ffffffffffff' }), DIGEST)
  expect(other.choosable).toBe(false)
  expect(other.reason).toContain('ffffffffffff')
  expect(card(tattoo({ kind: 'cut', cut_from: DIGEST }), DIGEST).choosable).toBe(true)
  // An upload serves every render.
  expect(card(tattoo({}), 'ffffffffffff').choosable).toBe(true)
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
