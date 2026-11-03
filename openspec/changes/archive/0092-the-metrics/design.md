# Design — 0092 the metrics

A script per measure, a catalogue naming them, the docs naming both. **Verdict: feasible.**

## Context

MinionsFactory's collector, `skills/mf-build/scripts/metrics.py`, reads a target's `metrics/catalogue.toml` and runs
each metric as `uv run --script <path> <args>` from the repository's root, no shell, 300 s, with `MF_METRICS_CHANGE`,
`MF_METRICS_BASE` and `MF_METRICS_HEAD` set. A metric's value is its last stdout line, a number; any other outcome is
recorded `unavailable` with the first stderr line, never a halt. MF ships no scripts to a target.

## Goals / Non-Goals

**Goals:** every metric of [D3](#d3) collected on the build's tree and the release's; each script held by a test.

**Non-Goals:** a metric no command can produce; a `watch` set before there is history.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | Scripts live in `scripts/metrics/`, each a PEP 723 file (`requires-python = ">=3.12"`, `dependencies = []`), stdlib alone, its logic in functions a test imports and a `main()` that prints one number or exits 1 with its reason on stderr. They cite no change id and never name the changelog file | MF's layout, outside `tools/`'s guards; `tests/test_changelog.py` and the no-history check read these files | `tools/metrics/`; copies citing MF's changes |
| <a id="d2"></a>**D2** | The scripts, written for isekai on MF's model: **`tests_collected.py`** runs `uv run --frozen pytest --collect-only -q` with its args and prints the selected count, the `N` of `N/M tests collected`; **`backlog.py`** counts `^- \*\*\S+·` lines in the primary's `.minions/backlog.md`, found through `git rev-parse --path-format=absolute --git-common-dir`; **`conformance.py`** `trailer` (commits in base..head whose `Change` trailer is not the change id), `minions` (`git ls-files .minions` lines), `amends` (subjects `docs(<change-id>): amend the change directory` in base..head); **`references.py`** (a relative link to a missing file or anchor, and a `D<n>` with no `### D<n> ·` heading, across `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `THREAT_MODEL.md` and `docs/*.md`); **`reading_set.py`** (the words of `AGENTS.md`, `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, `THREAT_MODEL.md`, `docs/principles.md` and `docs/decisions.md`); **`counts.py`** `pinned` (`PINNED`'s keys in `tests/test_flow.py`), `scenarios` (`^#### Scenario:` across `openspec/specs/*/spec.md`), `decisions` (`^### D\d+ ·` in `docs/decisions.md`) | the operator's Q2: MF's measures, isekai's tree; MF's own count the pre-deselect total and misses `op·` cards | reading MF's repository from a build |
| <a id="d3"></a>**D3** | `metrics/catalogue.toml` holds, by group: **proof** `tests-unit` (`tests_collected.py` with the gate's pytest arguments: `--ignore=tests/e2e` and a `--deselect=` for each `LOOPBACK` test in the `Makefile`), `tests-browser` (`tests_collected.py` with `make e2e`'s: `tests/e2e` and the `LOOPBACK` test ids), `gate-seconds` (station); **debt** `open-backlog-cards`, `watch = 10`; **conformance** `commits-without-trailer`, `minions-files-tracked`, `amends`, `broken-references`; **size** `diff-lines`, `diff-files`, `phases` (station), `shared-reading-set`, `pinned-flows`, `living-scenarios`, `decisions`. Each has its `title`, `unit` and `better` | the next version moves tests between the gate and the browser run; ten is the paydown line | a `watch` on every metric |
| <a id="d4"></a>**D4** | `AGENTS.md`'s *Layout* names `metrics/` and `scripts/metrics/`; `CONTRIBUTING.md`'s *The evidence a change carries* says the build drafts the values and the release commits them; `docs/decisions.md` gains `### D47 · A change is measured from isekai's own catalogue` | the decisions in force say what holds | |

## Tests

| layer | adds | removes |
|---|---|---|
| unit | `tests/test_metric_scripts.py`: each script's counting function on a fixture tree in `tmp_path`, and each `main()`'s refusal, `spec_exempt` as structural | none |
| end-to-end | none | none |

The gate's pytest passes 1441 tests in a set-up worktree at `5cc0174` (`make gate`'s summary line). This change deletes and merges no test.

## Dependencies

None.

## Risks / Trade-offs

- **`tests_collected.py` needs a synced environment** → a run's worktree has one from `make setup`; `--frozen` keeps
  `uv` from rewriting the lock.
- **`backlog.py` reads an untracked file** → its value cannot be re-derived from git, as MF's cannot.
- **A script that fails records `unavailable`** → the page shows it; nothing halts.

## Verdict

**feasible.** Every file named exists at `5cc0174` or is new, and nothing behaves differently.
