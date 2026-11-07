# Tasks — 0116 Prepare per photograph

The verb, then the job that runs it, then the prose, per [design](design.md). Paths are from the repository root.

## Progress

- [x] 1 — The verb
- [x] 2 — The job
- [ ] 3 — The prose

## 1 — The verb

- [x] 1.1 **HALT CHECK** — `_per_item` opens the tagger once per call, through `opening`, as
  [Context](design.md#context) says. Verify: `grep -n -F 'opening.append(_once(resolve))' isekai/interface/cli.py`
  prints one line.
- [x] 1.2 In `isekai/interface/cli.py`, add `("prepare", "tag, caption, then sheet each photograph in turn, for the
  cells named")` to `VERBS` after `sheet`. In `build_parser`, leave `prepare` out of the `photos` and `--runs` loop, give
  it a `cells` positional (`nargs="+"`, `metavar="<run-id>/<flow>"`), its own `--runs` as the loop's, and
  `set_defaults(photos=[])`, and add it to the `--progress` tuple, per [D1](design.md#d1).
  Verify: `grep -n -F 'metavar="<run-id>/<flow>"' isekai/interface/cli.py` prints one line.
- [x] 1.3 In `isekai/interface/cli.py`, add `_prepare(args: argparse.Namespace, wired: Wiring) -> int` per
  [D1](design.md#d1), [D2](design.md#d2), [D3](design.md#d3) and [D4](design.md#d4), and route `verb == "prepare"` to
  it inside `dispatch`'s `try`, beside `migrate`. Verify: `grep -n -F 'def _prepare(args: argparse.Namespace, wired: Wiring) -> int:' isekai/interface/cli.py` prints one line.
- [x] 1.4 In `isekai/interface/cli.py`'s module docstring, add the line `prepare   (1)(2) each photograph's tags,
  prose, then its cells' sheets, in turn` after `sheet`'s, and in the paragraph below it, after "`tag` and `caption`
  take no flow, since they describe the photograph every flow reads (D17)," add "`prepare` names each flow in a cell,". Verify: `grep -n -F "each photograph's tags," isekai/interface/cli.py` prints one line.
- [x] 1.5 In `tests/test_pipeline_cli.py`, add `"prepare"` to `EXPECTED_VERBS` after `"sheet"`, and
  `"prepare": ["r1/summon-anime-wai"]` to `test_each_verb_is_reachable_as_a_subcommand`'s `own`, per
  [Tests](design.md#tests). Verify: `uv run pytest tests/test_pipeline_cli.py -k "verbs or subcommand or help"` exits 0.
- [x] 1.6 In `tests/test_pipeline_cli.py`, add `test_prepare_takes_each_photograph_in_turn`,
  `test_prepare_opens_the_tagger_once`, `test_prepare_refuses_a_cell_no_longer_assigned` and
  `test_prepare_refuses_a_bad_cell_before_any_run_opens`, with the markers [Tests](design.md#tests) names.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k test_prepare_` exits 0.

## 2 — The job

- [x] 2.1 In `isekai/interface/ui/jobs.py`, per [D5](design.md#d5): retype `Command`; replace `isekai_command` with
  `prepare_command`; add `cells_of`; make `_run` and `_start` start one child and set `job.flow` and `job.stage` from each
  line. Rewrite the module docstring's Prepare line as `└ answers ─▶ prepare <cells>: each photograph tag ─▶ caption ─▶
  its sheets ─▶ done`, and `PREPARE`'s comment to say the one child takes each photograph through them in turn.
  Verify: `grep -n -F 'def prepare_command(runs: Path, cells: Sequence[str]) -> list[str]:' isekai/interface/ui/jobs.py` prints one line.
- [x] 2.2 In `isekai/interface/ui/jobs.py`, confirm `isekai_command` has no reader left.
  Verify: `git grep -n isekai_command -- isekai` prints nothing.
- [x] 2.3 In `tests/test_ui_jobs.py`, make `_Script` take one script: `__call__(runs, cells)` appends `list(cells)` to
  `asked` and returns `[sys.executable, "-c", script, *run ids]`, each cell's run id once, in order. Update each caller:
  - `_Script({"<verb>": X})` → `_Script(X)`, and `_Script({})` → `_Script("pass")`;
  - `test_prepare_totals_count_each_stages_cells_once`: one `_reports` of its tag, caption and sheet lines, in that order;
  - `test_stop_interrupts_the_stage_and_starts_no_later_one`: steps `plan({FLOW: [run.id, done.id]}, {FLOW: True})`,
    a `{"stage": "sheet", "done": 0, "of": 2}` row, `asked == [[f"{run.id}/{FLOW}", f"{done.id}/{FLOW}"]]`;
  - `test_a_stage_that_fails_before_it_reports_ends_the_job_naming_the_log`: `("failed", None)`, and the message holds
    `prepare ended before reporting`;
  - `test_a_stage_reporting_an_item_done_sends_that_cells_new_stage`: steps `_steps(run)`;
  - each `asked == ["tag"]` → `asked == [[f"{run.id}/{FLOW}"]]`;
  - `test_a_photograph_is_described_once`: assert `plan`'s verbs, then `prepare_command(tmp_path, cells_of(steps))`
    parses with `build_parser` as `prepare` over `["r1/<FLOW>", "r1/<other>"]`; add the marker
    `ui:prepare:each-photograph-in-turn` and a step: `cells_of(plan({FLOW: ["r1", "r2"], other: ["r2"]}, …))` is
    `["r1/<FLOW>", "r2/<FLOW>", "r2/<other>"]`.

  Verify: `uv run pytest tests/test_ui_jobs.py` exits 0.
- [x] 2.4 In `tests/test_ui.py`'s `test_sigint_ends_streams_without_cancellation_output`, the patched `_command`
  `lambda verb, flow, runs, ids: sleep` → `lambda runs, cells: sleep`, and its steps `[Step(None, "tag", (run.id,))]`
  → `[Step(None, "tag", (run.id,)), Step("summon-anime-wai", "sheet", (run.id,))]`.
  The type change forces this edit; the Verify proves the test passes after it, and may pass before by a race.
  Verify: `uv run pytest tests/test_ui.py -k test_sigint_ends_streams_without_cancellation_output` exits 0.
- [x] 2.5 In `tests/e2e/test_prepare.py`, the comment above `PREPARED`: "Three CLI children start in turn, each importing
  the package." → "One CLI child imports the package, then prepares the photograph."
  Verify: `grep -n -F 'One CLI child imports the package' tests/e2e/test_prepare.py` prints one line.

## 3 — The prose

Each edit keeps its grepped phrase on one line, rewrapping around it.

- [ ] 3.1 In `docs/decisions.md`'s D4, "Prepare is `tag`, `caption` and `sheet` run as children" → "Prepare is `prepare`
  run as one child, each photograph through `tag`, `caption` and its sheets in turn", and add `0116` to its *Made by*,
  per [D6](design.md#d6). Verify: `grep -n -F 'run as one child, each photograph through' docs/decisions.md` prints one line.
- [ ] 3.2 In `docs/decisions.md`'s D1, add after `--new-version`'s bullet: "- **`prepare`** runs `tag`, then `caption`,
  per photograph, then its sheets; each refusal costs only its own step, so a caption's never holds back a sheet." Add
  `0116` to its *Made by*. Verify: `grep -n -F "so a caption's never holds back a sheet" docs/decisions.md` prints one line.
- [ ] 3.3 In `README.md`: add `prepare` after `sheet` in the verb list `import | assign | tag | caption | sheet`; "and
  *Prepare* runs `tag` and `caption` once per photograph, then `sheet` per flow, over what changed as one job, the CLI's
  own verbs as children" → "and *Prepare* runs `isekai prepare` over what changed as one job, each photograph tagged,
  captioned and sheeted before the next, the CLI's own verb as a child"; "`--progress json` — on `tag`, `caption` and
  `sheet`" → "`--progress json` — on `tag`, `caption`, `sheet` and `prepare`".
  Verify: `grep -n -F 'captioned and sheeted before the next, the CLI' README.md` prints one line.
- [ ] 3.4 In `docs/data-flow.md`, the paragraph *Prepare is a job of those children*: "runs `tag` and `caption` once over
  the photographs of every assigned cell with no sheet, naming no flow, and `sheet` per flow over its cells, each with"
  → "runs `prepare` once over every assigned cell with no sheet, each photograph tagged, captioned and sheeted before
  the next, with"; its diagram's `Prepare ─▶ probe ─▶ tag ─▶ caption ─▶ sheet      children, --progress json` →
  `Prepare ─▶ probe ─▶ prepare: per photograph tag ─▶ caption ─▶ sheet   one child, --progress json`, the arrows below
  rewrapped to it. Verify: `grep -n -F 'each photograph tagged, captioned and sheeted before' docs/data-flow.md` prints one line.
- [ ] 3.5 In `docs/modules.md`, "runs `python -m isekai tag | caption`, once per photograph and naming no flow, then
  `python -m isekai sheet` per flow," → "runs `python -m isekai prepare` over the cells, each photograph tagged,
  captioned and sheeted in turn,". Verify: `grep -n -F 'over the cells, each photograph tagged, captioned and sheeted in turn' docs/modules.md` prints one line.
- [ ] 3.6 In `isekai/interface/README.md`: `cli.py`'s row, after "`tag` and `caption` once per photograph, naming none —"
  add "and `prepare` over cells, each photograph through both and its sheets in turn —"; `ui/jobs.py`'s row, "`tag` →
  `caption` once per photograph, then `sheet` per flow, run as CLI children" → "one `prepare` child, each photograph
  through `tag` → `caption` → its sheets". Verify: `grep -n -F 'child, each photograph through' isekai/interface/README.md` prints one line.
- [ ] 3.7 In `isekai/interface/ui/README.md`'s *Prepare* bullet, "runs `isekai tag` and `caption` once over the
  photographs, naming no flow — the description is every flow's — then `sheet` per flow, as children, each with
  `--progress json`, each line of their prose" → "runs `isekai prepare` over the cells as one child, each photograph
  tagged, captioned and sheeted before the next, with `--progress json`, each line of its prose".
  Verify: `grep -n -F 'over the cells as one child, each photograph' isekai/interface/ui/README.md` prints one line.
