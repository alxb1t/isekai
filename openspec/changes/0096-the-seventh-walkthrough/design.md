# Design — 0096 the seventh walkthrough

Each finding's fix, settled at the grilling. **Verdict: feasible.**

## Context

The findings are in the vault. Each fix below is the grilling's, read at `38d0034`. The open version
`0095-the-session-queue` edits `isekai/interface/ui/app.py`'s `_rendering` and `tests/test_ui_api.py`; this version edits
other functions of both.

## Goals / Non-Goals

**Goals:** each finding fixed as decided, each held by a unit test where one can fail.

**Non-Goals:** the shared caption and tags; any screen not named.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | The hub's `.hub__reason` "prepared · the tick stays" (`ui/src/views/Hub.vue:545–549`) goes; the `↵ review` / `↵ view` hint (`:550–554`) is placed absolutely, as `↵ view photo` is (`ui/src/app.css:1789–1793`). `.hub__reason` stays for `Hub.vue:613` and `RenderBar.vue` | a focused cell grows no line | |
| <a id="d2"></a>**D2** | The library row loses its per-flow chips on screen: `.library__chips`' chips (`ui/src/views/Home.vue:135–143`) and their CSS; "n sources without a flow" stays. The API keeps `Row.flows`, and the library requirement stands | the operator asked for the chips off the screen; `flows` holds `ui:approval:a-re-opened-input-is-not-counted-approved`'s approved count (`tests/test_ui_api.py:597–604`) | removing the counts from the API and the spec |
| <a id="d3"></a>**D3** | `.viewer__frame` is fixed at `calc(100vw - 64px)` × `calc(100vh - 96px)`, `display: flex`, the image centred by `margin: auto`; `.viewer--actual` and `.viewer__pair` as they are | the dialog keeps its size while an image loads | sizing from each image's width |
| <a id="d4"></a>**D4** | The hub's viewer names an image `` `${source.name} · ${flow} · v${version}` `` (`Hub.vue:214`), the drawer's `` `${flow} · v${version}` `` (`ui/src/composables/useSessionViewer.ts:25`); `.viewer__title` takes `contain: inline-size`, one line, cut by an ellipsis. The pick alone gains `max-height: calc(100vh - 96px)`, its rows scrolling inside | no name widens the dialog; the pick sits inside the window | |
| <a id="d5"></a>**D5** | One function, `tagger_of(run, flow)`, follows `tags_from` from a flow's newest sheet, sheet to sheet, to the flow holding a tag list, stopping at a flow seen twice. `_from_source` (`isekai/pipeline/sheet.py:280–301`) reads the list it leads to; `_caption`, `_wd14` and `_tags` (`isekai/interface/ui/app.py:1292–1309, 1565–1618`) read the input's flow's own, else its tagger's | each sheet names the next, so D17's rule holds; one walk for every reader | any flow holding a caption, which summon and conjure both do |
| <a id="d6"></a>**D6** | `discard` (`isekai/pipeline/review.py:491–512`), for a draft drafted from another flow's approval in a flow holding nothing but that draft and one sheet whose producer is the drafting's, also deletes the sheet and the flow's directory through `run.py`'s own removal; otherwise it deletes the draft alone. Review then opens on no flow | the operator: discard removes the draft, and drafting again is one key | stopping Review re-copying the sheet |
| <a id="d7"></a>**D7** | `0091·R2`: each plain `(Dn)` design cite in a comment the card names, and `cells.ts:77`'s, is rewritten to say what it decides, citing a decision in force as `D27` where one holds | `CODING_STANDARDS.md`'s comment rule | |

## Tests

| layer | adds | removes |
|---|---|---|
| unit | `tagger_of` over two hops and a loop; the sheet, the caption and both lists borrowed two hops back; a drafted draft undone whole and a sheet's own draft discarded alone; a page step that the library row draws no chip | none |
| end-to-end | none | none |

This change deletes and merges no test.

## Dependencies

None.

## Risks / Trade-offs

- **A small image sits in a full-size frame** → the frame's ground is the dialog's; the image stays centred.
- **A discard now removes a sheet** → only one the drafting wrote, in a flow holding nothing else; the test holds a
  tagged flow untouched.

## Verdict

**feasible.** Every file and symbol named exists at `38d0034`.
