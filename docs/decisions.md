# Decisions

The choices in force today, each with its reason and the change that made it. A decision states a
choice and why; it never repeats a value a file already declares — it names the file instead. When a
change overturns a decision, it edits this page; the change's own `design.md` keeps the history.

## The product

### D0 · Self-hosted, open-source, open models

**The product is self-hosted, open-source, and runs on open models only.** No SaaS and no closed
provider API: every model it runs is open-weight, on hardware the operator controls — a local model
server, a rented GPU. The repository is public, under Apache-2.0.

- **Why:** learning to run the whole stack is the point, and a closed API would hide exactly the part
  worth learning.
- **Made by:** the project's founding decision.

### D29 · What `summon` preserves

**Identity is face, hair, clothes and pose, held together. A tattoo is outside it.**

- **Why:** these are what a viewer checks first. The graph carries the face and the pose, and the
  approved sheet's tags carry hair and clothes
  ([D10](#d10--the-face-and-the-pose-are-carried-by-the-graph)). A tattoo is local and arbitrary;
  neither holds it, and bundling it would make every version a research version.
- **Made by:** the project's founding decision.

### D30 · A public repository, for learning

**The deliverable is a public repository, not a hosted service. Its payoff is learning and a
portfolio piece, not product polish.**

- **Why:** a portfolio piece is read, not signed up for, and tuning comes after the stack runs
  end to end.
- **Made by:** the project's founding decision.

## Stages and verbs

### D1 · Stage ① is one verb

**`caption` writes the prose, then the WD14 tags, then the hosted tags, for each flow named.**

- **Why:** one command for everything the photograph is read into. The order was chosen to isolate
  failures when the sheet was built from prose.
- **Known consequence:** the sheet now reads WD14's tags, so an unreachable Ollama stops the sheet's
  input too. The caption/tag split separates them.
- **Made by:** `0020`.

### D2 · A table fills the sheet

**The sheet is filled from WD14's tags by one authored table, `scripts/field_map.json`, read from tag to
field. No model decides a sheet.**

- **Why:** WD14's tags are all in the vocabulary, because its label file *is* the vocabulary, and a table
  cannot invent a tag. The router placed 73% of the tags offered, and 90% of those survived review.
- **Made by:** `0021`.

### D3 · The hand path stays

**`review` and `approve` stay working verbs.** The review UI is the guided path; the hand path stays.

- **Why:** deleting it would make stage ③ a single point of failure for the whole pipeline.
- **Made by:** `0018`.

### D4 · The review UI is stage ③ alone

**No upload, no captioning, no generate button. Nothing in the browser spends money.**

- **Why:** review is where a person decides quality. A button that spends would put the paid stage
  behind a web page.
- **Made by:** `0018`.

## Models

### D5 · One arm

**JoyCaption reads the photograph and WD14 tags it, both on this machine. No hosted provider.**

- **Why:** [D0](#d0--self-hosted-open-source-open-models) — and the sheet needs nothing a closed
  model offered: the router places 73–77% of the tags with the local tagger and the table alone.
- **Made by:** `0022`.

### D6 · Ollama at a fixed local address

**Ollama is reached over plain HTTP at a fixed local address, never through a proxy.** The address is a
constant, with no flag and no environment variable. The call uses Ollama's own `/api/generate`, which
carries the sampling options the OpenAI-compatible endpoint cannot.

- **Why:** a photograph's destination must not be changeable by accident — an exported `http_proxy`
  once sent every photograph off the machine.
- **Made by:** `0019`.

### D7 · WD14 is one artifact in two files

**WD14's model and its label file are pinned to one revision and verified together before the first
inference** — `scripts/vocabulary.json`.

- **Why:** row N of the label file names output N of the model. A pair from two revisions mislabels
  every tag, silently.
- **Made by:** `0020`.

### D8 · The base

**Both flows draw on WAI-illustrious-SDXL.** A flow on another base is a new flow, named for that base
([D15](#d15--a-flow-is-named-for-what-it-is)). The checkpoint and its digest belong to each flow.

- **Why:** the sheet's tags are how a render is steered, so the base's grasp of tags is the ceiling. Its
  LoRA ecosystem is what keeps the style library and a character LoRA within reach.
- **Made by:** `0010`.

## The render

### D9 · Composition comes from noise

**The photograph never enters the latent: the render starts from an empty latent at full denoise.**

- **Why:** seeding the latent with the photograph blurred every render — linework came out about ten
  times weaker than the photograph's own. Starting from noise clears the style bar three times over.
- **Made by:** `0013`; `0014` deleted img2img.

### D10 · The face and the pose are carried by the graph

**The face and the pose are carried by the graph — InstantID's face embedding, OpenPose's pose — never
by words in a prompt. Hair and clothes are carried by the approved sheet's tags. A flow that takes no
photograph makes no identity claim.**

- **Why:** a face cannot be described into a render, so the embedding carries it and the pose leg carries
  the body. Hair and clothes are what tags name well, and a person corrects them at review.
- **Made by:** `0013`, `0017`.

### D11 · The photograph is scaled once

**The photograph is scaled once, before any node reads it, from its own header. It is refused past the
aspect limit, never clamped.** The numbers are `shared/image.py`'s.

- **Why:** every node must see one pixel grid, and no node can work out the size itself. A clamp would
  distort the aspect ratio.
- **Made by:** `0010`, `0011`.

### D12 · The flow owns the prompt's fixed words

**The quality words and the negative prompt belong to the flow; the subject's tags come from the
approved sheet.**

- **Why:** the prompt's fixed words are part of the flow's pinned configuration, changed only by a new
  flow or a recorded re-pin. The subject is the person's, corrected at review.
- **Made by:** `0016`, `0025`.

### D13 · The seed reproduces the graph, not the pixels

**The seed is recorded, and `--seed` reproduces the submitted graph, not the pixels.**

- **Why:** GPU computation does not promise bit-identical output, and identity does not need it to. One
  integer is the whole reproducibility contract.
- **Made by:** `0013`.

## Flows

### D14 · A flow is one flat directory

**A flow is one flat directory of named files — `flow.json`, `graph.json`, `schema.json`,
`caption.briefing.md` — and it shares nothing with another flow.**

- **Why:** the pin covers only the files directly in the directory, so a nested file would escape the
  freeze. Sharing nothing means a change to one flow can never change another.
- **Made by:** `0016`, `0022`.

### D15 · A flow is named for what it is

**A flow's identifier is `<verb>-<style>-<base>`, with `-v2` added only for a second generation of the
same combination.**

- **Why:** the base is in the name because other bases are candidates. A name describing the
  implementation behind a flow, rather than the flow, stops meaning anything when that implementation
  changes.
- **Made by:** `0022`.

## Runs

### D16 · A run is keyed by the photograph's bytes

**A run's id is a prefix of the photograph's digest plus a readable slug. Opening the same photograph
again resumes the same run.**

- **Why:** the photograph is the one thing every flow shares, and its bytes are what identify it. A
  renamed file is the same run; a re-exported one is not.
- **Made by:** `0013`, `0016`.

### D17 · Input above, flow below

**`runs/<input>/<flow>/<stage>/`.**

- **Why:** adding a flow adds one subtree, and no flow can read another's artifacts.
- **Made by:** `0016`.

### D18 · Runs stay out of what git tracks

**Everything a run produces lives in its runs root — `.data/runs` by default, which git ignores. A runs
root inside the repository must sit under `.data/`; one outside it may sit anywhere.**

- **Why:** a run holds a copy of the photograph, so a person's likeness is in it by construction.
  Anywhere else inside the repository, those files would be one `git add` from being published.
- **Made by:** `0014`, `0018`.

## Code and environment

### D19 · One place builds the components

**`wiring.py` builds the components, and the CLI and the review UI both use it.**

- **Why:** the runs-root check ([D18](#d18--runs-stay-out-of-what-git-tracks)) and the choice of
  reader, tagger and transport happen in one place, so neither front end can skip them.
- **Made by:** `0015`, `0018`.

### D20 · The entry point loads no third-party package

**The entry point loads no third-party package at module scope; a package is imported inside the verb
that needs it.**

- **Why:** `show` and the other free verbs work on a checkout that has installed none of the models.
- **Made by:** `0025`.

### D21 · Retries follow what can fail

**A stage that calls a local model may retry a dropped call. A deterministic stage gets one attempt, and
so does the paid render.** The numbers are `run.py`'s `BUDGETS`.

- **Why:** a deterministic stage fails the same way twice, while a call to the local model server can
  drop and succeed on the next attempt. The paid stage is never retried on its own.
- **Made by:** `0013`, `0023`.

### D22 · Dependencies are declared and pinned

**Runtime dependencies are declared and pinned exactly. `[eval]` is the only optional extra.**

- **Why:** an optional extra that the gate's `uv sync` is not told about gets uninstalled — the tagger
  disappeared on every gate run. The pins decide what a second machine installs.
- **Made by:** `0025`.

### D23 · System dependencies refuse rather than being assumed

**Ollama and node are system dependencies. A missing one refuses, naming what installs it.**

- **Why:** `uv sync` cannot install either, so the refusal must name the command that does.
- **Made by:** `0018`, `0019`.

### D24 · The review UI serves only this machine

**The review UI serves only on the local loopback address, and checks `Host` and `Origin` on every
request.** A request with no `Origin` header is let through — a known, low risk.

- **Why:** the page shows personal photographs and writes approvals. Nothing off the machine, and no
  other site open in the browser, may reach it.
- **Made by:** `0018`, `0023`.

### D25 · Option shortcuts match the physical key

**UI shortcuts using Option match `event.code` and call `preventDefault()`.**

- **Why:** on macOS, Option types characters — `Option+Space` would put an invisible non-breaking space
  into a tag field — and Space also presses a focused button.
- **Made by:** `0021`.

## Infrastructure

*May change with the move to serverless rendering, which is being researched.*

### D26 · Renders run on a rented GPU

**A RunPod pod runs this project's own ComfyUI image, with PyTorch built for CUDA 12.8.**

- **Why:** the render is the only work that needs a GPU, and renting by the second costs less than owning
  one. The Blackwell GPU has no kernels in older CUDA builds.
- **Made by:** the founding setup.

### D27 · The models live on a network volume

**The volume holds exactly the manifest. A pod refuses to start on a volume below the capacity floor** —
the floor is `start.sh`'s.

- **Why:** re-downloading every session costs more than the idle rent, and a volume filled only from the
  manifest is clean by construction. A missing mount would fall through to the container disk: it would
  render, bill, and lose everything at teardown.
- **Known break:** the floor `start.sh` declares is larger than the real volume, so a boot on it holds and
  bills without rendering.
- **Made by:** `0009`, `0011`.

### D28 · The image carries code, the volume carries weights

**The image lives on GHCR with no weights baked in, and `up.sh` alone creates pods. Metered work runs on
a release-candidate tag.**

- **Why:** only `up.sh` knows the image, the volume mount and the SSH key, so a pod made any other way has
  no models and no way in. A release-candidate tag stops a pre-release build from replacing the image a
  rollback depends on.
- **Made by:** `0010`, `0011`.
