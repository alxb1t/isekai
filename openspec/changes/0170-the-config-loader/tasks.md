# The config loader — tasks

Hold each loader's whole refusal messages, add `read_keyed`, then switch the loaders to it. See [design](design.md).

## Progress

- [x] 1 — The pins · moderate
- [ ] 2 — The helper · moderate
- [ ] 3 — The switch · moderate

## 1 — The pins

- [x] 1.1 **HALT CHECK** In `tests/test_caption.py`, after `test_a_config_carrying_an_unknown_key_is_refused`, add `test_a_config_with_unknown_keys_is_refused_in_full` and `test_a_config_with_missing_keys_is_refused_in_full`, per [D3](design.md#d3). The first writes `briefing`, `model`, `zeta` and `alpha` through `_config`; the second writes `{}`. Each compares `str(excinfo.value)` to the whole message of `caption.json` that [D3](design.md#d3) gives. The first binds `caption:selection:an-unknown-key-is-refused` alone; the second binds `caption:selection:an-absent-or-empty-model-is-refused` alone.
  Verify: `uv run pytest tests/test_caption.py::test_a_config_with_unknown_keys_is_refused_in_full tests/test_caption.py::test_a_config_with_missing_keys_is_refused_in_full` exits 0.
- [x] 1.2 **HALT CHECK** In `tests/test_ink.py`, after `test_ink_extract_refuses_a_key_the_config_lacks`, add `test_ink_config_with_unknown_keys_is_refused_in_full` and `test_ink_config_with_missing_keys_is_refused_in_full`, per [D3](design.md#d3). The first calls `_config(tmp_path, zeta=1, alpha=1)`; the second calls `_config(tmp_path, floor=None, reach=None)`. Each compares `str(excinfo.value)` to the whole message of `ink.json` that [D3](design.md#d3) gives, and carries `spec_exempt("structural: a config's whole refusal")`.
  Verify: `uv run pytest tests/test_ink.py::test_ink_config_with_unknown_keys_is_refused_in_full tests/test_ink.py::test_ink_config_with_missing_keys_is_refused_in_full` exits 0.
- [x] 1.3 **HALT CHECK** In `tests/test_tattoo_library.py`, after `test_tattoo_config_refuses_a_wrong_key_naming_it`, add `test_tattoo_config_with_unknown_keys_is_refused_in_full` and `test_tattoo_config_with_missing_keys_is_refused_in_full`, per [D3](design.md#d3). The first writes `_declared(zeta=1, alpha=1)` to `tmp_path / "tattoo.json"`; the second writes a dict comprehension over `_declared()` that leaves out `outline_min` and `floor_stage1`. Each compares `str(excinfo.value)` to the whole message of `tattoo.json` that [D3](design.md#d3) gives, and carries `spec_exempt("structural: a config's whole refusal")`.
  Verify: `uv run pytest tests/test_tattoo_library.py::test_tattoo_config_with_unknown_keys_is_refused_in_full tests/test_tattoo_library.py::test_tattoo_config_with_missing_keys_is_refused_in_full` exits 0.
- [x] 1.4 Run `tools.mutate` over the block of `load_caption_config`, `isekai/foundation/caption_config.py` lines 34-45, with `tests/test_caption.py`. A survivor gets one more case in that file, and the run is repeated.
  Verify: `uv run python -m tools.mutate isekai/foundation/caption_config.py:34-45 --tests tests/test_caption.py` exits 0.
- [x] 1.5 Run `tools.mutate` over the block of `load_ink_config`, `isekai/shared/ink.py` lines 76-87, with `tests/test_ink.py`. A survivor gets one more case in that file, and the run is repeated.
  Verify: `uv run python -m tools.mutate isekai/shared/ink.py:76-87 --tests tests/test_ink.py` exits 0.
- [x] 1.6 Run `tools.mutate` over the block of `load_tattoo_config`, `isekai/pipeline/tattoos.py` lines 168-179, with `tests/test_tattoo_library.py`. A survivor gets one more case in that file, and the run is repeated.
  Verify: `uv run python -m tools.mutate isekai/pipeline/tattoos.py:168-179 --tests tests/test_tattoo_library.py` exits 0.

## 2 — The helper

- [ ] 2.1 Write `tests/test_config.py` with a module docstring, and `test_read_keyed_returns_the_document_it_read` carrying `spec_exempt("structural: the block the config loaders share")`. It writes `{"b": 2, "a": 1}` to `tmp_path / "x.json"`, calls `read_keyed(path, ("a", "b"))` and asserts the result equals `{"a": 1, "b": 2}`. It patches nothing ([D4](design.md#d4)).
  Verify: `grep -c '^def test_' tests/test_config.py` prints `1`.
- [ ] 2.2 Write `isekai/foundation/config.py` per [D1](design.md#d1): a module docstring, `read_keyed(path: Path, keys: Sequence[str]) -> Any`, the block of `load_caption_config` reading its key tuple from the `keys` parameter, and `return document`. It imports `json`, `Sequence`, `Path`, `Any` and `Refusal` only.
  Verify: `uv run pytest tests/test_config.py` exits 0.
- [ ] 2.3 In `isekai/foundation/README.md`, add a `config.py` row after the `caption_config.py` row of `## Files`: reads a JSON config by the keys a build reads, refusing a key it does not read and a key it lacks. Add `` | `config.py` | — | — | `` after the `caption_config.py` row of `## Imported by` ([D5](design.md#d5)).
  Verify: `grep -c '^| .config.py. |' isekai/foundation/README.md` prints `2`.
- [ ] 2.4 Run `uv run python -m tools.derive_imported_by`, which re-derives the `refusal.py` row to name `config.py`.
  Verify: `uv run pytest tests/test_docs.py` exits 0.

## 3 — The switch

- [ ] 3.1 In `isekai/foundation/caption_config.py`, replace the block of `load_caption_config` with `document = read_keyed(path, KEYS)`, add `from isekai.foundation.config import read_keyed` before the `refusal` import, and delete `import json` and `from typing import Any` ([D2](design.md#d2)).
  Verify: `git grep -n -E "^import json|json\.loads|import Any" -- isekai/foundation/caption_config.py` prints nothing.
- [ ] 3.2 In `isekai/shared/ink.py`, replace the block of `load_ink_config` with `document = read_keyed(path, KEYS)`, add `from isekai.foundation.config import read_keyed` between the `atomic_write` and `refusal` imports, and delete `import json`; `Any` goes from the `typing` import and `TYPE_CHECKING` stays.
  Verify: `git grep -n -E "^import json|json\.loads|, Any" -- isekai/shared/ink.py` prints nothing.
- [ ] 3.3 In `isekai/pipeline/tattoos.py`, replace the block of `load_tattoo_config` with `document = read_keyed(path, KEYS)` and add `from isekai.foundation.config import read_keyed` between its `atomic_write` and `refusal` imports. `json` and `Any` stay: other functions read them.
  Verify: `grep -c 'read_keyed' isekai/pipeline/tattoos.py` prints `2`.
- [ ] 3.4 In `isekai/shared/README.md`, the sentence naming what `ink.py` imports reads `ink.py` imports `atomic_write`, `config` and `refusal` ([D5](design.md#d5)).
  Verify: `grep -c 'ink.py. imports .atomic_write., .config. and .refusal.' isekai/shared/README.md` prints `1`.
- [ ] 3.5 Run `uv run python -m tools.derive_imported_by`, which fills the `config.py` row with its importers: `caption_config.py`, `pipeline/tattoos.py` and `shared/ink.py`.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [ ] 3.6 Run `tools.mutate` over the lines of `read_keyed`, which the range `1-80` of `isekai/foundation/config.py` holds whole, with the helper's and the loaders' test files. A survivor gets one more case in the loader's test file that reaches it, and the run is repeated.
  Verify: `uv run python -m tools.mutate isekai/foundation/config.py:1-80 --tests tests/test_config.py tests/test_caption.py tests/test_ink.py tests/test_tattoo_library.py` exits 0.
