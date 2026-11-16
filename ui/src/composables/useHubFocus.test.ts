import { expect, vi } from 'vitest'
import { nextTick, ref, shallowRef } from 'vue'
import { at } from '../stores/collection'
import { spec } from '../test/spec'
import { restoredSpot, spotName, useHubFocus } from './useHubFocus'

const sources = [
  { name: 'a', digest: 'da' },
  { name: 'b', digest: 'db' },
  { name: 'c', digest: 'dc' },
]
const flows = ['flat', 'vivid']

spec('ui:hub:the-hub-keeps-its-focus', () => {
  // A held name still drawn is the spot.
  expect(restoredSpot(sources, flows, undefined, at('b', 'vivid'))).toEqual({ row: 1, column: 2 })
  // A source cell's name has no flow.
  expect(restoredSpot(sources, flows, undefined, at('c', ''))).toEqual({ row: 2, column: 0 })
  // A held name no longer there, or none held, gives the first spot.
  expect(restoredSpot(sources, flows, undefined, at('gone', 'flat'))).toEqual({ row: 0, column: 0 })
  expect(restoredSpot(sources, flows, undefined, null)).toEqual({ row: 0, column: 0 })
  // A collection with no source has no spot.
  expect(restoredSpot([], flows, undefined, at('a', 'flat'))).toBeUndefined()
})

spec('ui:hub:a-rendered-cell-opens-its-newest-image', () => {
  // A sent cell is its source's row and its flow's column, over a held name.
  expect(restoredSpot(sources, flows, { digest: 'dc', flow: 'flat' }, at('a', 'flat'))).toEqual({
    row: 2,
    column: 1,
  })
  // A sent cell no source holds gives the held name's spot.
  expect(restoredSpot(sources, flows, { digest: 'gone', flow: 'flat' }, at('b', 'vivid'))).toEqual({
    row: 1,
    column: 2,
  })
  // A sent flow no column holds gives the held name's spot.
  expect(restoredSpot(sources, flows, { digest: 'da', flow: 'gone' }, at('b', 'flat'))).toEqual({
    row: 1,
    column: 1,
  })
})

spec('ui:hub:an-edge-row-shows-the-head', async () => {
  const cell = { focus: vi.fn(), scrollIntoView: vi.fn() }
  const querySelector = vi.fn(() => cell)
  const grid = shallowRef({ querySelector } as unknown as HTMLElement)
  const reveal = vi.fn()
  const remember = vi.fn()
  const hub = useHubFocus({ sources: ref(sources), flows: ref(flows), grid, reveal, remember })

  // A key's move past both ends clamps to the last row and column, and reveals the cell.
  hub.place(5, 9, 'key')
  await nextTick()
  expect(hub.focus.value).toEqual({ row: 2, column: 2 })
  expect(remember).toHaveBeenCalledExactlyOnceWith(spotName(sources, flows, { row: 2, column: 2 }))
  expect(querySelector).toHaveBeenCalledExactlyOnceWith('[data-row="2"][data-column="2"]')
  expect(cell.focus).toHaveBeenCalledExactlyOnceWith({ preventScroll: true })
  expect(reveal).toHaveBeenCalledExactlyOnceWith(cell, 2, 3)
  expect(cell.scrollIntoView).not.toHaveBeenCalled()

  // A move without a key scrolls the cell into view, nearest, and reveals nothing.
  reveal.mockClear()
  hub.place(0, 0)
  await nextTick()
  expect(hub.focus.value).toEqual({ row: 0, column: 0 })
  expect(cell.scrollIntoView).toHaveBeenCalledExactlyOnceWith({ block: 'nearest' })
  expect(reveal).not.toHaveBeenCalled()

  // A move by rows and columns is a key's move from where the focus is.
  hub.moveBy(1, 0)()
  await nextTick()
  expect(hub.focus.value).toEqual({ row: 1, column: 0 })
  expect(remember).toHaveBeenLastCalledWith(spotName(sources, flows, { row: 1, column: 0 }))
  expect(reveal).toHaveBeenCalledExactlyOnceWith(cell, 1, 3)

  // With no source a move changes nothing.
  const none = useHubFocus({ sources: ref([]), flows: ref(flows), grid, reveal, remember })
  remember.mockClear()
  querySelector.mockClear()
  none.place(1, 1)
  await nextTick()
  expect(none.focus.value).toEqual({ row: 0, column: 0 })
  expect(remember).not.toHaveBeenCalled()
  expect(querySelector).not.toHaveBeenCalled()
})
