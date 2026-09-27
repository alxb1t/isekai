---
version: v0.24.1
---

# 0034 — RunPod's REST v2

`infra/up.sh` and `infra/down.sh` move from RunPod's REST v1 to v2 before v1 retires on 2026-11-15: the API
move alone, with today's behaviour kept, and proved on one metered boot.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the v1 → v2 mapping, and every choice that keeps today's behaviour |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | none — no requirement names the API version ([D6](design.md#d6)) |

## Why

**RunPod retires REST v1 on 2026-11-15.** Both scripts call `https://rest.runpod.io/v1/pods`, so after that date
no pod can be created, and — worse — none can be torn down, which leaves a pod billing.

**v2 is not a rename.** Its create body is strict and reshaped, its pod carries SSH where v1 carried an IP and a
port map, and it places one GPU type where v1 took a list.

## What Changes

- **`up.sh` creates on `POST /v2/pods`**, trying each type in `RUNPOD_GPU_TYPE` in order until one has capacity
  ([D1](design.md#d1)).
- **`up.sh` polls `GET /v2/pods/{id}` until `.ssh.direct` is set**; a read that fails counts as not ready, so the
  deadline teardown always runs ([D2](design.md#d2)).
- **`down.sh` deletes on `DELETE /v2/pods/{id}`**: only 204 tears down; a 404 asks for the MCP's confirmation
  ([D3](design.md#d3)).
- **Every call reports its status** and RunPod's `problem+json` `title` and `detail` ([D4](design.md#d4)).
- **The static tests move to v2**, and gain a guard that no script calls the retired API ([D5](design.md#d5)).
- **One metered boot proves it** ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None — `skip_specs` ([D6](design.md#d6)).

## Impact

- **Files:** `infra/up.sh`, `infra/down.sh`, `tests/test_infra.py`, `README.md`, `start.sh`, `.env.example`,
  `CHANGELOG.md`.
- **Behaviour:** the same boot, the same teardown, the same outputs; an API error is reported by name instead of
  as a raw body.
- **Patch conditions** ([D6](design.md#d6)): no format version moves, no verb or flag is deprecated, the product is
  unchanged, and no requirement is added.
- **Dependencies:** none.

## Not in this change

- **`P2`, `eu-only` and every privacy card** — the privacy version, after the evaluation minor.
- **A floor on the network volume's own size** — a new guard no requirement demands.
- **Retries and backoff**, beyond the GPU list.
- **Declaring `jq` and `curl` as system dependencies.**
