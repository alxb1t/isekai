import { afterEach, expect, vi } from 'vitest'
import page from '../index.html?raw'
import styles from './styles.css?raw'
import themes from './themes.css?raw'
import { spec } from './test/spec'
import { KEPT, THEMES, chooser, shown } from './themes'

afterEach(() => {
  vi.unstubAllGlobals()
})

type Tokens = Record<string, string>

const CATPPUCCIN = ['latte', 'frappe', 'macchiato', 'mocha']

/* The text, the grounds it is drawn on and the ratio it must reach, per D48. */
const PAIRS: [string[], string[], number][] = [
  [['--ink', '--ink-2'], ['--ground', '--raised', '--raised-2'], 4.5],
  [['--ink-3', '--ink-muted'], ['--ground', '--raised', '--raised-2'], 3],
  [['--focus'], ['--ground', '--raised', '--raised-2'], 3],
  [['--accent-ink'], ['--ground', '--raised', '--raised-2', '--ground-deep'], 4.5],
  [['--band'], ['--accent'], 4.5],
  [['--color-text'], ['--color-bg', '--color-surface'], 4.5],
  [['--color-accent'], ['--color-bg', '--color-surface'], 4.5],
  [['--color-text'], ['--overlay'], 4.5],
]

/* A sheet's comment-free `selector { … }` runs, each with its custom properties. */
function blocks(sheet: string): [string, Tokens][] {
  const bare = sheet.replace(/\/\*[\s\S]*?\*\//g, '')
  return [...bare.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map(([, selector, body]) => [
    selector.trim(),
    Object.fromEntries([...body.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)].map(([, k, v]) => [k, v.trim()])),
  ])
}

/* Nocturne's colour tokens: every `:root` block's but the font, space and radius ones. */
function nocturne(): Tokens {
  const rooted = blocks(styles).filter(([selector]) =>
    selector.split(',').some((part) => part.trim() === ':root'),
  )
  return Object.fromEntries(
    rooted
      .flatMap(([, tokens]) => Object.entries(tokens))
      .filter(([name]) => !/^--(font|space|radius)-/.test(name)),
  )
}

/* Each Catppuccin block of `themes.css`, by its `data-theme` id, in file order. */
function catppuccin(): [string, Tokens][] {
  return blocks(themes).flatMap(([selector, tokens]) => {
    const id = /^\[data-theme="([a-z]+)"\]$/.exec(selector)?.[1]
    return id ? [[id, tokens] as [string, Tokens]] : []
  })
}

const HEX = /^#[0-9a-f]{6}$/i

/* WCAG 2.x's relative luminance of a `#rrggbb`. */
function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((at) => {
    const c = parseInt(hex.slice(at, at + 2), 16) / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

/* WCAG 2.x's contrast ratio between two `#rrggbb`s, e.g. black on white → 21. */
function ratio(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

spec('ui:themes:each-catppuccin-theme-meets-aa', () => {
  const flavours = catppuccin()
  expect(flavours.map(([id]) => id)).toEqual(CATPPUCCIN)
  for (const [id, tokens] of flavours) {
    for (const [texts, grounds, least] of PAIRS) {
      for (const text of texts) {
        for (const ground of grounds) {
          expect(tokens[text], `${id} ${text}`).toMatch(HEX)
          expect(tokens[ground], `${id} ${ground}`).toMatch(HEX)
          const got = ratio(tokens[text], tokens[ground])
          expect(got, `${id}: ${text} on ${ground}`).toBeGreaterThanOrEqual(least)
        }
      }
    }
  }
  // Nocturne is the vendored sheet's own: its ratios are shown, never held.
  const own = nocturne()
  for (const [texts, grounds] of PAIRS) {
    for (const text of texts) {
      for (const ground of grounds) {
        if (HEX.test(own[text]) && HEX.test(own[ground])) {
          const got = ratio(own[text], own[ground]).toFixed(2)
          console.info(`nocturne: ${text} on ${ground} ${got}`)
        }
      }
    }
  }
})

spec('ui:themes:a-theme-sets-every-colour-token', () => {
  const own = Object.keys(nocturne())
  expect(own).toContain('--band')
  expect(own).toContain('--color-accent-2-900')
  const flavours = catppuccin()
  expect(flavours.map(([id]) => id)).toEqual(CATPPUCCIN)
  for (const [id, tokens] of flavours) {
    expect(Object.keys(tokens), id).toEqual(expect.arrayContaining(own))
    for (const [name, value] of Object.entries(tokens)) {
      const colours = value.match(/#[0-9a-f]+\b/gi) ?? []
      expect(colours.length, `${id} ${name}`).toBeGreaterThan(0)
      for (const colour of colours) expect(colour, `${id} ${name}`).toMatch(/^#([0-9a-f]{6}|[0-9a-f]{8})$/i)
      expect(value, `${id} ${name}`).not.toMatch(/color-mix\(|var\(|rgba\(/)
    }
  }
})

/* A store that records each write. */
function store(): { setItem(key: string, value: string): void; writes: [string, string][] } {
  const writes: [string, string][] = []
  return { setItem: (key, value) => void writes.push([key, value]), writes }
}

spec('ui:themes:the-dialog-previews-keeps-and-restores', () => {
  const root = { dataset: { theme: 'frappe' } as DOMStringMap }
  const kept = store()
  const choice = chooser(root, kept)
  expect(choice.opened).toBe('frappe')

  choice.preview('mocha')
  expect(root.dataset.theme).toBe('mocha')
  choice.preview('nocturne')
  expect(root.dataset.theme).toBe('nocturne')
  expect(kept.writes).toEqual([])

  choice.restore()
  expect(root.dataset.theme).toBe('frappe')
  expect(kept.writes).toEqual([])

  choice.keep('latte')
  expect(root.dataset.theme).toBe('latte')
  expect(kept.writes).toEqual([[KEPT, 'latte']])

  // A browser that refuses storage still shows the theme kept, for this page.
  const refused = { dataset: { theme: 'macchiato' } as DOMStringMap }
  const refusing = chooser(refused, {
    setItem: () => {
      throw new Error('denied')
    },
  })
  expect(() => refusing.keep('mocha')).not.toThrow()
  expect(refused.dataset.theme).toBe('mocha')

  // A root with no theme, or one no theme has, shows Nocturne.
  expect(shown({ dataset: {} })).toBe('nocturne')
  expect(shown({ dataset: { theme: 'solarized' } })).toBe('nocturne')
})

spec('ui:themes:the-first-paint-shows-the-kept-theme', () => {
  const head = page.slice(0, page.indexOf('</head>'))
  const inline = /<script>([\s\S]*?)<\/script>/.exec(head)
  expect(inline, 'a classic script in <head>').not.toBeNull()
  // It stands before the module script, so it runs before the first paint.
  expect(page.indexOf('<script>')).toBeLessThan(page.indexOf('<script type="module"'))
  const run = new Function(inline![1])

  const paint = (name: string | null) => {
    const root = { dataset: {} as DOMStringMap }
    vi.stubGlobal('localStorage', { getItem: (key: string) => (key === KEPT ? name : null) })
    vi.stubGlobal('document', { documentElement: root })
    run()
    return root.dataset.theme
  }
  for (const { id } of THEMES) expect(paint(id), id).toBe(id)
  expect(paint('solarized')).toBeUndefined()
  expect(paint(null)).toBeUndefined()

  // A browser that refuses `localStorage` paints Nocturne rather than failing.
  vi.stubGlobal('localStorage', {
    getItem: () => {
      throw new Error('denied')
    },
  })
  expect(() => run()).not.toThrow()
})
