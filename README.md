# isekai

Turn a photo of a person into an anime image — while keeping the person **recognizable** —
using **open models** on a **rented GPU, on demand**. A reproducible, provider-agnostic
pipeline: build once, spin up a GPU for minutes, convert, tear down.

> **Status: v0.8.0, in development.** The pipeline works end to end: one path, five seeded
> variations per run, and a CLI whose whole required surface is the photo. Development follows
> OpenSpec SDD — `openspec/` is authoritative for what the code does and what is being built
> next.

## Why this exists

A hands-on way to learn how open image models are run and set up end to end: containerizing
a model runtime, renting GPUs by the second, persisting large weights, and driving the
pipeline headlessly from a CLI. The anime images are the demo; the **infrastructure and the
learning** are the point.

## How it works

- **Model:** one path (see below), on open weights — Animagine XL 4.0 with InstantID and an
  SDXL ControlNet stack.
- **Runtime:** [ComfyUI](https://github.com/comfyanonymous/ComfyUI) in a Docker container.
- **Compute:** [RunPod](https://www.runpod.io/) GPU pod, **per-second** billing. The Docker
  image runs directly as the pod — no VM to provision.
- **Weights:** kept on a persistent RunPod **network volume**, not baked into the image.
- **Interface:** a headless CLI (`convert.py`) that drives ComfyUI over its API. The runtime
  is **stdlib-only** — no wheels needed to run a conversion.

```
Local (your machine)                          RunPod
┌────────────────────────┐                    ┌──────────────────────────────────────┐
│ repo: isekai           │                    │ GPU Pod (ephemeral)                  │
│ infra/up.sh, down.sh   │ ── create pod ───▶ │  runs ghcr image directly (ComfyUI)  │
│ ssh -L 8188 (tunnel)   │ ◀── tunnel :8188   │  (host is already GPU-ready)         │
│ convert.py me.jpg      │ ── API call ─────▶ │        │ mounts ▼                     │
└────────────────────────┘                    │   ┌─────────────────────────────┐    │
        ▲                                     │   │ network volume: models/     │    │
        │ ghcr.io/alxb1t/isekai (free)        │   └─────────────────────────────┘    │
        │ (RunPod pulls it as the pod)        └──────────────────────────────────────┘
                                                     │  down.sh → remove pod; volume persists
```

**Lifecycle:** `up.sh` (create pod from the image + attach volume) → `convert.py photo.jpg`
→ `down.sh` (remove pod, billing stops). Only the pod is ephemeral and metered.

## The path

There is one, `workflows/pipeline.json`, and nothing about it is typed at the command line.
Identity is four axes, and each is carried by a mechanism rather than by a sentence:

| Axis | Carried by |
|---|---|
| Face | InstantID — face embedding + keypoints, on an Animagine XL 4.0 base |
| Composition | img2img: latent init from the photo (`VAEEncode`, `denoise < 1`) |
| Pose & structure | a ControlNet stack — Tile → OpenPose → Lineart |
| Register | the positive prompt, **committed to the graph** and pinned by a test |

## Quickstart

Run `cp .env.example .env` and fill in your RunPod values.

Each session is: **up the pod → open the tunnel → convert → tear down.**

1. Create the pod. It prints the SSH and tunnel commands when ready.
   ```sh
   ./infra/up.sh
   ```
2. In a second terminal, open the tunnel it printed:
   ```sh
   ssh -i ~/.ssh/id_ed25519_runpod -N -L 8188:localhost:8188 root@<ip> -p <port>
   ```
3. Back in the first terminal, convert:
   ```sh
   python convert.py me.jpg
   ```
   Five renders and a manifest land in a directory named for the run's UTC start instant:
   ```
   outputs/20260904T141530Z/
   ├── 0.png … 4.png     one image per variation
   └── run.json          the seed, the five derived seeds, the dials in force
   ```
4. Tear the pod down to stop billing — **this is the step that costs money if you skip it**:
   ```sh
   ./infra/down.sh
   ```

Useful flags: `-o DIR` picks the output directory (default `./outputs`) · `--variations N`
renders N varied outputs, five by default and 25 at most, and `--seed` makes them reproducible
(every seed used is printed and recorded in `run.json`) · `--denoise`, `--cfg` and `--ip-weight`
set the base dial values that variations jitter around.

## Setup

**Prerequisites:**

1. A **RunPod account** with an API key and a small prepaid balance.
2. A **network volume**, in the same datacenter you configure — required before `up.sh` works.
3. An SSH key registered with RunPod.

Then `cp .env.example .env` and fill it in; it is gitignored and holds every secret.

## Development

**The gate is declared once**, as the `gate` array in `.minions/minions.toml`. The root
`Makefile`, this file and CI (`.github/workflows/ci.yml`) mirror it; change one and you
change all four, in the same commit.

```sh
make gate
```

runs exactly these five, in this order:

```sh
uv sync --locked            # environment, from the tracked lock
uv run ruff format --check .  # format
uv run ruff check .         # lint
uv run ty check             # types
uv run pytest               # tests
```

All five green, or the work is not done. The suite is **fully offline and deterministic** —
the ComfyUI transport is faked behind a Protocol and no test touches a GPU or the network.
Image quality and identity fidelity are judged live on a pod, by eye.

`CLAUDE.md` carries the repo's facts and the change contract; `openspec/specs/` is the
living, test-backed spec, and `openspec/changes/` is the work in flight.

## Repository layout

```
isekai/
├── convert.py                 # headless CLI: photo in → anime out via ComfyUI API
├── isekai/                    # the package: injection, mutation, overrides, transport
├── tests/                     # the suite and its fakes
├── workflows/                 # pipeline.json (the API graph) + pipeline_ui.json (the export)
├── infra/
│   ├── up.sh                  # create pod + attach volume, print the tunnel command
│   └── down.sh                # remove pod, billing stops
├── scripts/
│   └── download_models.sh     # pull weights onto the network volume (runs on the pod)
├── openspec/                  # living specs + changes — authoritative for scope & progress
├── .minions/minions.toml      # the gate array (the rest of .minions/ is gitignored)
├── Makefile                   # `make gate`
├── Dockerfile                 # ComfyUI + CUDA PyTorch (cu128; no models baked in)
├── docker-compose.yml         # run the image on any GPU host / local testing
├── start.sh                   # baked into the image as its start command
├── .github/workflows/         # CI: run the gate; build & push the image to GHCR
├── CLAUDE.md                  # repo facts + the change contract, for agents
└── .env.example               # shape only — no secrets, no paths
```

## Provisioning flow — how `up.sh` and `start.sh` fit together

The two scripts run in **different places at different times**. The common confusion is
thinking `up.sh` downloads/runs the image — it doesn't. `up.sh` only makes **API calls**;
**RunPod's GPU host** pulls the image and runs it, and the image's baked-in **`start.sh`** is
what boots SSH + ComfyUI *inside* the container.

| Script | Runs **where** | Runs **when** | Does what |
|---|---|---|---|
| `start.sh` | **inside the container, on the pod** | every container boot (baked into the image as its start command) | authorize your key → start `sshd` → start ComfyUI |
| `infra/up.sh` | **on your machine** | when you want a pod | calls the RunPod REST API, polls, prints the SSH + tunnel commands |
| `infra/down.sh` | **on your machine** | when you're done | `DELETE`s the pod → per-second billing stops |

```
BUILD TIME (once, or when the image changes)
  Dockerfile + start.sh  ──▶  CI builds image  ──▶  GHCR (ghcr.io/alxb1t/isekai)
  (start.sh is baked INTO the image as its start command)

PROVISION TIME (every session — this is up.sh / down.sh)

  YOUR MACHINE                     RUNPOD                              GHCR
  ────────────                     ──────                              ────
  ./infra/up.sh
    │ 1  POST /v1/pods ──────────▶ control plane
    │    (image, GPU, volume,           │ 2  place pod on a GPU host
    │     PUBLIC_KEY, port 22)          ▼
    │                             GPU host (driver + toolkit ready)
    │                                  │ 3  pull image ───────────────▶ ghcr image
    │                                  │ ◀──────────── ~14 GB ──────────┘
    │                                  │ 4  run container → CMD = /start.sh:
    │                                  │      • authorized_keys ← PUBLIC_KEY
    │                                  │      • start sshd            (:22)
    │                                  │      • mount volume → /opt/ComfyUI/models
    │                                  │      • exec ComfyUI          (:8188)
    │ 5  poll GET /v1/pods ───────────▶│
    │    ◀──── publicIp + port(22) ────┘
    ▼
  prints:  ssh ...   and   ssh -N -L 8188:localhost:8188 ...

USE IT
  ssh -L 8188:localhost:8188 ...    opens a private tunnel to the pod
  convert.py photo.jpg ──▶ localhost:8188 ──tunnel──▶ ComfyUI ──▶ GPU ──▶ anime.png

TEAR DOWN
  ./infra/down.sh  ──▶  DELETE /v1/pods/{id}  ──▶  pod removed, billing stops
                                                   (volume + GHCR image persist)
```

## Cost

On-demand and cheap: an RTX 4090 at ~$0.34–0.69/hr (per-second billing), a free public-repo
container image on GHCR, and ~$3.50/mo for the models volume (or $0 if re-downloaded per
session). A full working pipeline costs on the order of **$10 or less** to stand up.

## License

[Apache-2.0](LICENSE). Model weights are licensed separately by their publishers.
