# photo-to-anime

## Quickstart

Run `cp .env.example .env` and fill your RunPod values.

On each session we do:
up the infra -> setup tunnel -> convert image -> tear down infra

1. Create the pod. Once done it should output the ssh for the tunnel.
`$ ./infra/up.sh`

2. In the second terminal paste to open a tunnel:
`ssh -i ~/.ssh/id_ed25519_runpod -N -L 8188:localhost:8188 root@<ip> -p <port>`

3. In the first terminal run the command to convert the image:
`python convert.py me.jpg -o out.png --prompt "turn this into anime"`

4. Once the session is completed remove the pod to stop billing
`./infra/down.sh`


## Setup

**Prerequisites:**

1. A **RunPod account** with an API key and a small prepaid balance.
2. A **network volume** — required before `up.sh` will work.
3. An SSH key registered with RunPod.


Turn a photo of a person into an anime image — while keeping the person **recognizable** —
using **open models** on a **rented GPU, on demand**. A reproducible, provider-agnostic
pipeline: build once, spin up a GPU for minutes, convert, tear down.

> 🚧 **Status: work in progress — Phases 0–3 done; Phase 4 (first conversion) next.** A
> learning + portfolio project built step by step. Some sections still describe the target
> design; a full docs pass lands in the final phase.

## Why this exists

A hands-on way to learn how open image models are run and set up end to end: containerizing
a model runtime, renting GPUs by the second, persisting large weights, and driving the
pipeline headlessly from a CLI. The anime images are the demo; the **infrastructure and the
learning** are the point.

## How it works

- **Model:** [Qwen-Image-Edit 2511](https://huggingface.co/Qwen) (Apache-2.0) — an
  instruction-edit model that restyles a photo to anime while preserving identity.
- **Runtime:** [ComfyUI](https://github.com/comfyanonymous/ComfyUI) in a Docker container.
- **Compute:** [RunPod](https://www.runpod.io/) GPU pod (RTX PRO 4500, 32 GB; the tier is
  swappable), **per-second** billing. The Docker image runs directly as the pod — no VM to
  provision.
- **Weights:** kept on a persistent RunPod **network volume**, not baked into the image.
- **Interface:** a headless CLI (`convert.py`) that drives ComfyUI over its API.

```
Local (your machine)                          RunPod
┌────────────────────────┐                    ┌──────────────────────────────────────┐
│ repo: photo-to-anime   │                    │ GPU Pod (RTX 4090, ephemeral)         │
│ runpodctl up.sh/down.sh│ ── create pod ───▶ │  runs ghcr image directly (ComfyUI)   │
│ ssh -L 8188 (tunnel)   │ ◀── tunnel :8188   │  (host is already GPU-ready)          │
│ convert.py me.jpg      │ ── API call ─────▶ │        │ mounts ▼                      │
└────────────────────────┘                    │   ┌─────────────────────────────┐    │
        ▲                                      │   │ network volume: models/(Qwen)│   │
        │ ghcr.io/<you>/photo-to-anime (free)  │   └─────────────────────────────┘    │
        │ (env only — RunPod pulls it as pod)  └──────────────────────────────────────┘
                                                     │  down.sh → remove pod; volume persists
```

**Lifecycle:** `up.sh` (create pod from the image + attach volume) → `convert.py photo.jpg`
→ `down.sh` (remove pod, billing stops). Only the pod is ephemeral and metered.

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

## Repository layout

```
photo-to-anime/
├── CLAUDE.md                  # agent guide for working in this repo
├── .env.example               # template for local paths + deploy config
├── Dockerfile                 # ComfyUI + uv + CUDA PyTorch (no models baked in)   (planned)
├── docker-compose.yml         # run the image on any GPU host / local testing      (planned)
├── .github/workflows/         # CI: build & push image to GHCR                      (planned)
├── infra/
│   ├── up.sh                  # runpodctl: create pod + attach volume + tunnel      (planned)
│   └── down.sh                # runpodctl: remove pod                               (planned)
├── scripts/
│   └── download_models.sh     # pull Qwen-Image-Edit onto the network volume        (planned)
├── workflows/
│   └── qwen-image-edit.json   # the ComfyUI pipeline graph                          (planned)
├── convert.py                 # headless CLI: photo in → anime out via ComfyUI API  (planned)
├── examples/                  # input/output pairs                                  (planned)
└── docs/blog.md               # writeup                                             (planned)
```

## Quickstart

_(planned — will be a three-command flow: `up.sh` → `convert.py <photo>` → `down.sh`)_

## Setup

1. Copy the env template and fill it in (it's gitignored):
   ```sh
   cp .env.example .env
   ```
2. The rest of setup (Docker, RunPod, models) is built out across the project phases.

## Cost

On-demand and cheap: RTX 4090 at ~$0.34–0.69/hr (per-second billing), a free public-repo
container image on GHCR, and ~$3.50/mo for the models volume (or $0 if re-downloaded per
session). A full working pipeline costs on the order of **$10 or less** to stand up.

## License

[Apache-2.0](LICENSE) — matching the Qwen-Image-Edit model license.
