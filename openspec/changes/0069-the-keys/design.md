# Design — 0069 the keys

How every key is declared once, kept out of text fields, and drawn into the hints.
**Verdict: feasible** — the stores are in place; the views keep their handlers' bodies and hand their keys to one
listener.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `7fd6be3` (`v0.42.0`):

- **Window listeners:** `ui/src/App.vue:68`, `ui/src/views/Home.vue:60`, `ui/src/views/Hub.vue:356`,
  `ui/src/views/Renders.vue:190`, `ui/src/views/RenderLarge.vue:76`, `ui/src/views/Compare.vue:59`,
  `ui/src/views/Review.vue:432`, `ui/src/components/ImportSheet.vue:248`, `ui/src/components/RenderDialog.vue:49`,
  `ui/src/components/ReviseConfirm.vue:63`. None checks for a text field; `App.vue:48` says its keys fire "text
  fields included". Element-level: `ui/src/components/TagInput.vue:132`, `Home.vue:107`,
  `ui/src/components/RendersBlock.vue:86-87`.
- **Option keys:** `App.vue:51`; `Hub.vue:299-309`; `Home.vue:28`; `Review.vue:365-389`; `Renders.vue:140-145`;
  `RenderLarge.vue:56`; `ReviseConfirm.vue:54` (`⌥↵`, deselect the refused images and revise the rest).
- **The tag cheatsheet** is `ui/src/components/CheatsheetOverlay.vue`, opened by `⌥Space` from inside a tag field
  (`Review.vue:365-368`). `Mod` is already one key for `⌘↵` and `⌘Z` (`Review.vue:358`).
- **Review's panes:** `PANES = ['rail', 'source', 'sheet']` (`Review.vue:80`), `movePane` (`:298`), on `⌥←→`
  (`:389`); plain `↑↓` move the rail or scroll the source pane (`:393-405`); `⌥F` the photo (`:370`). The design
  spec's §7 calls `⌥←→` the flow.
- **Hints:** the hub's key bar (`Hub.vue:501`); `appbar__key` spans and `⌥` text in `App.vue`, `ReviseConfirm.vue`,
  `RenderBar.vue`, `ImportSheet.vue`, `SourcePanel.vue`, `RenderDialog.vue`, `PhotoOverlay.vue`,
  `CheatsheetOverlay.vue`, `Renders.vue`, `Hub.vue`, `RefusalPage.vue`, `Session.vue`, `RenderLarge.vue`, `Home.vue`.
- **The import sheet:** `committing` (`ImportSheet.vue:66`) disables Add files… and Import (`:105`, `:275`), not
  Cancel (`:227`) or `Esc` (`:238`). The in-flight step rides
  `test_importing_a_new_batch_opens_its_hub_with_every_source_unassigned` (`tests/e2e/test_import.py:155-180`).
- **`⌃↓` walk refusals** is in the design spec's §7 and nowhere in `ui/src`.
- **D25** in `docs/decisions.md` covers Option shortcuts.

| measured at the cut | value | command |
|---|---|---|
| vitest tests | 10 | `cat ui/src/*.test.ts ui/src/*/*.test.ts \| grep -c "^spec("` |
| e2e tests | 21 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |
| `⌥` in the design spec | 35 | `grep -c "⌥" ui/design/spec.md` |

## Goals / Non-Goals

