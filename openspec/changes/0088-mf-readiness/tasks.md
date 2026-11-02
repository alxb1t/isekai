# Tasks — 0088 mf readiness

The worktree, the changelog, the documents, the threat model, then the ruleset, per [design](design.md). Paths are
relative to the repository's root.

## Progress

- [x] 1 — The worktree
- [x] 2 — The changelog
- [x] 3 — The documents
- [ ] 4 — The threat model
- [ ] 5 — The ruleset **HUMAN**

## 1 — The worktree

- [x] 1.1 Add a `setup` target to `Makefile` per [D1](design.md#d1), listed in `.PHONY`, its comment saying it restores
  what a fresh worktree lacks and that the gate never fetches. `uv run python -m isekai.boundary.provision fetch
  config/vocabulary.json` is its last line. The `gate` recipe keeps its lines, and `make -n gate` prints what it did.
  `Makefile` changes by exactly these lines:
  ```diff
  - .PHONY: gate browsers drift derive
  + .PHONY: gate setup browsers drift derive
  + # Restore what a fresh worktree lacks: the environment, the browser toolchain,
  + # Chromium and the vocabulary. Not part of the gate, which never fetches.
  + setup:
  +     uv sync --locked
  +     npm ci --prefix ui
  +     $(MAKE) browsers
  +     uv run python -m isekai.boundary.provision fetch config/vocabulary.json
  ```
  Verify: `make -n setup | grep -c -E 'uv sync --locked|npm ci --prefix ui|playwright install chromium|provision fetch config/vocabulary.json'` prints `4`.
- [x] 1.2 Add to `AGENTS.md`, after its `## The quality gate` section, the section in
  [The run's lines](design.md#the-runs-lines), word for word.
  Verify: `grep -c -E '^- \*\*(Worktrees|Workspace setup|Ship network):\*\*' AGENTS.md` prints `3`, and `grep 'Ship network:' AGENTS.md | grep -c '`'` prints `0`.
- [x] 1.3 Name `make setup` where a person is told to restore `ui/node_modules/`: the `ui/node_modules/` row of `AGENTS.md`'s
  ignored-roots table, the Development paragraph of `README.md`, and the comment above `Install Node` in
  `.github/workflows/ci.yml`. `tools/npm_ui.py` and `isekai/interface/ui/bundle.py` keep their refusals.
  Verify: `grep -c 'make setup' README.md .github/workflows/ci.yml` prints a count above 0 for each file.
- [x] 1.4 Open `_wait`'s request in `tests/e2e/conftest.py` through the opener of [D3](design.md#d3).
  Verify: `grep -c 'ProxyHandler({})' tests/e2e/conftest.py` prints `1`, and `uv run pytest tests/e2e/test_routes.py` exits 0.

## 2 — The changelog

- [x] 2.1 **HALT CHECK** Prove phase 1's commit in a worktree with no ignored files. No file changes.
  Verify: `git worktree add --detach ../try-0088 HEAD && (cd ../try-0088 && make setup && make gate); code=$?; git worktree remove ../try-0088; test $code -eq 0` exits 0.
- [x] 2.2 In `tests/test_changelog.py`, per [D4](design.md#d4), add `LAST_NAMED = (0, 60, 0)` beside `FIRST_CHANGE`. In
  `format_problems`, a heading from `FIRST_CHANGE` through `LAST_NAMED` must name its change, one below must not, and one
  above may; a bullet directly under a heading above `LAST_NAMED` passes. The module docstring says so.
  Verify: `uv run pytest tests/test_changelog.py` exits 0.
- [x] 2.3 Add `test_a_release_after_the_line_needs_no_change_or_section` to `tests/test_changelog.py`, marked
  `spec_exempt`: `format_problems` of an `[Unreleased]` heading, then `## [0.60.1] - 2026-11-01`, then a bullet, is `[]`.
  Verify: `uv run pytest tests/test_changelog.py -k after_the_line` exits 0.
- [x] 2.4 In `CHANGELOG.md`'s preamble, before → after: ``A version's heading names its change: `## [0.25.0] - 2026-09-27 · 0035-the-flow-skills`.`` → ``A version's heading is its tag and date, `## [0.60.1] - 2026-11-01`; each up to `0.60.0` also names its change.``
  Verify: `sed -n 1,10p CHANGELOG.md | grep -c '0.60.1'` prints `1`.

## 3 — The documents

- [x] 3.1 Create `CODING_STANDARDS.md` per [D5](design.md#d5), its sections `## Baseline` and `## Project rules`: move
  `AGENTS.md`'s `## Engineering conventions` into the first and its *How a spec reads* into the second, word for word.
  Point `tests/test_spec_prose.py`'s docstring at `CODING_STANDARDS.md`.
  Verify: `grep -c 'How a spec reads' CODING_STANDARDS.md` prints a count above 0, and `grep -c 'Engineering conventions' AGENTS.md` prints `0`.
- [x] 3.2 Create `CONTRIBUTING.md`, its sections `## How a change lands` and `## The evidence a change carries`: move
  `AGENTS.md`'s `## The quality gate` and `## How a change is cut here` there, rewritten per [D5](design.md#d5). Add
  `CONTRIBUTING.md` to `MAY_CITE` in `tests/test_changelog.py`.
  Verify: `grep -c 'bump:' CONTRIBUTING.md` prints a count above 0, `grep -c 'version: vX.Y' CONTRIBUTING.md` prints `0`, and `grep -c 'How a change is cut here' AGENTS.md` prints `0`.
- [x] 3.3 Create `ARCHITECTURE.md` per [D6](design.md#d6), linking `docs/README.md`, `docs/modules.md`, `docs/data-flow.md`,
  `docs/principles.md`, `docs/decisions.md` and `docs/pins.md`.
  Verify: `wc -l < ARCHITECTURE.md` prints a number below `45`, and `grep -c 'docs/modules.md' ARCHITECTURE.md` prints a count above 0.
- [x] 3.4 Cut `AGENTS.md` to instructions: add [The mandatory lines](design.md#the-mandatory-lines) to its opening, and
  update its paragraph naming `## How a change is cut here` and the `README.md` lines naming what `AGENTS.md` carries.
  Verify: `grep -c 'CODING_STANDARDS.md' AGENTS.md` and `grep -c 'ARCHITECTURE.md' AGENTS.md` each print a count above 0.

## 4 — The threat model

- [ ] 4.1 Create `THREAT_MODEL.md` per [D7](design.md#d7). Worth protecting names the photographs and likeness, `.env` and
  the RunPod key, the money a pod or volume bills, and `main`. Entry points name a worker's reach, `isekai render` and
  `gpunit`, an upload, and a pod.
  Verify: `grep -c '^## ' THREAT_MODEL.md` prints `4`, and `grep -c 'Not written yet' THREAT_MODEL.md` prints `0`.
- [ ] 4.2 Add a link to `THREAT_MODEL.md` to `AGENTS.md`'s second mandatory line.
  Verify: `grep -c 'THREAT_MODEL.md' AGENTS.md` prints a count above 0.

## 5 — The ruleset

- [ ] 5.1 Create the ruleset of [D8](design.md#d8):

  ```sh
  gh api -X POST repos/alxb1t/isekai/rulesets --input - <<'JSON'
  {"name":"protect main","target":"branch","enforcement":"active",
   "conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"],"exclude":[]}},
   "rules":[{"type":"deletion"},{"type":"non_fast_forward"}]}
  JSON
  ```

  Verify: `gh api repos/alxb1t/isekai/rulesets --jq '.[].name'` prints `protect main`.
- [ ] 5.2 Read its rules back:

  ```sh
  gh api repos/alxb1t/isekai/rulesets --jq '.[0].id'
  gh api repos/alxb1t/isekai/rulesets/<that id> --jq '[.rules[].type] | sort | join(" ")'
  ```

  Verify: the second command prints `deletion non_fast_forward`.
