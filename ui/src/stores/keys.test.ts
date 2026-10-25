import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import { type Command, type Press, controlled, isControl, isMac, useKeyStore } from './keys'

/* Every screen's and component's source, as the page draws them. */
const SOURCES = import.meta.glob<string>(['../*.vue', '../views/*.vue', '../components/*.vue'], {
  query: '?raw',
  import: 'default',
  eager: true,
})

beforeEach(() => {
  setActivePinia(createPinia())
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

/* A focused text input, which records whether it was left. */
function field(): EventTarget & { left: boolean } {
  const input = { tagName: 'INPUT', type: 'text', left: false, blur: () => (input.left = true) }
  return input as unknown as EventTarget & { left: boolean }
}

function command(id: string, code: string, given: Partial<Command> = {}): Command {
  return { id, keys: [{ code }], label: id, run: vi.fn(), ...given }
}

spec('ui:keys:a-key-is-matched-by-the-physical-key', () => {
  const keys = useKeyStore()
  const hub = command('hub', 'KeyH', { keys: [{ code: 'KeyH', shift: true }] })
  keys.declare('everywhere', [hub])

  // A Cyrillic layout types Р on the key a Latin one prints H.
  const ran = keys.press({ ...press('KeyH', { shiftKey: true }), key: 'Р' } as Press)

  expect(ran).toBe(true)
  expect(hub.run).toHaveBeenCalledOnce()
  expect(keys.press(press('KeyH'))).toBe(false)
})

spec('ui:keys:mod-is-command-or-control', () => {
  const keys = useKeyStore()
  const sheet = command('cheatsheet', 'KeyK', { keys: [{ code: 'KeyK', mod: true }] })
  keys.declare('screen', [sheet])

  keys.mac = true
  expect(keys.press(press('KeyK', { metaKey: true }))).toBe(true)
  expect(keys.press(press('KeyK', { ctrlKey: true }))).toBe(false)
  keys.mac = false
  expect(keys.press(press('KeyK', { ctrlKey: true }))).toBe(true)
  expect(keys.press(press('KeyK', { metaKey: true }))).toBe(false)

  expect(sheet.run).toHaveBeenCalledTimes(2)
})

spec('ui:keys:no-command-fires-in-a-text-field', () => {
  const keys = useKeyStore()
  keys.mac = true
  const letter = command('revise', 'KeyE')
  const modded = (id: string, code: string) =>
    command(id, code, { keys: [{ code, mod: true }], inField: true })
  const approve = modded('approve', 'Enter')
  const undo = modded('undo', 'KeyZ')
  const sheet = modded('cheatsheet', 'KeyK')
  keys.declare('screen', [letter, approve, undo, sheet])
  const target = field()

  expect(keys.press(press('KeyE', { target }))).toBe(false)
  keys.press(press('Enter', { target, metaKey: true }))
  keys.press(press('KeyZ', { target, metaKey: true }))
  keys.press(press('KeyK', { target, metaKey: true }))
  keys.press(press('Escape', { target }))

  expect(letter.run).not.toHaveBeenCalled()
  expect(approve.run).toHaveBeenCalledOnce()
  expect(undo.run).toHaveBeenCalledOnce()
  expect(sheet.run).toHaveBeenCalledOnce()
  expect(target.left).toBe(true)
})

spec('ui:keys:an-overlay-takes-the-keys-first', () => {
  const keys = useKeyStore()
  const below = command('revise', 'KeyE')
  const everywhere = command('library', 'KeyL')
  const above = command('edit', 'KeyE')
  keys.declare('everywhere', [everywhere])
  keys.declare('screen', [below])
  const overlay = keys.declare('overlay', [above])

  keys.press(press('KeyE'))
  keys.press(press('KeyL'))

  expect(above.run).toHaveBeenCalledOnce()
  expect(below.run).not.toHaveBeenCalled()
  expect(everywhere.run).not.toHaveBeenCalled()
  keys.drop(overlay)
  keys.press(press('KeyE'))
  expect(below.run).toHaveBeenCalledOnce()
})

spec('ui:keys:esc-closes-the-nearest-thing-first', () => {
  const keys = useKeyStore()
  const back = command('back', 'Escape')
  const close = command('close', 'Escape')
  keys.declare('screen', [back])
  keys.declare('overlay', [close])
  const target = field()

  // The suggestion list is the field's own: its handler answers the first Esc.
  const first = press('Escape', { target })
  first.preventDefault()
  keys.press(first)
  expect(target.left).toBe(false)
  expect(close.run).not.toHaveBeenCalled()

  keys.press(press('Escape', { target }))
  expect(target.left).toBe(true)
  expect(close.run).not.toHaveBeenCalled()

  keys.press(press('Escape'))
  expect(close.run).toHaveBeenCalledOnce()
  expect(back.run).not.toHaveBeenCalled()
})

spec('ui:keys:hints-come-from-the-declarations', () => {
  const keys = useKeyStore()
  keys.mac = true
  keys.declare('everywhere', [command('hub', 'KeyH', { keys: [{ code: 'KeyH', shift: true }] })])
  keys.declare('screen', [
    command('revise', 'KeyE', { label: 'revise' }),
    command('approve', 'Enter', { keys: [{ code: 'Enter', mod: true }], label: 'approve' }),
  ])

  expect(keys.hint('revise')).toBe('e')
  expect(keys.hint('hub')).toBe('⇧H')
  expect(keys.hint('approve')).toBe('⌘↵')
  expect(keys.listed.map((one) => `${one.keys} ${one.label}`)).toEqual([
    '⇧H hub',
    'e revise',
    '⌘↵ approve',
  ])
  keys.mac = false
  expect(keys.hint('approve')).toBe('Ctrl+↵')

  // A screen command on an everywhere key is the one listed, as it is the one that runs.
  keys.declare('screen', [command('renders', 'KeyI', { keys: [{ code: 'KeyI', shift: true }] })])
  keys.declare('everywhere', [
    command('library', 'KeyI', { keys: [{ code: 'KeyI', shift: true }], label: 'renders' }),
  ])
  expect(keys.listed.filter((one) => one.keys === '⇧I').map((one) => one.id)).toEqual(['renders'])

  // The key list, opened on ? or the app bar's ? button, is the one place keys are listed.
  expect(keys).not.toHaveProperty('bar')
  expect(Object.keys(SOURCES)).toContain('../views/Hub.vue')
  for (const [file, source] of Object.entries(SOURCES))
    expect(source, file).not.toMatch(/KeyBar|key-bar/)
})

spec('ui:keys:a-focused-control-keeps-enter-and-space', () => {
  const element = (tagName: string, given: object = {}) =>
    ({ tagName, ...given }) as unknown as EventTarget

  expect(isControl(element('BUTTON'))).toBe(true)
  expect(isControl(element('INPUT', { type: 'checkbox' }))).toBe(true)
  expect(isControl(element('A', { href: '/renders/b' }))).toBe(true)
  expect(isControl(element('SELECT'))).toBe(true)
  // A grid cell or the page itself leaves the keys to the screen.
  expect(isControl(element('DIV'))).toBe(false)
  expect(isControl(element('BODY'))).toBe(false)
  expect(isControl(null)).toBe(false)
})

spec('ui:keys:an-esc-ending-a-composition-closes-nothing', () => {
  const keys = useKeyStore()
  const close = command('close', 'Escape')
  keys.declare('overlay', [close])
  const target = field()

  const ending = press('Escape', { target, isComposing: true })

  expect(keys.press(ending)).toBe(false)
  expect(ending.defaultPrevented).toBe(false)
  expect(target.left).toBe(false)
  expect(close.run).not.toHaveBeenCalled()
})

spec('ui:keys:review-panes-move-from-a-field-on-macos', () => {
  // The platform is read from the client hint first, else the deprecated `platform`.
  expect(isMac({ userAgentData: { platform: 'macOS' }, platform: 'Linux x86_64' })).toBe(true)
  expect(isMac({ platform: 'MacIntel' })).toBe(true)
  expect(isMac({ platform: 'Linux x86_64' })).toBe(false)
  expect(isMac(undefined)).toBe(false)

  const keys = useKeyStore()
  // As Review declares them: plain l is text in a field, ⌃L moves the pane.
  const right = command('right', 'KeyL')
  const fieldRight = command('field-right', 'KeyL', {
    keys: [controlled('KeyL')],
    label: 'pane right',
    inField: true,
  })
  keys.declare('screen', [right, fieldRight])
  const target = field()

  keys.mac = true
  expect(keys.press(press('KeyL', { target }))).toBe(false)
  expect(keys.press(press('KeyL', { target, ctrlKey: true }))).toBe(true)
  expect(fieldRight.run).toHaveBeenCalledOnce()
  expect(keys.hint('field-right')).toBe('⌃L')

  keys.mac = false
  expect(keys.press(press('KeyL', { target, ctrlKey: true }))).toBe(false)
  expect(fieldRight.run).toHaveBeenCalledOnce()
  expect(right.run).not.toHaveBeenCalled()
  expect(keys.hint('field-right')).toBe('')
  expect(keys.listed.map((one) => one.id)).toEqual(['right'])
})
