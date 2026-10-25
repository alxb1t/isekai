import { defineStore } from 'pinia'
import { computed, ref, shallowRef } from 'vue'

/* Every keyboard command the page offers, declared once by the screen or overlay
   that offers it, and the one listener's dispatch over them (D25). The key list
   and every button's hint read these declarations. */

/** Where a command is offered: everywhere, on the screen, or in an overlay over it. */
export type Scope = 'everywhere' | 'screen' | 'overlay'

/** A physical key, by `event.code`, and its modifiers. Mod is ⌘ on macOS, Ctrl elsewhere. */
export interface Key {
  code: string
  shift?: boolean
  mod?: boolean
  ctrl?: boolean
  /* Offered on macOS alone, and drawn nowhere else. */
  macOS?: boolean
}

/** Return a key pressed with ⇧. */
export const shifted = (code: string): Key => ({ code, shift: true })

/** Return keys pressed with no modifier. e.g. plain('KeyJ', 'ArrowDown') */
export const plain = (...codes: string[]): Key[] => codes.map((code) => ({ code }))

/** Return a key pressed with Mod. */
export const modded = (code: string): Key => ({ code, mod: true })

/** Return a key pressed with ⌃, offered on macOS alone, where ⌃ is free of the window manager. */
export const controlled = (code: string): Key => ({ code, ctrl: true, macOS: true })

/** One command: its keys, its label in the hints, and what it runs. */
export interface Command {
  id: string
  keys: Key[]
  label: string
  run: () => void
  /* Whether it runs while focus is in a text field. */
  inField?: boolean
  /* Whether it is offered now; one that is not lets the key reach the next. */
  when?: () => boolean
}

/** What the listener reads of a `keydown`; a `KeyboardEvent` is one. */
export interface Press {
  code: string
  shiftKey: boolean
  metaKey: boolean
  ctrlKey: boolean
  altKey: boolean
  defaultPrevented: boolean
  /* An input method is composing: the key is its own. */
  isComposing?: boolean
  target: EventTarget | null
  preventDefault(): void
}

/** A command as the hints show it. */
export interface Entry {
  id: string
  keys: string
  label: string
}

interface Layer {
  id: number
  scope: Scope
  commands: Command[]
}

const TEXT = new Set(['text', 'search', 'number'])

/** Return whether `target` is a text field: a text input, a textarea or an editable element. */
export function isField(target: EventTarget | null): boolean {
  const element = target as Partial<HTMLInputElement> | null
  if (!element) return false
  if (element.isContentEditable) return true
  if (element.tagName === 'TEXTAREA') return true
  return element.tagName === 'INPUT' && TEXT.has((element.type ?? 'text').toLowerCase())
}

