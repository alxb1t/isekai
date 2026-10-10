---
version: v0.35.1
backlog: [0058·R2, 0058·R3, 0058·R4, 0058·R8, 0058·R9]
---

# 0059 — the pod in Python

No bash is left in isekai. The pod's start, the model download and the gate's browser check become tested Python,
and the pod's privacy is proven unchanged, offline and on a real pod. **A patch: no feature, the product
unchanged.**

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the start module, `fetch`, the parity table, the pod's proof |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `pod-image` · `image-generation` |

## Why

**What runs on the pod is tested by reading its text.** `start.sh`'s steps are checked by matching literal lines,
and `download_models.sh` by grepping its loops; a correct rewrite that reads differently fails, and a wrong one
that reads the same passes. In Python each step runs in a test against a fake filesystem.

**The pod's privacy must not move.** ComfyUI's directories in memory, no render metadata, the memory holds: each
keeps its key, and the pod itself is checked once more.

## What Changes

- **`isekai/boundary/pod_start.py`** replaces `start.sh`: the volume, the namespace, provisioning, memory, then
  `exec` into ComfyUI ([D1](design.md#d1), [D2](design.md#d2)).
- **`provision.py fetch`** replaces `download_models.sh`: the transfer over `urllib`, argparse, an anchored default;
  `wget` leaves the image; the remedies name the new command ([D3](design.md#d3)).
- **The memory step** reads the type from `/proc/mounts`, says so when it cannot, and reports swap without holding
  ([D4](design.md#d4)).
- **`tools/typecheck_ui.py`** replaces `typecheck_ui.sh` ([D5](design.md#d5)).
- **Privacy parity**: every privacy key held by a test of `pod_start`'s behaviour; the parity table
  ([D6](design.md#d6)).
- **The cards that ride along**: the volume path read once (`0058·R9`); the build record refuses a `COPY` it cannot
  read (`0058·R4`); the pins guide's recipe rebuilds before re-recording (`0058·R3`); the seeds-from diagram and a
  docstring name `isekai render` (`0058·R2`); a workflow comment cites no design (`0058·R8`)
  ([D7](design.md#d7)).
- **A metered proof** with the privacy check on the pod ([D8](design.md#d8)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pod-image`:
  - *Everything ComfyUI writes lives in the pod's memory* — an unreadable type holds; swap is reported.
- `image-generation`:
  - *A flow renders on another flow's seeds when the operator names it* — the diagram names `isekai render`.

## Impact

- **Files:** `isekai/boundary/pod_start.py` (new), `isekai/boundary/provision.py`, `isekai/shared/vocabulary.py`,
  `isekai/boundary/ollama.py`, `tools/typecheck_ui.py` (new), `tools/image_record.py`, `Dockerfile`, `Makefile`,
  `config/image.json`, `.github/workflows/build-image.yml`, `docs/principles.md`, `docs/decisions.md`,
  `docs/pins.md`, `README.md`, `start.sh`, `tools/download_models.sh` and `tools/typecheck_ui.sh` (deleted), and
  the tests.
- **Behaviour:** the pod does what it did; the laptop's download remedy is a Python command.
- **Dependencies:** none ([Dependencies](design.md#dependencies)).
- **Spend:** one render session on a real pod, under the 45-minute ceiling, by hand ([D8](design.md#d8)).

## Not in this change

- **`0058·R5`, `R6`, `R7`** — `render.py`, `gpu.py` and the Comfy client are not opened; they wait for their
  triggers.
- **The uv build-tool setting** — parked until research finds one.
- **A change to any flow, render, review or the UI.**
