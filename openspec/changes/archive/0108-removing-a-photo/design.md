# Design — 0108 removing a photo

A `without` set of `<runs>/<run-id>/<flow>` paths runs from the dialog's tiles through the quote, the confirm and the
job to `isekai render --without`, where `short()` wants none of them. **Verdict: feasible.**

## Context

`short(runs, ids, wired)` (`isekai/interface/render.py:722-753`) walks each run's tracked flows: unapproved ones go to
`left_out`, a damaged approval's `shortfall()` refusal to `refused` (`:741-745`), and a run's lack to `wanted`
(`:746-747`); the lines are built from `wanted`. `quote(roots, wired)` (`:796-824`) calls it per root and keeps the
roots short or refusing. `_session` (`:836-929`) re-plans with `short()` when no request is named (`:868-883`), and
`again(roots)` (`:152-156`) is the retry its limit names (`retry`, `:848`; `reached()`, `:917-922`).

`render`'s positionals are runs roots and requests (`_Targets`, `isekai/interface/cli.py:192-213`; the arguments,
`:388-420`), so a path positional would read as a missing root. `run_session` (`render.py:470-525`) calls `_session`
at `:520-522`; the test helper `session()` (`tests/test_render.py:151-177`) builds its `Namespace` with no `without`.

The server's `quoted(names)` (`isekai/interface/ui/app.py:463-486`) quotes the named collections; `post_quote`
(`:532-543`) and `post_render` (`:546-585`) call it, and `post_render` compares limit and images before
`jobs.render(...)` (`:579-584`). `_quoted_row` (`:1471-1513`) gives each source `name`, `digest`, `version` and no run
id (`source()`, `:1481-1490`), and the row a `left_out` list (`:1508-1511`). `Jobs.render` (`isekai/interface/ui/jobs.py:347-382`)
runs `_run_render` → `_render_child`, whose verb line is `self._render(limit, roots, id)` (`:575`); `RenderCommand`
takes exactly those positionals (`:121`), as do the fakes in `tests/test_ui_jobs.py`.

The dialog is `ui/src/components/RenderDialog.vue`: plain thumbnails (`:172-188`), the *Not included* groups
(`:190-215`), the refusal line (`:216`), `shown` falling back to the first quote's row (`:42-51`), first focus on
*Keep the volume open* (`:121-129`). `ui/src/thumbs.ts` caps a flow at `ROW_THUMBS` 15 (`:8`, `:34-45`) and keys a
thumbnail `collection|digest|flow` (`:26`). The import sheet's tiles (`ui/src/components/ImportSheet.vue:360-411`,
`:466-488`) and `useEdges` (`ui/src/composables/useEdges.ts:1-12`) are the patterns mirrored.

## Goals / Non-Goals

**Goals:**
- One removal, the same in the page and the terminal: the page's is the verb's `--without`.
- What is taken out never renders, and nothing on disk changes for it.

