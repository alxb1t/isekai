# isekai

Turn a photo of a person into an anime image — while keeping the person **recognizable** —
using **open models** on a **rented GPU, on demand**. A reproducible, provider-agnostic
pipeline: build once, spin up a GPU for minutes, convert, tear down.

> **Status: released.** One render path: a **staged pipeline** —
> `python -m isekai caption | sheet | review | approve | generate | show` — which reads a
> photograph into prose, sorts the prose into a sheet of canonical tags, lets a human correct the
> sheet, and renders from it on a stack provisioned from a pinned, checksummed manifest.
> Development follows OpenSpec SDD, and **`openspec/` is authoritative** for what the code does and
> for what is being built next — this banner deliberately names no version, because a forward
> reference here is one reordering away from being wrong.
>
> **⚠️ Work in progress: the first two stages are not yet open.** Reading a photograph and sorting
> the result both run through the **`claude` CLI**, so they need that binary on `PATH` and an
> Anthropic subscription — a fresh clone without one can do neither. Nothing else here does: the
> render itself, the provisioning and the whole test suite are unaffected. **Replacing both with
> open, digest-pinned models is upcoming work**, and the seam they sit behind exists so that is a
> swap rather than a rewrite.

## Why this exists

A hands-on way to learn how open image models are run and set up end to end: containerizing
a model runtime, renting GPUs by the second, persisting large weights, and driving the
pipeline headlessly from a CLI. The anime images are the demo; the **infrastructure and the
learning** are the point.

## How it works

- **Model:** one path (see below), on open weights — WAI-illustrious-SDXL v17.0 with InstantID
  and an SDXL ControlNet stack.
