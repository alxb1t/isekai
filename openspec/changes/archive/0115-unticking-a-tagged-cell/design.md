# Design — 0115 unticking a tagged cell

How the page lets a tagged cell's tick and Discard take it back. Verdict: `feasible` — the page's edits and their
tests; the server's guard stays as it is.

## Context

A cell's stage is read by `stage()` in `isekai/interface/ui/library.py`. With no approval, draft or sheet, it falls
through to the photograph's tag list, which every flow shares
([D17](../../../docs/decisions.md#d17--input-above-flow-below)), and reads *tagged*. So an empty flow directory on a
tagged photograph reads *tagged*: a flow just ticked on it, and a flow whose last render was deleted
([D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)).

```
<run>/<flow>/        empty ──▶ photo/wd14/ holds a list? ──yes──▶ tagged
                                        │
                                        no ──▶ assigned
```

The page treats *assigned* and *tagged* alike for Prepare and apart for the untick:

| where | reads | at the base |
|---|---|---|
| the Prepare bar's count, `changes` in `ui/src/views/Hub.vue` | `pending`: assigned or tagged | counts it |
| the checkbox's `disabled` and `tick`'s filter, `locked` in `Hub.vue` | anything but assigned | locks it |
| Discard, `discard` in `Hub.vue` | `stage === 'assigned'` | skips it |
| a click or `↵`, `action` in `ui/src/cells.ts` | `tagged` → `none` | does nothing |

The server would take the untick. `assign` in `isekai/foundation/run.py` deletes a flow's directory only while it is
empty, and refuses one holding files, naming it (`… holds work, so it stays assigned`).
`POST /api/c/{collection}/assign` in `isekai/interface/ui/app.py` answers each source on its own, a refusal beside the
cells that changed.

## Goals / Non-Goals

**Goals**

- A tagged cell's tick and Discard take it back, as they take an assigned cell.
- One predicate decides what the bar counts, what Discard takes and what the tick may take back.

**Non-Goals**

- The stage word: an empty directory on a tagged photograph still reads *tagged* (brief Q4).
- The delete: it keeps the flow assigned, per D50 (brief Q2).
- The server: its refusal of a directory holding work stays the guard.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `action` in `ui/src/cells.ts` returns `tick` for `tagged`, beside `null` and `assigned`; `unreadable` alone returns `none` | a tagged cell holds no sheet, so its one act is the tick | a new stage word for an empty directory (brief Q4) |
| <a id="d2"></a>**D2** | `pending` and `locked` move from `Hub.vue` to `ui/src/cells.ts`, exported. `pending(cell)` is `assigned` or `tagged`; `locked(cell)` is a stage that is not `null` and not pending. `Hub.vue`'s `changes`, `discard`, `tick` and the checkbox's `disabled` read them | the bar, Discard and the tick read one rule, and a unit test holds it; `Hub.vue` has no mounted test | inline edits in `Hub.vue`, held by no unit test |
| <a id="d3"></a>**D3** | The checkbox's class `hub__tick--assigned` becomes `hub__tick--pending`, set by `pending(cell)`; `ui/src/app.css` renames its rule | the design spec's accent fill means "can be unticked"; a grey enabled tick would read as locked | keeping the fill for *assigned* alone |
| <a id="d4"></a>**D4** | The server is unchanged. An untick of a tagged cell whose directory holds files is refused by `assign`, and the refusal shows on the cell | the guard is on disk, where the work is; the page cannot see a directory's files | a page-side check of the directory |

### D2 in code

`locked` keeps its meaning for every stage but *tagged*:

```
stage      null   assigned  tagged  sheet  draft  approved  rendered  unreadable
pending    no     yes       yes     no     no     no        no        no
locked     no     no        no      yes    yes    yes       yes       yes
```

`discard` → `sources.value.filter((one) => pending(cell(one, flow)))`. Its comment, "every pending cell that holds no
work yet", already says so.

## Tests

Every test is a unit test (`T1`). The page's choice is a pure function in `cells.ts`, and the server's untick is a
request; no browser alone shows either, so no end-to-end test is added. No test is deleted or merged.

| layer | adds | changes |
|---|---|---|
| unit · vitest | `spec('ui:hub:a-tagged-cell-with-no-work-unticks', …)` in `ui/src/cells.test.ts`: `pending` and `locked` per the D2 table | `ui:hub:a-click-follows-the-cells-stage`'s `tagged` row: `'none'` → `'tick'` |
| unit · pytest | a step in `tests/test_ui_api.py`'s untick test, after its refusal step: `POST /api/c/{collection}/assign` ticks `conjure-anime-wai` for `ada.jpg`, and `GET /api/c/{collection}/hub` reads its cell `tagged`; the same route unticks it, and the hub reads its cell's `stage` `None`, its directory is gone and `photo/wd14/` still holds its list | the test is renamed `test_an_untick_is_refused_on_work_and_takes_an_empty_tagged_flow` and carries `ui:hub:a-tagged-cell-with-no-work-unticks` beside `ui:hub:a-prepared-tick-stays`, which its refusal step still holds |
| end-to-end | none | none |

The pytest step extends the test that already reaches the state: `made` carries a tag list and a flow holding work
(`T2`). Its step stands on the fixture's tag list, not on the refusal step's change (`T3`).

Counted at `aaefd7a9`, and as planned:

| count | command | at `aaefd7a9` | planned |
|---|---|---|---|
| `tests/test_ui_api.py` | `uv run pytest tests/test_ui_api.py --collect-only -q \| tail -1` | 97 | 97 |
| the suite | `uv run pytest --ignore=tests/e2e --collect-only -q \| tail -1` | 1509 | 1509 |
| `tests/e2e` | `uv run pytest tests/e2e --collect-only -q \| tail -1` | 19 | 19 |
| `spec(` blocks in `ui/src/cells.test.ts` | `grep -c '^spec(' ui/src/cells.test.ts` | 5 | 6 |

## Dependencies

None.

## Risks / Trade-offs

- **A tagged cell whose directory holds files** — a stray file, an empty `review/` — now offers an untick the server
  refuses. The refusal names the directory to delete by hand, on the cell, as any refused untick does today.
- **A tagged cell reads *tagged* yet unticks.** The word stays, per brief Q4; the accent fill (D3) says the tick can
  be taken back.

## Verdict

`feasible`. The page's edits — `action`, `pending`, `locked`, the tick's class — and their prose. The server's refusal
of a directory holding work is the guard, unchanged.
