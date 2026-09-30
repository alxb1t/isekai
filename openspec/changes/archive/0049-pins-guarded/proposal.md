---
version: v0.31.1
backlog: [0013·R8, 0013·S2, 0033·R1, 0033·R3, 0033·R7, 0042·S1]
---

# 0049 — pins guarded

The pins' claims hold without anyone remembering to check them. Every clone in the image must carry its commit; a
bumped source-only package fails until its build tools are recorded again; the caption and tags goldens hold their
producer keys; a bad runtime report is classified as the transport classifies it, and read once; a weekly job goes
red when a pinned source moves; the models root resolves from anywhere. Nothing baked into the image changes.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each guard's shape, and the drift job |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `comfy-transport`, `image-generation` |

## Why

**Some guards hold less than they claim.** The clone check counts only GitHub clones written one way; the build-tool
check keys packages by name, so a bump needing a new tool stays green; the caption and tags goldens never saw a
pinned producer.

**A bad runtime report is misworded and re-asked.** It reads "carries no 'NoneType' object…" where the transport says
"a shape this build does not read", and every photograph asks again.

**Nothing re-derives the manifests.** Each deriver says a re-run leaves its file byte-identical, and nothing runs one.

**The models root depends on where the operator stands**, unlike every other root.

## What Changes

- **Every `git clone` in the `Dockerfile` is counted, whatever its flags or host** ([D1](design.md#d1)).
- **The source-only packages' build tools are keyed by name and version**; pins.md names what a backend adds while it
  builds ([D2](design.md#d2)).
- **The caption and tags goldens are captured from pinned producers** ([D3](design.md#d3)).
- **A malformed runtime report is refused as the transport refuses a shape it does not read, and is not asked again
  in the session** ([D4](design.md#d4)).
- **The models root is anchored on the package** ([D5](design.md#d5)).
- **The stale "16.5 GiB" leaves `infra/up.sh` and the tests** ([D6](design.md#d6)).
- **A weekly `drift.yml` re-derives the fetched manifests and goes red on a diff**; `make derive` fails on one too
  ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `comfy-transport`: MODIFIED *The server's runtime is read from its own report* — gains a report in a shape this
  build does not read, refused as permanent.
- `image-generation`: MODIFIED *A render records the image and the runtime it ran on* — gains a report refused
  as permanent, asked once and submitting nothing, and a transient one, asked again by the next render.

## Impact

- **Files:** `tools/derive_image_project.py`, `isekai/pipeline/generate.py`, `isekai/interface/cli.py`,
  `isekai/shared/vocabulary.py`, `evaluation/__main__.py`, `infra/up.sh`, `Makefile`, `.github/workflows/drift.yml`,
  `docs/pins.md`, `docs/principles.md`, `tests/golden/caption.json`, `tests/golden/tags.json`, and their tests.
- **Behaviour:** a malformed report's refusal changes its words and is not re-asked; the models root no longer
  depends on the working directory.
- **Formats:** no run file kind or manifest version moves. No file the image copies changes.
- **Dependencies:** none.
- **Spend:** none. The drift job runs on GitHub's free runners.

## Not in this change

- **A guard that the tree matches the pinned image, and `provision.py` on argparse** — with the next image rebuild.
- **`start.sh`'s "16.5 GiB" and `tools/download_models.sh`'s default models root** — baked into the image; with the
  next image rebuild.
- **A uv setting that refuses an unhashed build tool** — `image/pyproject.toml` is baked; with the next image rebuild.
- **Refusing a session once, with no record, for a failed report** — a new requirement.
- **Watching for new upstream versions** — P8, parked.
