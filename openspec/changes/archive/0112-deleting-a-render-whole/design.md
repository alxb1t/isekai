# Design — 0112 deleting a render whole

An approval's last render deletes it through review's `withdraw`, down to the flow's sheets once no approval is left;
a draft from another flow's image copies it into the flow's `sources/`, and a copy of an approval names the target's own
sheet. **Verdict: feasible.**

## Context

Every line below is at `41560908`, the base. See [proposal](proposal.md) — Why.

- **The delete** — `delete_render` (`isekai/interface/ui/app.py:1146-1164`) and `_discard`
  (`isekai/interface/cli.py:593-633`) call `drop_thumbnails`, `discard_render` (`isekai/pipeline/generate.py:377-399`),
  then `withdraw(run, flow, version)` (`isekai/pipeline/review.py:601-632`). `withdraw` acts only on the newest approval
  with no draft above it, deletes its prompt and failure records and calls `cancel`, which writes the draft back.
- **The discard** — `discard` (`review.py:493-522`) deletes the waiting draft, and through `_drafting_wrote`
  (`:525-548`) the sheet, the flow's directory and its assignment when the sheet's producer holds `tags_from`.
- **The draft** — `draft_from` (`review.py:234-281`) records `image={"flow": source, …}` (`:278-280`) for a named
  seed. `drafting_approval` (`:295-329`) checks only the seed's record, `<seed>.render.json` (`:320-328`).
  `draft_across` (`isekai/interface/drafting.py:26-55`) fills a first sheet with `tags_from=source`; so does
  `refuse_image_drafts` (`:77-107`).
- **The sheet** — `prepare_sheet` (`isekai/pipeline/sheet.py:149-197`) records `tags_from` (`:184-185`);
  `_superseded` (`:199-227`) stays silent for such a sheet through `tagged_from` (`:281-288`).
  `SheetProducer` (`isekai/foundation/artifacts.py:148-159`) declares the key.
- **The page** — `_drafted` (`app.py:1330-1356`) returns the draft's sheet fields and the other flow's image while it
  exists; `ui/src/views/Review.vue:56-70` builds `revised` from it, and `ui/src/components/SourcePanel.vue:100-105`
  heads it `drafted from FLOW vN · seed N`.
- **The copy** — `_copy_approval` (`review.py:997-1076`) writes the source's body, its `sheet` the source's number
  (`:1010-1012`), so `revise` of the copy names a sheet the target lacks and `_differs` (`:1154-1171`) refuses it.
  `approve_flow` (`cli.py:994-1015`) calls `approve(…, source=args.source)`.
- **The layout** — `run.py:136-140` names the stage directories; `run_view.unread` (`isekai/interface/run_view.py:240-288`)
  names any other entry of a flow's directory as not read.

```
 isekai discard <image> · DELETE /api/c/…/renders/…
   ├─ drop_thumbnails(run, image)
   ├─ discard_render(image)                 image, record, emptied group
   └─ withdraw(run, flow, version)          its group gone?                            (D1)
         ├─ approval v, and each older one with no group:
         │     prompts/NNN.json, its failure records, sources/NNN.png, review/NNN.approved.json
         ├─ v the newest? the waiting draft and its sources/ copy
         └─ no approval left? sheets/ review/ prompts/ sources/, outputs/ when empty ─▶ <flow>/ empty
```

## Goals / Non-Goals

**Goals:**
- A deleted render's flow shows nothing to review once its last approval goes: the Hub cell reads *tagged*, Review
  opens empty.
- No file of one flow names a file of another.

