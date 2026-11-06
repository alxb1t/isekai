# Tasks — 0110 the small fixes

The count first, then the measure, per [design](design.md). No spec delta, per [D3](design.md#d3).

## Progress

- [ ] 1 — The count
- [ ] 2 — The metric

## 1 — The count

- [ ] 1.1 In `ui/src/themes.test.ts`'s `PAIRS`, `[['--accent-ink'], ['--ground', '--raised', '--raised-2'], 4.5],` →
  `[['--accent-ink'], ['--ground', '--raised', '--raised-2', '--ground-deep'], 4.5],`, per [D1](design.md#d1).
  Verify: `grep -n -F "'--raised-2', '--ground-deep'], 4.5]," ui/src/themes.test.ts` prints a line.
- [ ] 1.2 In `ui/src/app.css`'s `.appbar__count`, `color: var(--accent);` → `color: var(--accent-ink);`, per
  [D1](design.md#d1).
  Verify: `grep -n -x -F '  color: var(--accent);' ui/src/app.css` prints nothing.
- [ ] 1.3 In `ui/design/spec.md`'s AppBar line, "unapproved sheets in mono 11 `accent`" → "unapproved sheets in mono 11
  `accent-ink`", per [D1](design.md#d1).
  Verify: `grep -n 'unapproved sheets in mono 11 .accent-ink.' ui/design/spec.md` prints a line.

## 2 — The metric

- [ ] 2.1 In `tests/test_metric_scripts.py`'s `test_the_backlog_is_in_the_primary_checkouts_minions`,
  `/ ".minions" / "backlog.md"` → `/ ".minions" / "debt.md"`, per [D2](design.md#d2).
  Verify: `grep -n -F '/ ".minions" / "debt.md"' tests/test_metric_scripts.py` prints a line.
- [ ] 2.2 In `scripts/metrics/backlog.py`, per [D2](design.md#d2): `"backlog.md"` → `"debt.md"`; "the primary checkout's
  backlog holds" → "the primary checkout's debt file holds"; "cards in a backlog" → "cards in a debt file"; "Return the
  backlog file" → "Return the debt file"; `backlog unreadable:` → `debt unreadable:`.
  Verify: `uv run pytest tests/test_metric_scripts.py` exits 0.
- [ ] 2.3 **HALT CHECK** The script reads the primary's `.minions/debt.md`, the premise of [D2](design.md#d2).
  Verify: `uv run --script scripts/metrics/backlog.py` exits 0 and prints a number.
- [ ] 2.4 In `metrics/catalogue.toml`, `title = "Open backlog cards"` → `title = "Open debt cards"`, per
  [D2](design.md#d2).
  Verify: `grep -n -F 'title = "Open debt cards"' metrics/catalogue.toml` prints a line.