- **Runtime:** [ComfyUI](https://github.com/comfyanonymous/ComfyUI) in a Docker container.
- **Compute:** [RunPod](https://www.runpod.io/) GPU pod, **per-second** billing. The Docker
  image runs directly as the pod — no VM to provision.
- **Weights:** kept on a persistent RunPod **network volume**, not baked into the image, and
  provisioned from a **pinned, checksummed manifest** — every artifact is addressed by an
  immutable revision and verified by SHA-256 before anything loads it. The volume is
  **namespaced per project**, so a volume shared with another project has no shared files.
- **Interface:** a headless CLI (`python -m isekai`) that drives ComfyUI over its API. The
  runtime is **stdlib-only** — no wheels needed to run a conversion.

```
Local (your machine)                          RunPod
┌────────────────────────┐                    ┌──────────────────────────────────────┐
│ repo: isekai           │                    │ GPU Pod (ephemeral)                  │
│ infra/up.sh, down.sh   │ ── create pod ───▶ │  runs ghcr image directly (ComfyUI)  │
│ ssh -L 8188 (tunnel)   │ ◀── tunnel :8188   │  (host is already GPU-ready)         │
│ python -m isekai …     │ ── API call ─────▶ │        │ mounts ▼                     │
└────────────────────────┘                    │   ┌─────────────────────────────┐    │
        ▲                                     │   │ volume: /runpod-volume/     │    │
        │                                     │   │   isekai/ ← this project    │    │
        │ ghcr.io/alxb1t/isekai (free)        │   └─────────────────────────────┘    │
        │ (RunPod pulls it as the pod)        └──────────────────────────────────────┘
                                                     │  down.sh → remove pod; volume persists
```

**Lifecycle:** `up.sh` (create pod from the image + attach volume) →
`python -m isekai generate --server …` → `down.sh` (remove pod, billing stops). Only the pod is
ephemeral and metered.

## The path

There is one flow, `flows/summon-v1/`, and it is driven in staged verbs rather than typed as
options. Identity is carried by mechanisms rather than by a sentence:

| Axis | Carried by |
|---|---|
| Face | InstantID — face embedding + keypoints, on a WAI-illustrious-SDXL v17.0 base |
| Composition | from noise: `EmptyLatentImage` at `denoise` 1.0 |
| Pose | one ControlNet — OpenPose, off `DWPreprocessor` |
| Detail | a hires pass — RealESRGAN upscale, then a second sampler at `hires_denoise` 0.35 |
| Register | the prompts, **assembled per run** from a sheet of canonical tags a human approved |

A flow is a directory of two tracked files: `flow.json`, which declares its inputs, its dials, its
prompt fragments and the graph id of every node the render path edits; and `graph.json`, the API
graph. **Nothing locates a node by class** — the manifest names them, which is what lets a broken
flow be caught by the suite rather than by a boot. A flow is immutable: editing one is not a variant
of a flow, it is an untested flow.

Before any node reads the photo, it is scaled to a working resolution derived from its own
dimensions: aspect preserved, short side at 1024, both dimensions a multiple of 64, and refused past
4:1 rather than clamped. One pixel grid feeds the whole graph, so every consumer is handed the same
scaled image. That is a claim about which image each consumer *receives*, not about what it then does
internally — a preprocessor's own working resolution is a separate dial on that node, and
`DWPreprocessor` derives its pose hint at 512 today.

## Quickstart

Run `cp .env.example .env` and fill in your RunPod values.

The first three stages need **no GPU and no pod** — they are free and local. Only `generate` needs
an endpoint.

1. Read the photograph into prose, then sort the prose into a sheet of canonical tags:
   ```sh
   python -m isekai caption me.jpg
   python -m isekai sheet me.jpg
   ```
   Each run gets a directory under `.data/runs/`, named for the photograph's digest and its
   filename. Offer the photograph again, or the run's id — which one you meant is decided by
   what is on disk.
2. Correct the sheet. `review` copies it somewhere you may edit it; `approve` validates the edit
   and marks it approved. **Only an approved sheet is ever rendered** — the correction is the
   single largest measured gain in this pipeline.
   ```sh
   python -m isekai review me.jpg      # then edit the file it prints
   python -m isekai approve me.jpg
   ```
3. Create the pod. It prints the SSH and tunnel commands when ready, and tears itself down if it
   never becomes usable.
   ```sh
   ./infra/up.sh
   ```
4. In a second terminal, open the tunnel it printed:
   ```sh
   ssh -i ~/.ssh/id_ed25519_runpod -N -L 8188:localhost:8188 root@<ip> -p <port>
   ```
5. Back in the first terminal, render:
   ```sh
   python -m isekai generate me.jpg --server http://127.0.0.1:8188
   ```
   Each image lands under the run directory, named for the seed that produced it, beside a
   provenance artifact recording the flow, the seed, the sheet version and the digest of the graph
   actually submitted.
6. Tear the pod down to stop billing — **this is the step that costs money if you skip it**:
   ```sh
   ./infra/down.sh
   ```

`python -m isekai show me.jpg` prints a run's artifacts, versions and what produced each one.

Useful flags, as the parser states them:

- `--runs RUNS` — the directory runs live under. It may point outside the repository entirely, but
  not inside the working tree and outside `.data/`: a run directory holds a copy of the photograph,
  so that would be one `git add` from publishing it.
- `--flow FLOW` — a flow to act on. **Required on every stage verb and repeatable**: a stage
  cannot act without knowing which flow asked, because the flow is what supplies its briefing,
  its schema, its graph and its dials. There is no fallback — the earlier one was every
  *tracked* flow, which at catalogue scale is the absence of a selection rather than one. It
  repeats because flows batch: every flow named in one `generate` renders on one endpoint, and a
  second boot costs what eight more renders would.
- `--count COUNT` — how many renders per photograph per flow (default 1, seeds drawn).
- `--seed SEEDS` — render exactly this seed; repeatable, and not combinable with `--count`.
- `--server SERVER` — the ComfyUI endpoint, reached through the tunnel; **omit it to assemble every
  prompt and stop without rendering**, which is how a whole batch is checked before anything is
  rented.
- `--new-version` — on `caption`, `sheet` and `review`, write the next numbered artifact instead of
  doing nothing. Every stage decides whether it is done by a directory listing, so re-running one is
  free.

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
├── isekai/                    # the package, filed into six groups; one README.md each
│   ├── __main__.py            # the path `python -m isekai` resolves — a shim over interface/cli.py
│   ├── foundation/            # run directory & layout names, flow manifest & Schema, refusal
│   ├── pipeline/              # the four staged verbs: caption · sheet · review · generate
│   ├── shared/                # image header reader, vocabulary, atomic write
│   ├── boundary/              # ComfyUI transport, the hosted model, provisioning
│   ├── evaluation/            # the scorer, and the only importer of the [eval] extra
│   └── interface/             # the parser & dispatch, the composition, the run's account
├── tests/                     # the suite and its fakes
├── flows/summon-v1/           # flow.json = inputs, dials, prompt fragments, node roles;
│                              # graph.json = the API graph. A flow is immutable.
├── infra/
│   ├── up.sh                  # create pod + attach volume, print the tunnel command
│   └── down.sh                # remove pod, billing stops
├── scripts/
│   ├── download_models.sh     # thin driver: plan → wget → verify & land; takes the manifest
│   ├── models.json            # the pinned, checksummed manifest — what the stack IS
│   ├── vocabulary.json        # the tag list's manifest: `download_models.sh scripts/vocabulary.json`
│   └── derive_manifest.py     # re-derives every revision & digest; the manifest is its output
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
    │                                  │      • mount volume → /runpod-volume
    │                                  │      • /opt/ComfyUI/models → /runpod-volume/isekai
    │                                  │      • provision from scripts/models.json (verified)
    │                                  │      • exec ComfyUI          (:8188)
    │ 5  poll GET /v1/pods ───────────▶│
    │    ◀──── publicIp + port(22) ────┘
    ▼
  prints:  ssh ...   and   ssh -N -L 8188:localhost:8188 ...

USE IT
  ssh -L 8188:localhost:8188 ...    opens a private tunnel to the pod
  python -m isekai generate photo.jpg --server http://127.0.0.1:8188
                       ──▶ localhost:8188 ──tunnel──▶ ComfyUI ──▶ GPU ──▶ anime.png

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