const CONTROLS = new Set(['BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'SUMMARY'])

/** Return whether `target` is a control that answers `↵` and `Space` itself: a button, a link, an input. */
export function isControl(target: EventTarget | null): boolean {
  const element = target as Partial<HTMLAnchorElement> | null
  if (!element?.tagName) return false
  return CONTROLS.has(element.tagName) || (element.tagName === 'A' && Boolean(element.href))
}

/** What the platform check reads of `navigator`; `navigator` is one. */
export interface Platform {
  userAgentData?: { platform: string }
  platform?: string
}

/** Return whether `found` is macOS, by its client hint first, as `navigator.platform` is deprecated. */
export function isMac(found: Platform | undefined): boolean {
  return /mac|iphone|ipad/i.test(found?.userAgentData?.platform ?? found?.platform ?? '')
}

/** Return whether `key` is the key `event` pressed: its code and exactly its modifiers. */
export function matches(key: Key, event: Press, mac: boolean): boolean {
  if (event.code !== key.code || event.altKey) return false
  if (key.macOS && !mac) return false
  if (Boolean(key.shift) !== event.shiftKey) return false
  const ctrl = Boolean(key.ctrl) || (!mac && Boolean(key.mod))
  const meta = mac && Boolean(key.mod)
  return event.ctrlKey === ctrl && event.metaKey === meta
}

const GLYPHS: Record<string, string> = {
  ArrowUp: '↑',
  ArrowDown: '↓',
  ArrowLeft: '←',
  ArrowRight: '→',
  Enter: '↵',
  Escape: 'esc',
  Space: 'space',
  Backslash: '\\',
  Slash: '/',
}

/** Return how a key is written in a hint. e.g. {code: 'KeyH', shift: true} -> "⇧H" */
export function keyText(key: Key, mac: boolean): string {
  if (key.code === 'Slash' && key.shift) return '?'
  const letter = key.code.startsWith('Key') ? key.code.slice(3) : null
  const name =
    letter ?? (key.code.startsWith('Digit') ? key.code.slice(5) : (GLYPHS[key.code] ?? key.code))
  const bare = letter !== null && !key.shift && !key.mod && !key.ctrl
  const mod = key.mod ? (mac ? '⌘' : 'Ctrl+') : ''
  const ctrl = key.ctrl ? '⌃' : ''
  return `${ctrl}${key.shift ? '⇧' : ''}${mod}${bare ? name.toLowerCase() : name}`
}

export const useKeyStore = defineStore('keys', () => {
  const mac = ref(isMac(globalThis.navigator as Platform | undefined))
  /* Newest last. Shallow: a command's `run` is a closure, never state. */
  const layers = shallowRef<Layer[]>([])
  let made = 0

  /** Offer `commands` in `scope` until `drop` is called with the id returned. */
  function declare(scope: Scope, commands: Command[]): number {
    made += 1
    layers.value = [...layers.value, { id: made, scope, commands }]
    return made
  }

  function drop(id: number): void {
    layers.value = layers.value.filter((layer) => layer.id !== id)
  }

  /* The layers a key reaches, in the order it tries them: the top overlay masks
     everything below it, else the screens, newest first, then everywhere. */
  const reached = computed(() => {
    const newest = [...layers.value].reverse()
    const top = newest.find((layer) => layer.scope === 'overlay')
    if (top) return [top]
    return [
      ...newest.filter((layer) => layer.scope === 'screen'),
      ...newest.filter((layer) => layer.scope === 'everywhere'),
    ]
  })

  /** Run the first command the key reaches and return whether one ran. */
  function press(event: Press): boolean {
    // A field's own handler answered it, and stopped it there or marked it; or
    // an input method is composing, and the key is its own.
    if (event.defaultPrevented || event.isComposing) return false
    const field = isField(event.target)
    // In a field, Esc leaves it; the overlay or the screen takes the next one.
    if (field && event.code === 'Escape') {
      event.preventDefault()
      ;(event.target as HTMLElement).blur?.()
      return true
    }
    for (const layer of reached.value) {
      for (const command of layer.commands) {
        if (field && !command.inField) continue
        if (!command.keys.some((key) => matches(key, event, mac.value))) continue
        if (command.when && !command.when()) continue
        event.preventDefault()
        command.run()
        return true
      }
    }
    return false
  }

  function entry(command: Command): Entry {
    return {
      id: command.id,
      keys: command.keys
        .filter((key) => mac.value || !key.macOS)
        .map((key) => keyText(key, mac.value))
        .join(' '),
      label: command.label,
    }
  }

  /* Every declared command with a key on this platform, offered now or not: a
     `when` may read the page, which is not reactive. */
  const entries = (scope: Scope) =>
    layers.value
      .filter((layer) => layer.scope === scope)
      .flatMap((layer) => layer.commands.map(entry))
      .filter((one) => one.keys !== '')

  /** Everywhere's commands and the screen's, as the key list shows them; a key the
      screen declares is listed once, as the screen's command, the one it runs. */
  const listed = computed(() => {
    const screen = entries('screen')
    const taken = new Set(screen.map((one) => one.keys))
    return [...entries('everywhere').filter((one) => !taken.has(one.keys)), ...screen]
  })

  /** Return a command's keys by its id, from the newest layer that declares it, or null. */
  function hint(id: string): string | null {
    for (const layer of [...layers.value].reverse()) {
      const found = layer.commands.find((command) => command.id === id)
      if (found) return entry(found).keys
    }
    return null
  }

  return { mac, declare, drop, press, listed, hint }
})
