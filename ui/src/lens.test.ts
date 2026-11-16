import { expect } from 'vitest'
import { photographStep, viewedOf } from './lens'
import { spec } from './test/spec'

const photos = [
  { src: '/photo/a', name: 'a.jpg', width: 800, height: 600 },
  { src: '/photo/b', name: 'b.jpg', width: 600, height: 800 },
]

const revised = { src: '/image/1', seed: '144' }

spec('ui:review:the-photograph-opens-in-the-viewer', () => {
  expect(photographStep(null, false)).toBe('photo')
  expect(viewedOf('photo', photos, 0, null)).toEqual({ images: photos, start: 0 })
  expect(viewedOf('photo', photos, 1, null)).toEqual({ images: photos, start: 1 })
})

spec('ui:revise:side-by-side-shows-the-pair', () => {
  expect(photographStep(null, true)).toBe('pair')
  expect(viewedOf('pair', photos, 1, revised)).toEqual({
    images: [photos[1], { src: '/image/1', name: 'render · seed 144' }],
    start: 0,
  })
  expect(photographStep('pair', true)).toBe('photo')
  expect(viewedOf('photo', photos, 1, revised)).toEqual({ images: photos, start: 1 })
})

spec('ui:conjure-from:conjure-from-this-opens-review', () => {
  const drafted = { src: '/source/1', seed: null }
  expect(viewedOf('pair', photos, 0, drafted)?.images[1].name).toBe('the image it was drafted from')
  expect(viewedOf('pair', photos, 0, revised)?.images[1].name).toBe('render · seed 144')
})
