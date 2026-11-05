# Tasks — 0097 the gpunit upgrade

The pin, the lines, then the reason, per [design](design.md). Each new test carries the `spec` key or the `spec_exempt`
reason its task names.

## Progress

- [x] 1 — The pin
- [x] 2 — The lines
- [ ] 3 — The reason

## 1 — The pin

- [x] 1.1 **HALT CHECK** The `Dockerfile` still adds `v0.7.0`'s `boot.sh`, which [D2](design.md#d2) leaves in place.
  Verify: `grep -c 'gpunit/v0.7.0/boot/boot.sh' Dockerfile` prints `1`.
- [x] 1.2 Move `pyproject.toml:50`'s pin to `v0.12.0` per [D1](design.md#d1), then run `uv lock`.
  Verify: `grep -n 'rev=v0.7.0' uv.lock` prints nothing, and `uv run python -c "import gpunit; print(gpunit.__version__)"` prints `0.12.0`.
- [x] 1.3 Untie the boot script's tag in `tests/test_infra.py` per [D2](design.md#d2): `gpunit_tag` goes, `BOOT_SOURCE`
  and `boot_script_faults` change, and both boot-script tests keep their names.
  Verify: `grep -n 'gpunit_tag' tests/test_infra.py` prints nothing, and `uv run pytest tests/test_infra.py -k boot` exits 0.
- [x] 1.4 Rewrite `docs/pins.md`'s boot-script row and its gpunit recipe per [D3](design.md#d3).
  Verify: `grep -n 'too old for its gpunit' docs/pins.md` prints nothing, and `uv run pytest tests/test_docs.py` exits 0.
- [x] 1.5 Name exits 4 and 5 in `Volume`'s docstring in `isekai/boundary/gpu.py` per [D3](design.md#d3).
  Verify: `grep -c '4 no card in stock, 5 no card fits' isekai/boundary/gpu.py` prints `1`.

## 2 — The lines

- [x] 2.1 `run_gpunit` in `isekai/boundary/gpu.py` hands each line to `say` through `subprocess.Popen` per
  [D4](design.md#d4). In the same edit, `test_a_gpunit_verb_runs_in_its_own_session` in `tests/test_ui_jobs.py` records
  `Popen` and starts the real one on `[sys.executable, "-c", "pass"]`, so no test reaches gpunit; its assertions stay.
  Verify: `grep -n 'done.stdout' isekai/boundary/gpu.py` prints nothing, and `uv run pytest tests/test_ui_jobs.py -k own_session` exits 0.
- [x] 2.2 Write `tests/test_gpu.py` with `test_run_gpunit_says_a_line_before_the_verb_exits`, as
  [Tests](design.md#tests) describes, carrying `spec_exempt("structural: gpunit's lines reach say as they come")`.
  Verify: `uv run pytest tests/test_gpu.py` exits 0.
- [x] 2.3 Add `tests/test_gpu.py`, after `tests/stages.py`, to the `gpu.py` row's outside list in `isekai/boundary/README.md`'s *Imported by*.
  Verify: `grep -c 'tests/stages.py., .tests/test_gpu.py' isekai/boundary/README.md` prints `1`.

## 3 — The reason

- [ ] 3.1 **HALT CHECK** gpunit's exits for no card in stock and no card that fits are 4 and 5, as
  [D6](design.md#d6) reads them.
  Verify: `uv run python -c "from gpunit.log import NO_CAPACITY, NO_FIT; print(NO_CAPACITY, NO_FIT)"` prints `4 5`.
- [ ] 3.2 Add `REFUSED`, `refused_line` and `GpunitExit` to `isekai/boundary/gpu.py`; `run_gpunit`, `Gpunit` and
  `Volume` return a `GpunitExit` per [D5](design.md#d5). Add `test_run_gpunit_returns_the_last_refused_line` to
  `tests/test_gpu.py`, bound to `ui:render-job:a-refusal-names-its-kind-and-reason`.
  Verify: `uv run pytest tests/test_gpu.py -k refused` exits 0.
- [ ] 3.3 `isekai/boundary/README.md`'s `gpu.py` row names `run_gpunit` and `GpunitExit` per [D5](design.md#d5).
  Verify: `grep -c 'and its .GpunitExit., the exit' isekai/boundary/README.md` prints `1`.
- [ ] 3.4 Each gpunit double returns a `GpunitExit` per [D5](design.md#d5): `tests/stages.py`'s `_no_gpunit`,
  `tests/e2e/wiring.py`'s `_gpunit`, `tests/test_ui_billing.py`'s `_volume`, `tests/test_ui.py`'s `run=lambda`, and
  `tests/test_ui_jobs.py`'s `gpunit`, `_order`'s `run`, `unstartable` and `volume`; its `Volume().down` assert reads `.code`.
  Verify: `git grep -n 'say: Say) -> int' -- tests` prints nothing, and `grep -n 'run=lambda argv, say: 0' tests/test_ui.py` prints nothing.
- [ ] 3.5 Add `REFUSALS` to `isekai/interface/render.py` per [D6](design.md#d6); `isekai render`'s `except Refused`
  prints the kind and returns `refused.code` per [D8](design.md#d8). Add `test_a_refused_session_exits_with_gpunits_code`
  to `tests/test_render.py`, bound to `cli:render-session:a-refused-session-exits-with-gpunits-code`.
  Verify: `uv run pytest tests/test_render.py -k refused` exits 0.
- [ ] 3.6 `run_session`'s docstring in `isekai/interface/render.py` names exits 4 and 5 per [D8](design.md#d8).
  Verify: `grep -c '4 no card in stock · 5 no card fits' isekai/interface/render.py` prints `1`.
- [ ] 3.7 Add `refusal` and `_Slot.refused` to `isekai/interface/ui/jobs.py` and read them per [D7](design.md#d7). Add
  `test_a_refused_window_names_its_kind_and_reason` and `test_a_refused_render_names_its_kind_and_reason` to
  `tests/test_ui_jobs.py`, bound to `ui:render-job:a-refusal-names-its-kind-and-reason`.
  Verify: `uv run pytest tests/test_ui_jobs.py -k refused` exits 0.
- [ ] 3.8 Amend D36 in `docs/decisions.md` per [D9](design.md#d9).
  Verify: `grep -c 'Refusals:.. .isekai render. exits' docs/decisions.md` prints `1`.
