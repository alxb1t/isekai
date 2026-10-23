import { defineStore } from 'pinia'
import { computed, ref, shallowRef } from 'vue'

/* Every keyboard command the page offers, declared once by the screen or overlay
   that offers it, and the one listener's dispatch over them (D25). The key bar,
   the key list and every button's hint read these declarations. */

/** Where a command is offered: everywhere, on the screen, or in an overlay over it. */
export type Scope = 'everywhere' | 'screen' | 'overlay'

/** A physical key, by `event.code`, and the modifiers it is pressed with. Mod is ⌘ on macOS, Ctrl elsewhere. */
export interface Key {
  code: string
  shift?: boolean
  mod?: boolean
  ctrl?: boolean
}

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

function onMac(): boolean {
  const found = globalThis.navigator as
    | (Navigator & { userAgentData?: { platform: string } })
    | undefined
  return /mac|iphone|ipad/i.test(found?.userAgentData?.platform ?? found?.platform ?? '')
}

/** Return whether `key` is the key `event` pressed: its code and exactly its modifiers. */
export function matches(key: Key, event: Press, mac: boolean): boolean {
  if (event.code !== key.code || event.altKey) return false
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
  const plain = letter !== null && !key.shift && !key.mod && !key.ctrl
  const mod = key.mod ? (mac ? '⌘' : 'Ctrl+') : ''
  return `${key.ctrl ? '⌃' : ''}${key.shift ? '⇧' : ''}${mod}${plain ? name.toLowerCase() : name}`
}

export const useKeyStore = defineStore('keys', () => {
  const mac = ref(onMac())
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

  const offered = (command: Command) => command.when?.() ?? true

  /** Run the first command the key reaches and return whether one ran. */
  function press(event: Press): boolean {
    // A field's own handler answered it, and stopped it there or marked it.
    if (event.defaultPrevented) return false
    const field = isField(event.target)
    // D3: in a field, Esc leaves it; the overlay or the screen takes the next one.
    if (field && event.code === 'Escape') {
      event.preventDefault()
      ;(event.target as HTMLElement).blur?.()
      return true
    }
    for (const layer of reached.value) {
      for (const command of layer.commands) {
        if (field && !command.inField) continue
        if (!command.keys.some((key) => matches(key, event, mac.value))) continue
        if (!offered(command)) continue
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
      keys: command.keys.map((key) => keyText(key, mac.value)).join(' '),
      label: command.label,
    }
  }

  const entries = (scope: Scope) =>
    layers.value
      .filter((layer) => layer.scope === scope)
      .flatMap((layer) => layer.commands.filter(offered).map(entry))

  /** The screen's commands, as its key bar lists them. */
  const bar = computed(() => entries('screen'))

  /** Everywhere's commands and the screen's, as the key list shows them. */
  const listed = computed(() => [...entries('everywhere'), ...entries('screen')])

  /** Return a command's keys by its id, from the newest layer that declares it, or null. */
  function hint(id: string): string | null {
    for (const layer of [...layers.value].reverse()) {
      const found = layer.commands.find((command) => command.id === id)
      if (found) return entry(found).keys
    }
    return null
  }

  return { mac, layers, declare, drop, press, bar, listed, hint }
})
