---
version: v0.37
---

# 0061 — ui groundwork

`isekai ui` stops being one flow's review page and becomes the app's shell over a **library**: no arguments, a Home
listing `~/isekai/`, a hub per batch, and the review surface inside it. A browser test harness proves it, reaching no
GPU and no Ollama.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the library, the routes, the test seam, the defects, the tests |
| [design-spec](design-spec.md) | the app's screens, tokens and journeys — the UI arc's design, of which this change builds the shell |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` · `cli` · `agent-skills` |

```
isekai ui ──▶ /                      Home: every batch in the library, by last activity
               └▶ /b/<batch>/hub      sources × flows, each cell's stage; ↵ opens Review
                    └▶ /b/<batch>/review/<run>/<flow>   the review surface; Approve → the next sheet
```

## Why

**The review surface serves one flow over run ids typed at the command line.** `summon` and `conjure` are separate servers, and
nothing on screen leads from one batch to the next. The app the design describes — import, assign, prepare, review,
render, revise — needs one server, one shell and the batch in the URL first.

**Nothing tests the browser.** The gate type-checks `ui/` and tests the server; the defects carried from the
backlog live in the page and the bundle's build, where no test reaches. A rewrite of the page needs a harness that
records what it does today.

**`run-flows` cannot follow.** Its review step starts two per-flow servers over `.data/`; once the UI is the tool,
the skill and `compare-renders` have no work left.

## What Changes

- **BREAKING — `isekai ui` takes no arguments** and serves the library at `ISEKAI_LIBRARY`, default `~/isekai`,
  on 8517 ([D1](design.md#d1)). `--flow`, the run ids and `--runs` leave the verb.
- **A batch is a library folder holding `sources/`**, with `runs/` and `log.txt` beside it ([D2](design.md#d2)).
- **A shell with routes**: Home, the hub and Review, the batch and the run's digest in every URL, on `vue-router`
  ([D3](design.md#d3)).
- **The hub, read-only**: each source × tracked flow's stage from a listing of `runs/`; ↵ opens Review
  ([D4](design.md#d4)).
- **Review inside the shell**: a queue of unapproved sheets; opening a sheet with no draft writes one through
  `review` ([D5](design.md#d5)).
- **A test harness**: vitest for the composables, Playwright from pytest for the app, both in the gate and CI;
  `ISEKAI_WIRING=<module:factory>` swaps in the doubles ([D6](design.md#d6), [D7](design.md#d7)).
- **The carried defects fixed**: 0018·R5, 0018·R8, 0018·R12, 0023·R5, 0023·S1, 0032·R1 ([D8](design.md#d8)).
- **BREAKING — `run-flows` and `compare-renders` deleted**, with the `agent-skills` capability
  ([D9](design.md#d9)).
- **The design spec** enters as `ui/design/spec.md`; the old `ui/design/` is deleted ([D10](design.md#d10)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - REMOVED *The review surface is started by a verb and refuses before it serves* — the library replaces the
    invocation, and refusals move onto the page.
  - REMOVED *The batch is the invocation's arguments and lives only in memory* — a batch is a folder.
  - ADDED *The surface serves one library, from a verb that takes no arguments*.
  - ADDED *A folder in the library is a batch when it holds `sources/`*.
  - ADDED *Every screen has a URL naming its batch and its run*.
  - ADDED *The hub shows each source's stage in each tracked flow, read from the run directory*.
  - ADDED *Review is a queue of unapproved sheets, and opening one writes its draft*.
  - ADDED *The page's save state is true to the requests in flight, and a pending edit is sent on leaving*.
  - MODIFIED *The surface answers only requests addressed to the address it bound* — a request without `Origin` is
    answered only when `Sec-Fetch-Site` says it came from the page.
  - MODIFIED *A missing caption is shown with the command that writes it* — the command names the runs root.
- `cli`:
  - REMOVED *Every stage verb requires the flows it acts on, and takes more than one*, and
  - ADDED *A stage verb requires the flows it acts on, and takes more than one* — the same rule and keys, without
    the serving verb's exactly-one clause and its scenario.
- `agent-skills`:
  - REMOVED *Every command a skill names is one this build accepts* — no skill is left.

## Impact

- **Code:** `isekai/interface/ui/` (`__init__.py`, `batch.py` → a library module, `app.py`, `bundle.py`),
  `isekai/interface/cli.py` (the `ui` parser and `_OneFlow`), `isekai/interface/wiring.py` (the seam), `ui/src/`.
- **Dependencies:** `vue-router`, `vitest`, `pytest-playwright` ([Dependencies](design.md#dependencies)); Chromium
  through `make browsers`.
- **Gate and CI:** `make gate` gains `tools.test_ui`; CI runs `make browsers` first.
- **Docs:** `README.md`, `CLAUDE.md`, `docs/decisions.md` (D4, D18, D19, D24 and new D40, D41), `docs/data-flow.md`,
  `docs/modules.md`, `isekai/interface/ui/README.md`.
- **Deleted:** `.claude/skills/run-flows/`, `.claude/skills/compare-renders/`, `tests/test_agent_skills.py`,
  `ui/design/`.

## Not in this change

- **Ticking flows, `isekai assign`, New batch, import, conversion and Prepare** — run flow's.
- **`/events` over SSE and `--progress json`** — they arrive with the first job.
- **Render, the Renders view, editing ④ Renders, billing alerts** — render's.
- **Revise and compare** — revise's.
- **A newer sheet after approval** (op·review-newer-sheet) — run flow's, where Prepare writes sheets.
- **Moving a `.data/` batch into the library** — by hand, by the operator.
- **Building the bundle at packaging time** — the bundle stays built on demand.
