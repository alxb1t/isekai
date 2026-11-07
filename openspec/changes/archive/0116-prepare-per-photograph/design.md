# Design — 0116 Prepare per photograph

How Prepare takes each photograph end to end through one `prepare` child. Verdict: `feasible` — a verb composed from
the three verbs' own work, one child in place of a child per stage, and their prose.

## Context

Prepare at the base, in `isekai/interface/ui/jobs.py`:

```
post_prepare ─▶ library.unprepared(grid) ─▶ plan(todo, tagged) ─▶ Jobs.prepare
  plan  = [Step(None, "tag", tagged runs), Step(None, "caption", every run), Step(flow, "sheet", its runs)…]
  _run  = for step in plan: one child `python -m isekai <verb> [--flow f] --runs R --progress json <ids>`
```

- **The totals.** `_Job.asked(verb)` reads the plan's steps; `describe()` sums them per stage in `PREPARE` order. A
  line counts in `_Job.complete` when its `(flow, run)` is asked, its state is `done`, and `REACHED` holds for it.
- **The lines.** `cell_event` in `isekai/interface/ui/app.py` turns each line into cell events: a line naming no flow
  gives one per assigned flow, a line naming a flow gives that cell's. Neither reads which child wrote it.
- **The verbs.** `_per_item` in `isekai/interface/cli.py` returns one identifier's work for `tag`, `caption` or
  `sheet`, with its own `_Reporter` and, for `tag`, the `opening` thunk that loads the tagger once per `_per_item`
  call. `across` in `isekai/foundation/run.py` collects each `Refusal` and goes on.
- **An unticked cell.** Since `0115` a tagged cell with an empty directory unticks; `assign --remove` deletes the
  directory. `sheet()` in `isekai/pipeline/sheet.py` writes under `run.directory(flow, SHEETS)` whether or not the
  flow's directory still exists, so a sheet queued for an unticked cell would make its directory again.
- **Readers of what moves.** `isekai_command` is read by `jobs.py` and `tests/test_ui_jobs.py` alone. A `Command`'s
  signature is read by `jobs.py`, `tests/test_ui_jobs.py`'s `_Script`, and `tests/test_ui.py`, which patches `_command`. `VERBS` is read by `tests/test_pipeline_cli.py`'s `EXPECTED_VERBS`.

## Goals / Non-Goals

**Goals**

- A photograph's cells reach *sheet* before the next photograph is tagged (brief Q1, Q2).
- One child per job; the tagger loads once (brief Q1).
- The bar keeps `tag · caption · sheet`, its totals from the plan (brief Q4).
- A cell unticked mid-job refuses its sheet and counts in nothing (brief Q6).

**Non-Goals**

- Parallel photographs (brief Q3).
- A live refresh on Review, or a gate on Review or approval (brief Q2, Q5).
- Any change to `tag`, `caption` or `sheet` run alone, or to `ui/`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | A new verb, `prepare`, takes cells `<run-id>/<flow>`, split at the last `/`. It groups them by run, in the order each run is first named. Each run gets `tag` when one of its cells' flows declares `tagger`, then `caption`, then `sheet` for each of its cells in the order named, before the next run starts. It takes `--runs` and `--progress json`; it takes no `--flow`, no photograph path and no `--new-version`. A cell whose `wired.runs_root / <run-id> / FRAME_NAME` is not a file is refused at selection, so no step opens a new run | each photograph's assigned flows differ, so a cell is the one argument that says what to sheet; a run id is enough because a cell's run is assigned, so it exists | a `--flow` list (it would sheet a flow on a photograph not assigned it); one child per photograph (the tagger would load per photograph) |
| <a id="d2"></a>**D2** | `_prepare` in `cli.py` composes `_per_item`'s work: one `tag` work and one `caption` work for the whole invocation, and one `sheet` work per distinct flow, each over `{flow: loaded}`. The vocabulary and the field map are read once, through `replace(wired, vocabulary=vocabulary, field_map=lambda _: mapped())`, where `vocabulary = _once(wired.vocabulary)` and `mapped = _once(lambda: wired.field_map(vocabulary()))` | each verb's work, its lines and its refusals stay the code `tag`, `caption` and `sheet` run, and the one `tag` work opens the tagger once (`opening`) | a second copy of the three verbs' bodies |
| <a id="d3"></a>**D3** | Before a cell's sheet, `_prepare` checks `wired.runs_root / <run-id> / <flow>` is a directory. When it is not, it prints the sheet's `refused` line alone, with no `start` line before it, and collects `<run-id>/<flow> is not assigned, so prepare makes no sheet for it; run \`python -m isekai assign --flow <flow> --runs <runs> <run-id>\` first` | an unticked cell is the operator's choice; `sheet()` alone would make the directory again. A refused line counts in no stage (`_Job.complete`) | a guard in `sheet()`, which would change the hand path |
| <a id="d4"></a>**D4** | Each step of a photograph runs under `across`, so a refusal costs only its own step: a `caption` refusal leaves the sheets to run, and a `tag` refusal leaves each tagged flow's sheet to refuse on its own missing list | D1 in force: the sheet reads WD14's tags, so its input must not wait on Ollama. Decided by the cutter | skipping a photograph's sheets after any refusal |
| <a id="d5"></a>**D5** | In `jobs.py`, `Command` becomes `Callable[[Path, Sequence[str]], list[str]]`, the runs root and the cells. `isekai_command` becomes `prepare_command(runs, cells)`, the line `python -m isekai prepare --runs <runs> --progress json <cell>…`. A new `cells_of(steps)` returns `<run>/<flow>` for each run, in the order the sheet steps first name it, each run's flows in sheet-step order. `plan`, `Step`, `PREPARE`, `REACHED` and `_Job` are unchanged: the plan is the totals. `_run` starts one child and sets `job.flow` and `job.stage` from each line it reads | the bar and the events read lines, never children, so one child changes neither (brief Q4) | a new totals message from the verb |
| <a id="d6"></a>**D6** | `docs/decisions.md`'s D4 says Prepare is `prepare` run as one child, and D1 says `prepare` runs `tag` then `caption` per photograph, the sheet after, each refusal its own. Each adds `0116` to *Made by*. D17 is unchanged: a photograph is still described once | A7: a decision is edited where it lives | a new decision for the verb |

