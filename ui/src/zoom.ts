import type { Point } from './types'

/* The panel's view of one image: `screen = image * scale + (x, y)`, in viewport pixels. */
export interface View {
  scale: number
  x: number
  y: number
}

export interface Size {
  width: number
  height: number
}

export const SCALE_FLOOR = 0.25
export const SCALE_CEILING = 16

/* The most of the image a pan may push out of the viewport: this much stays in. */
export const KEPT_IN_VIEW = 48

/** Return the view that shows the whole image centred, whatever its scale.
    e.g. a 400x200 image in 200x200 -> scale 0.5 at (0, 50) */
export function fitted(image: Size, viewport: Size): View {
  const scale = Math.min(viewport.width / image.width, viewport.height / image.height)
  return {
    scale,
    x: (viewport.width - image.width * scale) / 2,
    y: (viewport.height - image.height * scale) / 2,
  }
}

/** Return `view` zoomed by `factor` keeping the image point under `at`, held between
    `floor` and the ceiling. e.g. a factor of 2 at the pointer doubles the scale there */
export function zoomedAt(view: View, factor: number, at: Point, floor = SCALE_FLOOR): View {
  const scale = Math.min(SCALE_CEILING, Math.max(floor, view.scale * factor))
  const [ix, iy] = toImage(view, at)
  return { scale, x: at[0] - ix * scale, y: at[1] - iy * scale }
}

/** Return `view` at one image pixel per screen pixel about the viewport's centre. */
export function actual(view: View, viewport: Size): View {
  const centre: Point = [viewport.width / 2, viewport.height / 2]
  const [ix, iy] = toImage(view, centre)
  return { scale: 1, x: centre[0] - ix, y: centre[1] - iy }
}

/** Return `view` moved by `dx`, `dy`, with some of the image left in the viewport.
    e.g. a pan far past the left edge leaves `KEPT_IN_VIEW` pixels of it showing */
export function panned(view: View, dx: number, dy: number, image: Size, viewport: Size): View {
  return {
    scale: view.scale,
    x: kept(view.x + dx, image.width * view.scale, viewport.width),
    y: kept(view.y + dy, image.height * view.scale, viewport.height),
  }
}

function kept(offset: number, drawn: number, room: number): number {
  const least = Math.min(KEPT_IN_VIEW, drawn, room)
  return Math.min(room - least, Math.max(least - drawn, offset))
}

/** Return the image point a viewport point shows. */
export function toImage(view: View, at: Point): Point {
  return [(at[0] - view.x) / view.scale, (at[1] - view.y) / view.scale]
}

/** Return the viewport point an image point is drawn at. */
export function toScreen(view: View, at: Point): Point {
  return [at[0] * view.scale + view.x, at[1] * view.scale + view.y]
}
