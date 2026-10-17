---
version: v0.36
backlog: [0059·R8, 0059·R9, 0059·R16, 0059·S3]
---

# 0060 — the working window

isekai moves to gpunit `v0.7.0` and renders inside a **working window**: `gpunit volume up` makes the models volume
when a batch is rendered, and `gpunit volume down`, the only teardown, ends it when the operator is done. Past its
ceiling, an overdue volume bills until a gpunit sweep deletes it.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the pin, the window, the pod's cards, the skill, the rebuild and the proof |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `model-provisioning` · `pod-image` |

```
step 4 go ──▶ gpunit volume up --yes ──▶ isekai render (a pod; the first fills <volume>/isekai)
                 create, or extend          step 4 again: a new pod, every model skipped as verified
step 5 ──▶ "another batch?" ── no ──▶ gpunit volume down          (the only teardown)
```

## Why

**Pod work is broken.** `gpunit.toml`'s kept volume answers 404 and the account lists no network
volume, so `isekai render` refuses before any create. A kept volume also bills every hour nobody renders.

**gpunit `v0.7.0` makes the volume a window.** It creates `gpunit-isekai` for a stated ceiling and deletes it on
`volume down`. It needs a `boot.sh` from `v0.6.0` or later, so the image is rebuilt.

**The rebuild is the trigger** for the cards the old image record held back: each fixes `pod_start.py` or
`provision.py`, files that record pinned.

## What Changes

- **The pin:** gpunit `v0.7.0` in `pyproject.toml` and `uv.lock`; the `Dockerfile` `ADD`s `boot.sh` from `v0.7.0`
  with its checksum ([D1](design.md#d1)).
- **The window:** `gpunit.toml`'s kept `volume` → `volume_gb = 50` and `volume_ceiling = "4h"`; the
  volume test, README, D27 and the pins guide say so ([D2](design.md#d2), [D3](design.md#d3)).
- **The pod's cards:** the docstring's stale `(D2)` goes (`0059·R8`); an unread swap table is said, never
  defaulted (`0059·R9`); a source that answers 4xx moves on at once (`0059·R16`); `/dev/shm`'s type is read from
  the mount its device is (`0059·S3`) ([D4](design.md#d4)).
- **The order lives in `run-flows`:** step 4's go quotes the volume, then `volume up`, then `isekai render`; step 5
  asks *another batch?* and runs `volume down` on no. `CLAUDE.md`'s GPU protocol names the volume
  ([D5](design.md#d5)).
- **The image is rebuilt** as `v0.36-rc1` and re-pinned, by hand ([D6](design.md#d6)).
- **A metered window:** `volume up`, a first and a second render, each on a new pod, then `volume down`
  ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `model-provisioning`:
  - *A transfer that fails advances to the next declared source* — a source that answers 4xx has failed at once.
  - *A provisioning failure leaves the pod reachable* — the session's spec declares a window volume, not a named
    one; the window clears the pod's capacity floor.
- `pod-image`:
  - *Everything ComfyUI writes lives in the pod's memory* — the type is read from the mount the memory directory's
    device is; an unread swap table is printed as unread.

## Impact

- **Files:** `pyproject.toml`, `uv.lock`, `Dockerfile`, `config/image.json`, `gpunit.toml`,
  `isekai/boundary/pod_start.py`, `isekai/boundary/provision.py`, `.claude/skills/run-flows/SKILL.md`,
  `CLAUDE.md`, `README.md`, `docs/decisions.md`, `docs/pins.md`, and the tests.
- **Behaviour:** a render needs a window volume up; the first pod of a window downloads the models, the next skip.
- **Dependencies:** gpunit moves from `v0.2.0` to `v0.7.0` ([Dependencies](design.md#dependencies)).
- **Spend:** one window — `volume up`, the first and second render sessions, `volume down` — about $0.60, by hand
  ([D7](design.md#d7)).

## Not in this change

- **`0058·R5`, `R6`, `R7`** — their triggers are unmet; `render.py`, `gpu.py` and the Comfy client are not opened.
- **A change to a flow, the sheet, the prompt or a model.**
- **A volume deleted by hand**, or a skill added.
- **`volume_datacenter`** — stock chooses the data centre, until a window lands where the cards are not.
