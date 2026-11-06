# Design — 0107 the slowest card

The estimate takes each image at its median or the configured figure, whichever is higher, with the figures raised to
what pods take; `read_runtime` keeps the first device's name in the runtime it already records. **Verdict: feasible.**

## Context

`estimate()` (`isekai/interface/render.py:609-626`) sums `boot_s + teardown_s` and, per key, `count ×
median(recorded or [per_image_s])` (`:624`), times `limit_factor`, at least `FLOOR_S` (`HOLD_SECONDS + 300`, `:82`) and
at most the ceiling. So `per_image_s` counts only for a key with no records. The medians are the newest `RECENT`
durations per (collection, flow), with no card in the key (`recent()` `:591-606`, `estimated()` `:633-646`).

`config/render.json` holds `boot_s` 180, `per_image_s` 60, `teardown_s` 120, `limit_factor` 1.5, `volume_rate` 0.005;
`load_timing` refuses a missing key (`:562-579`). The quote's price is `limit_s / 3600 × (max_hourly + volume_rate)`
(`quote()`, `:796-824`).

`read_runtime(client)` (`isekai/pipeline/generate.py:581-597`) reads `report["system"]`'s versions and ignores
`report["devices"]`; a missing version is refused as `unread`. Its result, `Runtime`
(`isekai/foundation/artifacts.py:88-93`), is read once per session and written whole as the sidecar's `"runtime"`
(`generate.py:708`).

`FakeComfyClient`'s default report is `{"system": dict(FAKE_SYSTEM), "devices": []}` (`tests/fakes.py:63`).
`tests/golden/render.json` pins the render sidecar's bytes (`tests/test_artifact_bytes.py`), its `runtime` block at
`:20-24`.

ComfyUI's `/system_stats` lists `devices`, each with a `name` in ComfyUI's own form, e.g.
`cuda:0 NVIDIA L4 : cudaMallocAsync`.

## Goals / Non-Goals

**Goals:**
- A session on any card in `gpunit.toml`'s list fits its limit.
- Every render on a pod records the card it ran on, in the record it already writes.

