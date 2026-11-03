import { createPinia, setActivePinia } from 'pinia'
import { afterEach, expect, vi } from 'vitest'
import { nextPane, type Pane, paneKeys } from './panes'
import { type Press, plain, useKeyStore } from './stores/keys'
import { spec } from './test/spec'

afterEach(() => {
  vi.unstubAllGlobals()
})

/* A keydown outside any field, with ⌃ when `ctrl`. */
function press(code: string, ctrl = false): Press {
  const event = {
    code,
    shiftKey: false,
    metaKey: false,
    ctrlKey: ctrl,
    altKey: false,
    defaultPrevented: false,
    target: null,
    preventDefault: () => {
      event.defaultPrevented = true
    },
  }
  return event
}

spec('ui:keys:review-moves-between-its-panes', () => {
  vi.stubGlobal('navigator', { platform: 'MacIntel' })
  setActivePinia(createPinia())
  const keys = useKeyStore()
  expect(keys.mac).toBe(true)
  let at: Pane = 'rail'
  const visited: Pane[] = []
  const within = vi.fn()
  keys.declare('screen', [
    ...paneKeys(keys.mac, (step) => visited.push((at = nextPane(at, step))), vi.fn()),
    // ④'s own `l`, as Review declares it on macOS.
    { id: 'four-right', keys: plain('KeyL'), label: 'next', run: within },
  ])

  for (let pressed = 0; pressed < 3; pressed += 1) keys.press(press('KeyL', true))
  expect(visited).toEqual(['source', 'sheet', 'renders'])

  keys.press(press('KeyL'))
  expect(within).toHaveBeenCalledOnce()
  expect(at).toBe('renders')
  expect(nextPane('renders', 1)).toBe('renders')
  expect(nextPane('rail', -1)).toBe('rail')
})
