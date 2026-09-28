---
version: v0.26
backlog: [op·comfy-proxy, 0001·multipart, 0030·S2, 0031·S2, 0013·R10, 0031·R3, 0031·S3, op·tag-string, 0031·S4, 0035·R10, 0035·S5, op·known-hosts]
---

# 0037 — the boundaries

Each boundary refuses what it cannot trust: the ComfyUI transport, the review surface, the run frame and the render
session. One feature — the second half of the security version — proved on one metered session.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each boundary's rule, its numbers, and how the tests move |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `comfy-transport`, `ui`, `run-directory`, `pod-image` |

## Why

**The code between isekai and the outside trusts what it is handed.**

- **The ComfyUI client** follows any proxy the environment names, with the photograph in the body; waits for ever on
  a pod that stopped answering; frames its upload with a fixed boundary; and quotes an endpoint's error with its
  control characters.
- **The review surface** answers a damaged file with a server error, and saves a tag list sent as a string as its
  letters.
- **A run frame** can point a run at any image on the machine.
- **The render session's watchdog** can outlive its session, and its tunnel keeps every pod's host key in the
  operator's own file.

**Why now:** since v0.25 an agent runs render sessions unattended, which is the premise `0013·R10` was settled on
2026-09-20 without.

## What Changes

- **The transport ignores the environment's proxy**, as the reader's does; D6 covers both ([D1](design.md#d1)).
- **Every request times out at 60 s, and a render at 600 s**, each refused as transient; a prompt id that is not a
  non-empty string is refused as permanent ([D2](design.md#d2), [D3](design.md#d3)).
- **The upload's boundary is random and in no part, and a name's quote and line breaks are escaped**
  ([D4](design.md#d4)).
- **An endpoint's error text keeps printable characters only** ([D5](design.md#d5)).
- **The review surface refuses a damaged file or a malformed draft update by name** ([D6](design.md#d6)).
- **A frame's photograph name must be one plain filename, and its keys are checked** ([D7](design.md#d7)).
- **The watchdog ends with its session, and each session keeps its own known hosts** ([D8](design.md#d8),
  [D9](design.md#d9)).
- **The render script reaches its tunnel without a proxy** ([D11](design.md#d11)).
- **One metered session proves it**, with a dead `http_proxy` exported ([D10](design.md#d10)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `comfy-transport`:
  - ADDED *The transport ignores any proxy the environment names*.
  - ADDED *Every request to the endpoint is bounded in time*.
  - ADDED *An endpoint's error text is quoted in printable characters only*.
  - MODIFIED *Hand-built multipart encoding* — a boundary in no part, and escaped names.
  - MODIFIED *Render completion polling* — a deadline, and a prompt id that must be a string.
- `ui`: ADDED *A damaged run file or a malformed draft update is refused, never failed*.
- `run-directory`: ADDED *A run's photograph is named inside the run*.
- `pod-image`:
  - ADDED *A render session's guards end with it*.
  - ADDED *A render session reaches its tunnel without a proxy*.

## Impact

- **Code:** `isekai/boundary/comfy/client.py`, `isekai/boundary/comfy/multipart.py`, `isekai/pipeline/generate.py`,
  `isekai/interface/ui/app.py`, `isekai/foundation/run.py`, `infra/render.sh`.
- **Tests:** `tests/test_generate.py`, `tests/test_resume.py`, `tests/test_sheet_stage.py`,
  `tests/test_pipeline_cli.py`, `tests/fakes.py`, `tests/test_multipart.py`, `tests/test_ui_api.py`,
  `tests/test_run_directory.py`, `tests/test_infra.py`.
- **Docs:** `docs/decisions.md` (D6).
- **Behaviour:** a failure that hung or crashed is now refused and recorded; the product — sheets, prompts,
  images — is unchanged.
- **Formats:** no run file kind or manifest version moves.
- **Dependencies:** none.

## Not in this change

- **Stripping EXIF** (`priv·exif`), **checking the pod's host key** (`op·P2`) and **refusing a non-EU data centre**
  (`priv·eu-only`) — the privacy version.
- **`show` surviving an unreadable frame** (`0030·R4`) — rejected by 0030's design D5.
- **`Origin` on every request** (`0023·S1`) — a known low risk the `ui` spec defends.
- **A bounded read of an endpoint's error body** — its trigger is an endpoint that is not the operator's own.
- **Any change to the flows, the prompt or the image.**