**Non-Goals:**
- Parsing the device's name into a card: the name is kept as reported, until a per-card quote reads it.
- Keying the medians by card ([proposal](proposal.md#not-in-this-change)).
- A `comfy-transport` delta: `system_stats` returns the report whole, as now, and its scenario's versions still hold;
  the device is read by the render stage, under `image-generation`.
- The ESTIMATE mockup at `ui/design/spec.md:293`: an illustration, its price line already not `gpunit.toml`'s.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | In `estimate()`, each key's time per image is `max(statistics.median(recorded), timing.per_image_s)` when the key has records, else `timing.per_image_s`. The docstring gains the line `Each key's images take its recorded median or `per_image_s`, whichever is higher.`, and its example's two lines become `e.g. 4 images at a recorded median of 90 s, per image 95, boot 480,` and `teardown 120, factor 1.5 -> Estimate(980.0, 1470, False)`, the second at the first's continuation indent | Brief Q1. A 4500's medians quote an L4 short, and the card is whichever is in stock. One line, so `estimated()`, the quote and the session keep one estimate | the figure alone, with medians as now: the medians stay in charge (brief Facts) |
| <a id="d2"></a>**D2** | `config/render.json`: `boot_s` 180 → 480, `per_image_s` 60 → 95; `teardown_s`, `limit_factor` and `volume_rate` unchanged. The comment above `RENDER_CONFIG` (`render.py:77`) → `# A session's figures, and the least time an image is quoted at (D26).`; `Timing`'s first docstring line (`:549`) → `` `config/render.json`: the figures, and the least time an image is quoted at. ``. Both fit ruff's 88 columns on one line | Brief Q2. Boot was 340–506 s on every card; 95 s is the L4's median | `teardown_s` 120 → a few seconds: kept as headroom (brief Q2) |
| <a id="d3"></a>**D3** | `read_runtime` keeps the first device's name: when `report.get("devices")` is a non-empty list whose first entry is a mapping with a `str` `name`, the result gains `"device": <that name>`, last; any other shape adds nothing and refuses nothing. The helper is `_first_device(report: dict[str, Any]) -> str \| None`, after `read_runtime`. `read_runtime`'s first docstring line → `Return the versions the endpoint reports, and its first device's name.`; its body gains the line `A report naming no device is read without one; the device decides nothing.` | Brief Q3: `read_runtime` already fetches the report. The device decides nothing, so a report without it is read as now, and the versions' refusal is unchanged | refusing a report with no device: a render would fail on a record it does not need |
| <a id="d4"></a>**D4** | `Runtime` gains `device: NotRequired[str]`, after `pytorch_version`; its docstring → `The versions a ComfyUI endpoint reports, and its first device's name.` The sidecar writer is unchanged: `"runtime": ran_on` carries the key | Brief Q3: one optional key. It is what the endpoint reports about itself, read once per session, so it sits with the versions. An optional record key moves no version (D32) | a top-level `device` key: one report split across keys, and a writer edit for nothing |
| <a id="d5"></a>**D5** | `tests/fakes.py` gains `FAKE_DEVICE = "cuda:0 NVIDIA L4 : cudaMallocAsync"`, after `FAKE_SYSTEM`, under a comment `# The device FakeComfyClient lists first, as ComfyUI names it.`; the default report becomes `{"system": dict(FAKE_SYSTEM), "devices": [{"name": FAKE_DEVICE, "type": "cuda", "index": 0}]}`. `tests/golden/render.json`'s `runtime` gains `"device": "cuda:0 NVIDIA L4 : cudaMallocAsync"` after `pytorch_version`. `tests/test_render.py`'s `STATS` keeps `"devices": []` | A pod always lists its device, so the suite's renders record one, as a pod's do. `STATS` answers `await_endpoint` over HTTP, and no test reads a device from it | a fake listing no device by default: the golden sidecar would never pin where the key sits |
| <a id="d6"></a>**D6** | The record, per [the record](#the-record): D26 amended in `docs/decisions.md`, its `Made by:` gaining `` `0107` ``; `docs/data-flow.md` and `ui/design/spec.md` say the rule | A7: a decision in force is edited where it lives. The docs say what holds once the code does, so they close the change | each doc in its code's phase: the rule's phase would touch every doc for one line of code |

## The device's absence

The reports `test_a_report_naming_no_device_records_none` reads, one case each, by id. For each, `read_runtime` returns
the versions alone, with no `device` key, and refuses nothing ([D3](#d3)).

| id | report |
|---|---|
| `empty` | `{"system": dict(FAKE_SYSTEM), "devices": []}` |
| `absent` | `{"system": dict(FAKE_SYSTEM)}` |
| `unnamed` | `{"system": dict(FAKE_SYSTEM), "devices": [{"type": "cuda"}]}` |
| `not-text` | `{"system": dict(FAKE_SYSTEM), "devices": [{"name": 7}]}` |

## The record

The text edits of [D6](#d6). Each block replaces the lines named, as they stand: no line around them is rewrapped.
Line numbers are at `HEAD`, before any edit: apply each file's blocks from the bottom up.

**`docs/decisions.md`, D26's rule** — lines `:478-481` become:

```text
**A RunPod pod runs this project's own ComfyUI image, with PyTorch built for CUDA 12.8. A session's limit
and price are its quote's, at most `gpunit.toml`'s `ceiling` and `max_hourly`**: the limit is the work's
estimate from recorded durations, each image at no less than `config/render.json`'s `per_image_s`, never
below the provisioning hold plus five minutes, and gpunit refuses a card dearer than `max_hourly`. Each
render records the device it ran on.
```

**D26's Why** — after line `:485`, two lines are added:

```text
  A median recorded on a fast card says nothing of a slow one, and gpunit takes whichever card is in
  stock, so the figure per image is the slowest card's.
```

**D26's Made by** — line `:486` becomes:

```text
- **Made by:** the founding setup, `0063`, `0107`.
```

**`docs/data-flow.md`** — line `:236` becomes these lines; `:235` and `:237` stay:

```text
records its `duration` and the card it ran on, and the next session's limit is
estimated from the durations, each image at no less than the configured time
per image
```

**`ui/design/spec.md`** — lines `:324-325` become these lines; `:326` stays:

```text
- **The estimate**: boot + images × time per image + teardown; boot 8:00 and teardown 2:00, each image at its
  recorded median or 1:35, whichever is higher; one boot and one teardown for every ticked collection.
  The limit is 1.5× the estimate, under the configured
```

## Tests

Every new test is a unit test; nothing reaches a browser (`T1`). The device's recording is a step in the test that
already writes a render on a pinned pod (`T2`).

| layer | adds | removes |
|---|---|---|
| unit | `tests/test_render.py`: `test_a_median_below_the_configured_figure_takes_the_figure` (`cli:render-limit:a-fast-median-takes-the-figure`); `tests/test_generate.py`: `test_a_report_naming_no_device_records_none` (`image-generation:runtime:no-device-records-none`), over [the device's absence](#the-devices-absence)'s reports, and a step and key (`image-generation:runtime:a-render-records-its-device`) in `test_a_render_on_a_pinned_pod_records_its_image_and_runtime` | none |
| end-to-end | none | none |

Existing tests that change or stay green:

- `test_the_runtime_is_read_from_the_endpoints_own_report` (`tests/test_generate.py:1741`) turns red on the fake's
  device: its expected mapping gains `"device": FAKE_DEVICE`.
- `test_each_kind_is_written_byte_for_byte[render]` (`tests/test_artifact_bytes.py`) turns red on the same: the golden
  file gains the line ([D5](#d5)).
- The estimate tests at `tests/test_render.py:1136-1244` stay green: `TIMING`'s `per_image_s` is 60, below their
  medians of 90 and 400. `test_a_short_sessions_limit_is_the_hold_plus_five_minutes` reads the new figures:
  `(480 + 95 + 120) × 1.5` is 1042.5 s, below the 1200 s floor, so it holds.
- `test_one_quote_covers_every_ticked_collection` (`tests/test_ui_api.py:2436-2462`) quotes collections with no
  records from `load_timing()`, so it holds.

Counted with `uv run pytest <file> --collect-only -q | tail -1` at `e404f132`, and as planned:

| file | at `e404f132` | planned |
|---|---|---|
| `tests/test_render.py` | 44 | 45 |
| `tests/test_generate.py` | 109 | 113 |
| the suite, `uv run pytest --ignore=tests/e2e --collect-only -q` | 1496 | 1501 |
| `tests/e2e`, `uv run pytest tests/e2e --collect-only -q` | 19 | 19 |

No test is deleted or merged.

## Dependencies

None.

## Risks / Trade-offs

- [The "at most" grows: a 12-image session from about $0.39 to about $0.66] → accepted (brief Q4); billing is per
  second, so a fast card is billed for its real time, not its limit.
- [A future card slower than 95 s per image] → its sessions stop short again; the recorded device shows which card,
  and `per_image_s` is one config line.
- [ComfyUI changes its device name's form] → the name is kept as reported, so nothing reads it wrong; a per-card quote
  parses it when it is built.

## Moved since the brief

Nothing moved: `HEAD` is `e404f132`, the brief's base, and every fact re-read there stands. The brief's example device
name, "NVIDIA L4", is ComfyUI's `cuda:0 NVIDIA L4 : cudaMallocAsync`; [D3](#d3) keeps it as reported.

## Verdict

**Feasible.** Each phase is green alone: the rule, the card, the record.
