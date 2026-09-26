# isekai

Turn a photo of a person into an anime image — while keeping the person **recognizable** —
using **open models** on a **rented GPU, on demand**. A reproducible, provider-agnostic
pipeline: build once, spin up a GPU for minutes, convert, tear down.

> **Status: released.** One render path: a **staged pipeline** —
> `python -m isekai caption | sheet | review | approve | generate | show | ui` — which reads a
> photograph into prose and tags, fills a sheet of canonical tags from the tags by a table, lets a
> human correct the sheet — at `$EDITOR` or on a local browser surface that knows the vocabulary —
> and renders from it on a stack provisioned from a pinned, checksummed manifest.
> Development follows OpenSpec SDD, and **`openspec/` is authoritative** for what the code does and
> for what is being built next — this banner deliberately names no version, because a forward
> reference here is one reordering away from being wrong.
>
> **The whole pipeline runs on open models.** Stage ① reaches JoyCaption over a local
> [Ollama](https://ollama.com) and nothing here needs an API key or a subscription; stage ② reaches
> no model at all. The flow's manifest names the one model it runs, in a required `model` key, and
> both tracked flows name the same one. *(Until v0.22 there was a second arm over the `claude` CLI,
> selected by a flow declaring no `hosted` block. Nothing had called it for anything measured since
> v0.19, so v0.22 removed it and the block with it.)*
> **The model is not digest-pinned**; the flow names it and nothing verifies the bytes behind the
> name. That travels with provisioning, and this version does not claim it.

## Why this exists

A hands-on way to learn how open image models are run and set up end to end: containerizing
a model runtime, renting GPUs by the second, persisting large weights, and driving the
pipeline headlessly from a CLI. The anime images are the demo; the **infrastructure and the
learning** are the point.

## How it works

- **Model:** open weights — WAI-illustrious-SDXL v17.0 with InstantID and an SDXL ControlNet
  stack. How the render path uses them is [`docs/`](docs/README.md)'s.
- **Runtime:** [ComfyUI](https://github.com/comfyanonymous/ComfyUI) in a Docker container.
- **Compute:** [RunPod](https://www.runpod.io/) GPU pod, **per-second** billing. The Docker
  image runs directly as the pod — no VM to provision.
- **Weights:** kept on a persistent RunPod **network volume**, not baked into the image, and
  provisioned from a **pinned, checksummed manifest** — every artifact is addressed by an
  immutable revision and verified by SHA-256 before anything loads it. The volume is
  **namespaced per project**, so a volume shared with another project has no shared files.
- **Interface:** a headless CLI (`python -m isekai`) that drives ComfyUI over its API. Its
  import rule is [docs D20](docs/decisions.md#d20--the-entry-point-loads-no-third-party-package).

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
`python -m isekai generate --flow … --server …` → `down.sh` (remove pod, billing stops). Only the pod is
ephemeral and metered.

## Architecture

How the system is built is [`docs/`](docs/README.md): the [principles](docs/principles.md), the
[decisions](docs/decisions.md) in force, the [modules](docs/modules.md) and the
[data flow](docs/data-flow.md).

## Running a flow

Photograph in, anime image out, in the order an operator actually types it. Do `## Setup` below once
first — it is the prerequisites, the `.env`, and the system binaries — then this page is the whole
run.

**Everything through `approve` is local and free. `generate` rents a GPU and spends real money.**

```
   free, on your machine                     │  metered, on a rented GPU
   ① caption   ② sheet   ③ review/approve    │  ④ up.sh → tunnel → generate → down.sh
                                             ▲
                                   the line where it starts costing
```

### ① Read the photograph

Put the photograph somewhere gitignored — `.inputs/` exists for exactly this, because a photograph an
operator supplies is an input rather than something a run generated, and it holds a person's likeness.
Then:

```sh
python -m isekai caption --flow summon-anime-wai .inputs/me.jpg
```

One verb, and it writes and reports each artifact in order: the prose, then a scored tag list from the
local WD14 tagger, then a raw one from the hosted model. **The local list is what fills the sheet**, so it
needs `bash tools/download_models.sh config/vocabulary.json` to have been run.

If Ollama is not running, `caption` refuses the photograph at the prose, before either list; if only
the hosted list is missing, its own call failed. The prose is a reading aid with no machine consumer.
Neither list is narrowed on disk; the review surface shows the WD14 list, and the hosted list filtered
to what the vocabulary carries.

`--flow` is required on every stage verb. A stage cannot act without knowing which flow asked, because
the flow supplies the briefing it reads and the schema it fills against.

### ② Fill the sheet

```sh
python -m isekai sheet --flow summon-anime-wai .inputs/me.jpg
```

Each run gets a directory under `.data/runs/`, named for the photograph's digest and its filename,
and every artifact sits under the flow that produced it:
`<input-id>/<flow-id>/{captions,wd14,tags,sheets,review,prompts,outputs}/`. From here on, offer the
photograph again or the run's id — which one you meant is decided by what is on disk.

### ③ Correct the sheet, and approve it

In a browser, which is the recommended path:

```sh
python -m isekai ui <run-id> --flow summon-anime-wai
```

Or by hand, which stays a fully working path:

```sh
python -m isekai review --flow summon-anime-wai .inputs/me.jpg   # then edit the file it prints
python -m isekai approve --flow summon-anime-wai .inputs/me.jpg
```

**Only an approved sheet is ever rendered**, and the correction is the single largest measured gain in
this pipeline. `ui` is described under *Correcting the sheets in a browser* below; when you are done
there, stop it with Ctrl-C.

### ④ Rent the GPU — this is where it starts costing

```sh
./infra/up.sh
```

It prints the SSH and tunnel commands when the pod is ready, and tears itself down if the pod never
becomes usable. **Billing is per second and starts here.**

### ⑤ Open the tunnel, in a second terminal

```sh
ssh -i ~/.ssh/id_ed25519_runpod -N -L 8188:localhost:8188 root@<ip> -p <port>
```

Use the address `up.sh` printed. Leave it running.

### ⑥ Render, back in the first terminal

```sh
python -m isekai generate --flow summon-anime-wai .inputs/me.jpg --server http://127.0.0.1:8188
```

Each image lands under the run directory, named for the seed that produced it, beside a provenance
artifact recording the flow, the seed, the sheet version and the digest of the graph actually
submitted. **Download anything you want to keep before the next step** — renders live on the pod's
ephemeral disk, and only the models volume persists.

Omit `--server` to assemble every prompt and stop without rendering, which is how a whole batch is
checked before anything is rented. Assembly happens before any endpoint is acquired either way, so a
malformed sheet costs nothing rather than a boot.

### ⑦ Tear the pod down

```sh
./infra/down.sh
```

**This is the step that costs money if you skip it.** The volume persists; the pod does not.

### Afterwards

```sh
python -m isekai show .inputs/me.jpg
```

Prints a run's artifacts, versions and what produced each one. It reaches no model and no GPU, and it
works on a checkout that has provisioned nothing.

### Correcting the sheets in a browser

Step ③ by hand edits a JSON file in a text editor. `isekai ui` does the same work on a surface that
knows the vocabulary — canonical spelling, the post count behind every tag, and a live token count
against the encoder's 77-token window, none of which a text editor can tell you:

```sh
python -m isekai ui <run-id> [<run-id> …] --flow summon-anime-wai
```

It resolves the batch, refuses everything it can refuse, prints a URL and blocks; correct and approve
each sheet in the browser, then stop it with Ctrl-C and go on to `generate`. **Nothing on the page
reaches a model or a GPU** — its scope is stage ③ alone.

- `--flow` is **required and takes exactly one** here, unlike on the stage verbs: the surface shows one
  schema's fields in one fixed order, so a second flow would be a second page rather than a wider one.
- It needs **node**, to build the bundle: `npm install` in `ui/` the first time. The bundle is built on
  demand, and a missing toolchain refuses naming what installs it. Nothing else has to be installed —
  the server is a declared dependency of this project, as is the local tagger's stack.
- `review` and `approve` keep working exactly as before. They are deprecated as *guidance*, never as
  code — deleting the hand path would make ③ a single point of failure for the whole pipeline.
- **The source pane shows the caption one sentence to a block**, and under it the two tag lists
  `caption` produced: the scored WD14 list **whole**, with its confidences, then the hosted model's
  list **filtered to what the flow's vocabulary carries**, every chip with its post count. The
  asymmetry is the point — WD14 is scored against the vocabulary it emits, so every tag it returns is
  committable by construction, while the hosted model's is not. **The filter is on the way to the
  page and never on the way to disk**: the artifact under `tags/` still holds every tag the model
  returned, so a tag missing from the pane is one no field could have taken, not one that was lost.
  Both are read-only — the picker at stage ② is still the only path into a field — and an absent
  list simply draws nothing.

### Useful flags, as the parser states them

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

**The Python side is one command and takes no flag:**

```sh
uv sync
```

It installs everything a run needs, because the local tagger's stack and the review surface's server
are declared dependencies. There is no extra to opt into — `[eval]`, the scorer's stack, is the only
one left, and no verb in the pipeline needs it.

**System dependencies — two, and no verb needs both.**

| binary | needed by | absent means |
|---|---|---|
| `ollama` | ① of every flow, for the reader and the hosted tagger | stage ① refuses, naming the command that creates the model |
| `node` | `isekai ui`, to build the bundle once | that verb refuses, naming the install |

*(There were three. `claude` was the first, and v0.22 removed the arm that needed it.)* Each refuses
rather than assuming, and neither is a Python dependency — `uv sync` cannot install either, which is
why each refusal names the command that does.

**To run stage ①**, install [Ollama](https://ollama.com), then, from the repository root:

```sh
ollama create joycaption-beta-one-q4k -f config/joycaption.Modelfile
```

**One command, because there is one model.** It builds the reader from a committed recipe, and the
same alias answers the hosted tagger — which is exactly why the tag prompt is unframed: two calls to
one model must not arrive framed differently.
**`config/joycaption.Modelfile`'s header names the two GGUF files it needs,
with their sha256, their byte counts and their pinned source revision** — they are not in this
repository and `models/` is gitignored, so fetch them into `models/joycaption/` first.

**After creating the reader, check that it can see.** `ollama show joycaption-beta-one-q4k` must
list `vision` under Capabilities **and** print a Projector block. A model whose vision projector is
missing loads, answers fluently, and describes nothing — the failure is silent, and no code here
detects it.

## Development

Run the gate:

```sh
make gate
```

`make -n gate` prints its commands; the root `Makefile` declares them, and CI
(`.github/workflows/ci.yml`) runs `make gate` too.

Its browser half, `tools/typecheck_ui.sh`, runs `vue-tsc --noEmit` over `ui/` and needs
`ui/node_modules/`. It is **not** restored for you — run `npm install` in `ui/` once, as the
review surface already asks.

The suite reads the provisioned tag list, which is gitignored. Fetch it once with
`bash tools/download_models.sh config/vocabulary.json`, or set `ISEKAI_VOCABULARY=absent` to
skip the checks that read it, as CI does.

Every command green, or the work is not done. The suite is **fully offline and deterministic** —
the ComfyUI transport is faked behind a Protocol and no test touches a GPU or the network.
Image quality and identity fidelity are judged live on a pod, by eye.

`CLAUDE.md` carries the process and the change contract; `docs/` is the architecture;
`openspec/specs/` is the living, test-backed spec, and `openspec/changes/` is the work in flight.

## Repository layout

```
isekai/
├── isekai/                    # the package, filed into groups; one README.md each
│   ├── __main__.py            # the path `python -m isekai` resolves — a shim over interface/cli.py
│   ├── foundation/            # run directory & layout names, flow manifest & Schema, refusal
│   ├── pipeline/              # the four staged verbs: caption · sheet · review · generate
│   │                          #   + tagging.py, not a verb: the two tag artifacts caption writes
│   ├── shared/                # image header reader, vocabulary, field validation, atomic write
│   ├── boundary/              # ComfyUI transport, the hosted models, the local tagger, provisioning
│   └── interface/             # the parser & dispatch, the composition, the run's account, ui/
├── evaluation/                # the scorer, beside the package it measures; the only importer
│   │                          #   of the [eval] extra — `uv run --extra eval python -m evaluation`
│   └── baseline/              # its calibration: the subjects' recipe, the labels, the agreement
├── tests/                     # the suite and its fakes
├── models/                    # gitignored; wd14/ holds the tag list and the 467 MB graph
├── flows/summon-anime-wai/    # one flow: flat, named files, and it is immutable
│   ├── flow.json              # the manifest: inputs, vocabulary, model, models, dials, prompt, nodes
│   ├── graph.json             # the API graph
│   ├── schema.json            # the sheet's field list, in prompt order
│   └── caption.briefing.md    # the standing instructions the photograph is read under
├── ui/                        # the review surface: Vue 3 + Vite; dist/ and node_modules/ ignored
│   ├── src/                   # the app; styles.css is a copy of design/, Inter vendored beside it
│   └── design/                # the imported design handoff — read-only, never edited
├── infra/
│   ├── up.sh                  # create pod + attach volume, print the tunnel command
│   └── down.sh                # remove pod, billing stops
├── config/                    # the files the pipeline reads
│   ├── models.json            # the pinned, checksummed manifest — what the stack IS
│   ├── vocabulary.json        # the tag list AND the tagger it indexes — one revision, two digests
│   ├── field_map.json         # tag → sheet field; derived by tools/derive_field_map.py
│   └── joycaption.Modelfile   # the local reader's recipe, for `ollama create`
├── tools/                     # operator tooling, run from the root: `python -m tools.<name>`
│   ├── download_models.sh     # thin driver: plan → wget → verify & land; takes the manifest
│   ├── derive_*.py            # re-derive the manifests and the field map: `make derive`
│   ├── manifest.py            # what every manifest deriver is made of
│   └── typecheck_ui.sh        # the gate's browser half
├── docs/                      # the architecture: principles, decisions, modules, data flow
├── openspec/                  # living specs + changes — authoritative for scope & progress
├── Makefile                   # `make gate`, and `make derive` to re-run the derivers
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
    │                                  │      • provision from config/models.json (verified)
    │                                  │      • exec ComfyUI          (:8188)
    │ 5  poll GET /v1/pods ───────────▶│
    │    ◀──── publicIp + port(22) ────┘
    ▼
  prints:  ssh ...   and   ssh -N -L 8188:localhost:8188 ...

USE IT
  ssh -L 8188:localhost:8188 ...    opens a private tunnel to the pod
  python -m isekai generate --flow summon-anime-wai photo.jpg --server http://127.0.0.1:8188
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
