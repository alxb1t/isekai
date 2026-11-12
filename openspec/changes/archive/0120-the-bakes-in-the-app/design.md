# The bakes in the app — design

The app counts, prices and shows the tattoo edit's bakes beside the images: the quote and the confirmation count them, a render's large view lists them, and a bake has an address. Verdict: feasible, ready to build, in the phases of [tasks](tasks.md).

## Context

A **bake** is an edit request with no image yet: `<seed>.edit-<k>.json` beside its render, written by `isekai edit` and run by the next `isekai render` session. The tattoo edit, the change this builds on, adds the records, `Edits` and `edits_of` in `isekai/interface/render.py`, the edit names in `isekai/foundation/run.py` and the `--pending` form of the verb; this change builds on them and adds no verb.

```
bake (record, no image) ── isekai render <runs> ──▶ image beside its render
        │                         ▲
        │ the quote counts it     │ the job's one verb, as for images
        ▼                         │
  Render bar ─▶ Render dialog ─ POST /api/render {images, bakes, limit_s, without}
        │
        └── the render's large view: the chain ─▶ …/<seed>/edit/<k>
```

The app counts only images: `render.quote` keeps a collection only when it is short or refuses, the confirmation compares `images`, and the bar shows only with images. A bake sits in a collection no listing reads, so a session of bakes alone cannot be offered.

## Goals / Non-Goals

