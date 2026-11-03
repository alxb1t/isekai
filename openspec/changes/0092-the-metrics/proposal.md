---
bump: patch
---

# 0092 — the metrics

isekai measures each change as MinionsFactory does: a catalogue of metrics the build and the release collect, each a
small script, the values committed with the release. No behaviour moves.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the catalogue and each script |
| [tasks](tasks.md) | the phases, in build order |

```
1 the scripts    scripts/metrics/: tests, cards, conformance, references, reading set, counts; their tests
2 the catalogue  metrics/catalogue.toml; AGENTS.md's Layout; CONTRIBUTING.md's evidence; D47
```

## Why

**The gate says whether isekai works, not where it is heading.** The releases record `metrics: none — no catalogue`.
The next version moves tests between the gate and the browser run, and its effect should be read as numbers, not
recalled.

## What Changes

- **`scripts/metrics/`** holds a script per measure, stdlib alone ([D1](design.md#d1), [D2](design.md#d2)).
- **`metrics/catalogue.toml`** names them; the build drafts the values, the release commits them to
  `metrics/changes/<change-id>.json` ([D3](design.md#d3)).
- **The docs** say where they live, and D47 records the catalogue ([D4](design.md#d4)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None: tooling and docs. `skip_specs: true`.

## Impact

- New: `scripts/metrics/`, `metrics/catalogue.toml`, `tests/test_metric_scripts.py`.
- `AGENTS.md`, `CONTRIBUTING.md`, `docs/decisions.md`.

## Not in this change

- Metrics that read MinionsFactory's skills: they measure MF, not isekai.
- A `watch` beyond the open cards': there is no history to set one from yet.
- The review-metrics page: its config is the operator's, outside the repo.
