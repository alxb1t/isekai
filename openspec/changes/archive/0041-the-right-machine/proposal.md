---
version: v0.29
backlog: [op·P2, priv·privacy-principle, 0033·volume-floor, op·pod-telemetry]
---

# 0041 — the right machine

Nothing reaches a pod until it has proved who it is: `up.sh` checks the pod's host key against the fingerprint the
pod printed, runs the pod beside its volume, and turns its libraries' telemetry off. The privacy principles and
decisions enter `docs/`. The last privacy version.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the check, the volume read, the switches, the docs text |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `pod-image` |

## Why

**The tunnel trusts the first key it sees.** Since v0.28 each pod makes its own host key and prints its fingerprint,
but `render.sh` still accepts whatever key answers, so a machine that is not the pod could receive the photograph.

**The rest is loose ends of the same boundary.** Nothing checks that a pod runs in its volume's data centre, or that
the volume holds the manifest. The pod's libraries may send usage reports, and nothing tells them not to. The privacy
rules the last versions built live in no document in the repository.

## What Changes

- **`up.sh` checks the host key** against the fingerprint in the pod's log, keeps it in `.runpod_known_hosts` on a
  match, and refuses and tears the pod down otherwise; `render.sh` tunnels with strict checking against it
  ([D1](design.md#d1), [D2](design.md#d2)).
- **`up.sh` reads the volume first** and refuses a data centre other than the volume's, or a volume smaller than the
  manifest ([D3](design.md#d3)).
- **The pod is created with its libraries' telemetry off** ([D4](design.md#d4)).
- **`docs/` gains the privacy principles, D34 and D35**, and D27 names the volume's data centre ([D5](design.md#d5)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pod-image`:
  - ADDED *A pod's host key is checked before anything is sent*.
  - ADDED *A pod runs beside its models volume*.
  - ADDED *A pod sends no usage report its libraries can be told not to send*.
  - MODIFIED *A render session's guards end with it* — the tunnel's key is the checked, per-pod one.

## Impact

- **Files:** `infra/up.sh`, `infra/render.sh`, `infra/down.sh`, `.gitignore`, `docs/principles.md`,
  `docs/decisions.md`, `tests/test_infra.py`.
- **Behaviour:** a pod that fails the host-key check, sits outside its volume's data centre, or has too small a
  volume is refused before anything is sent. The render is unchanged.
- **Formats:** no run file kind or manifest version moves.
- **Dependencies:** none; `ssh-keyscan` ships with the system's OpenSSH.
- **Spend:** one metered boot, 45 minutes and ~$0.30 ceiling.

## Not in this change

- **A region rule** — withdrawn: a self-hosted render owes nothing to GDPR; the volume's data centre is the only rule.
- **The image and `start.sh`** — the telemetry switches move into the image at its next rebuild.
- **A privacy section in the README** — the portfolio version owns the README.
- **Deleting old images from GHCR.**
