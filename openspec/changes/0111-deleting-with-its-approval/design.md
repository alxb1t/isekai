# Design — 0111 deleting with its approval

A discard that empties the newest approval's group cancels that approval through review's new `withdraw`, and copies
and drafts from another flow stop naming their source, so nothing outside the flow holds the cancel. **Verdict:
feasible.**

## Context

Every line below is at `2c89c4dd`, the base.

- **The delete** — `discard_render(image)` (`isekai/pipeline/generate.py:378-399`) unlinks the image, its record and
  an emptied group. The route `delete_render` (`isekai/interface/ui/app.py:1142-1156`) and the verb `_discard`
  (`isekai/interface/cli.py:605-626`) call it, then `drop_thumbnails(run, image)`
  (`isekai/interface/ui/library.py:476-492`), which globs `<seed>.*.jpg` after the image is gone (`0106·R1`).
  `rendered_at(image)` (`isekai/foundation/run.py:527`) returns `(run, flow, version, seed)`.
- **The cancel** — `cancel` (`isekai/pipeline/review.py:558-602`) deletes a copy (`copied_from`, `:577`) and writes any
  other approval back to its draft. `_cancelling` (`:605-656`) refuses on `_derived` (`:659-715`), which lists the
  approval's own prompt, failure records and group, then every other flow's copy, drafted approval and waiting draft
  naming it, with the commands that can go first (`firsts`).
- **The copy** — `_copy_approval` (`review.py:1004-1081`) writes nothing when the target's newest approval's
  `copied_from` equals `{source, latest}` (`:1041-1043`), else writes the source's body with `copied_from` added
  (`:1074-1080`). `came_from` (`:1221-1233`) names no own approval for a producer holding `copied_from`.
- **The draft** — `draft_from` (`review.py:235-281`) records `drafted_from` (`:276`) and, given a seed, `image`
  (`:277-279`); no seed carries no renders (`:274`). `_write_draft` (`:736-772`) writes `drafted_from` (`:768-769`);
  `drafted_from()` (`:1191-1203`) reads it for `cancel` (`:593`), `_drafting_wrote` (`:524-545`) and the server's
  `_drafted` (`app.py:1322-1342`). `ui/src/views/Review.vue:173` prints `from FLOW v1`; `:59-70` shows the image.
- **The checks** — `refuse_out_of_step` (`generate.py:427-468`) reads `copied_from`; `_generate` calls it for
  `--seeds-from` and `--in-step-with` (`cli.py:1116-1124`), `--in-step-with` is declared at `:458-469`, guarded at
  `:729-734` and ends the verb at `:1131`; `render.py`'s `_asked` runs it for a source rendering first
  (`isekai/interface/render.py:1025-1030`).
- **The types** — `CopiedFrom` (`isekai/foundation/artifacts.py:162-166`), `ChainProducer.drafted_from` (`:183`),
  `ApprovedProducer.copied_from` (`:194`).

```
 isekai discard <image> · DELETE /api/c/…/renders/…
   ├─ drop_thumbnails(run, image)        its own <seed>.<digest>.jpg, the image still there   (D7)
   ├─ discard_render(image)              image, record, emptied group
   └─ withdraw(run, flow, version)       newest? group gone? no draft waiting?                (D1)
         └─ prompt + failure records ─▶ cancel(run, flow) ─▶ NNN.draft.json  (a copy: deleted)
```

## Goals / Non-Goals

**Goals:**
- The Hub reads *draft* once the newest approval's last render is deleted, and the render dialog stops offering it.
- No flow depends on another: a copy or a draft from another flow holds its own fields and seeds.