**Non-Goals:**
- The one-offs of brief Q14b and Q17: run after release, dry run first, outside the change.
- Rewriting old files' `tags_from`, `drafted_from`, `copied_from` or cross-flow `image`: left as they are.
- A copy of the image for `approve --from`, or for a draft from another flow's approval naming no image.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `withdraw(run, flow, version) -> list[Path]` deletes per [the delete](#the-delete): `[]` unless `version` is an approval of `flow` whose group is gone; else that approval and each older one with no group, the waiting draft when `version` was the newest, and, with no approval left, the flow's other directories. It reads no file, so it never refuses; `_discard` loses its refusal branch | Brief Q9, Q10, Q11, Q11a, Q11b, Q12. Review owns approvals and drafts, and no stage imports another (`tests/test_layers.py`) | cancelling back to a draft: what `0111` shipped, brief Q9; keeping the sheets while older approvals with renders remain removed: they read that sheet |
| <a id="d2"></a>**D2** | The **source copy**: `run.py` gains `SOURCES = "sources"`; review gains `source_copy(run, flow, version) -> Path`, `run.directory(flow, SOURCES) / f"{version:03d}{OUTPUT_SUFFIX}"`. `draft_from` with a seed copies `group_of(run, source, approval) / f"{seed}{OUTPUT_SUFFIX}"` there with `write_atomically`, after every refusal (after `_refuse_edited`) and immediately before `_write_draft`, under the number the draft takes — `_waiting_number(run, flow)`, else `next_version(run.directory(flow, REVIEW))` — and records no `image`. `drafting_approval` refuses a seed whose image file is gone as it refuses one never rendered. `run_view.unread` reads `sources/` | Brief Q14, Q14a, Q15. Named by the draft's number, which its approval keeps, so Review finds it with no record, and the Q14b one-off rewrites no approval | recording the copy's name in the draft: a file to rewrite for each old approval; a copy beside the renders: it would count as one |
| <a id="d3"></a>**D3** | The page: `_drafted(one, path, body, remedy)` returns `None` unless `source_copy(run, flow, int(path.name[:3]))` is a file; else `{"fields": …, "version": N}`. `GET /api/c/{collection}/review/{digest}/{flow}/source/{version}` serves the copy, refusing one not there. `Drafted` is `{fields, version}`; `sourceCopyUrl` in `ui/src/api.ts` builds the route; `revised` loses `from`, its `seed` null for a copy, headed *the image it was drafted from* | Brief Q14: the page shows the photograph and that render with no reference to the source flow | naming the source flow in the kicker: brief Q14a, no reference |
| <a id="d4"></a>**D4** | `discard` deletes the waiting draft, then its source copy where one exists, then `sources/` when that empties it. `_drafting_wrote` and the flow's removal go | Brief Q13; supersedes `0111`'s C5, the undo keyed on `tags_from` | removing the sheet too: brief Q13 keeps the flow, and a sheet is the flow's own |
| <a id="d5"></a>**D5** | No cross-flow record: `sheet`'s and `prepare_sheet`'s `tags_from` becomes `drafted_from`, which shapes the refusal's remedy as now and is recorded nowhere. `SheetProducer.tags_from` and `tagged_from` go, and `_superseded` weighs every kept sheet | Brief Q15: new files stop writing it; old ones keep it, unread. The sheet is filled from the photograph's list, so a newer list supersedes it | keeping `tagged_from` for old sheets: Q15 ignores the field |
| <a id="d6"></a>**D6** | The copy's sheet, per [the copy](#the-copy): `_copy_approval` names the target's newest sheet and computes `edited` against it, refusing a target with none. `interface/drafting.py` gains `approve_across`, which fills a target with no sheet through `sheet()`, then copies; `approve_flow` calls it for `--from` | Brief Q16. `revise` copies the approval's `sheet`, so the copy's own makes its revision compare. The fill is the sheet stage's, so the composition is the interface's, as `draft_across` is | the fill inside review: a stage importing another |
| <a id="d7"></a>**D7** | The record, per [the record](#the-record): docs D4 and D49 edited and D50 added in `docs/decisions.md`; `docs/data-flow.md`, `docs/principles.md`, `README.md` and `isekai/interface/README.md` follow | A7 | leaving D49 saying a copy keeps the source's sheet |

## The delete

`withdraw` in `isekai/pipeline/review.py`, replacing the body at `:601-632`:

```python
def withdraw(run: Run, flow: str, version: int) -> list[Path]:
    """Delete approval `version` once its group is gone; return what went, absolute.

    With it go each older approval with no group, each with its prompt, failure
    records and source copy, and, where it was the newest, the draft waiting above
    it and that draft's source copy. A flow left with no approval keeps only its
    directory, its assignment: every path under sheets/, review/, prompts/ and
    sources/ goes, then those directories, then outputs/ when empty. Nothing is
    read, so nothing refuses.
    e.g. (run, f, 2), 001 rendered -> [f/prompts/002.json, f/review/002.approved.json]
    """
```

The order of the list, which `_discard` prints:

1. Each approval going, oldest first: `prompts/NNN.json`, each `attempts(prompts, NNN)` path, `source_copy(…, NNN)`,
   `approval_of(…, NNN)` — each that exists.
2. Where `version` was the newest approval: `current_draft(review)`, then the source copy of its number, each that
   exists.
3. Where no approval is left: for each of `sheets`, `review`, `prompts` and `sources` in that order that exists, each
   path of `sorted(directory.rglob("*"), reverse=True)`, then the directory; then `outputs` when it exists and is empty.

An older approval is one numbered below `version`; one whose group exists stays, and so does every newer approval. A
group no approval names, holding an image, keeps `outputs/` in place.

## The copy

`_copy_approval` renames its local `latest`, the target's newest approval's body (`:1038`), to `newest`, as it shadows
`run.latest`. After `validate` and before the write: `sheet_version = latest(run.directory(flow, SHEETS))`; `None`
refuses `f"{run.id}: flow {flow} has no sheet to copy {source}'s approval onto; run `{stage_command(run, 'sheet',
flow)}`, then `{copy}` again"`. It reads `held = read(target, SHEET_FILE, remedy=again)` with `target = sheet_of(run,
flow, sheet_version)`, `require(target, held, "fields", dict, again)`, where `again` is
``f"run `{stage_command(run, 'sheet', flow, options=NEW_VERSION)}`, then `{copy}` again"``. The copy written is
`{**body, "producer": producer, "flow": flow, "sheet": sheet_version, "fields": fields, "renders": renders}`, its
producer's `edited` set to `not same_fields(held["fields"], fields)`. The equal-copy check stays before all of it, so an
old copy in step writes nothing. The docstring's "`sheet` stays `source`'s: it is provenance" becomes "`sheet` is
`flow`'s newest sheet,", then on one line "which a revision of the copy is compared against".

In `isekai/interface/drafting.py`, after `draft_across`:

```python
def approve_across(
    run: Run,
    target: Flow,
    source: str,
    vocabulary: Callable[[], Vocabulary],
    field_map: Callable[[], FieldMap],
) -> tuple[Path | None, list[str]]:
    """Return `approve`'s answer for copying `source`'s latest approval under `target`.

    A target with no sheet has its sheet filled first from the photograph's tag
    list, as the sheet verb fills one, so the copy names a sheet of its own.
    e.g. (run, control, summon, …) -> (control/review/001.approved.json, [])
    """
```

It calls `sheet(run, target.id, target.schema, vocabulary(), field_map(), tagged=target.tagger,
flow_digest=target.digest)` when `latest(run.directory(target.id, SHEETS))` is `None`, then returns
`approve(run, target.id, target.schema, vocabulary(), source=source, excluded=field_map().excluded)`.
`approve_flow` calls it when `args.source` is not `None`, else `approve` as now.

## The record

`docs/decisions.md`:

- **D4** (`:83-101`): "and the newest approval its last render leaves through review's `withdraw`" → "and the
  approvals, drafts, sheets and source copies its last render leaves through review's `withdraw`". `Made by:` gains
  `` `0112` ``.
- **D49** (`:274-285`): its bold gains, after "taken once the same way", "; the copy names the target's own sheet,
  filled first where it holds none, and a draft from another flow's image holds a copy of that image in the target's
  `sources/`". `Made by:` gains `` `0112` ``.
- **D50**, after D49: `### D50 · The last render takes its approval, and a flow holds only its own files`. Bold:
  "Deleting an approval's last render deletes that approval, its prompt, its failure records and its source copy,
  every older approval with no render, and the newest's waiting draft; nothing goes back to a draft. A flow left with
  no approval keeps only its directory, its assignment: its sheets go too, and the photograph's tags and caption stay
  (D17). No file of one flow names a file of another." **Why:** the operator deletes a render to be rid of it; an
  approval, a draft or a sheet left behind kept the Hub and Review offering what was deleted, and a reference into
  another flow breaks when that flow's work goes. **Made by:** `0111`, `0112`.

`docs/data-flow.md`: `:72-75`, "A delete that empties the newest approval's group takes that approval back to its
draft, with its prompt and failure records; one that leaves images renders what it lacks at the next session." → "A
delete that empties an approval's group deletes that approval, older ones with no render and the newest's waiting
draft; a flow left with no approval keeps only its assignment (D50). One that leaves images renders what it lacks at
the next session." `:35`, "with --from, reads the source flow's approval instead" → "with --from, reads the source
flow's approval instead, onto its own sheet". The draft paragraph (`:54-61`) gains, after its first sentence, "Into
another flow, the image is copied into that flow's `sources/` under the draft's number." The run tree (`:157-161`)
gains `sources/    ③ the image a draft from another flow was drafted from` under `outputs/`.

`docs/principles.md:248-255`, *Known breaks*: the sentence on `discard` deleting a file the sheet stage wrote goes; the
`withdraw` sentence becomes "`pipeline/review.py`'s `withdraw` deletes the prompts and failure records the generate
stage wrote, numbered for each approval it deletes, and, once the flow holds no approval, the sheets the sheet stage
wrote and the flow's emptied `outputs/`."

`README.md`: the `--from` bullet (`:322-323`) gains "onto its own sheet, filled first from the photograph's tags where
it holds none"; the `--discard` bullet (`:334-336`) loses its last sentence and gains "with the image it was drafted
from, and leaves the flow and its sheet".

`isekai/interface/README.md:19`: `drafting.py`'s row gains "; and copies an approval across for `approve --from`, its
sheet filled first".

## The pipeline's tests

In `tests/test_review.py`, with its helpers `_approved_source`, `_summon_approved`, `_conjure`, `_approved` and `_image`:

| test | key | asserts |
|---|---|---|
| `test_a_draft_from_an_image_copies_it_into_the_targets_sources`, renamed from `test_a_drafted_draft_records_the_image_it_names_and_none_without` | `review:draft-from:a-draft-from-an-image-copies-it` | the unnamed draft holds no `image` and `source_copy(run, CONJURE, 1)` does not exist; after `discard`, the named draft holds no `image` and `source_copy(run, CONJURE, 1).read_bytes()` equals the image's bytes |
| `test_a_draft_naming_a_seed_its_approval_never_rendered_is_refused` | as now | a last step: with `SEED`'s image unlinked and its record left, `draft_from(…, seed=SEED)` refuses naming `rendered no seed {SEED}`, the run's snapshot unchanged |
| `test_a_drafted_draft_goes_alone_and_the_flow_stays`, rewritten from `test_a_drafted_draft_is_undone_whole_and_a_tagged_flows_alone` | `review:discard:a-drafted-draft-goes-alone` | CONJURE's sheet filled with `drafted_from=FLOW`, a draft from `FLOW` v1 seed `SEED`: `discard` returns the draft; the draft, its source copy and `sources/` are gone; `versions(…sheets) == [1]` and CONJURE's directory exists |
| `test_a_copy_names_the_targets_own_sheet`, new | `review:copy-from:the-copy-names-the-targets-own-sheet` | with no CONTROL sheet the copy refuses naming `sheet` and the run's snapshot is unchanged; with one, the copy's `sheet` is `1`, `producer["edited"]` is `False`; `_image(run, 1, 11, CONTROL)`, `revise(run, CONTROL, 1, 11)`, an edit and `approve` write `002.approved.json` |
| `test_the_last_render_takes_its_approval_and_the_waiting_draft`, rewritten from `test_the_newest_approvals_last_render_takes_it_back_to_its_draft` | `image-generation:discard:the-approval-goes-with-its-last-render`, `run-directory:idempotence:the-newest-approval-goes-with-its-last-render` | FLOW approvals 001, with `_image(run, 1, 11)`, and 002 with no group; a prompt and a failure record for 002, a file at `source_copy(run, FLOW, 2)`, and `review(run, FLOW, new_version=True)`: `withdraw(run, FLOW, 2)` returns those paths, the approval and the draft in [the delete](#the-delete)'s order; no draft is written; every other file of the run is as it was |
| `test_older_approvals_with_no_render_go_and_rendered_ones_stay`, rewritten from `test_an_older_approvals_last_render_leaves_it` | `image-generation:discard:older-render-less-approvals-go` | FLOW approvals 001 with an image, 002 and 003 with none: `withdraw(run, FLOW, 1) == []`, snapshot unchanged; `withdraw(run, FLOW, 3)` deletes 002 and 003; 001 and its group stay |
| `test_a_flow_left_with_no_approval_keeps_only_its_assignment`, rewritten from `test_a_waiting_draft_keeps_the_approval_its_last_render_left` | `image-generation:discard:a-flow-with-no-approval-keeps-its-assignment` | FLOW approved once, its prompt assembled, no group: `withdraw(run, FLOW, 1)` leaves `run.directory(FLOW)` an empty directory and `photo/`'s snapshot unchanged; then, with an image in `outputs/005/` and approval 001 again, `outputs/005/` and `outputs/` stay |

`_approved_source` also fills CONTROL's sheet, `sheet(run, schema, vocabulary, flow=CONTROL)` from `tests/stages.py`,
so every copy test copies onto a sheet; `test_a_copy_names_the_targets_own_sheet` deletes it for its refusal.

In `tests/test_sheet_stage.py`: `_drafted` passes `drafted_from=FLOW`;
`test_a_drafted_sheet_is_filled_from_the_photographs_list_and_names_its_source` becomes `…_and_names_no_source`, keyed
`sheet:output:a-drafted-sheet-names-no-source`, asserting `"tags_from" not in body["producer"]`;
`test_a_sheet_a_draft_wrote_is_never_weighed` is deleted. `tests/test_run_view.py:108` and `tests/test_resume.py:383`
pass `drafted_from=FLOW`. In `tests/test_generate.py`, the copies at `:2011` and `:2034` are preceded by a CONTROL
sheet, `sheet(…, flow=CONTROL)`; so is the copy in `tests/test_pipeline_cli.py`'s
`test_approve_cancel_answers_each_run_on_its_own` (`:702`), `sheet(rendered, schema, vocabulary,
flow="control-anime-wai")`.

`tests/test_run_view.py`'s `test_a_name_show_does_not_read_is_named` writes `run.directory(FLOW, "sources",
"001.png")` after `_rendered(run)`, before `unread(run) == []`, and gains the case `("sources", "notes.txt", False)`,
id `sources-file`.

## The server's and the verb's tests

- `tests/test_ui_api.py`'s `test_review_reads_a_drafted_draft_against_its_sheet_and_its_image`: `body["drafted"] ==
  {"fields": own, "version": 1}`; `GET {route}/source/1` answers 200 with the image's bytes, read before; with FLOW's
  seed-7 image unlinked, `drafted` and the route are unchanged; `GET {route}/source/2` answers 409.
- `test_review_keeps_an_approved_drafted_drafts_marks`: `body["drafted"] == {"fields": own, "version": 1}`.
- `test_a_draft_into_a_target_whose_waiting_draft_is_its_sheet_replaces_it` reads `["drafted"]["version"] == 1`;
  `test_a_selection_from_two_runs_drafts_each_into_the_flow_chosen` also asserts `"image" not in draft["producer"]`.
- `test_deleting_a_render_deletes_its_files_and_thumbnail`: after `v1/11`, `review/001.approved.json` is gone and
  `002.approved.json` stays; its last step's comment becomes `# The last approval's only render goes, and the flow
  keeps only its assignment.`, and after `v2/22`, `list(made.directory(FLOW).iterdir()) == []`.
- The CONTROL copy at `tests/test_ui_api.py:1141` is preceded by a CONTROL sheet.
- `tests/test_pipeline_cli.py`: `test_draft_writes_another_flow_from_the_images_approval_and_seed` (`:813`) asserts `"image" not in` the
  producer and the source copy's bytes equal the image's; `test_draft_assigns_a_target_with_no_sheet_and_fills_it_from_the_source`
  lists `["review", "sheets", "sources"]` and asserts `"tags_from" not in filled["producer"]`;
  `test_discarding_the_last_render_takes_its_approval_with_it` expects, after the group's lines, `prompts/001.json`,
  `review/001.approved.json`, `sheets/001.json`, `sheets`, `review`, `prompts`, `outputs`, then the thumbnail, and an
  empty flow directory; `test_approve_from_fills_a_target_with_no_sheet_first`, new
  (`review:copy-from:a-target-with-no-sheet-is-filled-first`): `approve --flow control-anime-wai --from
  summon-anime-wai <photo>` on a run whose summon is approved writes `control-anime-wai/sheets/001.json` and a copy
  whose `sheet` is `1`.

## The end-to-end steps

`tests/e2e/test_render.py`'s `test_conjure_from_this_opens_review`:

- `expect(revised).to_contain_text(f"drafted from {FLOW} v1 · seed 7")` → `to_contain_text("the image it was drafted
  from")`;
- the comment before the delete becomes `# The delete asks on No, then Yes lands on the Hub on the cell. FLOW's only
  render goes, and FLOW keeps only its assignment; CONJURE's draft holds its own copy.`;
- `expect(cell).to_have_attribute("data-stage", "draft")` → `"tagged"`;
- after opening CONJURE's Review, `expect(page.locator("[data-revised]")).to_have_count(0)` → the `[data-revised] img`
  has `complete` true and a `naturalWidth` other than 0; this step and the kicker's are phase 2's, the rest phase 5's.

## Tests

Every new test is a unit test (`T1`). No end-to-end test is added: the conjure-from-this test already reaches the
drafted draft and the deleted render, so the new assertions are its steps (`T2`), on the state its own acts made
(`T3`). Server-rendered state, one engine: Chromium (`T4`).

| layer | adds | removes |
|---|---|---|
| unit | `test_a_copy_names_the_targets_own_sheet`; `test_approve_from_fills_a_target_with_no_sheet_first`; the `sources-file` case | `test_a_sheet_a_draft_wrote_is_never_weighed` |
| end-to-end | steps in `test_conjure_from_this_opens_review` | its `drafted from FLOW v1` line |

Deleted, each retired by a decision:

| test | file | retired by |
|---|---|---|
| `test_a_sheet_a_draft_wrote_is_never_weighed` | `tests/test_sheet_stage.py` | [D5](#d5): a drafted sheet is weighed as any; `sheet:superseded:a-newer-tag-list-is-named` holds the warning |

Counted with `uv run pytest <file> --collect-only -q | tail -1` at `41560908`, and as planned:

| file | at `41560908` | planned |
|---|---|---|
| `tests/test_review.py` | 111 | 112 |
| `tests/test_pipeline_cli.py` | 65 | 66 |
| `tests/test_ui_api.py` | 97 | 97 |
| `tests/test_sheet_stage.py` | 43 | 42 |
| `tests/test_run_view.py` | 38 | 39 |
| the suite, `uv run pytest --ignore=tests/e2e --collect-only -q` | 1507 | 1509 |
| `tests/e2e`, `uv run pytest tests/e2e --collect-only -q` | 19 | 19 |

## Dependencies

None.

## Risks / Trade-offs

- An older approval going leaves a newer one whose `from` names it. Cancelling that newer one writes a draft whose
  approval refuses, naming the missing origin; `review --discard` and a fresh draft are the way on.
- `approve --from` on a target with no sheet writes the sheet before the copy's validation, so a copy refused by the
  target's schema leaves a sheet, as Prepare would have.
- Until the Q14b one-off runs, an old *Draft from this* approval shows the photograph alone, its marks gone.

## Verdict

Feasible at `41560908`: every symbol named exists, and no dependency is added.
