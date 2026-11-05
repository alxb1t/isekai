import { expect, vi } from 'vitest'
import { spec } from '../test/spec'
import { useEdges } from './useEdges'

spec('ui:batch-folder:an-edge-row-shows-the-head', () => {
  const page = { scrollTo: vi.fn(), scrollHeight: 900 }
  const reveal = useEdges(() => page as unknown as HTMLElement)
  const cell = () => ({ scrollIntoView: vi.fn() })
  // The first row brings the page's head into view, then its own cell.
  const first = cell()
  reveal(first as unknown as HTMLElement, 0, 3)
  expect(page.scrollTo).toHaveBeenCalledExactlyOnceWith({ top: 0 })
  expect(first.scrollIntoView).toHaveBeenCalledExactlyOnceWith({ block: 'nearest' })
  expect(page.scrollTo.mock.invocationCallOrder[0]).toBeLessThan(
    first.scrollIntoView.mock.invocationCallOrder[0],
  )
  // The last row brings the page's foot into view, then its own cell.
  page.scrollTo.mockClear()
  const last = cell()
  reveal(last as unknown as HTMLElement, 2, 3)
  expect(page.scrollTo).toHaveBeenCalledExactlyOnceWith({ top: 900 })
  expect(last.scrollIntoView).toHaveBeenCalledExactlyOnceWith({ block: 'nearest' })
  expect(page.scrollTo.mock.invocationCallOrder[0]).toBeLessThan(
    last.scrollIntoView.mock.invocationCallOrder[0],
  )
  // A row between scrolls the page to neither edge.
  page.scrollTo.mockClear()
  const middle = cell()
  reveal(middle as unknown as HTMLElement, 1, 3)
  expect(page.scrollTo).not.toHaveBeenCalled()
  expect(middle.scrollIntoView).toHaveBeenCalledExactlyOnceWith({ block: 'nearest' })
})
