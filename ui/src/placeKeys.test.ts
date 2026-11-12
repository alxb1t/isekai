import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, expect, vi } from 'vitest'
import { placeCommands } from './placeKeys'
import { type Press, useKeyStore } from './stores/keys'
import { spec } from './test/spec'

beforeEach(() => {
  setActivePinia(createPinia())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

/* A keydown as the listener reads it: no modifier, outside any field, unless given. */
function press(code: string, given: Partial<Press> = {}): Press {
  const event = {
    code,
    shiftKey: false,
    metaKey: false,
    ctrlKey: false,
    altKey: false,
    defaultPrevented: false,
    target: null,
    preventDefault: () => {
      event.defaultPrevented = true
    },
    ...given,
  }
  return event
}

function actions() {
  return { undo: vi.fn(), redo: vi.fn(), close: vi.fn() }
}

const element = (tagName: string, given: object = {}) => ({ tagName, ...given }) as unknown as EventTarget

spec('ui:place-keys:undo-redo-and-close-run-from-the-keys', () => {
  const keys = useKeyStore()
  const run = actions()
  keys.declare('screen', placeCommands(run))

  keys.mac = true
  expect(keys.press(press('KeyZ', { metaKey: true }))).toBe(true)
  expect(keys.press(press('KeyZ', { metaKey: true, shiftKey: true }))).toBe(true)
  expect(keys.press(press('Enter'))).toBe(true)
  expect([run.undo, run.redo, run.close].map((one) => one.mock.calls.length)).toEqual([1, 1, 1])

  keys.mac = false
  expect(keys.press(press('KeyZ', { ctrlKey: true }))).toBe(true)
  expect(keys.press(press('KeyZ', { ctrlKey: true, shiftKey: true }))).toBe(true)
  expect(keys.press(press('Enter'))).toBe(true)
  expect([run.undo, run.redo, run.close].map((one) => one.mock.calls.length)).toEqual([2, 2, 2])

  // Undo is not redo, and the bare letter is no command.
  expect(keys.press(press('KeyZ'))).toBe(false)

  // A text field keeps its own keys; the page does not press them there.
  const field = element('INPUT', { type: 'text', blur: vi.fn() })
  expect(keys.press(press('KeyZ', { ctrlKey: true, target: field }))).toBe(false)
  expect(keys.press(press('KeyZ', { ctrlKey: true, shiftKey: true, target: field }))).toBe(false)
  expect(keys.press(press('Enter', { target: field }))).toBe(false)
  expect([run.undo, run.redo, run.close].map((one) => one.mock.calls.length)).toEqual([2, 2, 2])

  // A focused button keeps ↵; with nothing focused ↵ closes again.
  vi.stubGlobal('document', { activeElement: element('BUTTON') })
  expect(keys.press(press('Enter'))).toBe(false)
  expect(run.close).toHaveBeenCalledTimes(2)
  vi.stubGlobal('document', { activeElement: element('BODY') })
  expect(keys.press(press('Enter'))).toBe(true)
  expect(run.close).toHaveBeenCalledTimes(3)
})

spec('ui:place-keys:the-keys-are-listed-with-the-apps', () => {
  const keys = useKeyStore()
  keys.mac = true
  keys.declare('screen', placeCommands(actions()))

  expect(keys.listed.map((one) => [one.id, one.keys])).toEqual([
    ['undo', '⌘Z'],
    ['redo', '⇧⌘Z'],
    ['close', '↵'],
  ])
  expect(keys.hint('redo')).toBe('⇧⌘Z')
  keys.mac = false
  expect(keys.hint('redo')).toBe('⇧Ctrl+Z')

  // A stage with no outline to close declares no close.
  const pairs = useKeyStore(createPinia())
  pairs.declare('screen', placeCommands({ undo: vi.fn(), redo: vi.fn() }))
  expect(pairs.listed.map((one) => one.id)).toEqual(['undo', 'redo'])
})
