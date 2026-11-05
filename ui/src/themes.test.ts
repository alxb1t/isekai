import { expect } from 'vitest'
import styles from './styles.css?raw'
import themes from './themes.css?raw'
import { spec } from './test/spec'

type Tokens = Record<string, string>

const CATPPUCCIN = ['latte', 'frappe', 'macchiato', 'mocha']

/* The text, the grounds it is drawn on and the ratio it must reach, per D48. */
const PAIRS: [string[], string[], number][] = [
  [['--ink', '--ink-2'], ['--ground', '--raised'], 4.5],
  [['--ink-3', '--ink-muted'], ['--ground', '--raised'], 3],
  [['--focus'], ['--ground', '--raised'], 3],
  [['--accent-ink'], ['--ground', '--raised'], 4.5],
  [['--band'], ['--accent'], 4.5],
  [['--color-text'], ['--color-bg', '--color-surface'], 4.5],
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
