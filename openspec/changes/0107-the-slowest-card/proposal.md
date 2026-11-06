---
bump: minor
---

# 0107 — the slowest card

A render session's limit covers the slowest card gpunit may take: each image is quoted at no less than a configured
figure, the boot at what pods really take, and each render records the card it ran on, for a per-card quote later.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, and the tests it costs |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `cli`, `image-generation` |

```
1 the rule    estimate(): each image at max(median, per_image_s); config/render.json boot_s 480, per_image_s 95
2 the card    read_runtime keeps the first device's name; Runtime's optional `device`; the fakes name a card
3 the record  D26 amended; docs/data-flow.md and ui/design/spec.md say the rule
```

## Why

**A session on an L4 runs past its limit**: the library's L4 sessions on 11-03 and 11-05 stopped short, at 13 of 15
and 10 of 12 images. The limit takes the median of the newest durations, recorded mostly on an RTX PRO 4500 at about
36 s an image, where an L4 takes 82–102 s; and the boot is 340–506 s on every card against a configured 180 s.
Raising the configured figures alone fixes nothing, as a figure counts only where no duration is recorded.

## What Changes

- **`estimate()`** in `isekai/interface/render.py` quotes each image at its recorded median or `per_image_s`,
  whichever is higher ([D1](design.md#d1)).
- **`config/render.json`**: `boot_s` 180 → 480, `per_image_s` 60 → 95 ([D2](design.md#d2)).
- **`read_runtime()`** in `isekai/pipeline/generate.py` keeps the name of the first device the endpoint's report lists,
  as `Runtime`'s optional `device`, so every render's `runtime` block records the card ([D3](design.md#d3),
  [D4](design.md#d4)).
- **The fakes** report one device, as a pod does; the golden render sidecar gains its line ([D5](design.md#d5)).
- **D26** is amended for the per-image figure; `docs/data-flow.md` and `ui/design/spec.md` say the rule
  ([D6](design.md#d6)).
- A session's "at most" grows with its limit: a 12-image session from about $0.39 to about $0.66.
- No run-file kind's version moves: `device` is an optional record key (D32 in force). No flow changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli` — *A render session's limit is estimated from its work, at most the configured ceiling*: each image is
  estimated at no less than the configured time per image.
- `image-generation` — *A render records the image and the runtime it ran on*: it also records the device the
  endpoint names first, when it names one.

## Impact

- Code: `isekai/interface/render.py`, `isekai/pipeline/generate.py`, `isekai/foundation/artifacts.py`.
- Config: `config/render.json`.
- Tests: `tests/test_render.py`, `tests/test_generate.py`, `tests/fakes.py`, `tests/golden/render.json`.
- Docs: `docs/decisions.md`, `docs/data-flow.md`, `ui/design/spec.md`.
- `gpunit.toml`, `flows/`, the Dockerfile, `pod_start.py`, the session record and every run-file kind's version are
  untouched.

## Not in this change

- Quoting per card: when enough renders record their device to give each card a median.
- `teardown_s`, the limit factor, the floor and gpunit's ceiling.
- Showing the device anywhere: the record is read by hand until a quote reads it.
