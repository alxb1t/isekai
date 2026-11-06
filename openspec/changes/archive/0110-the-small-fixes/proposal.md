---
bump: patch
version: 0.73.1
---

# 0110 — the small fixes

The Review tab's count meets AA on Latte, and the backlog measure reads MF's debt file again. No format, verb or
product moves.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision and the test cost |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | none: `skip_specs`, per [D3](design.md#d3) |

```
1 the count    .appbar__count on --accent-ink · the design spec's word · the PAIRS row on --ground-deep
2 the metric   backlog.py reads .minions/debt.md · its test · the catalogue's title
```

## Why

**The Review tab's count is the only `--accent` drawn as text**, and on Latte's `--ground-deep` it reads 4.45:1, under
AA. **The `open-backlog-cards` measure reads `.minions/backlog.md`**, which MF no longer writes: `0107`, `0108` and
`0109` record it unavailable. MF keeps the cards in `.minions/debt.md`.

## What Changes

- **`.appbar__count`** reads `--accent-ink`, as the bar's *Render* link does. The UI design spec's AppBar line says
  `accent-ink`. `themes.test.ts`'s `--accent-ink` row also holds it on `--ground-deep` ([D1](design.md#d1)).
- **`scripts/metrics/backlog.py`** counts the cards in the primary's `.minions/debt.md`; its docstrings and error say
  *debt*. Its path test follows. The catalogue's title becomes *Open debt cards*; the id stays ([D2](design.md#d2)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Each fix meets a requirement or decision as it stands, per [D3](design.md#d3):

- `ui` — *The app offers five themes, and the choice is kept*: "`accent-ink` … 4.5:1 … on the grounds they are drawn
  on" already covers the count on `--ground-deep`; the code now meets it.
- The backlog measure is [D47](../../../docs/decisions.md#d47--a-change-is-measured-from-isekais-own-catalogue)'s; no
  requirement specifies it. The script reads the file MF keeps.

## Impact

- `ui/src/app.css`, `ui/src/themes.test.ts`, `ui/design/spec.md`.
- `scripts/metrics/backlog.py`, `tests/test_metric_scripts.py`, `metrics/catalogue.toml`.

## Not in this change

- Latte's `--accent` itself: it is a fill token, and darkening it would make it equal `--accent-ink`
  ([D48](../../../docs/decisions.md#d48--a-theme-is-a-token-set-chosen-in-the-browser) rules out a Latte-only rule).
- The measure's id `open-backlog-cards`, the script's file name and `backlog_path`: one series, one name.
- The past records under `metrics/changes/`: records are history, never rewritten.
