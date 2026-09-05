# Tasks — 0010-illustrious-base

## Progress

- [ ] 1 — The manifest: WAI in, verified against the publisher's digest, Animagine still declared
- [ ] 2 — The working resolution: injection reads the photo and the graph scales before anything else
- [ ] 3 — The base and the register: `ckpt_name`, the CLIP layer, both prompts, `1girl` out
- [ ] 4 — Publish `:v0.10-rc`, the image the metered phases boot
- [ ] 5 — ⚠️ **GPU · HALT** — the probe: ControlNet comparisons, the dials, the gender check
- [ ] 6 — Apply the probe's verdicts: the dials into the graph, tile kept or dropped
- [ ] 7 — ⚠️ **GPU · HALT** — the final renders on WAI, at stated input resolutions
- [ ] 8 — Animagine leaves, and the docs describe an Illustrious base

## The per-phase ritual

Every phase, without exception:

1. **Test-first where there is logic.** Phase 8's docs half has none; phases 1–3 and 6 do. Red → green.
2. **Run each phase's stated verification — run it, never summarize it.** The commands are named in the phase
   detail below. Paste real output.
3. **Gate green before the commit** — `make gate`, which runs the five commands in `.minions/minions.toml`'s
   `gate` array, in order. A phase that leaves the gate red is not done. **Never weaken the gate to pass**;
   halt instead.
4. **Append that phase's entry under `## [Unreleased]` in `CHANGELOG.md`**, in the style of the entries already
   there, using `### Added` / `### Changed` / `### Removed` headings. Mark the register change **BREAKING**.
5. **Check the box** in the `## Progress` list above, in that phase's own commit. The first unchecked entry is
   the current phase; that is how the loop reads this file.
6. **One commit per phase**, staged **by name**, carrying the trailer `Change: 0010-illustrious-base` **contiguous**
   with `Co-Authored-By:` — no blank line between them, or git stops parsing the trailer block.

**This version is allowed to settle two things by eye, and it is the last one that may.** The
`denoise` / `ip_weight` values and the gender check are **preferences**, recorded as such (design.md D9).
Everything else it claims must be mechanical. *Chosen* is not *best*; *runs* is not *good*.

**Phases 1 and 4 reach the network.** Phase 1 derives digests from Hugging Face; phase 4 dispatches a CI run.
If either cannot reach its service, that is a halt with a named cause — never a hand-written digest, and never
a pod booted on an image whose build was not confirmed.

**Two phases spend real money and both are HALT phases.** A pod goes up only for a phase marked ⚠️ GPU here,
`infra/up.sh` creates it, `infra/down.sh` tears it down, and teardown is confirmed through the RunPod MCP with
what it returned recorded. The ceiling is **45 minutes and ~$0.30 per pod session**; exceeding it is a halt,
not a judgement call. **Both metered phases must set `RUNPOD_IMAGE`** — see phase 4.

**Animagine stays declared and on the volume until phase 8.** It is the rollback and the probe's comparison
base, and a re-provision against a manifest that no longer declares it would remove both, silently
(design.md D3).

## Phase detail

### 1 — The manifest: WAI in, verified against the publisher's digest, Animagine still declared

Add WAI-illustrious-SDXL v17.0 to `scripts/derive_manifest.py` and re-derive `scripts/models.json`. The bytes
come from a pinned Hugging Face mirror revision; the digest is **the SHA-256 Civitai itself publishes** for the
model version, which is what makes the mirror a CDN rather than a trust root (design.md D1). Declare the
byte-identical **Hugging Face** alternates, so v0.9's fallback walking has somewhere to go if the primary mirror
disappears mid-version. Do **not** declare Civitai's own download as a source: `provision.py`'s pinned-source
check accepts only a Hugging Face `resolve/<40-hex>/` URL, and widening it for one entry would weaken the
no-mutable-ref check to buy availability six mirrors already supply (design.md D1). Civitai is the publisher of
the **digest** here, not a source.

`mirror_entries_without_an_alternate` will demand those alternates by itself: it treats any Hugging Face org
absent from the manifest's `publishers` list as a mirror, and WAI has no first-party HF repo at all.

**Two things not to write into the record as evidence.** Every published WAI version reports the *identical*
byte count, so size discriminates nothing — only the digest does. And Civitai's digest is computed by the
platform after upload: a strong independent cross-check of the mirror, not a signature by the model's author.

Animagine's entry **stays**. Nothing is removed here.

**Verification:**
- re-run `scripts/derive_manifest.py` and `git diff --exit-code scripts/models.json` — no drift between the
  tool and the committed data
- `uv run pytest tests/test_manifest.py -q` — green, including the mirror-needs-an-alternate check
- `make gate` — exit 0

### 2 — The working resolution: injection reads the photo and the graph scales before anything else

Add a scale node to `workflows/pipeline.json` between the image loader and **every** consumer — the latent
encoder, the identity node and both ControlNet preprocessors — so one pixel grid feeds the whole graph and no
control hint is registered against a different one.