**Non-Goals:**
- A `RenderCommand` signature change: the job appends the flags ([D4](#d4)).
- A CLI message for a session `--without` empties: it reads as nothing short, as the dialog never sends one.
- `ui/design/spec.md`: the paydown's.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `short(runs, ids, wired, without: Collection[Path] = ())`: a lack is wanted only when `runs / run_id / flow not in without`, checked after `shortfall()`, so a damaged approval is refused all the same. `quote(roots, wired, without: Collection[Path] = ())` passes it to each `short()`. Both docstrings say so | Brief Q1, Q3. A path on the root as named is what the CLI and the server both build | the check before `shortfall()` (brief Facts): a damaged approval taken out would pass silently, against Q3 |
| <a id="d2"></a>**D2** | The flag, per [the flag](#the-flag): `--without` on `render`; `run_session` passes `list(getattr(args, "without", None) or [])` to `_session`, after `texts`; `_session` refuses it beside a request, maps it with `_taken(roots, without)`, and gives the result to `short()` and `again()`. `without_flags(without: Sequence[Path]) -> list[str]` and `_taken(roots: Sequence[Path], without: Sequence[Path]) -> list[Path]`, which raises [the flag](#the-flag)'s path refusals, sit after `again`, which gains `without: Sequence[Path] = ()` | Brief Q2, Q4. A path, as `draft` and `discard` take. `_taken` names each path by its root as the verb names it, so `again()` and `short()` read one form | a positional `<runs>:<id>/<flow>`: `_Targets` reads it as a missing root |
| <a id="d3"></a>**D3** | The server: `_taken_out(value: object, found: Mapping[str, Path]) -> list[Path]` after `_quoted_row` reads `without`: absent is `[]`; else each entry is `{collection, run, flow}`, all strings, its collection in `found`, its run in `render.run_ids(found[c] / library.RUNS)` and its flow in that run's `flows`; it returns `found[c] / library.RUNS / run / flow`. `quoted(names, without: object = None)` takes them out of the quote, then, once `found` keeps only the quoted collections, keeps only `taken`'s paths under their runs roots, and returns `(found, made, described, taken)`; `post_quote` passes `payload.get("without")`, `post_render` `body.get("without")` and `jobs.render(..., without=taken)`. `source()` gains `"run": run_id` | Brief Q2: the quote's sources gain their run id. Each name is checked against what the collection holds, so no path the page sends reaches the disk unchecked (`THREAT_MODEL.md`: the browser) | trusting the page's run id: a `../` would name a folder outside the collection; passing a dropped collection's paths: the verb would refuse them after `volume up` |
| <a id="d4"></a>**D4** | `Jobs.render(..., without: Sequence[Path] = ())` passes `tuple(without)` through `_run_render` to `_render_child`, whose line becomes `[*self._render(limit, roots, job.session["id"]), *without_flags(without)]`, `without_flags` imported from `isekai.interface.render`. `RenderCommand` and `render_command` are unchanged | The fakes take three positionals, so they hold; an option after the positionals parses as one | a `without` keyword on `render_command`: each fake breaks, or the call branches on it |
| <a id="d5"></a>**D5** | The tiles' data: `QuoteSource` gains `run: string`; `TakenOut` is `{ collection: string; run: string; flow: string }` in `ui/src/types.ts`. In `ui/src/thumbs.ts`, `Thumb` gains `run`; `thumbs(collection, flow, sources, out: ReadonlySet<string> = new Set())` drops each source whose key is in `out` before the cap, `out` the thumbnail keys taken out; `allOut(row, out)` is true when the row has a source and each is in `out`; `NOTHING_LEFT = 'Nothing left to render.'`; `confirmReason(rows, out, disabled)` is `NOTHING_LEFT` when `rows` is not empty and `allOut` holds for each, else `disabled`; `tileMoved(sizes, index, move)` is the flat index after `move` over flows of `sizes` tiles, each size above 0, by `grid.ts`'s `moved`; with no size it returns `index`. `api.ts`: `quoteRender(collections?, without: TakenOut[] = [])` sends `{ collections, without }` when `collections` is given; `startRender` gains a last `without: TakenOut[]` | Brief Q6, Q7, Q8. Each rule is a pure function, so a unit test holds it (`T1`) | the rules inside `RenderDialog.vue`: only a browser could test them |
| <a id="d6"></a>**D6** | The dialog's state, per [the dialog](#the-dialog): `out`, a `Map<string, TakenOut>` by thumbnail key, and `outKeys = computed(() => new Set(out.value.keys()))`, which `thumbs`, `allOut` and `confirmReason` take, the last over `rows.value`, every row the first quote listed; a row all out is `gone`, its tick unticked and disabled, its label `all removed`; `names` leaves gone rows out; `taken` is `out`'s entries of `names`; each `ask()` and `confirm()` sends `taken`; the footer and the confirm read `confirmReason` | Brief Q6: `shown` would bring a gone row back with its tiles, and `NOTHING_SHORT` names the wrong reason | a gone row dropped: the operator loses where the photographs went |
| <a id="d7"></a>**D7** | The tiles and keys, the keys added to the one `useKeys('overlay', …)` list at `RenderDialog.vue:113`, as a second list would hide its `cancel` and `confirm`: each thumbnail is a `div` `class="render-dialog__thumb"` `data-tile` `:title="thumb.title"`, the roving stop (`tabindex` 0 on the focused tile, else the first), holding a `×` `button` `.render-dialog__remove`, `tabindex="-1"`, `aria-label` ``Take ${thumb.title} out``. Keys in the `overlay` layer, `when: onTile`: `photo-left` `h` `←`, `photo-right` `l` `→`, `photo-up` `k` `↑`, `photo-down` `j` `↓`, label `move`; `take-out` `⌫`, label `take the photograph out`. `sizes` lists each drawn flow's tile count, in order, leaving out a flow with none, and a tile's row is its flow's place there. After a removal the focus takes the tile now at the removed one's flat index across the dialog, else the last tile, else *Keep the volume open*. The first focus is the first tile, else the checkbox. `Tab` follows the page's order | Brief Q8, Q12: the import sheet's pattern. The page's order keeps one `Tab` loop, which `useHeldFocus` holds | a `Tab` key jumping to the checkbox: a second order beside the page's |
| <a id="d8"></a>**D8** | `useEdges(page, centred = false)`: when `centred`, the first row only scrolls `page` to its top and the last only to its foot, with no `scrollIntoView`, and any other row's cell `scrollIntoView({ block: 'center' })`; unchanged otherwise. The dialog reveals with `useEdges(() => list.value, true)` over `.render-dialog__collections`, a row being a flow with tiles | Brief Q13: centred where the scroll allows, the edges at the ends. One composable keeps the edges' rule in one place | a second composable: the edge rule twice |
| <a id="d9"></a>**D9** | The left-out lines go: the *Not included* block and `groups` in `RenderDialog.vue`, `leftOut` and `Left` in `thumbs.ts`, `left_out` in `types.ts`'s `QuotedCollection` and in `_quoted_row`, `.render-dialog__thumb--left` in `app.css`. `Short.left_out` and the verb's `left out:` lines stay; `.render-dialog__left` stays, for the refusal line | Brief Q11: show only those included | moving them to a summary line: Q11 drops them |
| <a id="d10"></a>**D10** | The record, per [the record](#the-record): docs D3, D4 and D36 amended in `docs/decisions.md`, each `Made by:` gaining `` `0108` ``; `README.md`, `isekai/interface/README.md` and `isekai/interface/ui/README.md` name the flag | A7: a decision in force is edited where it lives | each doc in its code's phase: three phases would touch the same docs |

## The flag

`isekai/interface/cli.py`, after `--session` on `render`:

```python
made["render"].add_argument(
    "--without",
    action="append",
    type=Path,
    default=None,
    metavar="<runs>/<run-id>/<flow>",
    help="take that run's flow out of what renders; repeatable, beside no request",
)
```

The refusals `_session` and `_taken` raise, each a `Refusal`:

| when | text |
|---|---|
| a request and a `--without` | `--without takes a run's flow out of what each approval lacks, and a request names what renders; give one or the other` |
| `path.parent.parent` resolves to no named root | `--without {path} is under no runs root this session names; name its collection's runs/ too, or drop it` |
| `path.parent.name` is not one of `run_ids(root)`, or `path.name` not one of that run's `flows` | `--without {path} names no run's flow; give <runs>/<run-id>/<flow>` |

`without_flags([Path("b/runs/r1/f")])` is `["--without", "b/runs/r1/f"]`; `again(roots, without)` is
`shlex.join([... "render", *map(str, roots), *without_flags(without)])`.

The server's refusals, from `_taken_out`:

| when | text |
|---|---|
| `without` is not a list of mappings of strings | `the quote names no list of photographs taken out; close Render and open it again` |
| an entry its collection does not hold | `the quote takes out {run}/{flow}, which {collection} does not hold; close Render and open it again` |

## The dialog

What a removal does in `RenderDialog.vue`, per [D6](#d6)–[D8](#d8):

```
 tile focused ──⌫ / ×──▶ out += its key ──▶ row all out? ──yes──▶ untick, label "all removed"
                                 │                 └─no──┐
                                 ▼                       ▼
                        thumbs() drops it, the next past the cap shows
                                 │
                                 ▼
                 ask(names, taken) ──▶ the quote counts what is left
                                 │
                                 ▼
          focus: the tile now at its index, else the last, else Keep the volume open
```

The template, from `:150`: the tick's label reads `all removed` for a gone row in place of its count, its checkbox
`:checked="ticked.has(row.collection) && !row.gone"` and `:disabled="row.gone"`; each flow's `<span>` thumbnails become
the `data-tile` tiles of [D7](#d7), the `<img>` and `×N` kept; the `v-for="group in row.groups"` block goes. The
section's `ref="list"` is on `.render-dialog__collections`. The comment heading the script says the dialog shows what
renders, takes a photograph out on `×` and `⌫`, and opens on the first tile.

`app.css`: `.render-dialog__thumb:focus` is `outline: 2px solid var(--focus); outline-offset: 2px;`, as an inset shadow would paint under the image, `.render-dialog__remove` and its `:hover`
take `.import__remove`'s, and `.render-dialog__thumb--left` goes.

## The planner's tests

Each in `tests/test_render.py`, after `test_many_collections_render_in_one_session_in_the_order_named`, on its
helpers: `counted`, `images`, `session`, `real`, `FakeOpen`, `Calls`, `log`. In each, `root` is
`tmp_path / "b" / "runs"`, `ada` is `counted(tmp_path, schema, vocabulary, "ada", 1)` and `bea` is
`counted(tmp_path, schema, vocabulary, "beatrix", 0)`.

| test | it does | it asserts |
|---|---|---|
| `test_a_flow_named_without_is_not_rendered` | `session(root, without=[root / bea.id / FLOW], generate=_dispatch_argv, wiring=real(root, vocabulary))` | status 0; `images(ada) == 2`, `images(bea) == 0`; `render.quote([root], real(root, vocabulary), [root / bea.id / FLOW]).images == 1`; `build_parser().parse_args(["render", str(root), "--without", str(root / bea.id / FLOW)]).without` is that path in a list |
| `test_a_without_naming_nothing_is_refused`, `ids=["no-root", "no-flow"]` | `ada` alone; `session(root, without=[path], opener=opener)` for `path` a made `tmp_path / "c" / "runs" / ada.id / FLOW`, then `root / ada.id / "no-such-flow"` | status 1; `opener.opened == 0`; `f"--without {path}"` in `log(root)` |
| `test_a_without_beside_a_request_is_refused` | `ada` alone; `session(root, f"{FLOW}=1", without=[root / ada.id / FLOW], opener=opener)` | status 1; `opener.opened == 0`; `"give one or the other"` in `log(root)` |
| `test_a_damaged_approval_taken_out_is_still_refused` | `ada` alone, its newest approval's `renders` set to `{"count": 0}` as `tests/test_ui_api.py:1825-1827` does; `session(root, without=[root / ada.id / FLOW], opener=opener, wiring=real(root, vocabulary))` | status 1; `opener.opened == 0`; `f"{approval.name}: its renders count 0 renders nothing"` in `log(root)`, `approval` the file damaged |
| `test_the_limits_retry_keeps_each_without` | `ada` and `bea`; the watchdog of `tests/test_render.py:421-448`, `held` its `generate`, with no request and `without=[root / bea.id / FLOW]`, `wiring=real(root, vocabulary)` | status 143; `f"isekai render {root} --without {root / bea.id / FLOW}` renders only the rest"` in `log(root)` |

## The server's tests

Each in `tests/test_ui_jobs.py`, after `test_a_confirmation_shorter_than_the_quote_now_gives_is_refused`, on
`_quoting`, `_approved` and `_order`. `taken` is `[{"collection": "b", "run": ada.id, "flow": FLOW}]`, `ada` and
`beatrix` each `_approved(folder, "<name>.jpg", FLOW, schema, vocabulary)`.

| test | key | it asserts |
|---|---|---|
| `test_the_render_job_carries_each_photograph_taken_out` | `ui:render:a-photograph-taken-out-leaves-the-quote` | `_order`'s script now writes `sys.argv[4:]` after the session, joined by spaces, so a line with none reads as before; `jobs.render({"b": folder}, limit=1500, total=1, keep_open=False, without=[path])` records `f"render 1500 {id} --without {path}"`; `build_parser().parse_args([*render_command(1500, roots, id)[3:], *without_flags([path])]).without == [path]` |
| `test_a_photograph_taken_out_leaves_the_quote_and_the_session` | `ui:render:a-photograph-taken-out-leaves-the-quote` | the quote with `"without": taken` lists `beatrix.jpg` alone, its `run` `beatrix.id`, and counts 1 image; with `Jobs.render` monkeypatched to record its keywords and return `{}`, `POST /api/render` with that `without`, its `limit_s` and `images: 1` answers 200, and the recorded `without` is `[folder / "runs" / ada.id / FLOW]` |
| `test_a_photograph_no_quoted_run_holds_is_refused`, `ids=["no-run", "outside"]` | `ui:render:a-photograph-not-quoted-is-refused` | the quote whose `without` names run `nobody`, then `../b`, answers 409, its refusal holding `close Render and open it again`; `POST /api/render` with that `without`, `limit_s` and `images` answers 409 the same |

## The dialog's tests

- **`tests/test_ui_jobs.py`**: the quote test becomes `test_the_quote_lists_each_flows_images_and_the_price`; its
  `assert row["left_out"] == [...]` becomes `assert "left_out" not in row` and
  `assert row["flows"][1]["sources"][0]["run"] == ada.id`, `ada` the run `_approved(folder, "ada.jpg", …)` returns.
- **`ui/src/components/RenderDialog.test.ts`**: the `leftOut` block (`:41-64`) and its import go; `source()` gains
  the field `` run: `r${index}` ``. The blocks added, each `spec(<key>, …)`:

| key | it asserts |
|---|---|
| `ui:render:taking-out-shows-the-next` | over 17 sources, `thumbs('c', 'summon-anime-wai', sources, new Set(['c\|d3\|summon-anime-wai']))` titles `p0`–`p2` and `p4`–`p15`, each `v1`, and `more` is 1 |
| `ui:render:nothing-left-disables-render` | `confirmReason([row], out, null)` is `NOTHING_LEFT`, `'Nothing left to render.'`, with each of `row`'s keys in `out`, and `null` with one left; a row with no source gives `'refused'` for `disabled` `'refused'` |
| `ui:render:the-tiles-move-by-flow` | `tileMoved([3, 2], i, move)`: `(0, 'column+')` → 1, `(2, 'column+')` → 2, `(0, 'column-')` → 0, `(2, 'row+')` → 4, `(4, 'row-')` → 1, `(1, 'row+')` → 4 |

- **`ui/src/composables/useEdges.test.ts`**: a block `ui:render:a-key-move-centres-the-tile` on `useEdges(page, true)`:
  `(middle, 1, 3)` calls `scrollIntoView({ block: 'center' })` and no `scrollTo`; `(first, 0, 3)` calls
  `scrollTo({ top: 0 })` and `(last, 2, 3)` `scrollTo({ top: 900 })`, neither calling `scrollIntoView`.

## The end-to-end steps

In `test_the_render_dialog_opens_on_its_first_photograph` (`tests/e2e/test_render.py:52-100`), after the `Tab` loop
and before its `Escape`, a step on `WIDE`'s row, whose four photographs render one image each:

```python
    # A tile is taken out by ⌫ and by its ×; a row with none left says so.
    wide = dialog.locator(f'[data-collection="{WIDE}"]')
    tiles = wide.locator("[data-tile]")
    expect(tiles).to_have_count(4)
    tiles.first.focus()
    page.keyboard.press("l")
    expect(tiles.nth(1)).to_be_focused()
    page.keyboard.press("Backspace")
    expect(tiles).to_have_count(3)
    expect(wide).to_contain_text("3 images")
    expect(tiles.nth(1)).to_be_focused()
    for _ in range(3):
        tiles.first.locator(".render-dialog__remove").click()
    expect(tiles).to_have_count(0)
    expect(wide).to_contain_text("all removed")
    expect(wide.locator("[data-tick]")).not_to_be_checked()
```

The test's opening lines change too: `expect(keep).to_be_focused()` becomes
`expect(dialog.locator("[data-tile]").first).to_be_focused()`; the comment `# ↵ on the checkbox neither ticks it nor
renders.` becomes `# ↵ on the first tile neither ticks the checkbox nor renders.`; and the `Tab` loop counts
`tabbable = dialog.locator('button:enabled:not([tabindex="-1"]), input')`, named on its own line before the loop's
`for _ in range(tabbable.count()):`.

## The record

The text edits of [D10](#d10). Each block replaces the lines named, as they stand: no line around them is rewrapped.
Line numbers are at `HEAD`, before any edit: apply each file's blocks from the bottom up.

**`docs/decisions.md`, docs D3** — line `:77` becomes:

```text
**`review` and `approve` stay working verbs.** The review UI is the guided path; the hand path stays. The Render
dialog's removal is `render --without`, so a session the page starts is one the terminal can run.
```

Line `:80` becomes:

```text
- **Made by:** `0018`, `0108`.
```

**docs D4** — line `:97` becomes:

```text
  confirmation carries the quote it showed and the photographs taken out of it, and a quote grown since is
  refused. The quote compares
```

Line `:99` becomes:

```text
- **Made by:** `0018`, `0061`, `0062`, `0063`, `0080`, `0106`, `0108`.
```

**docs D36** — line `:547` becomes:

```text
its count, in each collection it names, less each `--without`, on one pod. Three bounds hold it: the laptop's
watchdog at the session's
```

Line `:561` becomes:

```text
- **Made by:** `0035`, `0043`, `0044`, `0052`, `0058`, `0063`, `0083`, `0097`, `0108`.
```

**`README.md`** — line `:184` becomes:

```text
one runs root alone. `--without <runs>/<run-id>/<flow>`, repeatable and beside no request, takes that run's flow out
of what renders. The session stops at its limit — `--limit SECONDS`, or the work's estimate from recorded
```

**`isekai/interface/README.md`** — in the `render.py` row, line `:20`, this text:

```text
finds what each approval lacks or takes the requests,
```

becomes:

```text
finds what each approval lacks, less each `--without`, or takes the requests,
```

**`isekai/interface/ui/README.md`** — line `:31` becomes:

```text
  per collection and flow what renders, each source with its run, less what `without` takes out, and one
  estimate, limit and price at most.
```

Line `:33` becomes:

```text
  --progress json <runs>… --without …`, then `volume down` unless the window is kept.
```

## Tests

Every new test is a unit test but the tiles' keys, which only a browser shows; they are steps in the dialog's existing
end-to-end test, which already opens it over every collection (`T1`, `T2`). The removal steps run on `WIDE`'s row,
which nothing earlier in that test touches (`T3`). Client behaviour, so they run on every engine the suite has:
Chromium (`T4`).

| layer | adds | removes |
|---|---|---|
| unit | `tests/test_render.py`: a test per new `cli:render-short:*` key, the naming-nothing one over a path under no named root and one naming no flow; `tests/test_ui_jobs.py`: the quote and confirm with a photograph taken out, the refusal over a run the collection does not hold and a `../` one, and the job's line; `ui/src/components/RenderDialog.test.ts`: `ui:render:taking-out-shows-the-next`, `ui:render:nothing-left-disables-render`, `ui:render:the-tiles-move-by-flow`; `ui/src/composables/useEdges.test.ts`: `ui:render:a-key-move-centres-the-tile` | `RenderDialog.test.ts`'s `leftOut` block (`:41-64`), retired with `leftOut` by the delta (brief Q11); its key, `ui:render:the-dialog-shows-thumbnails-by-flow`, stays on the file's other blocks |
| end-to-end | steps in `tests/e2e/test_render.py`'s dialog test: the first tile focused, then `WIDE`'s tiles moved and taken out (`ui:render:a-tile-is-taken-out-by-its-key`) | none |

Renamed, each keeping its body but the lines named in [tasks](tasks.md):

| at `e404f132` | becomes |
|---|---|
| `test_the_render_dialog_opens_on_its_checkbox` (`tests/e2e/test_render.py:52`) | `test_the_render_dialog_opens_on_its_first_photograph`, its key `ui:dialogs:the-render-dialog-opens-on-its-first-photograph` |
| `test_the_quote_lists_each_flows_images_what_is_left_out_and_the_price` (`tests/test_ui_jobs.py:1034`) | `test_the_quote_lists_each_flows_images_and_the_price`, its `left_out` assertion now that the row holds none |

Counted with `uv run pytest <file> --collect-only -q | tail -1` and `npx vitest run` in `ui/` at `e404f132`, and as
planned:

| file | at `e404f132` | planned |
|---|---|---|
| `tests/test_render.py` | 44 | 50 |
| `tests/test_ui_jobs.py` | 28 | 32 |
| the suite, `uv run pytest --ignore=tests/e2e --collect-only -q` | 1496 | 1506 |
| `tests/e2e`, `uv run pytest tests/e2e --collect-only -q` | 19 | 19 |
| vitest, `npx vitest run` in `ui/` | 69 | 72 |

The one vitest block removed is mapped above (`I16`); no pytest test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- [The `Tab` from the first tile passes each later collection's tick before *Keep the volume open*] → accepted: one
  `Tab` order, the page's ([D7](#d7)); with one collection the checkbox is one `Tab` away, as brief Q12 asks.
- [A removal is lost when the dialog closes] → accepted: it is the session's choice, and nothing on disk records it.
- [`0107-the-slowest-card` edits `render.py` and `tests/test_render.py` too] → other hunks; `mf-integrate` merges it
  first, as `after:` orders.

## Moved since the brief

Nothing moved: `HEAD` is `e404f132`, the brief's base, and every fact re-read there stands. The brief's Facts thread
the check before `shortfall()` and `without` as a keyword on `render_command`; Q3 and the fakes decide otherwise
([D1](#d1), [D4](#d4)). Q11, Q12 and Q13 override the brief's Facts and Q8 where they differ.

## Verdict

**Feasible.** Each phase is green alone: the planner, the server, the dialog, the record.
