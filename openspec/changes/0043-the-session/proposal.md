---
version: v0.30
backlog: [op·P1]
---

# 0043 — the session

No pod bills unseen. `up.sh` places a pod only on a host that can render, and refuses while any `isekai` pod exists;
`down.sh` leaves none; the pod stops itself at its ceiling and at the end of every hold; and `render.sh` is recorded
as the session. One rc build, one metered phase: a render boot and a stop boot.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the gates, the reconciler, the pod's stop, the holds, D36, and the evidence |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `pod-image`, `model-provisioning` |

## Why

**A pod can bill with nothing watching it.** `render.sh`'s watchdog runs on the laptop, so a laptop that sleeps or
dies leaves the pod running with the photograph in its memory. A hold ends with its process exiting, which a
restarted container would repeat forever. Nothing lists the account's pods: a second `up.sh` overwrites the record
and orphans the first pod, and a lost create leaves one no file names.

**A pod can be placed where it cannot render.** The create asks for no host RAM and no CUDA version, and some RTX
4090 hosts report a driver below what torch's cu128 build needs. Nothing reads a card's VRAM before placing it.

## What Changes

- **The create carries floors for host RAM and the host's CUDA version, and a listed card below 24 GB of VRAM is
  skipped; an unknown card refuses** ([D1](design.md#d1)).
- **`up.sh` refuses while `.runpod_pod_id` exists or an `isekai` pod is listed**, and a lost create names
  `down.sh` ([D2](design.md#d2)).
- **`down.sh` leaves no `isekai` pod** — the recorded one, then every other listed ([D3](design.md#d3)).
- **The pod stops itself** 45 minutes after it starts, through RunPod's API with the key RunPod gives it
  ([D4](design.md#d4)).
- **Every hold ends in that stop** instead of in its process exiting ([D5](design.md#d5)).
- **ComfyUI starts without the key** in its environment ([D6](design.md#d6)).
- **D36 records `render.sh` as the session**; `generate.py`, `CLAUDE.md` and `README.md` follow
  ([D7](design.md#d7)).
- **A new image, built on request and proved on a render boot and a stop boot** ([D8](design.md#d8),
  [D9](design.md#d9)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pod-image`:
  - ADDED *A pod is placed only on a host that can render* — the floors, the VRAM skip, the unknown card.
  - ADDED *No `isekai` pod goes unseen* — `up.sh`'s refusals, `down.sh` leaving none, the lost create, the
    session's guard.
  - ADDED *A pod stops itself at its ceiling* — the timer, the stop's retries, the key kept from ComfyUI.
- `model-provisioning`:
  - MODIFIED *A provisioning failure leaves the pod reachable* — the bounded hold ends in the pod stopping itself.

## Impact

- **Files:** `infra/up.sh`, `infra/down.sh`, `infra/pods.sh` (new), `tools/stop_pod.sh` (new), `start.sh`,
  `Dockerfile`, `config/image.json`, `tests/test_infra.py`, `docs/decisions.md`, `isekai/pipeline/generate.py`,
  `CLAUDE.md`, `README.md`.
- **Behaviour:** the render is unchanged; a pod refuses, stops or is removed where it used to bill.
- **Formats:** no run file kind or manifest version moves.
- **Dependencies:** none.
- **Spend:** one metered phase, each boot inside 45 minutes and ~$0.30.

## Not in this change

- **Booting on intent, warming the models, and clearing ComfyUI's history** — declined at the grilling.
- **A Python `session()`**, **a session lock**, and **an architecture gate**.
- **The rehash at boot**, and **the idle volume's rent**.
- **An account key on the pod**, and **RunPod's REST v1**.
