import { expect } from 'vitest'
import { spec } from './test/spec'
import type { Point } from './types'
import {
  KEPT_IN_VIEW,
  SCALE_CEILING,
  SCALE_FLOOR,
  actual,
  fitted,
  panned,
  toImage,
  toScreen,
  zoomedAt,
} from './zoom'

const IMAGE = { width: 400, height: 200 }
const VIEWPORT = { width: 200, height: 200 }

function near(got: Point, want: Point): void {
  expect(got[0]).toBeCloseTo(want[0], 6)
  expect(got[1]).toBeCloseTo(want[1], 6)
}

spec('ui:panel:a-zoom-keeps-the-point-under-the-pointer', () => {
  const view = fitted(IMAGE, VIEWPORT)
  for (const pointer of [[30, 80], [199, 1], [100, 100]] as Point[]) {
    const under = toImage(view, pointer)
    for (const factor of [2, 0.5, 3.3]) {
      const next = zoomedAt(view, factor, pointer)
      near(toScreen(next, under), pointer)
    }
  }
  expect(zoomedAt(view, 2, [30, 80]).scale).toBeCloseTo(view.scale * 2, 9)
})

spec('ui:panel:a-zoom-is-held-between-the-floor-and-the-ceiling', () => {
  const view = { scale: 1, x: 0, y: 0 }
  expect(zoomedAt(view, 1000, [10, 10]).scale).toBe(SCALE_CEILING)
  expect(zoomedAt(view, 0.0001, [10, 10]).scale).toBe(SCALE_FLOOR)
  // A fitted image smaller than the floor may be zoomed out to its own fit, no further.
  expect(zoomedAt(view, 0.0001, [10, 10], 0.1).scale).toBe(0.1)
})

spec('ui:panel:a-pan-keeps-part-of-the-image-in-view', () => {
  const view = { scale: 1, x: 0, y: 0 }
  const left = panned(view, -100000, 0, IMAGE, VIEWPORT)
  expect(left.x + IMAGE.width).toBe(KEPT_IN_VIEW)
  const right = panned(view, 100000, 0, IMAGE, VIEWPORT)
  expect(right.x).toBe(VIEWPORT.width - KEPT_IN_VIEW)
  const up = panned(view, 0, -100000, IMAGE, VIEWPORT)
  expect(up.y + IMAGE.height).toBe(KEPT_IN_VIEW)
  const down = panned(view, 0, 100000, IMAGE, VIEWPORT)
  expect(down.y).toBe(VIEWPORT.height - KEPT_IN_VIEW)
  // A pan inside the allowance moves the view exactly, and never the scale.
  expect(panned(view, -10, 20, IMAGE, VIEWPORT)).toEqual({ scale: 1, x: -10, y: 20 })
  // An image drawn smaller than the allowance keeps all of itself in view.
  const small = panned({ scale: 0.01, x: 0, y: 0 }, -100000, 0, IMAGE, VIEWPORT)
  expect(small.x).toBe(0)
})

spec('ui:panel:fit-and-one-to-one', () => {
  const fit = fitted(IMAGE, VIEWPORT)
  expect(fit.scale).toBe(0.5)
  near(toScreen(fit, [0, 0]), [0, 50])
  near(toScreen(fit, [IMAGE.width, IMAGE.height]), [200, 150])

  const one = actual(fit, VIEWPORT)
  expect(one.scale).toBe(1)
  // One image pixel is one screen pixel, and the viewport's centre keeps its image point.
  expect(toScreen(one, [201, 100])[0] - toScreen(one, [200, 100])[0]).toBe(1)
  near(toImage(one, [100, 100]), toImage(fit, [100, 100]))
})

spec('ui:panel:a-point-converts-both-ways', () => {
  const view = { scale: 2.5, x: -37, y: 12 }
  for (const point of [[0, 0], [123.5, 77.25], [-4, 900]] as Point[]) {
    near(toImage(view, toScreen(view, point)), point)
    near(toScreen(view, toImage(view, point)), point)
  }
})
