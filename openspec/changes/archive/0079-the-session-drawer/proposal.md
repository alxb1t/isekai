---
version: v0.52
---

# 0079 — the session drawer

The running render opens in a drawer every screen offers on `⌃;`. The Sessions tab, its list, the session pages and
`⇧S` go.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the drawer's store, its dialog, its keys, what is removed |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
any screen ──⌃; or ●──▶ ┌──── the drawer, half the window ────┐
 (dark backdrop)        │ RENDER · <batch> · ● 06:41 · Stop   │──↵──▶ the viewer over it
                        │ grid · steps · outcome · ⇧I Renders │
                        └──── esc / ⌃; / the backdrop ────────┘
```

## Why

**A running render is the app's, not a batch's, but its page is dressed as one batch's tab.** From another batch `⇧S`
opens the running session and the tabs follow its batch, while the Sessions tab, drawn with the same `⇧S`, opens this
batch's list. A finished session's images are on Renders, so its list and page have little left to say.

## What Changes

- **The drawer's store** — the running render, else the last one this app saw end ([D1](design.md#d1)).
- **The drawer** — a modal dialog with the session page's content, its keys and its viewer ([D2](design.md#d2)).
- **`⌃;` and `●`** open it; confirming a render opens it ([D3](design.md#d3)).
- **Removed** — the session routes and pages, the Sessions tab, `⇧S`, the sessions list's endpoint and store
  ([D4](design.md#d4)).
- **The docs** — the design spec's routes, journeys and keys; the data flow's render line ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - MODIFIED *Every screen has a URL naming its batch and its run* — the session routes gone; the drawer has no URL.
  - MODIFIED *Render is confirmed in a dialog that quotes what renders, its limit and its price at most* — the
    confirmation opens the drawer.
  - MODIFIED *Every command has one key, declared once, and none fires while typing* — `⌃;` from a field; the drawer
    keeps a focused control's `↵` and `Space`.
  - REMOVED *Each batch's render sessions are listed and shown from their records* — no list, no page.
  - ADDED *The running render opens in a drawer every screen offers* — the drawer, its keys, its record, its last
    session.

## Impact

- **Code:** `isekai/interface/ui/app.py`, `isekai/interface/ui/library.py`, `ui/src/App.vue`, `ui/src/router.ts`,
  `ui/src/api.ts`, `ui/src/app.css`, `ui/src/stores/batch.ts`, `ui/src/stores/drawer.ts` (new),
  `ui/src/components/SessionDrawer.vue` (new), `ui/src/components/RenderDialog.vue`, `ui/src/components/RenderBar.vue`;
  `ui/src/views/SessionPage.vue` and `ui/src/views/Sessions.vue` deleted.
- **Tests:** `tests/test_ui_api.py`, `ui/src/stores/batch.test.ts`, `ui/src/stores/drawer.test.ts` (new),
  `tests/e2e/conftest.py`, `tests/e2e/test_render.py`.
- **Docs:** `ui/design/spec.md`, `docs/data-flow.md`.

## Not in this change

- **The render job, its records and the CLI** — the drawer reads what they write.
- **A finished session found again** — its images are on Renders; its record stays on disk.
- **Renders and the hub** — their Render bar's link opens the drawer instead of a page, and nothing else moves.
