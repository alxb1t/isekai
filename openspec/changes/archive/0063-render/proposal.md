---
version: v0.39
---

# 0063 — render

The render runs from the browser. A dialog quotes what will render, how long and at most what price; its
confirmation opens the volume window, runs a session whose limit fits the work, and closes the window unless kept.
The images come back into a Renders view.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the count and seeds, what is short, the limit, the job, billing, the Renders view, the proof |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `review` · `image-generation` · `cli` · `pod-image` · `ui` |

```
hub ─▶ Render ─▶ dialog: per flow, estimate, limit, price at most ─▶ confirm
        ─▶ gpunit volume up ─▶ isekai render --limit … --progress json ─▶ gpunit volume down (unless kept)
        ─▶ /session: image n of N ─▶ done ─▶ /b/<batch>/renders
```

## Why

**A render needs a terminal.** Everything up to Approve now runs in the browser; the paid step does not, and its
volume window is opened and closed by hand.

**A fixed 45 minutes caps a batch.** At about a minute an image, a session fits some thirty; a larger batch needs a
second go, and a small one could run on.

**The approval does not say how many images it wants.** Count and seeds are flags on a command, so a re-roll of the
same sheet is a different invocation, not a decision the sheet records.

## What Changes

- **④ Renders**: a draft and its approval carry a count and seeds; Review edits them; a typed seed is used as it is
  ([D1](design.md#d1)).
- **`render <runs>` renders what is short** of each approval's count ([D2](design.md#d2)).
- **A limit per session**, estimated from recorded durations, never below the pod's provisioning hold plus five
  minutes, at most `gpunit.toml`'s ceiling, which becomes `3h`; the render record gains its duration
  ([D3](design.md#d3)).
- **`max_hourly = 0.90` in `gpunit.toml`** bounds the price the dialog quotes ([D4](design.md#d4)).
- **`render --progress json`** ([D5](design.md#d5)).
- **The render job**: volume up, render, volume down unless kept; Stop ([D6](design.md#d6)).
- **Billing state from gpunit's records**: the pod and volume alerts, the quiet volume item ([D7](design.md#d7)).
- **The Render dialog, `/session`, the Renders view and thumbnails** ([D8](design.md#d8), [D9](design.md#d9)).
- **`CLAUDE.md`'s cost rule** follows the quoted limit ([D10](design.md#d10)).
- **A metered proof**: two images rendered from the UI, on the operator's go ([D11](design.md#d11)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `review`:
  - ADDED *A draft carries how many images to render and which seeds, and approval checks them*.
- `image-generation`:
  - ADDED *An approval states how many images it renders, its listed seeds first*.
  - ADDED *A render records how long it took*.
- `cli`:
  - ADDED *A render with no request renders every approval short of its count*.
  - ADDED *A render session's limit is estimated from its work, at most the configured ceiling*.
  - ADDED *A render session reports its steps as JSON lines when asked*.
- `pod-image`:
  - MODIFIED *The pod stops itself through gpunit's boot at its ceiling* — the ceiling is the session's limit, at most
    `gpunit.toml`'s, which with its timeout ends before a fresh window does.
- `ui`:
  - ADDED *Render is confirmed in a dialog that quotes what renders, its limit and its price at most*.
  - ADDED *The render job opens the volume, renders, and closes the volume unless kept*.
  - ADDED *Billing state is read from gpunit's own records*.
  - ADDED *The Renders view shows each source's images by flow and version*.

## Impact

- **Code:** `isekai/pipeline/review.py`, `isekai/pipeline/generate.py`, `isekai/foundation/artifacts.py`,
  `isekai/interface/render.py`, `isekai/boundary/gpu.py`, `isekai/interface/ui/jobs.py`, `app.py`, `library.py`,
  `ui/src/`; new `isekai/interface/ui/billing.py`, `config/render.json`.
- **Configuration:** `gpunit.toml` — `ceiling = "3h"`, `max_hourly`.
- **Docs:** `CLAUDE.md`, `docs/decisions.md` (D26, D36), `README.md`, `docs/data-flow.md`.
- **Spend:** the last phase rents one session, quoted, on the operator's go.

## Not in this change

- **Revise, compare, the before and after** — revise's.
- **Recording what a session actually spent** — parked until a quote proves wrong.
- **More than one batch per session** — a batch is what one render pays for.
