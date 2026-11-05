/* The themes the dialog offers, and the chooser that previews, keeps and
   restores one (D48). Nocturne is the absence of a kept name. */

export const THEMES = [
  { id: 'nocturne', name: 'Nocturne' },
  { id: 'latte', name: 'Latte' },
  { id: 'frappe', name: 'Frappé' },
  { id: 'macchiato', name: 'Macchiato' },
  { id: 'mocha', name: 'Mocha' },
] as const

export type Theme = (typeof THEMES)[number]['id']

/** The `localStorage` key `ui/index.html`'s head script reads. */
export const KEPT = 'isekai.theme'

/** The page's root as the chooser reads it: `document.documentElement` in the app. */
export interface Root {
  dataset: DOMStringMap
}

/** The store the choice is kept in: `localStorage` in the app. */
export interface Kept {
  setItem(key: string, value: string): void
}

/** Return the theme `root` shows: its `data-theme` when a theme's id, else Nocturne. */
export function shown(root: Root): Theme {
  const held = root.dataset.theme
  return THEMES.find((one) => one.id === held)?.id ?? 'nocturne'
}

/** Return a chooser over `root` that previews a theme, keeps one in `kept`, or
    restores the one it opened on. */
export function chooser(root: Root, kept: Kept) {
  const opened = shown(root)
  const preview = (theme: Theme) => {
    root.dataset.theme = theme
  }
  return {
    opened,
    preview,
    keep(theme: Theme): void {
      preview(theme)
      kept.setItem(KEPT, theme)
    },
    restore: () => preview(opened),
  }
}