**Goals:** one declaration per command; no command while typing; one map on macOS and Linux; every hint generated.
**Non-Goals:** ④ as slots; the Review route; Side by side; walking refusals; a user-editable map.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `ui/src/stores/keys.ts`, `useKeyStore`, holds the declared **commands** by scope; `ui/src/composables/useKeys(scope, commands)` declares them on mount and drops them on unmount; `App.vue` installs the one `keydown` listener; scopes stack everywhere → screen → overlay, the top overlay masking all below; a command is `{id, keys: [{code, shift, mod}], label, run, inField}` | one declaration per command | a listener per view |
| [D2](#d2) | a **text field** is an `input` of type text, search, number or none, a `textarea`, or a `contenteditable`; there only `Esc`, `Mod+↵`, `Mod+Z`, `⇧Mod+Z` and `Mod+K` run, each declared `inField`; a field's own `@keydown` (TagInput, the import's name) runs before the listener | typing is text | a per-view guard |
| [D3](#d3) | `Esc`: an open suggestion list closes (TagInput's own), else the field blurs, else the top overlay closes, else the screen's `Esc`; a billing alert declares none | one order | |
| [D4](#d4) | the map below; plain letters only where the findings name them — `e`, `c`, `\` — and `⇧N`, `⇧A`, `⇧G` keep `⇧` on every screen; a dialog's secondary confirm, `ReviseConfirm`'s deselect-and-revise, is `⇧↵`; **Mod** is `⌘` on macOS, `Ctrl` elsewhere | no Option key; one key per command across screens | `g` on Renders beside `⇧G` on the hub |
| [D5](#d5) | `ui/src/panes.ts`: `PANES` is rail, source, sheet, ④; `h` / `l` and `←` / `→` move between them outside a field; `j` / `k` are `↓` / `↑` in each; `⌃E` / `⌃Y` scroll the source pane 120 px; `↵` on the source pane opens the photo; ④'s inner keys are unchanged | the settled Review keys, written once | ④'s `Tab` order now |
| [D6](#d6) | `ui/src/components/KeyList.vue`, opened by `?` on every screen, lists everywhere's commands and the screen's; `ui/src/components/KeyBar.vue` under each screen lists the screen's; `ui/src/components/KeyHint.vue` draws a button's key by command id; the tag cheatsheet opens on `Mod+K` | hints that cannot drift | `?` for the tag cheatsheet |
| [D7](#d7) | `0068·R9`: Cancel disabled and `Esc` declared to do nothing while `committing`; `0068·R11`: the in-flight step moves into its own test, bound to `ui:sheet:a-commit-in-flight-holds-the-sheet`; `0068·R10`: retired, see the erratum | the cards' fixes | a server-side refusal of the cancel |
| [D8](#d8) | D25 rewritten in `docs/decisions.md`: *shortcuts match the physical key* — `⇧`+letter, plain letters where nothing is typed, Mod for `⌘` / `Ctrl`, never inside a text field | a decision in force edited where it lives | |

### D4

| | keys |
|---|---|
| everywhere, outside a field | `⇧L` library · `⇧H` hub · `⇧R` the queue's head · `⇧I` Renders · `⇧S` session · `?` the key list |
| actions | `⇧N` new batch · `⇧A` add sources · `⇧G` the Render dialog · `⇧E` revise (Review) · `⇧F` the next flow (Review) |
| lists | `⇧J` / `⇧K` as `⇧↓` / `⇧↑` — Review's next and previous sheet, the hub's row selection |
| Home, hub | `h j k l` as the arrows · `Space` tick · `↵` the cell's action · `Mod+↵` Prepare |
| Renders | `h j k l` between cells · arrows between images · `↵` the large view · `Space` select · `e` revise |
| large view, Compare | `e` revise · `c` compare · `\` swap · `Esc` back |
| Review | panes per [D5](#d5) · `Mod+↵` Approve · `Mod+Z` / `⇧Mod+Z` · `Mod+K` the tag cheatsheet |
| dialogs | `Mod+↵` confirm · `⇧↵` the secondary confirm · `Esc` cancel |

```
before                       after
⌥0 ⌥1 ⌥2 ⌥3 ⌥4               ⇧L ⇧H ⇧R ⇧I ⇧S
⌥N ⌥A ⌥R ⌥E                  ⇧N ⇧A ⇧G ⇧E · e where nothing is typed
⌥↑↓ · ⌥←→                    ⇧K ⇧J · h l
⌥Space · ⌥F · ⌥↵             Mod+K · ↵ on the source pane · ⇧↵
⌃↓ walk refusals (unbuilt)   Mod+↓, when built
```

**Erratum, archived 0068:** `openspec/changes/archive/0068-the-store/design.md`'s `## Tests` table says no e2e test
was edited and leaves out the snapshot test. The fix edited `ui:sheet:an-import-opens-the-hub` in
`tests/e2e/test_import.py` and `ui:events:a-connection-starts-with-a-snapshot` in `tests/test_ui_jobs.py`. The
archive is frozen; this note is the correction (`0068·R10`).

**Arc Q103**, the Option-key scheme, is overturned by [D4](#d4).

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · vitest | `ui:keys:a-key-is-matched-by-the-physical-key`, `ui:keys:mod-is-command-or-control`, `ui:keys:no-command-fires-in-a-text-field`, `ui:keys:an-overlay-takes-the-keys-first`, `ui:keys:esc-closes-the-nearest-thing-first`, `ui:keys:hints-come-from-the-declarations` | none | `ui/src/stores/keys.test.ts` |
| unit · vitest | `ui:keys:renders-moves-by-cell-and-by-image`, `ui:keys:review-moves-between-its-panes` | none | `ui/src/grid.test.ts`, `ui/src/panes.test.ts` |
| unit · vitest | `ui:keys:a-focused-control-keeps-enter-and-space`, `ui:sheet:leaving-mid-commit-keeps-the-folder` | none | `ui/src/stores/keys.test.ts`, `ui/src/staging.test.ts` |
| e2e | `ui:keys:a-command-waits-until-the-field-is-left`, `ui:sheet:a-commit-in-flight-holds-the-sheet` | `Alt+Digit1` and `Alt+Space` in `tests/e2e/test_review.py`; `Alt+KeyE` in `tests/e2e/test_render.py`; the in-flight step out of `test_importing_a_new_batch_opens_its_hub_with_every_source_unassigned` | `tests/e2e/test_review.py`, `tests/e2e/test_import.py`, `tests/e2e/test_render.py` |

**End-to-end runs added:** two tests, on Chromium only (T4). Only a browser holds focus in a field, so the field rule's
proof is end-to-end; its logic is the vitest scenario (T1). The in-flight hold needs the real sheet and a held commit;
it leaves the import test, where it rode a scenario it does not prove (T2, T3).

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a component's own `@keydown` and the window listener both act on one key → the field's handler stops the
  event it consumes; the listener skips an event already handled.
- **[Risk]** `Mod+K` is the browser's search on Linux → the listener calls `preventDefault()`, as pages may for
  `Ctrl+K`.
- **[Trade-off]** `⇧`+letter costs a second finger → commands never collide with typing, on any layout.

## Verdict

**Feasible.** The handlers' bodies stay; their keys move into one declared map.
