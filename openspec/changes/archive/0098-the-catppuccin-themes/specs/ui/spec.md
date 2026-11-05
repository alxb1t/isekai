## ADDED Requirements

### Requirement: The app offers five themes, and the choice is kept

The system SHALL offer five themes: Nocturne, the default, then Catppuccin's Latte, Frappé, Macchiato and Mocha.
`⇧T` SHALL open, on every screen, a modal theme dialog listing them in that order, each name drawn in its own
theme's colours, the current one focused. `j` `k` and `↓` `↑` SHALL move the focus and apply the focused theme at
once; `↵` SHALL keep it and close; `Esc` and a click on the backdrop SHALL restore the theme the dialog opened on and
close. The kept theme SHALL be stored in the browser, per origin, and applied before the first paint; a stored name
no theme has SHALL open on Nocturne. A theme SHALL set every colour token the app and the sheet declare. Each
Catppuccin theme SHALL meet WCAG AA: `ink`, `ink-2`, `accent-ink` and the sheet's text 4.5:1, and `ink-3`,
`ink-muted` and `focus` 3:1, on the grounds they are drawn on.

A look is the person's, so the browser keeps it, not the library
([D48](../../../docs/decisions.md#d48--a-theme-is-a-token-set-chosen-in-the-browser)). A theme seen before it is
chosen is chosen once, and `Esc` is a clean undo. Contrast is the one way a token set can break the app.

```
⇧T ─▶ dialog, the current theme focused
        j k ↓ ↑ ─▶ the focused theme applied ──┐
        ↵ ────────▶ kept, closed               │ repeat
        esc ──────▶ the opening theme, closed ◀┘
reload ─▶ <head> reads the kept name ─▶ data-theme ─▶ first paint
```

#### Scenario: each Catppuccin theme meets AA
- **Key:** `ui:themes:each-catppuccin-theme-meets-aa`
- **Layers:** unit
- **WHEN** each Catppuccin theme's tokens are read
- **THEN** every text token reaches its ratio on each ground it is drawn on

#### Scenario: a theme sets every colour token
- **Key:** `ui:themes:a-theme-sets-every-colour-token`
- **Layers:** unit
- **WHEN** each Catppuccin theme's block is read beside Nocturne's tokens
- **THEN** it sets every colour token Nocturne declares, each to a hex value

#### Scenario: the dialog previews, keeps and restores
- **Key:** `ui:themes:the-dialog-previews-keeps-and-restores`
- **Layers:** unit
- **WHEN** the chooser previews one theme, then restores, then keeps another
- **THEN** each preview applies its theme and writes nothing
- **AND** the restore applies the opening theme, and the keep writes its theme

#### Scenario: the first paint shows the kept theme
- **Key:** `ui:themes:the-first-paint-shows-the-kept-theme`
- **Layers:** unit
- **WHEN** the page's head script runs over each kept name, an unknown one and none
- **THEN** each theme's name is applied as it was kept
- **AND** an unknown name or none applies nothing, which is Nocturne

#### Scenario: a chosen theme survives a reload
- **Key:** `ui:themes:a-chosen-theme-survives-a-reload`
- **Layers:** e2e
- **WHEN** `⇧T` opens the dialog, `↓` moves to Latte and `↵` keeps it
- **THEN** the page is drawn in Latte
- **AND** after a reload it still is
