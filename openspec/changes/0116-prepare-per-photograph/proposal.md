---
bump: minor
---

# 0116 — Prepare per photograph

Prepare takes each photograph end to end — tag, caption, then its sheets — before it starts the next, through a new
`prepare` verb run as one child. A photograph's cells reach *sheet* · "↵ review" as soon as that photograph is ready.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision and the test cost |
| [tasks](tasks.md) | the phases, in build order |
| `specs/cli/spec.md` | the `prepare` verb |
| `specs/ui/spec.md` | the Prepare requirement |

```
1 the verb    cli.py: prepare <run-id>/<flow>… · each photograph tag → caption → its sheets · its tests
2 the job     jobs.py: one prepare child · the plan stays the totals · its tests · the e2e comment
3 the prose   decisions D1 and D4 · README · data-flow · modules · the interface README
```

## Why

**On a big batch the first sheet waits for every photograph.** Prepare runs one `tag` child over every photograph,
then one `caption` child over every photograph, then one `sheet` child per flow. A caption is one local Ollama call
per photograph, so the first cell turns *sheet* only after the whole batch is read. Nothing forces that order: no lock,
no batch call, and no decision chose it for throughput. The operator wants to start review on the first photograph
while the rest prepare.

## What Changes

- **A new verb, `prepare`**, takes cells `<run-id>/<flow>`. It takes each photograph in turn through `tag` (when one of
  its flows declares the tagger), `caption`, then the sheet of each of its cells, and prints the lines those verbs
  print under `--progress json` ([D1](design.md#d1), [D2](design.md#d2)).
- **The local tagger loads once per invocation**, whatever the number of photographs ([D2](design.md#d2)).
- **A cell unticked while the job runs refuses its sheet**, naming `assign`, writes nothing and counts in no stage
  ([D3](design.md#d3)).
- **A refusal costs only its own step**: a caption that refuses leaves the photograph's sheets to run
  ([D4](design.md#d4)).
- **Prepare runs one `prepare` child for the whole job.** The plan still gives the bar's three totals, and the SSE
  events and `REACHED` are unchanged ([D5](design.md#d5)).
- **D4 and D1 in `docs/decisions.md`** say Prepare is `prepare`, and that it runs the photograph's verbs in turn
  ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli` — ADDED *The prepare verb takes each photograph through tagging, reading and its cells' sheets in turn*: the
  verb, its cells, its order, its one tagger, its refusals.
- `ui` — *Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer*: one
  `prepare` invocation over the cells, each photograph in turn; an unticked cell counts in no stage; *a photograph is
  described once* now reads the one invocation; a scenario is added, *each photograph in turn*.

## Impact

- `isekai/interface/cli.py`, `isekai/interface/ui/jobs.py`.
- `tests/test_pipeline_cli.py`, `tests/test_ui_jobs.py`, `tests/test_ui.py`, `tests/e2e/test_prepare.py` (a comment).
- `docs/decisions.md`, `README.md`, `docs/data-flow.md`, `docs/modules.md`, `isekai/interface/README.md`,
  `isekai/interface/ui/README.md`.
- No dependency, no new file kind, no page change: `ui/` is untouched.

## Not in this change

- **Parallel photographs.** One local Ollama model serves the captions, so photographs go one after another (brief
  Q3).
- **A live refresh on Review.** A sheet opened before its caption lands shows the `caption` command until a reload
  (brief Q2).
- **A gate on Review or approval while Prepare runs.** No route checks the Prepare slot, and none will (brief Q5).
- **The three verbs.** `tag`, `caption` and `sheet` keep their behaviour; the hand path still runs them one at a time.
