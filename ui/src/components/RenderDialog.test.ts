import { expect } from 'vitest'
import { spec } from '../test/spec'
import { leftOut, ROW_THUMBS, thumbs } from '../thumbs'

const source = (index: number, images = 1) => ({
  name: `p${index}.jpg`,
  digest: `d${index}`,
  version: 1,
  images,
})

spec('ui:render:the-dialog-shows-thumbnails-by-flow', () => {
  const row = thumbs('c', 'summon-anime-wai', Array.from({ length: 17 }, (_, index) => source(index)))
  expect(ROW_THUMBS).toBe(15)
  expect(row.thumbs.map((one) => one.title)).toEqual(
    Array.from({ length: 15 }, (_, index) => `p${index}.jpg v1`),
  )
  expect(row.more).toBe(2)
  expect(thumbs('c', 'summon-anime-wai', [source(0)]).more).toBe(0)
})

spec('ui:render:the-dialog-shows-thumbnails-by-flow', () => {
  const [once, twice] = thumbs('c', 'f', [source(0), source(1, 2)]).thumbs
  expect(once.times).toBeNull()
  expect(twice.times).toBe(2)
})

spec('ui:render:the-dialog-shows-thumbnails-by-flow', () => {
  const [unversioned] = thumbs('c', 'f', [{ ...source(0), version: null }]).thumbs
  expect(unversioned.title).toBe('p0.jpg')
  expect(thumbs('c', 'f', [{ ...source(0), version: 3 }]).thumbs[0].title).toBe('p0.jpg v3')
})

spec('ui:render:the-dialog-shows-thumbnails-by-flow', () => {
  const [one] = thumbs('my c', 'summon-anime-wai', [{ ...source(0), name: 'a b.jpg' }]).thumbs
  expect(one.key).toBe('my c|d0|summon-anime-wai')
  expect(one.src).toBe('/api/c/my%20c/sources/a%20b.jpg/thumb')
  expect(one.fallback).toBe('/api/c/my%20c/review/d0/summon-anime-wai/photo')
})

spec('ui:render:the-dialog-shows-thumbnails-by-flow', () => {
  const left = (index: number, reason: string, flow: string) => ({
    name: `p${index}.jpg`,
    digest: `d${index}`,
    version: 1,
    flow,
    reason,
  })
  const groups = leftOut('c', [
    left(0, 'a draft', 'summon-anime-wai'),
    left(1, 'not approved', 'summon-anime-wai'),
    left(2, 'a draft', 'conjure-anime-wai'),
    left(3, 'a draft', 'summon-anime-wai'),
  ])
  expect(groups.map(({ reason, flow }) => `${reason} · ${flow}`)).toEqual([
    'a draft · summon-anime-wai',
    'not approved · summon-anime-wai',
    'a draft · conjure-anime-wai',
  ])
  expect(groups[0].thumbs.map((one) => one.title)).toEqual(['p0.jpg v1', 'p3.jpg v1'])
  expect(groups[0].thumbs.every((one) => one.times === null)).toBe(true)
  expect(groups[2].thumbs[0].key).toBe('c|d2|conjure-anime-wai')
  expect(groups.every((one) => one.more === 0)).toBe(true)
})
