---
version: v0.30.1
backlog: [0043·R3, 0043·R4, 0043·R5, 0043·R7, 0043·S5]
---

# 0044 — the session proved

v0.30 shipped without its pod acceptance. This patch boots the image `main` pins, `v0.30-rc2`, as shipped — a render
boot and a stop boot — and tightens the laptop side first: the pod listing bounded, exact and failing closed, and a
refused session that leaves a listed pod alone. No rebuild.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the listing, the lost create, the README, the changelog, and the render and stop boots |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `pod-image` |

## Why

**The image `main` pins has never booted.** RunPod had no capacity for v0.30's acceptance, and `v0.30-rc2` was built
after it, so the pod's own stop, the timer and the placement floors are proved by stub tests alone. D28 asks for a
pod before a digest merges.

**The listing can hang, miss, or over-match, and a refused session sweeps.** A repeated cursor loops `isekai_pods`
forever; a pod with no image field is skipped in silence; the image is matched as a prefix. `render.sh`'s teardown
runs `down.sh` after any `up.sh` failure, so a session refused beside a listed pod deletes that pod.

## What Changes

- **The listing refuses a repeated cursor, matches this project's image exactly, and refuses a pod named `isekai`
  with no image** ([D1](design.md#d1)).
- **A lost create exits 3, and a session with no record sweeps only after one** ([D2](design.md#d2)).
- **`README.md`'s provisioning diagram, script table and lifecycle line** name the pod check, the catalogue read, the
  sweep and the stop timer ([D3](design.md#d3)).
- **`0.30.0`'s changelog entry gains its `### Security` heading, and a bullet outside a section is refused**
  ([D4](design.md#d4)).
- **A render boot and a stop boot on `v0.30-rc2`**, which also read the listing live, the key's scope and the stop's
  signal path ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pod-image`:
  - MODIFIED *No `isekai` pod goes unseen* — gains a repeated cursor refused, only this image listed, a pod with no
    image refused, and a refused session leaving a listed pod.

## Impact

- **Files:** `infra/pods.sh`, `infra/up.sh`, `infra/render.sh`, `tests/test_infra.py`, `tests/test_changelog.py`,
  `README.md`, `CHANGELOG.md`.
- **Behaviour:** the render is unchanged; a listing fault refuses instead of hanging or missing, and a refused
  session leaves another pod alone.
- **Formats:** no run file kind or manifest version moves.
- **Dependencies:** none.
- **Spend:** one metered phase, a render boot and a stop boot, each inside 45 minutes and ~$0.30.

## Not in this change

- **A rebuild** — `start.sh` and `tools/stop_pod.sh` stay as `v0.30-rc2` holds them; what the stop boot shows of a
  refused key and the stop's signal path is carded for the next rebuild.
- **A session lock.**
- **The pool's versions.**
