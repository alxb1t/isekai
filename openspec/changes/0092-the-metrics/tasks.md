# Tasks — 0092 the metrics

The scripts, then the catalogue and the docs, per [design](design.md).

## Progress

- [x] 1 — The scripts
- [ ] 2 — The catalogue

## 1 — The scripts

- [x] 1.1 Write `scripts/metrics/tests_collected.py` and `scripts/metrics/backlog.py` per [D1](design.md#d1) and
  [D2](design.md#d2).
  Verify: `uv run --script scripts/metrics/tests_collected.py tests/e2e` prints a whole number above 0, and `uv run --script scripts/metrics/backlog.py` prints a whole number.
- [x] 1.2 Write `scripts/metrics/conformance.py`, `scripts/metrics/references.py`, `scripts/metrics/reading_set.py` and
  `scripts/metrics/counts.py` per [D2](design.md#d2).
  Verify: `uv run --script scripts/metrics/counts.py pinned` prints `6`, and `uv run --script scripts/metrics/references.py` prints a whole number.
- [x] 1.3 Add `tests/test_metric_scripts.py`, importing each script's counting function from its file, per
  [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_metric_scripts.py` exits 0.

## 2 — The catalogue

- [ ] 2.1 Write `metrics/catalogue.toml` per [D3](design.md#d3).
  Verify: `grep -c '^\[\[metric\]\]' metrics/catalogue.toml` prints `15`, and `grep -c 'watch = 10' metrics/catalogue.toml` prints `1`.
- [ ] 2.2 Name `metrics/` and `scripts/metrics/` in `AGENTS.md`'s *Layout*, the measuring in `CONTRIBUTING.md`'s
  *The evidence a change carries*, and add D47 to `docs/decisions.md`, per [D4](design.md#d4).
  Verify: `grep -c '^### D47 ' docs/decisions.md` prints `1`, and `grep -c 'scripts/metrics' AGENTS.md` prints a count above 0.