**Non-Goals:**
- A migration of files carrying `copied_from` or `drafted_from` ([D9](#d9)).
- A change to `--seeds-from`, which reads seeds at render time.
- A change to `revise()` of a copy's image, which keeps the source's sheet number as before.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `withdraw(run: Run, flow: str, version: int) -> list[Path]` in `review.py`, after `cancel`: returns `[]` unless `approved_versions(run.directory(flow, REVIEW))` is not empty and its last is `version`, `group_of(run, flow, version)` does not exist and `current_draft` of that directory is `None`. Else it reads the approval with `_approval(run, flow, version, …)`, refusing a damaged one, deletes `prompts/NNN.json` and each `attempts(prompts, version)` path that exists, calls `cancel(run, flow)`, and returns those paths and the approval's, absolute | Brief Q1, Q2, Q3, Q5, Q7, Q13. `review.cancel`'s own code, so a copy is deleted and any other approval goes back to its draft. In the review stage: no stage imports another (`tests/test_layers.py`), and `cancel` is review's | the composition in `discard_render`: the render stage would import review; a third confirm text: brief Q6 |
| <a id="d2"></a>**D2** | `_derived(run, flow, version) -> list[str]` lists only the approval's prompt, failure records and group; the loop over other flows and `firsts` go. `_cancelling` drops the `len(firsts) == len(derived)` branch; its other ways stay | Brief Q9: what another flow took holds its own copy | keeping `firsts` empty: a branch no input reaches |
| <a id="d3"></a>**D3** | The copy, per [the copy](#the-copy): `_copy_approval` writes the source's body, its producer without `copied_from`, `drafted_from` and `image`, plus `"copied": True`, and `renders` from `copied_renders`; it writes nothing when the target's newest approval `is_copy` and holds equal fields (`same_fields`) and equal `renders_of`. `came_from` and `cancel` test `is_copy(producer)` where they tested `copied_from` | Brief Q10, Q11, Q17. `copied` names no approval, so no reference can go stale; a copy has no draft of its own, so its cancel still deletes it, as `cli.py:1001` prints | a copy cancelled to a draft: its producer and `sheet` are the source flow's numbers, and approving that draft reads the wrong flow's sheet |
| <a id="d4"></a>**D4** | The draft: `draft_from` drops `drafted_from=`, and with `seed` `None` passes `copied_renders(run, source, approval, carried)` as its renders. `_write_draft` loses its `drafted_from` parameter; `drafted_from()` and `CopiedFrom` are deleted. `_drafting_wrote` keys on the drafted sheet alone: the draft's `sheet` names a sheet whose producer's `tags_from` is a string | Brief Q10, Q14, Q17. `tags_from` is written only when a draft fills a first sheet (`artifacts.py:147`), so the undo needs no source | keying the undo on `image`: a draft from an approval naming no image would lose its undo |
| <a id="d5"></a>**D5** | The checks go: `refuse_out_of_step` from `generate.py`; `--in-step-with`, its guards and its `return` from `cli.py`, `_generate` keeping `borrowed[run.id] = source_seeds(…)[1]`; `_asked` in `render.py` skips a request whose source renders first (`if request.by_count or late: continue`) and passes `--seeds-from` to the rest. `in_session_sources` stays, as it refuses a dependent before its source | Brief Q11 and Q17: the seeds are copied, so nothing is checked | keeping `--in-step-with` as a no-op: a flag that checks nothing |
| <a id="d6"></a>**D6** | The page: `_drafted(one, draft, body, remedy)` returns `None` unless `draft_image(body)` names a flow other than `one.flow.id`; else `{"fields": …}` from the draft's own sheet, plus `"image"` only while `group_of(run, image flow, version)` holds a file whose stem is the seed. `Drafted` in `ui/src/types.ts` loses `flow` and `approval`. `Review.vue`'s kicker line `from FLOW vN` becomes `if (drafted.value && !sheet.detail.value?.approved) return 'draft'` | Brief Q12, Q15. A drafted draft is from no tagger, so `draft from the tagger` would be false; `SourcePanel.vue`'s `drafted from FLOW vN · seed` heads the image only while it shows | copying the image into the target: brief Q15 |
| <a id="d7"></a>**D7** | `drop_thumbnails(run, image)` deletes `<seed>.<_digest(image)>.jpg` alone, reading the digest only after its collection check, and must run while the image exists; the route and `_discard` call it after `rendered`/`rendered_at` and before `discard_render` | Brief Q8, `0106·R1`: the digest is what tells two collections' thumbnails apart (`library.py:462-464`) | reading the digest inside `discard_render`: the render stage knows no library |
| <a id="d8"></a>**D8** | The record, per [the record](#the-record): docs D4, D17 and D38 edited and D49 added in `docs/decisions.md`; `docs/data-flow.md`, `docs/principles.md`, `docs/modules.md` and `README.md` follow | A7. Brief Q17: D38 is recorded as superseded | deleting D38: its anchor is linked from older archives |
| <a id="d9"></a>**D9** | A file carrying `copied_from` or `drafted_from` is left as it is. `is_copy` counts an old copy by the key's presence, its value never read | Brief Q16: no migration; an old copy has no draft to go back to either | reading neither: an old copy's cancel would write a draft on the source's sheet number |

## The copy

In `isekai/pipeline/review.py`, beside `came_from`:

```python
def is_copy(producer: Mapping[str, object]) -> bool:
    """Return whether an approval's producer says it is a copy of another flow's.

    A copy written before 0111 says so by `copied_from`, whose value is not read.
    e.g. {"copied": True} -> True; {"copied_from": {…}} -> True; {"from": 1} -> False
    """
    return producer.get("copied") is True or "copied_from" in producer


def copied_renders(run: Run, flow: str, version: int, body: ReviewApproved) -> Renders:
    """Return approval `version` of `flow`'s renders with every seed it rendered listed.

    Its listed seeds come first, then each seed its group holds an image of, and
    the count rises to their number where it is lower, so a copy renders the
    same seeds once and never reads its source again.
    e.g. {count 2, seeds []}, outputs/001/{11.png, 12.png} -> {count 2, seeds [11, 12]}
    """
```

`copied_renders` reads `renders_of(path, body, remedy)` with `path = approval_of(run, flow, version)` and
`remedy = f"restore it in {path} by hand"`, and the group's seeds as
`sorted(int(p.stem) for p in group.iterdir() if is_seed(p.stem))` when `group_of(run, flow, version).is_dir()`.

`_copy_approval`, after reading the source's body and building `fields`: `renders = copied_renders(run, source,
approval, body)`; then, where `mine` is the target's newest approval and `is_copy(latest["producer"])`,
`same_fields(latest["fields"], fields)` and `renders_of(mine, latest, …) == renders` hold, it returns `None` before
validating. The producer is built as
`producer = cast(ApprovedProducer, {k: v for k, v in body["producer"].items() if k not in _NOT_COPIED} | {"copied": True})`,
with `_NOT_COPIED = frozenset({"copied_from", "drafted_from", "image"})` beside `_copy_approval` and `cast` from
`typing`, so `ty` reads no key the type no longer declares. The copy written is
`{**body, "producer": producer, "flow": flow, "fields": fields, "renders": renders}`.
Its docstring drops "`copied_from` says where to look"; `approve`'s drops "the copy names where it came from";
`state`'s (`:142-143`) says a copy keeps its source's producer and says `copied`.

## The record

`docs/decisions.md`:

- **D4** (`:83-101`): "a deleted render through the render stage's `discard_render` and its thumbnails through the
  library's `drop_thumbnails`" → "a deleted render's thumbnails through the library's `drop_thumbnails`, the render
  through the render stage's `discard_render`, and the newest approval its last render leaves through review's
  `withdraw`". `Made by:` gains `` `0111` ``.
- **D38** (`:266-276`): its body becomes one bold line, "**Superseded by [D49](#d49--a-control-flow-is-its-subject-with-the-face-chain-at-zero-copied-once)
  in `0111`: a copy no longer names its source, and its seeds are copied rather than checked.**", and
  `- **Made by:** `0054`, `0103`; superseded by `0111`.`
- **D49**, after D38: `### D49 · A control flow is its subject with the face chain at zero, copied once`. Bold:
  "`control-anime-wai` is `summon-anime-wai`'s directory with `ip_weight` and `identity_cn_strength` at 0, held equal
  to it by a test. `approve --from` copies `summon`'s approval once — its fields and its seeds — and records neither
  the source flow nor its approval; a draft from another flow's approval is taken once the same way. A stage reads
  another flow's work only when the operator names it as a source; the photograph's description is every flow's
  (D17)." **Why:** the floor is the same sheet and the same noise with the face mechanism off, and the seeds travel
  with the copy, so that holds with no later check; a copy naming its source kept the source's approval from being
  cancelled or deleted with its renders. **Made by:** `0054`, `0103`, `0111`.
- **D17** (`:318`): its D38 link → D49.

`docs/data-flow.md:72-73`: "The newest approval it leaves short renders what it lacks at the next session." → "A
delete that empties the newest approval's group takes that approval back to its draft, with its prompt and failure
records; one that leaves images renders what it lacks at the next session." `:169`: the D38 link → D49.

`docs/principles.md:248-253`, *Known breaks*: after the `discard_render` sentence, add "`pipeline/review.py`'s
`withdraw` deletes the prompt and failure records the generate stage wrote, numbered for the newest approval whose last
render the operator discarded, before it cancels that approval."

`docs/modules.md:56-58`: "the render stage's `discard_render` and the library's `drop_thumbnails`" → "the library's
`drop_thumbnails`, the render stage's `discard_render` and review's `withdraw`".

`README.md:320-326`: `--seeds-from`'s second sentence goes; the `--in-step-with` bullet goes; `--from` becomes "copy
that flow's latest approval under each `--flow`, once, its seeds listed; a copy equal to it writes nothing, and any
other approval is copied over under the next number."

## The pipeline's tests

In `tests/test_review.py`, with the existing `_approved_source`, `_summon_approved` and `_conjure` helpers and `_image`, `tests/stages.py`'s `rendered_image`:

| test | key | asserts |
|---|---|---|
| `test_a_copy_carries_the_sources_seeds_and_names_no_source`, renamed from `test_a_copied_approval_names_its_flow_and_the_approval_it_came_from` | `review:copy-from:the-copy-carries-the-seeds` | `_image(run, 1, 11)` and `_image(run, 1, 12)` before the copy; the copy's `flow` is `CONTROL`, `producer["copied"] is True`, no `copied_from`, `renders == {"count": 2, "seeds": [11, 12]}` |
| `test_a_copy_leaves_the_sources_files_alone`, renamed from `test_a_copy_records_its_source_and_leaves_the_sources_files_alone` | `review:copy-from:the-copy-carries-the-seeds` | the source's snapshot is unchanged; the copy holds no `copied_from` |
| `test_a_target_not_copied_from_the_sources_latest_is_copied_again` | as now | `body["producer"]["copied"] is True` for `copied_from == …` |
| `test_a_drafted_draft_records_its_sheet_and_no_source_approval`, renamed from `test_a_drafted_draft_names_its_sheet_and_the_approval_it_came_from` | `review:draft-from:the-draft-records-no-source-approval` | the producer equality loses `drafted_from`; `assert "renders" not in body` becomes `body["renders"] == {"count": 1, "seeds": []}`, the source approval having rendered nothing |
| `test_a_draft_from_no_image_carries_the_approvals_seeds`, new | `review:draft-from:a-draft-from-no-image-carries-the-seeds` | `_image(run, 1, 11)`; `draft_from(run, CONJURE, FLOW, None, conjure)`'s renders are `{"count": 1, "seeds": [11]}` |
| `test_what_is_drafted_from_an_approval_holds_no_source_cancel`, rewritten from `test_an_approval_drafted_from_a_source_refuses_the_sources_cancel` | `review:draft-from:what-is-drafted-from-it-holds-no-source-cancel` | CONJURE approved from FLOW, then a CONJURE draft waiting from FLOW; `cancel(run, FLOW)` returns FLOW's `001.draft.json`; CONJURE's directory snapshot unchanged |
| `test_what_another_flow_took_holds_no_cancel`, rewritten from `test_a_copy_in_another_flow_refuses_the_sources_cancel` | `review:cancel:what-another-flow-took-holds-no-cancel` | CONTROL copied from FLOW; `cancel(run, FLOW)` returns FLOW's draft; CONTROL's snapshot unchanged |
| `test_the_newest_approvals_last_render_takes_it_back_to_its_draft`, new | `image-generation:discard:the-newest-approval-goes-with-its-last-render`, `run-directory:idempotence:the-newest-approval-goes-with-its-last-render` | FLOW approved, `prompt_artifact`, a `record_failure`, no group: `withdraw(run, FLOW, 1)` returns the prompt, the failure record and the approval; `001.draft.json` is back; a copy in CONTROL with no group is deleted by `withdraw(run, CONTROL, 1)` |
| `test_an_older_approvals_last_render_leaves_it`, new | `image-generation:discard:an-older-approval-stays` | approvals 001 and 002 of FLOW, no group: `withdraw(run, FLOW, 1) == []`, the run's snapshot unchanged |
| `test_a_waiting_draft_keeps_the_approval_its_last_render_left`, new | `image-generation:discard:a-waiting-draft-keeps-the-approval` | FLOW approved, `prompt_artifact`, `review(run, FLOW, new_version=True)`: `withdraw(run, FLOW, 1) == []`, snapshot unchanged |

Readers changed in place: `:1250` also asserts `"copied" not in producer`; `:1323` asserts `"drafted_from" not in`
the draft's producer; `test_a_drafted_draft_approves_as_an_edited_approval_and_no_copy` is unchanged: its draft names no image, and
`draft.read_bytes() == held` holds the cancel scenario. In `tests/test_pipeline_cli.py:821`, `drafted_from` → `"drafted_from" not in
draft["producer"]` beside the `image` assertion. In `tests/test_generate.py`,
`test_a_flow_renders_the_seeds_of_its_sources_latest_group` (`:1995`) gains the mark
`run-directory:layout:a-named-source-is-recorded`.

## The server's tests

- `tests/test_ui_api.py:2184` → `test_review_reads_a_drafted_draft_against_its_sheet_and_its_image`: `body["drafted"]
  == {"fields": own, "image": {"flow": FLOW, "version": 1, "seed": "7"}}`; then FLOW's seed-7 image is unlinked and
  `drafted` is `{"fields": own}`.
- `:2218` → `test_review_keeps_an_approved_drafted_drafts_marks`: the same dict, no `flow` or `approval`.
- `:2310` reads `["drafted"]["image"]["flow"] == FLOW`; `:2362` asserts `"drafted_from" not in draft["producer"]`.
- `test_deleting_a_render_deletes_its_files_and_thumbnail` (`:1680`) gains a last step, opened by the comment `# The newest approval's only render goes, and its approval with it.`: deleting `v2/22`, the newest
  approval's only render, leaves `review/002.draft.json` and no `review/002.approved.json`, and `001.approved.json`.
- `tests/test_ui_library.py`'s `test_dropping_a_renders_thumbnails_leaves_the_others` writes `group / "11.png"`, names
  its thumbnail `f"11.{library._digest(image)}.jpg"`, and asserts `11.bbb.jpg` — another collection's — and
  `22.ccc.jpg` stay.
- `tests/test_pipeline_cli.py`'s `test_discard_deletes_the_render_and_its_thumbnail` names its thumbnail by the image's
  digest and adds `7.other.jpg`, which stays. `test_discarding_the_last_render_takes_its_approval_with_it`, new, after
  it (`cli:discard:the-last-render-takes-its-approval`): a run approved, its prompt assembled and its only render
  discarded prints the group, `prompts/001.json` and `review/001.approved.json`, and leaves `review/001.draft.json`.

## The end-to-end steps

`tests/e2e/test_render.py`'s `test_conjure_from_this_opens_review`:

- the line `expect(page.locator(".form")).to_contain_text(f"from {FLOW} v1")` goes;
- the comment before the delete becomes `# The delete asks on No, then Yes lands on the Hub on the cell. FLOW's only
  render goes, so FLOW's approval goes back to its draft; CONJURE's draft holds its own.`;
- `expect(cell).to_have_attribute("data-stage", "approved")` → `"draft"`;
- after `assert not group_of(served.conjured, FLOW, 1).exists()`, it opens
  `f"{served.url}/c/{CONJURED}/review/{digest}/{CONJURE}"` and expects `.form` visible and `[data-revised]` to have
  count 0.

## Tests

Every new test is a unit test (`T1`). No end-to-end test is added: the CONJURE-from-FLOW test already reaches the
deleted render and the drafted draft, so the new assertions are its steps (`T2`), on the state its own delete made
(`T3`). Server-rendered state, one engine: Chromium (`T4`).

| layer | adds | removes |
|---|---|---|
| unit | `tests/test_review.py`: the new rows of [the pipeline's tests](#the-pipelines-tests); `tests/test_pipeline_cli.py`: `test_discarding_the_last_render_takes_its_approval_with_it` | the tests below |
| end-to-end | steps in `test_conjure_from_this_opens_review` | its `from FLOW v1` line |

Deleted, each retired by a decision:

| test | file | retired by |
|---|---|---|
| `test_a_copy_out_of_step_with_the_sources_renders_is_refused_before_any_endpoint` | `tests/test_generate.py` | [D5](#d5) |
| `test_a_damaged_approval_record_is_refused_by_name_before_any_endpoint` | `tests/test_generate.py` | [D5](#d5): nothing reads the approval's origin |
| `test_a_copy_behind_a_source_that_renders_first_is_refused_before_any_endpoint` | `tests/test_generate.py` | [D5](#d5) |
| `test_the_check_before_the_source_renders_is_refused_beside_a_server` | `tests/test_generate.py` | [D5](#d5): `--in-step-with` is deleted |
| `test_a_dependent_behind_its_source_in_one_session_refuses_before_the_pod` | `tests/test_render.py` | [D5](#d5) |

Counted with `uv run pytest <file> --collect-only -q | tail -1` at `2c89c4dd`, and as planned:

| file | at `2c89c4dd` | planned |
|---|---|---|
| `tests/test_review.py` | 107 | 111 |
| `tests/test_generate.py` | 113 | 105 |
| `tests/test_render.py` | 51 | 50 |
| `tests/test_pipeline_cli.py` | 64 | 65 |
| `tests/test_ui_api.py` | 97 | 97 |
| `tests/test_ui_library.py` | 25 | 25 |
| the suite, `uv run pytest --ignore=tests/e2e --collect-only -q` | 1511 | 1507 |
| `tests/e2e`, `uv run pytest tests/e2e --collect-only -q` | 19 | 19 |

## Dependencies

None.

## Risks / Trade-offs

- A damaged approval refuses `withdraw` after the render is gone: the route answers 409 and the verb exits 1, naming
  the approval; the render stays deleted, which the operator asked for.
- A copy's cancel still deletes it, so a delete of a copy's last render leaves the flow on what lies beneath; approving
  `--from` again restores it.
- A drafted approval made from no image shows no marks in Review: the app always drafts from an image.

## Verdict

Feasible at `2c89c4dd`: every symbol named exists, and no dependency is added.
