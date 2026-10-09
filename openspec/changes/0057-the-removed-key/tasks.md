# Tasks — 0057 the removed key

The key set a `spec` marker may name, and its twin, per [design](design.md).

## Progress

- [x] 1 — The checker

## 1 — The checker

- [x] 1.1 **HALT CHECK** — the checker reads the effective keys alone, and no `nameable` exists.
  Verify: `grep -c 'def nameable' tests/test_spec_bindings.py` prints `0`, and `grep -c 'return spec_keys(REPO_ROOT)' tests/test_spec_bindings.py` prints `1`.
- [x] 1.2 In `tests/test_spec_bindings.py`, add `nameable`, return it from the `keys` fixture, and reword the module docstring, per [D1](design.md#d1).
  Verify: `grep -c 'return nameable(REPO_ROOT)' tests/test_spec_bindings.py` prints `1`.
- [x] 1.3 In `tests/test_spec_bindings.py`, add `test_a_marker_on_a_removed_key_is_not_stray`, per [D2](design.md#d2).
  Verify: `uv run pytest -q tests/test_spec_bindings.py -k removed_key_is_not_stray` prints a line holding `1 passed`.