### D1 in code

```
prepare --runs R --progress json r1/summon r2/summon r2/conjure
  r1  across: tag(r1) · caption(r1) · sheet_summon(r1)
  r2  across: tag(r2) · caption(r2) · sheet_summon(r2) · sheet_conjure(r2)
  each sheet_<flow>: the D3 check, then the `sheet` work of `_per_item("sheet", …, {flow: loaded})`
```

A selection refusal — a cell with no `/` (`<cell>: not a cell; name one as <run-id>/<flow>`), an untracked flow (`_require_tracked`'s message), a run id with no run file (`<cell>: no run <run-id> under <runs>; run \`python -m isekai assign --flow <flow> --runs <runs> <photo>\` first`) — is raised before any run is opened,
inside `dispatch`'s `try`, so it prints `refused: …` and exits 1 as `_flows_for`'s does. Every run therefore exists when its steps start; a run file that cannot be read is refused by each step's own
`_run_for`, so each step reports its own `refused` line.

### D5 in code

`_run` at the base loops over steps; it becomes one child:

```
child = self._start(job, folder)            # argv = self._command(folder / RUNS, cells_of(job.steps))
for each line: job.flow, job.stage = line's flow, line's stage; cell events; complete
exit != 0 with no line, not stopping ─▶ failed: "prepare ended before reporting (exit N); read b/log.txt, then try again"
```

## Tests

Every new test is a unit test (`T1`): the verb is a function over doubles, and the job reads lines. The e2e
`ui:prepare:prepare-runs-the-assigned-cells` already reaches the one-photograph state and passes unchanged: its held
reader still holds `tag 1 of 1 · caption 0 of 1 · sheet 0 of 1`. Only its comment changes (`T2`). No test is deleted
or merged.

| layer | adds | changes |
|---|---|---|
| unit · `tests/test_pipeline_cli.py` | `test_prepare_takes_each_photograph_in_turn` (`cli:prepare:each-photograph-in-turn`, `cli:prepare:a-photograph-is-described-once`); `test_prepare_opens_the_tagger_once` (`cli:prepare:the-tagger-opens-once`); `test_prepare_refuses_a_cell_no_longer_assigned` (`cli:prepare:an-unassigned-cell-refuses`); `test_prepare_refuses_a_bad_cell_before_any_run_opens`, parametrized `no-slash`, `untracked` and `no-run` (`cli:prepare:a-bad-cell-is-refused`) | `EXPECTED_VERBS` gains `"prepare"` after `"sheet"`; `test_each_verb_is_reachable_as_a_subcommand`'s `own` gains `"prepare": ["r1/summon-anime-wai"]` |
| unit · `tests/test_ui_jobs.py` | none | `_Script` takes one script; `test_stop_interrupts_the_stage_and_starts_no_later_one`, `test_a_stage_that_fails_before_it_reports_ends_the_job_naming_the_log`, `test_prepare_totals_count_each_stages_cells_once`, `test_a_stage_reporting_an_item_done_sends_that_cells_new_stage`, `test_a_photograph_is_described_once` and the rest of `_Script`'s callers, per task 2.3 |
| unit · `tests/test_ui.py` | none | `test_sigint_ends_streams_without_cancellation_output`'s patched `_command` and its steps, per task 2.4 |
| end-to-end | none | `tests/e2e/test_prepare.py`'s comment above `PREPARED` |

The tagger test counts calls of a `wired.tagger` resolver wrapping `fake_wd14()`'s. The unassigned-cell test runs
two cells of one photograph, one whose directory was never made, so it stands on its own fixture (`T3`).

Counted at `a441b8b5`, and as planned:

| count | command | at `a441b8b5` | planned |
|---|---|---|---|
| `tests/test_pipeline_cli.py` | `uv run pytest tests/test_pipeline_cli.py --collect-only -q \| tail -1` | 66 | 73 |
| `tests/test_ui_jobs.py` | `uv run pytest tests/test_ui_jobs.py --collect-only -q \| tail -1` | 32 | 32 |
| the suite | `uv run pytest --ignore=tests/e2e --collect-only -q \| tail -1` | 1512 | 1519 |
| `tests/e2e` | `uv run pytest tests/e2e --collect-only -q \| tail -1` | 19 | 19 |

The planned 73: the four new tests, one parametrized three ways, are six, and the new `EXPECTED_VERBS` entry adds one case
to `test_each_verb_is_reachable_as_a_subcommand`, its one parametrized reader.

## Dependencies

None.

## Risks / Trade-offs

- **A slow photograph holds the next.** One Ollama model reads them in turn either way (brief Q3); the total time is
  unchanged.
- **A child that crashes mid-job ends the job.** At the base a later stage's child started anyway; now no later
  photograph runs. The job ends `done` with the bar short, as a refused photograph leaves it, and pressing Prepare
  again takes what is left.
- **Review opened before a caption lands** shows the `caption` command until a reload (brief Q2).

## Verdict

`feasible`. The verb composes the three verbs' work; the job runs one child and keeps its plan as the totals; D1 and
D4 say so.
