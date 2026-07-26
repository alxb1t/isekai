# photo-to-anime

Turn a photo of a person into an anime image — while keeping the person **recognizable** —
using **open models** on a **rented GPU, on demand**. A reproducible, provider-agnostic
pipeline: build once, spin up a GPU for minutes, convert, tear down.

> 🚧 **Status: work in progress (Phase 0).** This is a learning + portfolio project built
> step by step. The sections below describe the target design; parts not yet built are
> marked _(planned)_.

## Why this exists

A hands-on way to learn how open image models are run and set up end to end: containerizing
a model runtime, renting GPUs by the second, persisting large weights, and driving the
pipeline headlessly from a CLI. The anime images are the demo; the **infrastructure and the
learning** are the point.

## How it works

- **Model:** [Qwen-Image-Edit 2511](https://huggingface.co/Qwen) (Apache-2.0) — an
  instruction-edit model that restyles a photo to anime while preserving identity.
- **Runtime:** [ComfyUI](https://github.com/comfyanonymous/ComfyUI) in a Docker container.
- **Compute:** [RunPod](https://www.runpod.io/) GPU pod (RTX 4090, 24 GB), **per-second**
  billing. The Docker image runs directly as the pod — no VM to provision.
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