- **Goals:** bakes in the quote, the offer, the bar, the dialog and the confirmation; a bake's address, record, image and thumbnail; the chain on a render's large view; the photograph's thumbnail there; D4, the design spec and the READMEs say it.
- **Non-Goals:** the placement screen and its keys, a bake's compare, a delete of a bake, a tick for one bake, a bake's line in the session drawer, a browser test, a pod phase, a new verb or flag, a change to `per_edit_s`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the quote counts bakes: `Quote.edits` by runs root, `Quote.bakes`, a collection holding a bake kept | one session runs both, so one quote prices both | a second quote for bakes; a bake count the page adds up |
| [D2](#d2) | the confirmation carries `bakes` beside `images`, refused when the quote taken again differs | spend is bounded by what the operator read | `bakes` optional; a refusal on the limit alone |
| [D3](#d3) | the quote lists each bake under its collection; a bake leaves with its photograph's flow | `--without` names a run's flow, so a bake can leave no other way | a tick per bake: it needs a verb change |
| [D4](#d4) | the offer carries `bakes` and `other_bakes` | the bar and `⇧G` read the offer | a request per bake |
| [D5](#d5) | a bake's address is the sibling route `bake`, `…/:seed/edit/:k`, drawn by the large view | `…/:seed/<name>` collides with `compare` | a child of `render`; a screen of its own |
| [D6](#d6) | the server serves a bake's record, image and thumbnail, and the render's detail carries the chain, all through `run.py`'s names | the surface names no artifact | the surface spelling `.edit-` |
| [D7](#d7) | the chain is a pure function: rows by number, each one level in per bake it descends through | a node test can hold it | the rows built in the component |
| [D8](#d8) | a bake's view offers no write | a delete there would take the render and every bake; a draft or compare of a bake has no settled meaning | the render's actions on both |
| [D9](#d9) | the sheet shows the photograph's thumbnail, with no key | a key is the placement screen's | a thumbnail that opens compare |
| [D10](#d10) | the chain's frame has tokens in every theme | each new colour is a token per theme | a hex in `app.css` |
| [D11](#d11) | the dialog is titled for what it does; a bake row has a `×`; the estimate names bakes | the operator reads what spends | the title *Render n images* with bakes hidden |
| [D12](#d12) | the bar counts bakes and shows with bakes alone | the bar is the one way to the dialog | a second bar |
| [D13](#d13) | D4 of `docs/decisions.md` is amended; no decision is added | a decision is edited where it lives | prose here alone |
| [D14](#d14) | tests sit at the lowest layer; no end-to-end test | the standards' lowest-layer rule | a browser test for a count |

### D1

- `Edits` gains `records: tuple[Path, ...] = ()`, the pending records `edits_of` already walks.
- `Quote` gains `edits: dict[Path, Edits]`, by runs root, and the property `bakes`, the sum of their counts. `quote` builds `edits` for every root asked, and `shorts` keeps a root that is short, refuses a count or holds a bake.
- `Quote.blocked` returns `NOTHING_SHORT` only when the session has neither images nor bakes. The estimate is already one function of both (the tattoo edit's D7); a bake is estimated at the edit's `per_edit_s`.

### D2

- `POST /api/render` requires `bakes` as a whole number, as it requires `images`, and refuses with `the quote changed since it was shown: it now renders <n> bakes, not <m>` when `made.bakes` differs. The images message is as it was.
- `jobs.render` keeps `total=made.images`: the session's progress lines stay a render's.
- A body with no `bakes` is refused, naming that the quote must be read again. Each existing test that confirms a render adds `bakes`.

### D3

- `_quoted_row` adds `bakes`, a list of `{flow, name, digest, run, version, seed, k}`: the photograph's name and run as the tiles take them, `version` the approval whose group holds the record, `seed` a decimal string.
- Each record is read through `edit_at(image_of(record))`, so the version, seed and number come from the path and the surface parses no name.
- A tile's `×` and a bake row's `×` both put the photograph's key, `<collection>|<digest>|<flow>`, in `out`; `allOut` holds when every tile and bake key is in it.

### D4

- `GET /api/c/{collection}/render` adds `bakes`, the collection's, and `other_bakes`, every other collection's, each `edits_of(...).count` with nothing taken out.
- `disabled` is `None` while the collection or another holds an image short or a bake; the reason stays the refused count's, else the hold's. `idle`, today `short.lines or others`, also reads the bakes.
- `_quoted_row` takes the collection's `Edits`, `made.edits[<runs root>]`, beside its `Short`; `_quote` already holds `made`.

### D5

- `ui/src/router.ts` adds `bake`, `/c/:collection/renders/:digest/:flow/:version/:seed/edit/:k`, drawn by `RenderLarge.vue` with `k` a prop. `App.vue`'s `HUB_SCREENS` names it, so the Hub tab stays lit.
- The view is keyed by `route.path`, so each bake remounts it; `h` and `l` replace the address with a render's.
- An address whose `k` is no number the seed has an edit for shows the server's refusal.

### D6

- `library.bakes(group, seed)` returns `Bake(k, placed_on, baked_at, edit, state, reason)` per edit of the seed, by number: `placed_on` the number of the edit whose image is its `source`, or `None` for the render; `baked_at` the image's mtime, or `None` while queued; `edit` the edit's name. It lists numbers with `edit_numbers`, skips a number with no record (an image or a composite alone is no bake), and reads each record with `read(record, EDIT_FILE)`.
- A record that cannot be read is listed with `state` `damaged`, no `edit`, no `placed_on`, and `reason`, the refusal's text naming the file; `reason` is `None` otherwise. Its row opens no view, and its record, image and thumbnail routes refuse, naming the file. One damaged record costs only its own row.
- New routes under `…/renders/{digest}/{flow}/{version}/{seed}/edit/{k}`: the record as `{k, state, placed_on, baked_at, edit, reason}`; `/image`; `/thumb`, which is `library.thumbnail` over the edit's image. The path takes `k` as text, which a function refuses unless it is a whole number the seed has an edit for, as `_version` does, so no 422 answers. The image of a queued bake is refused naming the session that bakes it: `python -m isekai render <runs>`.
- `read_render` adds `bakes`, the chain as `{k, state, placed_on, baked_at, edit, reason}`, `state` `baked`, `queued` or `damaged`.
- A bake's row in the quote takes `name`, `digest` and `run` from `_quoted_row`'s `source()`, which stays as it is for the tiles, and its `version` from `edit_at`: the approval whose group holds its record.
- `delete_render` drops the thumbnail of each of the seed's edit images before `discard_render` takes them.
- `tests/test_ui.py` adds the spelling `.edit-` to what no module of the surface holds.

### D7

`ui/src/bakes.ts` holds the change's pure functions:

- `chainRows(bakes)`: the rows by number, each with `state` and `depth`, the rows its `placed_on` chain passes through. A `placed_on` naming no row is depth 0. A damaged row has no `placed_on`, so its chain ends there: its depth is 0 and a bake placed on it is depth 1.
- `offered(k)`: whether *Draft from this*, *Compare with…* and *Delete* show, only when `k` is absent.
- `dialogTitle(images, bakes)`: *Render 2 images*, *Render 2 images · 1 bake*, *Bake 1*.

### D8

On a bake's route the large view shows the image, the sheet's head and fields, the bake's record rows (*placed on*, *edit*, *baked*) and the chain, with *Back to Hub*. `Delete` there would remove the render and every bake (D50, and the tattoo edit's D9), and no deleting of an edit is in this change.

### D9

The sheet shows the photograph at its thumbnail size, from `photoUrl`, above the actions. It has no link and no key.

### D10

`--chain-ground` and `--chain-ring` join `styles.css`'s `:root` and each Catppuccin block of `ui/src/themes.css`, each a hex of that theme's palette. They colour the shown row of the chain, and `ui/design/spec.md` §2 names each in its token table. The brief names the tokens with the dialog's phase; they arrive with the chain, where they are first drawn.

### D11

- The dialog's title is `dialogTitle`. Under a collection's tiles a bake row shows its photograph's thumbnail and name, `v<version> · <seed> · edit <k>`, and a `×`. The estimate line reads `boot … · <n> images · <m> bakes · teardown …`, with no part for a count of zero.
- The confirm button reads *Render* with the price, and *Bake* with the price when no image is short.
- `thumbs.ts` adds `drawnBakes(row, out)`; `allOut` counts the bake keys.

### D12

- `RenderBar.vue` takes `bakes` and `otherBakes`: *<m> bakes queued* beside the images' text, the `+n` line counting both, the bar shown with bakes alone. `BarState` gains `bakes`, and `bar()` returns `render` when it is above zero.
- `collection.ts`'s `openDialog` and `NO_OFFER` take the new keys; `⇧G` opens the dialog on bakes alone.

### D13

`docs/decisions.md` D4's bold sentence and *Why* name the confirmation as image total, bake total and limit; its *Made by* gains `0120`. No decision is added: D52 is the next change's.

### D14

See [Tests](#tests).

## Tests

Tests sit at the lowest layer that can fail: the quote over `Run` fixtures in `tests/test_render.py`, the routes over the app's test client, the rules as pure functions under vitest. No browser test is added: `git diff --name-only main -- tests/e2e` prints nothing at the release.

| file | layer | holds |
|---|---|---|
| `tests/test_render.py` | unit | `Quote.edits`, `bakes`, the kept collection, `blocked` |
| `tests/test_ui_library.py` | unit | `library.bakes` |
| `tests/test_ui_api.py` | unit | the bake routes and refusals, the chain in the detail, the thumbnail's deletion, the offer, the quote's bakes, the confirmation |
| `tests/test_ui_jobs.py` | unit | each confirmation carries `bakes`; a bake-only job plans no image |
| `tests/test_ui.py` | unit | the surface spells no edit's file stem |
| `ui/src/bakes.test.ts` | unit | `chainRows`, `offered`, `dialogTitle` |
| `ui/src/components/RenderDialog.test.ts` | unit | `drawnBakes`, `allOut` and `confirmReason` with bakes |
| `ui/src/bars.test.ts`, `ui/src/stores/collection.test.ts` | unit | the bar with bakes alone, the offer's new keys, `⇧G` |
| `ui/src/themes.test.ts` | unit | unchanged: it holds the new tokens in each theme |

No test is deleted or merged, so no table of removals is owed.

## Dependencies

None.

## Risks / Trade-offs

- **A bake's landing is not drawn in the session drawer.** The session's progress lines stay a render's, so a session of bakes alone shows no image landing and reads none of none; the large view shows the bake after.
- **A bake leaves only with its photograph's flow.** The dialog cannot defer one bake of several in a flow; a bake row's `×` takes the flow out.
- **The estimate per bake is the edit's configured figure.** The design's mock shows `1:00`; `per_edit_s` is the tattoo edit's, and this change leaves it.
- **A branch shows as siblings.** Bakes placed on one image are sibling rows at one depth; no cascade is drawn.
- **Between the server's phase and the dialog's the page's confirmation lacks `bakes`.** The server refuses it, and the end-to-end suite, outside the gate, is red between them; the gate stays green.
- **A queued edit whose source changed refuses in the session, not in the quote.** The verb's free check runs before the pod, as the tattoo edit's D7 says.

## Verdict

Feasible. Each phase ends green; the server comes first because the screens read what it serves.
