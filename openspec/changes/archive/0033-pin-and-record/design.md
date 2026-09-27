# Design — 0033 pin and record

How the pod image, its environment, CI and the reader's model are pinned, and what each artifact records.
**Verdict: `feasible-with-caveats`** — the lock resolves today's package versions, so the acceptance judges
the renders by eye ([D8](#d8)). Every file, symbol and line below was re-checked at `main` `801ffec`.

## Context

- **The image:** `Dockerfile:2` `FROM nvidia/cuda:12.4.1-devel-ubuntu22.04` (a tag); `:13` uv from `:latest`;
  `:29` `uv venv --python 3.12` (no patch); `:32-33` the torch stack from the cu128 index; `:36` and `:54-55`
  `uv pip install -r` with no lock; `:45` CPU `onnxruntime==1.20.1`, then controlnet_aux's list installs an
  unpinned `onnxruntime-gpu` over it. ComfyUI, ComfyUI_InstantID and comfyui_controlnet_aux are pinned by
  commit (`:21-23`, `:39-42`, `:48-51`).
- **The boot:** `infra/up.sh:16` defaults `RUNPOD_IMAGE` to `ghcr.io/alxb1t/isekai:latest`; `:68` writes
  `.runpod_pod_id`; `:96-117` polls the API until port 22 is mapped — nothing contacts SSH.
  `infra/down.sh:18-19` removes `.runpod_pod_id` on HTTP 204. `docker-compose.yml:4` tags local builds `:latest`.
- **The build:** `.github/workflows/build-image.yml:8-16` builds on every push to `main` and on dispatch;
  `:62-66` pushes one tag and reads no digest. Every `uses:` in both workflows is a major tag; both run on
  `ubuntu-latest`; `ci.yml:18-20` pins no uv, `:33` Node `'22'`.
- **The reader:** the alias is a bare string in both flows; the GGUF digests live in a comment
  (`config/joycaption.Modelfile:13-21`). Ollama's on-disk manifest names each layer's digest by media type,
  and a GGUF layer's digest is the file's own sha256. `isekai/boundary/ollama.py:24-29` reads no environment.
- **The records:** `READER_OPTIONS` (`isekai/pipeline/caption.py:82-87`), `TAGGER_OPTIONS`
  (`isekai/pipeline/tagging.py:90-96`) and `FLOOR` (`isekai/boundary/wd14.py:105`) are recorded nowhere;
  `manifest_digest` (`isekai/foundation/flow.py:515`) has no production caller; the render's `sheet_version`
  is the approval's number (`isekai/pipeline/generate.py:412`, `:460`) and the prompt has none; the draft
  copies only `vocabulary` and `fields` (`isekai/pipeline/review.py:180-187`).
- **The transport:** `ComfyTransport` declares `upload_image`, `submit`, `history` and `view` (`isekai/boundary/comfy/contract.py:31-52`); ComfyUI at
  `250b2e9` serves `GET /system_stats` with `system.comfyui_version`, `python_version`, `pytorch_version`.

## Goals / Non-Goals

**Goals**

- A pod runs one image, named by digest, whose Python environment is locked.
- The reader's model is checked against its pinned files before it answers.
- Every artifact records the options, floor, flow and image that shaped it.

**Non-Goals**

- Anything the [proposal](proposal.md#not-in-this-change) sets out.
- Reproducing the environment behind past renders: it was never recorded.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | CI's actions by commit, its runner, uv and Node pinned; uv 0.12.19 everywhere | a major tag moves | leaving CI out of the pin |
| [D2](#d2) | base and uv by digest; the Python environment a locked uv project, `image/`; builds on request only | the image digest is the pin, the lock makes a rebuild the same | freezing from a built image; pinning apt |
| [D3](#d3) | `config/image.json` holds the digest; `up.sh` boots it and nothing else | a moving tag is not a pin | resolving `:latest` at boot |
| [D4](#d4) | `config/reader.json`, derived, keyed by alias; the alias checked once per model at its first call | the files behind an alias shape the prose | the manifest digest `/api/tags` reports |
| [D5](#d5) | the records, where each acts | the principle's *not yet held* list | recording in `show` only |
| [D6](#d6) | new keys optional under version 1; a changed meaning is a new key | a bump makes every old run unreadable | bumping each kind |
| [D7](#d7) | D6, D28, D32 and the principles updated | `docs/` records what is in force | |
| [D8](#d8) | one metered acceptance: the whole flow, both flows, every pin in place | the operator's ask | a render-only proof |
| [D9](#d9) | a minor, one feature | the record half adds run-file keys | a patch |
| [D10](#d10) | `docs/pins.md` — what pins buy and how each is moved, written after the acceptance | the principle says *why*; nothing says *how* | restating the principle; a docs patch after release |

### D1

**CI and the toolchain.**

- Every `uses:` in `.github/workflows/ci.yml` and `build-image.yml` names a commit SHA, the release in a
  comment: `actions/checkout@<sha> # v4.x.y`.
- `runs-on: ubuntu-24.04` in both. `astral-sh/setup-uv` gets `version: "0.12.19"`; Node an exact `22.x.y`.
- `pyproject.toml` gains `[tool.uv] required-version = "==0.12.19"`. The operator's uv is 0.8.24, so it is
  upgraded first; `uv.lock` is re-locked only if `uv lock --check` fails under 0.12.19.

### D2

**The image's inputs, and how it is built.**

- `FROM nvidia/cuda:12.4.1-devel-ubuntu22.04@sha256:<digest>`; `COPY --from=ghcr.io/astral-sh/uv:0.12.19@sha256:<digest>`.
  The build resolves each digest once (`docker buildx imagetools inspect`) and writes it into the `Dockerfile`.
- **`image/` is the pod's Python environment as its own uv project**, not a workspace member:
  - `image/pyproject.toml` — `[tool.uv] package = false`; `environments = ["sys_platform == 'linux' and platform_machine == 'x86_64'"]`;
    the torch stack pinned from the cu128 index (`[[tool.uv.index]]` with `explicit = true`, `[tool.uv.sources]`);
    `insightface==0.7.3`; ComfyUI's and comfyui_controlnet_aux's lists at their pinned commits;
    `build-constraint-dependencies` pinning insightface's build requirements.
  - **`onnxruntime-gpu` alone.** The CPU `onnxruntime` pin goes: both ship one module, and the -gpu build is
    the one installed last today and the one both custom-node packs ask for.
  - `image/uv.lock` carries every hash; `image/.python-version` holds the 3.12 patch uv 0.12.19 installs.
  - The `Dockerfile` copies `pyproject.toml`, `uv.lock` and `.python-version` one by one (`tests/test_infra.py:460` wants each source a file),
    sets `UV_PROJECT_ENVIRONMENT=/opt/ComfyUI/.venv`, and runs `uv sync --locked`. No `uv venv`, no `-r`.
- **`tools/derive_image_project.py`** reads the pinned commits from the `Dockerfile`, fetches both upstream
  lists, writes `image/pyproject.toml`'s dependencies — the pins above win over an upstream duplicate, a repeat
  (`yapf`) is written once, `onnxruntime` is left out — and runs `uv lock --project image`. It joins
  `make derive`, and the `Makefile`'s final `git diff --stat` covers `image/`. It writes no provisioning
  manifest, so `tests/test_derivation.py`'s list of manifest derivers does not take it.
- **`build-image.yml` runs on `workflow_dispatch` only**, with a required tag that is not `latest`; the build
  step gets an `id`, and a last step writes `steps.<id>.outputs.digest` to the job summary.
- **`boot-timing`:** `start.sh` prints `date -u` before each step — the SSH key, `sshd`, `provision`, the
  download, ComfyUI's `exec`; `up.sh` prints the UTC time the pod was created and the time the API reported
  port 22 mapped.

### D3

**The pin.**

```
config/image.json ──▶ up.sh ──▶ pod (image@sha256:…)
                         └──▶ .runpod_pod_image ──▶ generate records it
                                 down.sh removes it on 204
```

- `config/image.json`: `{"image": "ghcr.io/alxb1t/isekai", "tag": "<rc tag>", "digest": "sha256:<…>"}`.
  The tag is for a reader; the digest is the pin.
- `up.sh` reads it with `jq`, boots `<image>@<digest>`, and writes that reference to `.runpod_pod_image`
  beside `.runpod_pod_id`. The `RUNPOD_IMAGE` default and override go, with `.env.example:15-18`.
- `down.sh` removes `.runpod_pod_image` with `.runpod_pod_id`. `.gitignore` names it beside `:55`.
- `docker-compose.yml` tags a local build `isekai:local`.
- The digest comes from the build phase 3 dispatches; moving it later is a re-pin inside a change.

### D4

**The reader's pin.**

- **`config/reader.json`** is a provisioning manifest (`pinned`, `publishers`, `entries`) plus `aliases`:
  `{"joycaption-beta-one-q4k": {"model": "joycaption/<Q4_K>.gguf", "projector": "joycaption/<mmproj>.gguf"}}`,
  each naming an entry's `dest`. `concedo` is its publisher. `provision.Manifest` gains `aliases` as
  `NotRequired`; `provision.READER_MANIFEST_PATH` joins `tests/test_package_paths.py`.
- **`tools/derive_reader.py`** derives it through `tools/manifest.py` from concedo's repository at
  `acfe6bf78ae4e411cd5c7c8f4a71ba01f26a5b97`, and joins `make derive` and `tests/test_derivation.py`.
- `bash tools/download_models.sh config/reader.json` provisions the files into `models/joycaption/`, where
  the Modelfile's `FROM` lines look. The Modelfile's comment points at the manifest instead of listing digests.
- **The check**, in `isekai/boundary/ollama.py`: read `~/.ollama/models/manifests/registry.ollama.ai/library/<model>/latest`
  — a constant root, no environment, per `ollama.py:24-29` — and compare the layers whose media type is
  `application/vnd.ollama.image.model` and `…image.projector` with the manifest's digests. Memoised per model,
  run inside `OllamaReader.read` and `OllamaTagger.tag` before `ask`, so a completed stage never reads it.
  The root is injectable, so the suite reads a fixture.
- **Refusals, each spending no attempt:** no entry pins the model — name `config/reader.json`; no record at the
  root — name the path and `ollama create joycaption-beta-one-q4k -f config/joycaption.Modelfile`; a layer
  that differs — name both digests, then `bash tools/download_models.sh config/reader.json` and the create command.
- `Reading` and `Tagging` gain the verified `artifacts` (dest → digest record) and `pinned=True`.

### D5

**The records.**

| artifact | gains | from |
|---|---|---|
| caption producer | `options`, `artifacts`, `pinned: true` | `READER_OPTIONS`; [D4](#d4) |
| tags producer | `options`, `artifacts`, `pinned: true` | `TAGGER_OPTIONS`; [D4](#d4) |
| wd14 producer | `floor` | `wd14.FLOOR` |
| sheet | `flow_digest`; producer `floor` when the list records one | `sheet()` gains a required `flow_digest` keyword from `cli.py` |
| draft, approval | `schema_document`, `field_map` where the sheet records them | the sheet, then the draft |
| prompt | `flow_digest`, `sheet` | `manifest_digest(flow.id, flow.path.parent)`; the approval's `sheet` |
| render | `flow_digest`, `sheet`, `image`, `pinned`, `runtime` | the same; `.runpod_pod_image`; `/system_stats` |

- **`sheet` replaces `sheet_version` in new renders**, and `Render`'s `sheet_version` becomes `NotRequired`
  for old sidecars ([D6](#d6)). The outputs directory stays the approval's number; `run_view.rendered`'s
  docstring says *by approval*.
- **The runtime:** `ComfyTransport` gains `system_stats() -> dict`, a `GET` under `_reported`;
  `FakeComfyClient` answers it. `render()` gains required keywords `image: str | None` and
  `runtime: Callable[[], Runtime]`; `cli._generate` reads `.runpod_pod_image` and passes a thunk memoised
  per session. `render` calls the thunk after `if not wanted: return []` (`generate.py:417`), so a complete
  batch reads nothing.
- `runtime` is `{"comfyui_version", "python_version", "pytorch_version"}`, taken from the report's `system`.

### D6

**The version rule, written down as D32.** A version moves when a file written before the change could be
misread after it. A key that only records cannot be misread by its absence, so every key [D5](#d5) adds is
`NotRequired` under version 1. `sheet_version` changing meaning would be misread, so the sheet's number is a
new key, `sheet`.

### D7

**The record.** `docs/decisions.md`: **D6** — the alias is checked against `config/reader.json` before its
first call; **D28** — the image is pinned by digest in `config/image.json` and built on request; **D32** —
[D6](#d6)'s rule. `docs/principles.md`'s pinning list (`:184-187`) shrinks to the apt gap and its records line
(`:237-239`) empties. `README.md` replaces the by-hand GGUF fetch (`:279-281`) with the provisioning command,
and names `config/image.json`; `CLAUDE.md` names `.runpod_pod_image` beside `.runpod_pod_id`.

### D8

**The acceptance: the whole flow, with every pin in place.** One metered session under the standing ceiling
(45 minutes, ~$0.30), on a synthetic portrait:

```
grow isekai-models to 45 GB ─▶ download_models.sh config/reader.json (all SKIP)
─▶ tag ─▶ caption ─▶ sheet ─▶ ui: review and approve ─▶ up.sh (by digest)
─▶ generate: conjure --count 2, summon --count 1 ─▶ down.sh ─▶ MCP confirms the pod gone
```

Every artifact is checked for its records: `pinned: true` and both digests on the caption and tags, `floor`
on the list and the sheet, `flow_digest` on the sheet, prompt and render, `schema_document` and `field_map`
on the approval, `image`, `pinned: true` and `runtime` on each render. The renders are judged by eye against
the last accepted ones. D27's known break closes once the volume is grown.

### D9

**A minor.** It adds run-file keys, a provisioning manifest and a capability, and changes how a pod boots.
One feature: the pin and its record.

### D10

**`docs/pins.md`, the operating guide to the pins.** Added after the acceptance, at the operator's request, so it
is written from what the acceptance proved. It links to the principle *Everything that shapes an output is pinned*
for the reason and never restates it.

```
what pins buy     identity, not pixels · integrity, not cleanliness · comparable figures ·
                  attribution · no silent drift · rollback · fail before paying — and the price
the inventory     thing · pinned by · declared in · checked when
re-pinning        one recipe per inventory row
not pinned        apt, the Ollama runtime, the GPU and its driver, macOS — and the records that
                  stand in for them
when to re-pin    an advisory, or a deliberate upgrade — with a render comparison
```

- **The inventory names files, and a test holds it:** every repository path the guide names in backticks exists
  (`tests/test_docs.py`), so a moved file fails the gate instead of leaving the guide wrong.
- It is linked from `docs/README.md`'s table and from the principle's section in `docs/principles.md`.

## Settled at the cut

| premise | settled |
|---|---|
| `onnxruntime` is installed twice, CPU then -gpu | lock `onnxruntime-gpu` alone ([D2](#d2)) |
| the lock resolves today's versions, not the ones behind past renders | accepted, judged by eye ([D8](#d8)) |
| honouring `OLLAMA_MODELS` breaks *reads no environment* | a constant root ([D4](#d4)) |
| a once-per-invocation check would carry one flow's verdict to another | memoised per model; an unpinned model is refused ([D4](#d4)) |
| a new manifest must be derived through `tools/manifest.py`, and pass the mirror rule | `tools/derive_reader.py`; `concedo` its publisher ([D4](#d4)) |
| Q9's `sheet_version` would change meaning under version 1 | a new key, `sheet` ([D6](#d6)) |
| `up.sh` never contacts SSH | *port 22 mapped* is the timed event ([D2](#d2)) |
| uv is 0.8.24 here, 0.12.19 upstream | 0.12.19 everywhere ([D1](#d1)) |

## Dependencies

None added to isekai. The image's own packages move into `image/uv.lock`.

## Risks / Trade-offs

- [The lock resolves today's package versions] → the acceptance judges both flows' renders by eye.
- [`opencv-python`, `opencv-contrib-python` and `opencv-python-headless` all ship `cv2`] → the lock installs what
  today's image already overlays; recorded, not resolved.
- [A new Ollama stores models elsewhere] → the refusal names the path it read.
- [The check reads a private on-disk layout] → it is memoised, one small JSON read per model, and a changed
  layout refuses by name rather than passing.
- [The image build needs the branch on GitHub] → phase 3 is the operator's push and dispatch.

## Verdict

`feasible-with-caveats` — the renders are proved by the acceptance, not by the suite.
