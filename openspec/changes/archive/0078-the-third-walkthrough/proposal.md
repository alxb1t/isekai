---
version: v0.51
---

# 0078 — the third walkthrough

What the operator's third pass over the UI found, fixed in one version: the hub's row, Review from a field, the
flow chooser, the large view, the dialogs' focus, Revise on a waiting draft and the Library's row.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each fix, its keys and its layout |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
1 layout   hub row · Renders' source cell · Library's fifteen
2 keys     ⌃P · ⌃J ⌃K · ⌃/
3 review   the approved revision · Revise opens a waiting draft
4 chooser  the Review tab chooses a flow
5 large    ⇧E ⇧F · Compare with… · the button column
6 dialogs  modal, holding the focus
```

## Why

**A pass over every screen found what the operator trips on.** The hub's photograph and renders do not line up; a
tag field reaches neither the photograph, nor the next field by `Ctrl`, nor the key list; an approved revision loses
its image; the Review tab opens a flow nobody chose; the large view's *Compare…* does not read as a choice; a dialog
leaves the focus on the grid behind it; Revise refuses a draft it should open.

## What Changes

- **The hub's row** — the pictures at the cells' foot, `↵ view photo` in the corner, the stem alone
  ([D1](design.md#d1)); **Renders' source cell** the thumbnail alone ([D2](design.md#d2)); **the Library's row**
  fifteen thumbnails ([D3](design.md#d3)).
- **Review's keys from a field** — `⌃P` the photograph, or *Side by side* on a revision ([D4](design.md#d4)); `⌃J`
  `⌃K` on macOS ([D5](design.md#d5)); `⌃/` the key list everywhere, `?` gone ([D6](design.md#d6)).
- **An approved revision keeps its image** ([D7](design.md#d7)); **Revise opens a waiting draft**
  ([D8](design.md#d8)).
- **A flow chooser** on the Review tab, `⇧F` gone ([D9](design.md#d9)).
- **The large view** — `⇧E` `⇧F` ([D10](design.md#d10)); *Compare with…* ([D11](design.md#d11)); a button column
  ([D12](design.md#d12)).
- **Modal dialogs** holding the focus ([D13](design.md#d13)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - MODIFIED *A folder in the library is a batch when it holds `sources/`* — fifteen sources named, not seven.
  - MODIFIED *The hub shows each source's stage in each offered flow, and a tick assigns it* — the name and thumbnail
    shown, the size carried for the viewer; the pictures at the cells' foot.
  - MODIFIED *A version says what it was, and Compare shows a seed's two versions* — *Compare with…* picks in a dialog
    of tiles, or compares at once with one other image.
  - MODIFIED *Every command has one key, declared once, and none fires while typing* — `⌃/` the key list; `⌃/`, `⌃P`
    and macOS's `⌃J` `⌃K` from a field; a writing key shifted.
  - MODIFIED *Review opens a batch at its own address, lists every unrendered sheet, and Approve stays on the sheet* —
    the chooser; `⌃P` the photograph; the rail names the chooser's key.
  - MODIFIED *Revise starts from an image, and opens Review on its first draft* — a waiting draft opened; an approved
    revision keeps its image; *Side by side* on `⌃P`.
  - MODIFIED *Conjure from this drafts from an image's approval, and opens Review on it* — `⇧F`, not `f`.
  - ADDED *A dialog holds the focus while it is open* — modal dialogs, each on its first control.

## Impact

- **Code:** `isekai/interface/ui/app.py`, `isekai/interface/ui/library.py`, `ui/src/App.vue`, `ui/src/app.css`,
  `ui/src/panes.ts`, `ui/src/composables/useQueue.ts`, `ui/src/components/TagInput.vue`,
  `ui/src/components/KeyList.vue`, `ui/src/components/BatchRail.vue`, `ui/src/components/ImageViewer.vue`,
  `ui/src/components/RenderDialog.vue`, `ui/src/components/ReviseConfirm.vue`, `ui/src/components/ImportSheet.vue`,
  `ui/src/views/Hub.vue`, `ui/src/views/Home.vue`, `ui/src/views/Renders.vue`, `ui/src/views/Review.vue`,
  `ui/src/views/ReviewHead.vue`, `ui/src/views/RenderLarge.vue`, `ui/src/api.ts`, `ui/src/types.ts`.
- **Tests:** `tests/test_ui_library.py`, `tests/test_ui_api.py`, `ui/src/stores/keys.test.ts`,
  `ui/src/composables/useQueue.test.ts`, `ui/src/cells.test.ts`, `tests/e2e/conftest.py`, `tests/e2e/test_routes.py`,
  `tests/e2e/test_review.py`, `tests/e2e/test_render.py`.
- **Docs:** `ui/design/spec.md`, `docs/decisions.md` (D25).

## Not in this change

- **The session pages and `⇧S`** — the session drawer replaces them, cut on its own.
- **Conjure where conjure holds no sheet** — conjure without Prepare, cut on its own.
- **The review stage's refusals and the CLI** — the page goes to a waiting draft; `isekai revise` still refuses.
- **Every refusal's wording** — only Revise's waiting draft stops showing a command; the rest when the spec audit
  reads them.