Add to `isekai/workflow.py` a pure function that reads a photo's dimensions from its JPEG or PNG header and
returns the target: aspect preserved, short side at the working scale, both dimensions multiples of 64, in
**both** directions so a small photo is scaled up as well as a large one down. **Stdlib only** — no dependency
is added and nothing enters `convert.py`'s import graph beyond what is already there. An unreadable or
truncated header stops the run naming the file; there is no default size, because a silently wrong resolution
is a wrong render rather than an error (design.md D2).

`inject` gains the photo's local path. `pipeline.run` already holds it as `input_path` and passes it; it stays
an argument rather than becoming state.

**Verification:**
- `uv run pytest tests/test_workflow_injection.py -q` — green, with the five working-resolution scenarios bound
- prove the header parser against landscape, portrait and square fixtures of both formats, and against a
  truncated header
- `make gate` — exit 0

**Closes:** `workflow-injection:working-resolution:scale-precedes-every-consumer` ·
`…:short-side-at-the-working-scale` · `…:small-photos-are-scaled-up` ·
`…:dimensions-are-written-by-injection` · `…:unreadable-dimensions-are-refused`.

### 3 — The base and the register: `ckpt_name`, the CLIP layer, both prompts, `1girl` out

Point `ckpt_name` at WAI. Add a `CLIPSetLastLayer` between the checkpoint's CLIP and **both** text encoders,
and pin its value: every published WAI sample generates at clip skip 2 and none of its prose says so, so a
graph without it ships a configuration the publisher never tested while looking identical to one that does
(design.md D6).

Rewrite both prompts to the publisher's register (design.md D4): the positive is the content tags plus WAI's
ladder **appended last**, the negative is the publisher's own short form. Taking the publisher's positive while
keeping an eighteen-token negative would take half the guidance and ignore the half stated as a warning.

**`1girl` is removed; `solo` stays.** `solo` is what does the mode-selection work; `1girl` additionally asserts
a gender that the ID embedding already carries, so dropping it hands that axis to a mechanism already in the
graph rather than to a tagger that does not exist (design.md D5). This closes the defect v0.8 recorded and
named a later version as the owner of.

Both literals are re-pinned by equality. Fix the stale comment in `tests/test_workflow_injection.py` that names
**v0.9** as `1girl`'s owner — v0.9 changed no base and decided no register.

**Verification:**
- `uv run pytest tests/test_workflow_injection.py -q` — green, with the register and CLIP-layer scenarios bound
- `uv run pytest tests/test_manifest_binding.py -q` — green: the graph now names WAI, and phase 1 declared it
- `git grep -n "1girl" -- . ':!CHANGELOG.md' ':!openspec/changes/archive'` — no hits outside this change's own
  prose
- `make gate` — exit 0

**Closes:** `workflow-injection:committed-prompt:asserts-no-gender` · `…:string-is-pinned` (re-pinned literal)
· `workflow-injection:clip-layer:conditioning-stops-at-the-expected-layer`. The requirement's other three
scenarios are unchanged and keep their existing tests.

### 4 — Publish `:v0.10-rc`, the image the metered phases boot

The pod provisions from the manifest baked into the image it boots. `:latest` is v0.9's image and carries
v0.9's manifest, so a pod running it would never fetch the checkpoint the graph now names — the WAI entry
landed in phase 1, on this branch. Publish a release candidate and point the metered phases at it.

**`:latest` is not touched, and cannot be from here.** CI publishes it from a push to `main` and nowhere else;
the manual dispatch requires a tag and names it "never `latest`", precisely so a pre-release build cannot
clobber the image a rollback reaches for. The tag becomes v0.10's on merge, by the mechanism that already
exists.

**No `Dockerfile` edit is needed** — `ImageScale` and `CLIPSetLastLayer` are core ComfyUI, so this is a
rebuild, not a change.

**This phase's action is outward-facing and belongs to the operator**: dispatching a CI run publishes an
artifact to a public registry. Announce and hand off, as with a metered phase. The phase's own commit is its
`CHANGELOG.md` entry and ticked box; it changes no code.

**Verification:**
- `gh run list --workflow=build-image.yml --limit 3` — a `workflow_dispatch` run for tag `v0.10-rc` on this
  branch, completed successfully
- `docker build --check .` — exit 0
- `.env` names `RUNPOD_IMAGE=ghcr.io/alxb1t/isekai:v0.10-rc`; `.env.example` still declares shape only
- `make gate` — exit 0

### 5 — ⚠️ **GPU · HALT** — the probe: ControlNet comparisons, the dials, the gender check

**Announce, then stop.** The operator runs `infra/up.sh` with `RUNPOD_IMAGE` set. WAI provisions alongside
Animagine at boot, from the manifest, verified.

Three things, in this order, because the first is mechanical and the other two are not:

1. **ControlNet strength-to-zero comparison**, at a **fixed seed**: for each ControlNet, one render at its
   tuned strength and one at `0.0`. This asks whether the conditioning reaches the sampler at all — not
   whether the result is prettier — so it is falsifiable and needs no taste. A component indistinguishable
   from absent is a component that can be deleted with evidence (design.md D7). Record the verdict per
   ControlNet.
2. **`denoise` and `ip_weight`**, found by eye. They were tuned on Animagine and do not transfer. Record the
   chosen values *and* what they were chosen against.
3. **The gender check**: a **male** input photo, at the new register and a fixed seed, produces a
   male-presenting output. This is the one falsifiable acceptance criterion the register change gets, and it
   can fail.

Download the outputs before teardown — pod disk is ephemeral. Tear down with `infra/down.sh` and confirm
through the RunPod MCP, recording what it returned.

**Record as preferences, not measurements** (design.md D9): the chosen run's `run.json` plus a short note of
what was compared goes in this change's directory; the images stay in gitignored `outputs/`, because the
manifest and the seeds reproduce them and this repo claims reproducibility over the submitted workflow JSON,
never over pixels.

**A technical failure — the checkpoint will not load, or no ControlNet loads — defers the version rather than
half-shipping it.** Halt and say so; do not improvise a substitute component on metered time.

**Verification:** the per-ControlNet verdicts, the chosen dials and the gender-check outcome are recorded in
the change directory and in the phase's `CHANGELOG.md` entry · teardown confirmed through the MCP, with its
response recorded · the session's wall clock and cost are recorded against the ceiling.

### 6 — Apply the probe's verdicts: the dials into the graph, tile kept or dropped

Write the chosen `denoise` and `ip_weight` into `workflows/pipeline.json`. Then act on the tile verdict:

- **Indistinguishable from absent** → remove the tile ControlNet loader, its preprocessor and its apply node,
  rewire the stack, and remove its manifest entry. The `PREPROCESSOR_MODELS` mapping loses `TilePreprocessor`.
- **Distinguishable** → keep it, and record its publisher's animation disclaimer against it in `CHANGELOG.md`
  as a known deviation, with the comparison that justified keeping it.

Either way `inject`'s walk from the sampler's positive input must still reach the encoder through whatever
stack remains — that is the non-obvious property this graph has always had, and a shortened stack is exactly
when it would break unnoticed.

**If this phase changes `scripts/models.json`, republish the image before phase 7**, since the pod provisions
from the manifest the image carries.

**Verification:**
- `uv run pytest -q` — green, including the injection walk against the current stack
- `uv run pytest tests/test_manifest_binding.py -q` — green: every model the graph names is still declared
- `make gate` — exit 0

### 7 — ⚠️ **GPU · HALT** — the final renders on WAI, at stated input resolutions

**Announce, then stop.** Operator runs `infra/up.sh` with `RUNPOD_IMAGE` set.

Render the path on WAI for at least two photos of **different aspect ratios**, and record each input's
dimensions. The claim this version is allowed to make is "the path runs on WAI **at stated input
resolutions**" — v0.8's Verified block implied a generality it never tested, and the scale node exists so this
one does not repeat that.

Download the outputs before teardown. Tear down and confirm through the MCP. Clear `RUNPOD_IMAGE` from `.env`
afterwards — a stale value silently pins every later pod to an unreleased image.

**Verification:** `convert.py <photo>` exits 0 and writes `0.png`–`4.png` plus `run.json`, for each photo ·
the input dimensions and the resulting render dimensions are recorded · teardown confirmed through the MCP ·
wall clock and cost recorded against the ceiling.

**The `CHANGELOG.md` entry must state what this version did not establish**: nothing about identity, fidelity
or quality; not that the chosen dials are good, let alone optimal; not that any ControlNet improves output,
only that each retained one measurably changes it; not that the register improves anything. What it
establishes is that the path runs on WAI at stated input resolutions, and that a male photo yields a
male-presenting output.

### 8 — Animagine leaves, and the docs describe an Illustrious base

Remove Animagine's entry from `scripts/derive_manifest.py` and re-derive. It has been the rollback and the
probe's comparison base since phase 1; with the swap proven, a declared checkpoint nothing renders with is a
second path in everything but name, which this repository's one-path rule forbids (design.md D3).

`README.md`: the base in the path table and the "How it works" line become WAI-illustrious-SDXL v17.0; the
register row still points at the committed prompt. `CLAUDE.md`: the base, the register, the ControlNet stack
as it now stands, and the note that `1girl`'s defect is closed and by what mechanism. **Make no claim about
identity or quality anywhere in either.**

**Verification:**
- `git diff --exit-code scripts/models.json` after re-deriving — tool and data agree
- `uv run pytest -q` — green; the graph names nothing the manifest no longer declares
- `git grep -ni "animagine" -- README.md CLAUDE.md workflows/pipeline.json scripts/` — no hits
- `make gate` — exit 0
