---
version: v0.35
---

# 0058 — gpunit integration

**isekai rents its GPU through gpunit.** `isekai render` replaces `infra/render.sh` and opens its session with
`gpunit.session()`; `up.sh`, `down.sh`, `pods.sh`, `render.sh` and `stop_pod.sh` leave; the image boots gpunit's
`boot.sh -- /start.sh`. isekai gives gpunit a `gpunit.toml` and the API key in `.env`, and names no provider in its
code. **A minor: it delivers one feature, the render session on gpunit.**

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the verb, the seam, the pod, the specs' map, the build record, the proof |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `pod-image` · `model-provisioning` · `image-generation` |

## Why

**isekai carries a GPU lifecycle of its own in bash.** 600 lines place a pod, check its host key, tunnel, sweep and
stop it, tested by reading the scripts' text. gpunit now does all of it, tested as a library, and other projects
share it.

**isekai should reach the provider only through gpunit.** A second provider should cost isekai a `.env` line and a
`gpunit.toml`, not code.

## What Changes

- **`isekai render <runs> <flow>=<count|source> …`**, Python: the pre-pod pass, a 2640 s watchdog, a
  `gpunit.session()`, the endpoint wait, the flows, the batch log ([D1](design.md#d1)–[D4](design.md#d4)).
- **`isekai/boundary/gpu.py`**, the one seam to gpunit: `.env` read whole into the session's `environ`, gpunit
  imported only inside it ([D2](design.md#d2)).
- **A render records the session's image**; `.runpod_pod_image` and `wiring.POD_IMAGE` go ([D5](design.md#d5)).
- **`gpunit.toml`** committed with the pin, the cards, the floors, the ceiling and the volume; `.env` keeps the API
  key alone ([D6](design.md#d6)).
- **The image boots gpunit's `boot.sh`**: `ADD --checksum` at `v0.2.0`, `ENTRYPOINT`; `start.sh` loses its stop,
  key and sshd steps, reads `GPUNIT_VOLUME_*`, holds by exiting, and `exec`s ComfyUI ([D7](design.md#d7)).
- **The scripts leave:** `infra/up.sh`, `down.sh`, `pods.sh`, `render.sh`, `tools/stop_pod.sh`, and the tests
  that read them ([D8](design.md#d8)).
- **The decisions, principles, pins guide, README, `CLAUDE.md` and the run-flows skill** say gpunit
  ([D9](design.md#d9)).
- **`config/image.json` becomes the build record**: a SHA-256 per copied file, printed by `build-image.yml`, held by
  a test ([D10](design.md#d10)).
- **A metered proof**: built, re-pinned, one render session on a real pod ([D11](design.md#d11)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pod-image`:
  - *A pod boots only the image the repository pins by digest* — `gpunit.toml` pins; the render records the session's image.
  - *The image is built only on request…* — a URL-added file carries a checksum; the build record and its print.
  - *A boot prints when each step begins* — the pod-creation clause goes.
  - *A render session always tears its pod down* — `isekai render` over `gpunit.session()`.
  - *A render session reaches its tunnel without a proxy* — the verb's checks.
  - *A pod makes its own host key and prints its fingerprint* — through gpunit's boot script.
  - *A pod sends no usage report…* — `gpunit.toml`'s `[env]` sets none.
  - *A render session's watchdog ends with it* (added, replacing *…guards end with it*) — the watchdog alone.
  - *The session's spec asks for a host that can render* (added, replacing *A pod is placed only…*) — the floors.
  - *The pod stops itself through gpunit's boot at its ceiling* (added, replacing *A pod stops itself…*).
  - *A pod's host key is checked…*, *A pod runs beside its models volume*, *No `isekai` pod goes unseen* (removed)
    — gpunit's.
- `model-provisioning`:
  - *A provisioning failure leaves the pod reachable* — the hold ends by exiting; the volume told as `GPUNIT_VOLUME_ID`.
- `image-generation`:
  - *A render records the image and the runtime it ran on* — the session, not a pod-boot record, names the image.

## Impact

- **Files:** `isekai/interface/render.py` (new), `isekai/boundary/gpu.py` (new), `isekai/interface/cli.py`,
  `isekai/interface/wiring.py`, `isekai/boundary/comfy/client.py`, `isekai/pipeline/generate.py`, `gpunit.toml`
  (new), `config/image.json`, `Dockerfile`, `start.sh`, `.github/workflows/build-image.yml`, `pyproject.toml`,
  `uv.lock`, `.gitignore`, `.env.example`, `infra/` and `tools/stop_pod.sh` (deleted), `docs/decisions.md`,
  `docs/principles.md`, `docs/pins.md`, `README.md`, `CLAUDE.md`, `.claude/skills/run-flows/SKILL.md`,
  `evaluation/`, and the tests.
- **Behaviour:** a render on a pod runs through `isekai render`; a `generate --server` outside it renders unpinned;
  pods are named `gpunit-isekai`; each session has its own SSH key.
- **Dependencies:** `gpunit`, at runtime ([Dependencies](design.md#dependencies)).
- **Spend:** one render session on a real pod, under the 45-minute ceiling, by hand ([D11](design.md#d11)).

## Not in this change

- **The pod's start in Python, `download_models.sh` and `typecheck_ui.sh` in Python** — the next version, *the pod in
  Python*.
- **The rebuild's other cards** — `0042·R5`, `0042·S3`, Q110, the "16.5 GiB" figure: with *the pod in Python*.
- **A second provider** — trigger: gpunit growing one.
- **Synthetic Portraits** — its own repo.
