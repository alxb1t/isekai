# Tasks — 0026 the architecture in the repo

Prose phases: the sweep, then `docs/`, then the files that lose what `docs/` now holds.
Tests read some files edited here, but no string a test asserts changes ([design](design.md#context)).

## Progress

- [x] 1 — The sweep: code, tests and spec preambles
- [x] 2 — `docs/` written from the payload
- [x] 3 — `CLAUDE.md` keeps only process
- [ ] 4 — The group READMEs point at `docs/`
- [ ] 5 — `README.md` stops restating the architecture

Each site `S<n>` is a row of [D1](design.md#d1): its file, its *before* text and its *after*. Find a site
by its *before* text; line numbers are `2ccda2f`'s.

## 1 — The sweep: code, tests and spec preambles

- [x] 1.1 **HALT CHECK** — `cli.py` imports `wd14.py` at module scope, which S14's *after* rests on.
  Verify: `grep -n '^from isekai.boundary.wd14 import' isekai/interface/cli.py` prints one line.
- [x] 1.2 **HALT CHECK** — no test names `README.md`, `CLAUDE.md`, `docs/` or `openspec/`.
  Verify: `git grep -n -e README -e CLAUDE.md -e openspec -e 'docs/' -- 'tests/*.py'` prints only `tests/test_evaluate.py:708`.
- [x] 1.3 Apply S1, S2 and S3 to `isekai/pipeline/tagging.py`.
  Verify: `grep -n -e 'ships anyway' -e 'is not modified and is byte-identical' -e 'first producer in this repository' isekai/pipeline/tagging.py` prints nothing.
- [x] 1.4 Apply S4 and S5 to `isekai/interface/ui/batch.py`.
  Verify: `grep -n -e '.hosted. block never produces' -e '.reopened. below' isekai/interface/ui/batch.py` prints nothing.
- [x] 1.5 Apply S6 and S7 to `isekai/foundation/run.py`, S8 to `isekai/foundation/flow.py`, S9 to `tests/test_flow.py`.
  Verify: `grep -n -e 'The CLI did not return' -e 'sixth' isekai/foundation/run.py isekai/foundation/flow.py tests/test_flow.py` prints nothing.
- [x] 1.6 Apply S10 to `scripts/derive_field_map.py` and S11 to `tests/test_sheet_stage.py`.
  Verify: `grep -n -e 'last one that reads it' -e 'only authored group' -e 'carries that file' -e 'test_isolation' scripts/derive_field_map.py tests/test_sheet_stage.py` prints nothing.
- [x] 1.7 Apply S12 to `pyproject.toml`.
  Verify: `grep -n 'six endpoints' pyproject.toml` prints nothing.
- [x] 1.8 Apply S13–S17: `tests/test_pipeline_cli.py`, `tests/test_wd14.py`, `isekai/boundary/wd14.py`, `isekai/README.md`, `isekai/boundary/README.md`.
  Verify: `grep -n -e 'the only thing that would' -e 'the only check' -e 'the only module in the package' -e 'the only one in the package' tests/test_pipeline_cli.py tests/test_wd14.py isekai/boundary/wd14.py isekai/README.md isekai/boundary/README.md` prints nothing.
- [x] 1.9 Apply S18 to `isekai/README.md`.
  Verify: `grep -n 'Every .__init__.py. here holds' isekai/README.md` prints nothing.
- [x] 1.10 Apply S19 to `isekai/shared/vocabulary.py`'s module docstring.
  Verify: `grep -n -i -e 'cascade' -e 'curated' -e 'four-pass' -e 'still ships' isekai/shared/vocabulary.py` prints nothing.
- [x] 1.11 Apply S20 to `isekai/shared/image.py`, S21 to `isekai/pipeline/generate.py`, S22 to `isekai/interface/run_view.py`, S23 to `isekai/pipeline/review.py`.
  Verify: `grep -n -e 'carries no imaging' -e 'The four below' -e 'before a review UI exists' -e 'would move 26' isekai/shared/image.py isekai/pipeline/generate.py isekai/interface/run_view.py isekai/pipeline/review.py` prints nothing.
- [x] 1.12 Apply S24–S27 to `isekai/interface/cli.py`.
  Verify: `grep -n -e 'prose in, a sheet' -e 'sort a caption' -e 'photograph -> prose' -e 'anything downstream reads' -e 'descriptive prose' isekai/interface/cli.py` prints nothing.
- [x] 1.13 Apply S28, S29 and S30 to the `## Purpose` preambles of `comfy-transport`, `model-provisioning` and `sheet` under `openspec/specs/`.
  Verify: `grep -n -e 'stdlib-only' -e 'turning descriptive prose' openspec/specs/comfy-transport/spec.md openspec/specs/model-provisioning/spec.md openspec/specs/sheet/spec.md` prints nothing.
- [x] 1.14 Leave every requirement body to the delta, per [D2](design.md#d2).
  Verify: `git diff --name-only main -- openspec/specs/` prints `openspec/specs/comfy-transport/spec.md`, `openspec/specs/model-provisioning/spec.md` and `openspec/specs/sheet/spec.md`, and nothing else.

## 2 — `docs/` written from the payload

- [x] 2.1 **HALT CHECK** — `docs/` holds only `docs/arc/`, and `docs/arc/` holds only `modules.md` and `data-flow.md`, which [D4](design.md#d4) moves.
  Verify: `find docs -type f | sort` prints `docs/arc/data-flow.md` and `docs/arc/modules.md`, and nothing else.
- [x] 2.2 `git mv` `docs/arc/modules.md` and `docs/arc/data-flow.md` into `docs/`, and remove `docs/arc/`, per [D4](design.md#d4).
  Verify: `test ! -e docs/arc && test -f docs/modules.md && test -f docs/data-flow.md && echo ok` prints `ok`.
- [x] 2.3 Apply S31–S34 to `docs/data-flow.md`.
  Verify: `grep -n -e 'verbs outside the stages' -e 'the order is the failure isolation' -e 'may simply not be' -e 'the only producer here' docs/data-flow.md` prints nothing.
- [x] 2.4 Apply S35, S36, S47, S49, S50 and S51 to `docs/modules.md`.
  Verify: `grep -n -e 'Move any of those imports' -e 'the only thing holding' -e 'would be a lie' -e 'and not a layer' -e 'single named module' -e 'reaches down into' -e 'allowed to know about' docs/modules.md` prints nothing.
- [x] 2.5 Add `## How the components interact` to `docs/modules.md`, stating the facts [D5](design.md#d5) lists.
  Verify: `grep -c -e '^## How the components interact' -e 'wiring' -e 'StageFailure' docs/modules.md` prints a number above `2`.
- [x] 2.6 Write `docs/principles.md` from `payload/principles.md` under the prose rules, meaning unchanged, each principle keeping its title ([D3](design.md#d3)).
  Verify: `diff <(grep '^### ' docs/principles.md) <(grep '^### ' openspec/changes/0026-architecture-in-the-repo/payload/principles.md)` prints nothing.
- [x] 2.7 Apply S48 to `isekai/README.md`, so it no longer contradicts `docs/principles.md`.
  Verify: `grep -n -e 'not a layering rule' -e 'as a stack would be' isekai/README.md` prints nothing.
- [x] 2.8 Write `docs/decisions.md` from `payload/decisions.md` the same way, each decision keeping its id and title.
  Verify: `diff <(grep '^### D' docs/decisions.md | grep -v -e '^### D29' -e '^### D30') <(grep '^### D' openspec/changes/0026-architecture-in-the-repo/payload/decisions.md)` prints nothing.
- [x] 2.9 Add docs D29 and docs D30 to `docs/decisions.md` under *The product*, after docs D0, with the text [D7](design.md#d7) gives.
  Verify: `grep -c -e '^### D29 · What .summon. preserves' -e '^### D30 · A public repository, for learning' docs/decisions.md` prints `2`.
- [x] 2.10 Write `docs/README.md` from `payload/overview.md` the same way.
  Verify: `grep -o -e '(principles.md)' -e '(decisions.md)' -e '(modules.md)' -e '(data-flow.md)' docs/README.md | sort -u` prints `(data-flow.md)`, `(decisions.md)`, `(modules.md)` and `(principles.md)`.
- [x] 2.11 Re-point every `docs/arc/` link: `CLAUDE.md`, `README.md:374`, `isekai/README.md:34`.
  Verify: `git grep -n 'docs/arc' -- ':!CHANGELOG.md' ':!openspec/changes/archive' ':!openspec/changes/0026-architecture-in-the-repo'` prints nothing.
- [x] 2.12 Every relative link in `docs/` resolves.
  Verify: `cd docs && grep -oh '](\([a-z-]*\.md\)' *.md | sed 's/^](//' | sort -u | while read p; do test -f "$p" || echo "broken $p"; done` prints nothing.
- [x] 2.13 `docs/` names neither the operator's notebook nor a host path.
  Verify: `grep -rn -i -e 'vault' -e 'notebook' -e '/Users/' -e 'architecture-v' docs/` prints nothing.
  ⚠ Already passes at `2ccda2f`: a guard, not proof of the work.

## 3 — `CLAUDE.md` keeps only process

- [x] 3.1 **HALT CHECK** — `CLAUDE.md`'s sections are the ones [D8](design.md#d8) sorts.
  Verify: `grep '^## ' CLAUDE.md` prints *The quality gate*, *Engineering conventions*, *How a change is cut here*, *Layout*, *Rules the render path is under* and *Guardrails*, in that order.
- [x] 3.2 Add the import `@docs/principles.md` on its own line, above the first `---`.
  Verify: `grep -n '^@docs/principles.md$' CLAUDE.md` prints one line.
- [x] 3.3 Move out every row [D8](design.md#d8) marks *moved out*, and replace *Rules the render path is under* with its pointer to `docs/principles.md` and `docs/decisions.md`.
  Verify: `grep -n -e '^## Rules the render path is under' -e 'Option-modified keybinding' -e 'A parameter is a seam only if' CLAUDE.md` prints nothing.
- [x] 3.4 Delete the selectable-implementation constraint (S42) and rewrite the identity constraint (S37).
  Verify: `grep -n -e 'A selectable implementation is a measured one' -e 'Identity preservation is the product' CLAUDE.md` prints nothing.
- [x] 3.5 Rewrite the runs-root line (S40) and the *"design.md … nowhere else"* line, per [D8](design.md#d8).
  Verify: `grep -n -e 'Everything a run reads or writes is inside the repository' -e 'and nowhere else' CLAUDE.md` prints nothing.
- [x] 3.6 Re-flow the flows paragraph (S39).
  Verify: `grep 'freeze' CLAUDE.md | while IFS= read -r l; do [ "$(printf '%s' "$l" | wc -m)" -gt 105 ] && printf '%s\n' "$l"; done` prints nothing.
- [x] 3.7 Replace the `(major × 100) + minor` id rule with *the next free number*, per [D8](design.md#d8).
  Verify: `grep -n 'major × 100' CLAUDE.md` prints nothing.
- [x] 3.8 Add what a patch may hold, per [D8](design.md#d8).
  Verify: `grep -n 'MANIFEST_VERSION' CLAUDE.md | grep 'SCHEMA_VERSION'` prints one line.
- [x] 3.9 Add the notebook rows [D8](design.md#d8) marks *added*.
  Verify: `grep -c -i -e 'synthetic portrait' -e 'no pointer to the operator' CLAUDE.md` prints `2`.

## 4 — The group READMEs point at `docs/`

- [ ] 4.1 Replace the closing line of `isekai/README.md` and each group's `README.md` — `boundary`, `evaluation`, `foundation`, `interface`, `pipeline`, `shared` — per [D9](design.md#d9).
  Verify: `grep -rn "design record's" isekai/` prints nothing.
- [ ] 4.2 Each of those READMEs links `docs/principles.md` and `docs/decisions.md`.
  Verify: `grep -L -e 'docs/principles.md' isekai/README.md isekai/*/README.md; grep -L -e 'docs/decisions.md' isekai/README.md isekai/*/README.md` prints nothing.
- [ ] 4.3 Every `docs/` link in those READMEs resolves.
  Verify: `for f in isekai/README.md isekai/*/README.md; do d=$(dirname "$f"); grep -o '([./]*docs/[a-z-]*\.md' "$f" | tr -d '(' | while read p; do test -f "$d/$p" || echo "broken $f $p"; done; done` prints nothing.
  ⚠ Already passes at `2ccda2f`: a guard, not proof of the work.

## 5 — `README.md` stops restating the architecture

- [ ] 5.1 **HALT CHECK** — the section [D10](design.md#d10) removes is still there.
  Verify: `grep -n '^## The path' README.md` prints one line.
- [ ] 5.2 Apply S43–S46 to `README.md`.
  Verify: `grep -n -e 'sorts the prose' -e 'silently absent when Ollama' -e 'Neither tag list is narrowed —' -e 'change all four' README.md` prints nothing.
- [ ] 5.3 Replace `## The path` with `## Architecture`, per [D10](design.md#d10).
  Verify: `grep -n -e '^## The path' -e 'short side at 1024' -e 'hires_denoise. 0.35' README.md` prints nothing, and `grep -n '^## Architecture' README.md` prints one line.
- [ ] 5.4 Point *How it works* at `docs/`, and name the import rule by docs D20, per [D10](design.md#d10).
  Verify: `grep -n -e 'one path (see below)' -e 'imports no third-party package at module scope' README.md` prints nothing.
- [ ] 5.5 Name `docs/` in *Development*'s closing line.
  Verify: `sed -n '/^## Development/,/^## Repository layout/p' README.md | grep -c 'docs/'` prints a number above `0`.
- [ ] 5.6 Every `docs/` link in `README.md` resolves.
  Verify: `grep -o '(docs/[a-z-]*\.md' README.md | tr -d '(' | sort -u | while read p; do test -f "$p" || echo "broken $p"; done` prints nothing.
  ⚠ Already passes at `2ccda2f`: a guard, not proof of the work.
