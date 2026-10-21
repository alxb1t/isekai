# isekai

Turn a photo of a person into an anime image — while keeping the person **recognizable** —
using **open models** on a **rented GPU, on demand**. A reproducible, provider-agnostic
pipeline: build once, spin up a GPU for minutes, convert, tear down.

> **Status: released.** One render path: a **staged pipeline** —
> `python -m isekai import | assign | tag | caption | sheet | review | approve | revise | generate | show | ui | compare` —
> which cleans a photograph into a batch, reads it into prose and tags, fills a sheet of canonical tags from the tags by a table, lets a
> human correct the sheet — at `$EDITOR` or on a local browser surface that knows the vocabulary —
> and renders from it on a stack provisioned from a pinned, checksummed manifest.
> Development follows OpenSpec SDD, and **`openspec/` is authoritative** for what the code does and
> for what is being built next — this banner deliberately names no version, because a forward
> reference here is one reordering away from being wrong.
>
> **The whole pipeline runs on open models.** Stage ① reaches JoyCaption over a local
> [Ollama](https://ollama.com) and nothing here needs an API key or a subscription; stage ② reaches
> no model at all. The flow's manifest names the one model it runs, in a required `model` key, and
> every tracked flow names the same one. *(Until v0.22 there was a second arm over the `claude` CLI,
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
- **Weights:** kept on a RunPod **network volume** that lives for a working window, not baked
  into the image, and provisioned from a **pinned, checksummed manifest** — every artifact is
  addressed by an immutable revision and verified by SHA-256 before anything loads it. The volume is
  **namespaced per project**, so a volume shared with another project has no shared files.
- **Interface:** a headless CLI (`python -m isekai`) that drives ComfyUI over its API. Its
  import rule is [docs D20](docs/decisions.md#d20--the-entry-point-loads-no-third-party-package).

```
Local (your machine)                          RunPod
┌────────────────────────┐                    ┌──────────────────────────────────────┐
│ repo: isekai           │                    │ GPU Pod (ephemeral)                  │
│ isekai render, gpunit  │ ── create pod ───▶ │  runs ghcr image directly (ComfyUI)  │
│ ssh -L 8188 (tunnel)   │ ◀── tunnel :8188   │  (host is already GPU-ready)         │
│ python -m isekai …     │ ── API call ─────▶ │        │ mounts ▼                     │
└────────────────────────┘                    │   ┌─────────────────────────────┐    │
        ▲                                     │   │ volume: /runpod-volume/     │    │
        │                                     │   │   isekai/ ← this project    │    │
        │ ghcr.io/alxb1t/isekai (free)        │   └─────────────────────────────┘    │
        │ (RunPod pulls it as the pod)        └──────────────────────────────────────┘
                                                     │  teardown → pod deleted; volume ends with its window
```

**Lifecycle:** `uv run --env-file .env gpunit volume up` comes first: it opens a **working window**, making the
models volume or extending a live one to its ceiling from now. Then `python -m isekai render <runs>` assembles every prompt, opens a
[gpunit](https://github.com/alxb1t/gpunit) session — a pod from the image `gpunit.toml` pins by digest, the
volume attached, a tunnel checked against the pod's host key — renders each flow, and deletes the pod on every
exit, so billing stops. A pod left behind stops itself at its session's limit, never past `gpunit.toml`'s
3-hour ceiling. The first pod of a window
downloads the models onto the volume, and every later one skips them as verified. `gpunit volume down` ends the
window, and nothing bills once it has. The 4-hour ceiling is not a teardown: past it, the volume bills until
gpunit's next session, `up`, `status`, `down`, `volume up` or `volume down` sweeps it, if that delete succeeds.

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
   ① tag · caption ② sheet  ③ review/approve │  ④ – ⑦ render: pod → tunnel → generate → teardown
                                             ▲
                                   the line where it starts costing
```

### ① Read the photograph

Put the photograph somewhere gitignored — `.inputs/` exists for exactly this, because a photograph an
operator supplies is an input rather than something a run generated, and it holds a person's likeness.
Then:

```sh
python -m isekai tag --flow summon-anime-wai .inputs/me.jpg
python -m isekai caption --flow summon-anime-wai .inputs/me.jpg
```

Two independent verbs. `tag` writes a scored tag list from the local WD14 tagger, then a raw one from
the hosted model. **The local list is what fills the sheet**, so it needs
`uv run python -m isekai.boundary.provision fetch config/vocabulary.json` to have been run.
`caption` writes the prose, a reading aid with no machine consumer; skip it and the review surface
shows *no caption* and this command.

If Ollama is not running, `tag` still writes the WD14 list and refuses only the hosted one, and
`caption` refuses. Neither list is narrowed on disk; the review surface shows the WD14 list, and the
hosted list filtered to what the vocabulary carries.

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
python -m isekai ui     # serves ~/isekai, or the library ISEKAI_LIBRARY names
```

It serves a library rather than a run you name: a batch is a folder in it holding `sources/`, with its
runs in `runs/` beside it. A run reaches the browser when its runs root is a batch's — the batch below
shows how.

Or by hand, which stays a fully working path:

```sh
python -m isekai review --flow summon-anime-wai .inputs/me.jpg   # then edit the file it prints
python -m isekai approve --flow summon-anime-wai .inputs/me.jpg
```

**Only an approved sheet is ever rendered**, and the correction is the single largest measured gain in
this pipeline. `ui` is described under *Correcting the sheets in a browser* below; when you are done
there, stop it with Ctrl-C.

A render you mostly like goes back to a draft from the approval that made it, its seed kept, so the edit
lands on the same composition:

```sh
python -m isekai revise .data/runs/<run>/summon-anime-wai/outputs/001/1840266731.png
python -m isekai review --discard --flow summon-anime-wai .inputs/me.jpg   # drop a waiting draft
```

`isekai revise` takes image paths and checks every one before it writes: each run's flow gets a draft, or
none does. Approval refuses a revision that would only re-render images that exist.

### ④ – ⑦ Render on a rented GPU — this is where it starts costing

```sh
uv run --env-file .env gpunit volume up --yes   # open the window: the models volume, for 4 hours
python -m isekai render .data/runs                # what each approval lacks of its count
uv run --env-file .env gpunit volume down       # when the last batch is done
```

One verb is the whole session: it assembles every prompt of every run under the runs root, rents the pod
(④), tunnels to it (⑤), renders each flow (⑥), and deletes the pod (⑦) on every exit — an error or a Ctrl-C
included. **Billing is per second, from the pod's create to its deletion.** With no request it renders what
each approval lacks of the count Review set, its listed seeds first, and names each unapproved flow it leaves
out. A request is `<flow>=<count>`, or `<flow>=<source>` to render on another flow's latest seeds. The session
stops at its limit — `--limit SECONDS`, or the work's estimate from recorded durations — and prints `session
limit <seconds>s` as it opens; everything it says is shown and appended to `<runs>/../log.txt`.

From the app, a batch's **Render** quotes what renders, the limit and the price at most, and its confirmation
alone rents: the job opens the window, runs `render`, and closes the window unless it was kept open.

Each image lands under the run directory, named for the seed that produced it, beside a provenance
artifact recording the flow and its digest, the seed, the sheet, the digest of the graph actually
submitted, the image the session booted and the runtime it reported. Each render is downloaded as it
finishes: the pod's memory dies with it, and only the models volume persists, for its window.

`python -m isekai generate --flow … <photo>` without `--server` assembles every prompt and stops, which is
how a whole batch is checked before anything is rented; `render` does it first either way, so a malformed
sheet costs nothing rather than a boot.

**If a teardown fails, the pod may still bill:** `render` says so and names `uv run --env-file .env gpunit down`,
which deletes what the session left; `--env-file` hands it the key, since gpunit's CLI reads no `.env`. A session
refused beside a pod an earlier one left ends on the same command. The RunPod MCP confirms no `gpunit-isekai` pod is
left.

### Afterwards

```sh
python -m isekai show .inputs/me.jpg
```

Prints a run's artifacts, versions, what produced each one and every failure record, and names anything below a
flow it does not read. It reaches no model and no GPU, and it works on a checkout that has provisioned nothing.

### A batch of photographs, through both flows

The same steps for a directory of photographs and `summon` and `conjure`, one command per step. Written
for zsh, where `P=(…)` is an array of every file in the directory; in bash, use `"${P[@]}"` for `$P`.

```sh
B=~/isekai/2026-10-19   # a batch: a folder of the library holding sources/
R=$B/runs               # this batch's runs, beside its sources

# the batch: each photograph cleaned to its pixels and orientation, then each flow ticked
uv run python -m isekai import --batch $B ~/Pictures/trip/*.jpg
P=($B/sources/*)        # every photograph in the batch
uv run python -m isekai assign --runs $R --flow summon-anime-wai --flow conjure-anime-wai $P

# ① ② free: the stage verbs take every photograph and both flows at once
uv run python -m isekai.boundary.provision fetch config/reader.json   # once; it skips files already verified
uv run python -m isekai tag     --runs $R --flow summon-anime-wai --flow conjure-anime-wai $P
uv run python -m isekai caption --runs $R --flow summon-anime-wai --flow conjure-anime-wai $P
uv run python -m isekai sheet   --runs $R --flow summon-anime-wai --flow conjure-anime-wai $P

# ③ free: the library in a browser -- the batch's hub, then Review next
uv run python -m isekai ui
uv run python -m isekai show --runs $R $P

# ④ – ⑦ metered: the window's volume, then one pod renders both flows, and is deleted on every exit
uv run --env-file .env gpunit volume up --yes
uv run python -m isekai render $R conjure-anime-wai=2 summon-anime-wai=1
uv run --env-file .env gpunit volume down   # once no other batch follows
```

- **`import` cleans as it copies**: a source keeps its pixels and its orientation, its colour in sRGB,
  and nothing else; a HEIC or a WebP becomes a JPEG or a PNG, and a RAW is refused with its fix.
- **`isekai assign` ticks a flow**: it gives each source's run that flow's empty directory, and
  `--remove` takes away one that holds no work yet.
- **`ui` takes no arguments.** It serves every batch of the library; the batch's hub shows each
  photograph's stage in each flow, and *Review next* walks one flow's unapproved sheets, then the next
  flow's. Stop it with Ctrl-C.
- **`render` takes a count per flow**, and renders every run under `$R`.
- **`show` takes no `--flow`**: it reports every flow a run holds.

### Correcting the sheets in a browser

Step ③ by hand edits a JSON file in a text editor. `isekai ui` does the same work on a surface that
knows the vocabulary — canonical spelling, the post count behind every tag, and a live token count
against the encoder's 77-token window, none of which a text editor can tell you:

```sh
python -m isekai ui
```

It opens the library — `~/isekai`, or the directory `ISEKAI_LIBRARY` names, created when absent and
refused inside this repository outside `.data/` — prints a URL and blocks. Home lists the batches by
their newest file, and *New batch* imports photographs chosen in the file dialog, each with its own
upload bar. A batch's hub shows each photograph's stage in each flow `config/ui.json` offers: a tick
runs `isekai assign`, and *Prepare* runs `tag`, `caption` and `sheet` over what changed as one job,
the CLI's own verbs as children with `--progress json`, its cells moving live over `/events`. Review
corrects one sheet, its ④ setting how many images it renders and at which seeds, and Approve moves to the
next. **Render** opens a dialog quoting what renders and its price at most; **its confirmation is the one
act on the page that spends money**, and the session view shows it to *Nothing is billing.* Renders shows
each source's images by flow and approval, each version a revision or a re-roll of the one it came from,
and an image beside the sheet it came from. **Revise** (⌥E), from the large view or over a selection, runs
what `isekai revise` does and opens Review on each draft with the render beside the photograph; **Compare**
(C) shows a seed under two versions and the fields that changed. Every screen has
its own URL, so a reload lands where it was. Stop it with Ctrl-C, which interrupts a running job; mid-render
it says so and waits, up to the teardown's estimate and one volume verb, for the pod's teardown and the
window's close — killing it then can leave the window open, and a wait that runs out names `gpunit volume down`.
Prepare reaches the local Ollama, and refuses before it starts when nothing answers there.

- Opening a sheet with no draft writes one through `review`, as the verb would.
- It needs **node**, to build the bundle: `npm install` in `ui/` the first time. The bundle is built on
  demand, and a missing toolchain refuses naming what installs it. Nothing else has to be installed —
  the server is a declared dependency of this project, as is the local tagger's stack.
- `review` and `approve` keep working exactly as before. They are deprecated as *guidance*, never as
  code — deleting the hand path would make ③ a single point of failure for the whole pipeline.
- **The source pane shows the caption one sentence to a block**, and under it the two tag lists
  `tag` produced: the scored WD14 list **whole**, with its confidences, then the hosted model's
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
- `--count COUNT` — how many renders per photograph per flow, seeds drawn (default: the approval's count, else 1).
- `--seed SEEDS` — render exactly this seed; repeatable, and not combinable with `--count`.
- `--seeds-from FLOW` — render each run on the seeds of that flow's latest render; not combinable with
  `--count` or `--seed`. A flow whose approval is a copy made from another approval than the one those
  renders came from is refused before any boot.
- `--in-step-with FLOW` — refuse a flow whose approval is a copy of an older approval than that flow's latest, and
  render nothing; `render` runs it before the pod for a source it renders first in the same session.
- `--from FLOW` — on `approve`: copy that flow's latest approval under each `--flow`, recording the source;
  a copy already of the source's latest writes nothing, and any other approval is copied over under the next
  number.
- `--server SERVER` — the ComfyUI endpoint, reached through the tunnel; **omit it to assemble every
  prompt and stop without rendering**, which is how a whole batch is checked before anything is
  rented.
- `--batch BATCH` — on `import`: the batch directory, made when absent; otherwise the files join its
  `sources/`. A file with a source's bytes is skipped, and one with a taken name becomes `<stem>-2`.
- `--remove` — on `assign`: delete each flow's directory instead, refusing one that holds work.
- `--discard` — on `review`: delete each flow's waiting draft instead, refusing a flow whose highest
  number is approved.
- `--progress json` — on `tag`, `caption` and `sheet`: one JSON line per item's start and end on
  stdout, the prose on stderr. It is how Prepare reads a stage's progress.
- `--new-version` — on `caption`, `tag`, `sheet` and `review`, write the next numbered version of
  what that verb writes, and nothing another verb writes, instead of doing nothing. Every stage decides whether it is done by a directory listing, so re-running one is
  free.

## Setup

**Prerequisites:**

1. A **RunPod account** with an API key and a small prepaid balance.
2. Nothing else: `uv run --env-file .env gpunit volume up` makes the window's **network volume** from
   `gpunit.toml`'s `volume_gb` and `volume_ceiling`, and gpunit creates each pod of the window in its data centre.

Then `cp .env.example .env` and fill in the API key; it is gitignored and holds every secret. gpunit makes
each session's SSH key itself, under the gitignored `.gpunit/`.

**The Python side is one command and takes no flag:**

```sh
uv sync
```

It installs everything a run needs, because the local tagger's stack and the review surface's server
are declared dependencies. There is no extra to opt into, and the evaluator adds no package to the
list.

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
uv run python -m isekai.boundary.provision fetch config/reader.json
ollama create joycaption-beta-one-q4k -f config/joycaption.Modelfile
```

**The first fetches, the second builds.** `config/reader.json` pins the GGUF model and its vision
projector by digest; `fetch` lands both in `models/joycaption/` and verifies them. `ollama create`
builds the reader from the committed recipe, and the same alias answers the hosted tagger — which is
exactly why the tag prompt is unframed: two calls to one model must not arrive framed differently.

**Before its first call, `caption` and `tag` check the model.** Ollama's own record of it must name
the model and projector files `config/reader.json` pins, or the verb refuses and spends no attempt. A
model whose vision projector is missing loads, answers fluently and describes nothing; its record
names no projector, so it is refused rather than run.

## Development

Run the gate:

```sh
make gate
```

`make -n gate` prints its commands; the root `Makefile` declares them, and CI
(`.github/workflows/ci.yml`) runs `make gate` too.

Its browser half, `tools/typecheck_ui.py` and `tools/test_ui.py`, runs `vue-tsc --noEmit` and
vitest over `ui/` and needs `ui/node_modules/`. It is **not** restored for you — run `npm install` in
`ui/` once, as `isekai ui` already asks. The browser tests in `tests/e2e/` drive Chromium through
Playwright; fetch it once with `make browsers`. They serve the app on the suite's doubles through
`ISEKAI_WIRING`, so they reach no model either.

The suite reads the provisioned tag list, which is gitignored. Fetch it once with
`uv run python -m isekai.boundary.provision fetch config/vocabulary.json`, or set `ISEKAI_VOCABULARY=absent` to
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
│   ├── pipeline/              # the staged verbs: caption · tag · sheet · review · generate
│   │                          #   tagging.py is `tag`: the two tag lists
│   ├── shared/                # image header reader, vocabulary, field validation, atomic write
│   ├── boundary/              # ComfyUI transport, the hosted models, the local tagger, provisioning, the pod's start
│   └── interface/             # the parser & dispatch, the composition, the run's account, ui/
├── evaluation/                # the cohort evaluator and attribute recall, beside the package —
│                              #   `uv run python -m evaluation <runs> --cohort <dir>`,
│                              #   `uv run python -m evaluation.recall <runs>`
├── tests/                     # the suite and its fakes
├── models/                    # gitignored; wd14/ holds the tag list and the 467 MB graph
├── flows/summon-anime-wai/    # one flow: flat, named files, and it is immutable
│   ├── flow.json              # the manifest: inputs, vocabulary, model, tagger, models, dials, prompt, nodes
│   ├── graph.json             # the API graph
│   ├── schema.json            # the sheet's field list, in prompt order
│   └── caption.briefing.md    # the standing instructions the photograph is read under
├── flows/control-anime-wai/   # summon's files with the face dials at 0, held equal by a test
├── ui/                        # the app: Vue 3 + Vite + vue-router; design/spec.md; dist/ and node_modules/ ignored
│   ├── src/                   # the app; styles.css is the vendored stylesheet, Inter beside it
│   └── design/                # spec.md, the design the app is built to
├── gpunit.toml                # the render session's GPU: the pinned image, cards, floors, ceiling, volume
├── config/                    # the files the pipeline reads
│   ├── models.json            # the pinned, checksummed manifest — what the stack IS
│   ├── image.json             # the pod image's digest, the same gpunit.toml boots, and its build record
│   ├── reader.json            # the reader's model and projector, by digest, per alias
│   ├── vocabulary.json        # the tag list AND the tagger it indexes — one revision, two digests
│   ├── field_map.json         # tag → sheet field; derived by tools/derive_field_map.py
│   └── joycaption.Modelfile   # the local reader's recipe, for `ollama create`
├── tools/                     # operator tooling, run from the root: `python -m tools.<name>`
│   ├── derive_*.py            # re-derive the manifests, the field map and image/: `make derive`
│   ├── manifest.py            # what every manifest deriver is made of
│   ├── image_record.py        # the build record: each copied file's SHA-256, for config/image.json
│   ├── npm_ui.py              # the gate's browser half: run a ui/ script, or refuse
│   ├── typecheck_ui.py        # the gate's browser half: the types
│   └── test_ui.py             # the gate's browser half: vitest
├── docs/                      # the architecture: principles, decisions, modules, data flow
├── openspec/                  # living specs + changes — authoritative for scope & progress
├── Makefile                   # `make gate`; `make derive` and `make drift` re-run the derivers
├── image/                     # the pod's Python environment: a locked uv project, derived
├── Dockerfile                 # ComfyUI + CUDA PyTorch (cu128; no models baked in)
├── docker-compose.yml         # run the image on any GPU host / local testing
├── .github/workflows/         # CI: the gate; the weekly drift check; the image, on request
├── CLAUDE.md                  # repo facts + the change contract, for agents
└── .env.example               # shape only — no secrets, no paths
```

## Provisioning flow — how `isekai render`, gpunit and `pod_start.py` fit together

They run in **different places at different times**. `isekai render` downloads and runs nothing itself: it
opens a gpunit session, which makes **API calls** and checks the pod's SSH host key; **RunPod's GPU host**
pulls the image and runs it, and inside the container gpunit's `boot.sh` runs the image's
**`isekai/boundary/pod_start.py`**.

| Script | Runs **where** | Runs **when** | Does what |
|---|---|---|---|
| `python -m isekai render` | **on your machine** | when you want renders | assembles every prompt, opens a gpunit session on `gpunit.toml`, waits for ComfyUI through the tunnel, renders each flow, closes the session on every exit |
| `boot.sh` (gpunit's) | **inside the container, on the pod** | every container boot (the image's entrypoint) | arm the stop at the session's limit → authorize the session's key → start `sshd` on a host key made at boot → print its fingerprint → run `pod_start.py` without the API key; every way out stops the pod |
| `pod_start.py` | **inside the container, on the pod** | after `boot.sh`'s steps | prove the volume → provision the models onto it with `provision.py fetch` → put ComfyUI's files in memory → `exec` ComfyUI |

```
BUILD TIME (once, or when the image changes)
  Dockerfile + pod_start.py + gpunit's boot.sh  ──▶  CI builds on request  ──▶  GHCR

RENDER TIME (every session — this is isekai render)

  YOUR MACHINE                     RUNPOD                              GHCR
  ────────────                     ──────                              ────
  python -m isekai render <runs> <flow>=<count|source> …
    │ 0  assemble every prompt; nothing is rented yet
    │ 1  gpunit.session(gpunit.toml): refuse beside a recorded or listed pod,
    │    create the pod in the volume's data centre ──▶ control plane
    │                                  │ 2  place the pod on a GPU host
    │                                  │ 3  pull image ───────────────▶ ghcr image
    │                                  │ 4  ENTRYPOINT boot.sh -- pod_start.py:
    │                                  │      • arm the stop (the session's limit, at most gpunit.toml's ceiling)
    │                                  │      • own host key, start sshd (:22), print it
    │                                  │      • /opt/ComfyUI/models → <volume>/isekai
    │                                  │      • provision from config/models.json (verified)
    │                                  │      • ComfyUI's files → /dev/shm (memory)
    │                                  │      • exec ComfyUI           (:8188)
    │ 5  check the host key against the printed fingerprint, open the tunnel
    │ 6  wait for /system_stats, then generate each flow through 127.0.0.1:8188
    ▼
  every exit: the session deletes the pod and every listed pod of the project ──▶ billing stops
  the pod itself: the stop fires at the session's limit, or when the start ends ──▶ pod stops
                                    (the window's volume + GHCR image persist)
```

## Cost

On-demand and cheap: an RTX 4090 at ~$0.34–0.69/hr (per-second billing), a free public-repo
container image on GHCR, and about $0.02 for the models volume over a 4-hour window of 50 GB; nothing bills
once `gpunit volume down` closes the window. A window left open bills past its ceiling until gpunit's next
session, `up`, `status`, `down`, `volume up` or `volume down` sweeps the volume, if that delete succeeds. A full working pipeline costs on the order of **$10 or less** to stand up.

## License

[Apache-2.0](LICENSE). Model weights are licensed separately by their publishers.
