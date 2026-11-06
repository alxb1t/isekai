# Tasks — 0107 the slowest card

The rule, then the card, then the record, per [design](design.md). Paths are from the repository root.

## Progress

- [ ] 1 — The rule
- [ ] 2 — The card
- [ ] 3 — The record

## 1 — The rule

- [ ] 1.1 **HALT CHECK** — [D1](design.md#d1) edits the one line where `estimate` takes `per_image_s`.
  Verify: `grep -n 'statistics.median(recorded.get(key) or \[timing.per_image_s\])' isekai/interface/render.py` prints one line.
- [ ] 1.2 In `isekai/interface/render.py`, make `estimate` take each key's time per image per [D1](design.md#d1),
  and give its docstring the rule and [D1](design.md#d1)'s example.
  Verify: `grep -n 'Estimate(980.0, 1470, False)' isekai/interface/render.py` prints one line.
- [ ] 1.3 In `isekai/interface/render.py`, replace the comment above `RENDER_CONFIG` and `Timing`'s first docstring
  line with [D2](design.md#d2)'s text.
  Verify: `grep -c 'the least time an image is quoted at' isekai/interface/render.py` prints `2`.
- [ ] 1.4 In `config/render.json`, set `"boot_s": 480` and `"per_image_s": 95` per [D2](design.md#d2).
  Verify: `grep -c -E '"(boot_s": 480|per_image_s": 95),' config/render.json` prints `2`.
- [ ] 1.5 In `tests/test_render.py`, after `test_with_no_recorded_duration_the_configured_time_per_image_is_used`, add
  `test_a_median_below_the_configured_figure_takes_the_figure` (`cli:render-limit:a-fast-median-takes-the-figure`):
  `render.estimate({FLOW: 4}, {FLOW: [30.0, 36.0, 40.0]}, TIMING, 3 * 60 * 60)` has `seconds == 600 + 4 * 60 + 120`.
  Verify: `uv run pytest tests/test_render.py -k median_below_the_configured_figure` exits 0.

## 2 — The card

- [ ] 2.1 **HALT CHECK** — [D3](design.md#d3) reads the report `read_runtime` already fetches.
  Verify: `grep -n 'report = client.system_stats()' isekai/pipeline/generate.py` prints one line.
- [ ] 2.2 In `isekai/foundation/artifacts.py`, give `Runtime` the `device` key and the docstring of
  [D4](design.md#d4).
  Verify: `grep -n '    device: NotRequired\[str\]' isekai/foundation/artifacts.py` prints one line.
- [ ] 2.3 In `isekai/pipeline/generate.py`, add `_first_device` after `read_runtime`, and make `read_runtime` keep
  its name, per [D3](design.md#d3); `read_runtime`'s docstring takes D3's summary line and body line.
  Verify: `grep -n 'def _first_device(report: dict\[str, Any\]) -> str | None:' isekai/pipeline/generate.py` prints one line.
- [ ] 2.4 In `tests/fakes.py`, add `FAKE_DEVICE` and its comment after `FAKE_SYSTEM`, and list it in the default
  report, per [D5](design.md#d5).
  Verify: `grep -n '^FAKE_DEVICE = "cuda:0 NVIDIA L4 : cudaMallocAsync"$' tests/fakes.py` prints one line.
- [ ] 2.5 In `tests/golden/render.json`, add `"device": "cuda:0 NVIDIA L4 : cudaMallocAsync"` after
  `"pytorch_version"` in `runtime`, a comma ending the line before it, per [D5](design.md#d5).
  Verify: `uv run pytest tests/test_artifact_bytes.py` exits 0.
- [ ] 2.6 In `tests/test_generate.py`, import `FAKE_DEVICE` from `tests.fakes`; give
  `test_the_runtime_is_read_from_the_endpoints_own_report`'s expected mapping `"device": FAKE_DEVICE`, last.
  Verify: `uv run pytest tests/test_generate.py -k runtime_is_read_from_the_endpoints_own_report` exits 0.
- [ ] 2.7 In `tests/test_generate.py`, give `test_a_render_on_a_pinned_pod_records_its_image_and_runtime` the key
  `image-generation:runtime:a-render-records-its-device`; in its loop add `runtime = sidecar.get("runtime")`,
  `assert runtime is not None` and `assert runtime.get("device") == FAKE_DEVICE`.
  Verify: `grep -c 'image-generation:runtime:a-render-records-its-device' tests/test_generate.py` prints `1`.
- [ ] 2.8 In `tests/test_generate.py`, after `test_an_unfetched_report_keeps_the_transports_kind`, add
  `test_a_report_naming_no_device_records_none` (`image-generation:runtime:no-device-records-none`), parametrized
  over the reports of [the device's absence](design.md#the-devices-absence); `read_runtime` returns the versions alone.
  Verify: `uv run pytest tests/test_generate.py -k report_naming_no_device` exits 0.

## 3 — The record

- [ ] 3.1 In `docs/decisions.md`, replace D26's rule, extend its Why and replace its Made by with the lines of
  [the record](design.md#the-record).
  Verify: `grep -n 'each image at no less than' docs/decisions.md` prints one line.
- [ ] 3.2 In `docs/data-flow.md`, replace the line `records its` … `estimated from them` with the lines of
  [the record](design.md#the-record).
  Verify: `grep -n 'and the card it ran on, and the next session' docs/data-flow.md` prints one line.
- [ ] 3.3 In `ui/design/spec.md`, replace the estimate's first lines with the lines of
  [the record](design.md#the-record).
  Verify: `grep -n 'recorded median or 1:35, whichever is higher' ui/design/spec.md` prints one line.
