# Tasks — 0011-converge-paydown

## Progress

- [ ] 1 — `start.sh` and `up.sh`: the namespace block, the volume guard, the bounded hold
- [ ] 2 — Pin ComfyUI's core to the commit `:v0.10-rc` was built from
- [ ] 3 — The provisioning guards move from the suite into the module
- [ ] 4 — `workflow.py`: three stated ceilings
- [ ] 5 — CI enforces the `latest` protection it documents
- [ ] 6 — Publish `:v0.11-rc`, then ⚠️ **GPU · HALT** — the smoke test and the loader probe
- [ ] 7 — The PNG `eXIf` question, answered by phase 6's probe
- [ ] 8 — The trust root: WAI's digest is derived, not transcribed
- [ ] 9 — The record: the 1152, the pose grid, the probe artifacts, the exemption label

## The per-phase ritual

Every phase, without exception:

1. **Test-first where there is logic.** Phases 1–4, 7 and 8 have it; phase 9 is prose. Red → green.
2. **Run each phase's stated verification — run it, never summarize it.** The commands are named in
   the phase detail below. Paste real output.
3. **Gate green before the commit** — `make gate`, the five commands in `.minions/minions.toml`'s
   `gate` array, in order. A phase that leaves the gate red is not done. **Never weaken the gate to
   pass**; halt and say so.
4. **Phases 1, 2 and 3 are image-as-code**, so they also run `bash -n` on every changed shell script
   and `docker build --check`.
5. **Append that phase's entry under `## [Unreleased]` in `CHANGELOG.md`**, in the style of the
   entries already there, using `### Added` / `### Changed` / `### Fixed` / `### Notes`.
6. **Check the box** in the `## Progress` list above, in that phase's own commit. The first unchecked
   entry is the current phase; that is how the loop reads this file.
7. **One commit per phase**, staged **by name**, carrying the trailer `Change: 0011-converge-paydown`
   **contiguous** with `Co-Authored-By:` — no blank line between them, or git stops parsing the
   trailer block.

**This version settles nothing by eye.** v0.10 was the last one permitted to. Every acceptance
criterion below is a command, a test, or a comparison of numbers — including on the pod (design.md
D10, D11). If a phase's criterion cannot be checked that way, that is a plan problem; halt.

**No render change.** `workflows/pipeline.json` is not edited in any phase. Not the register, not a
dial, not a ControlNet strength, not `DWPreprocessor`'s resolution (design.md D9, D16).

**Three phases reach the network.** Phase 2 pulls `:v0.10-rc` from GHCR, phase 5's successor
dispatches a CI run, phase 8 fetches Civitai's API. If a service cannot be reached, that is a halt
with a named cause — never a hand-written digest, never upstream head substituted for the pin, and
never a pod booted on an image whose build was not confirmed.

**One phase spends real money.** Phase 6. A pod goes up only for a phase marked ⚠️ GPU here,
`infra/up.sh` creates it, `infra/down.sh` tears it down, and teardown is confirmed through the RunPod
MCP with what it returned recorded. The ceiling is **45 minutes and ~$0.30 per pod session**;
exceeding it is a halt, not a judgement call. At $0.74/hr the money ceiling binds at **24 minutes**,
so plan against 24 and treat 45 as the halt. **The ceiling is per session** — if phase 6 fails and a
fix requires a second session, that is a new session at its own ceiling, not an overrun of the first
(design.md, Risks).

**Phase 6 must set `RUNPOD_IMAGE`** to `:v0.11-rc` in `.env`, and clear it afterwards. `start.sh` and
the `Dockerfile` both changed, so `:latest` would boot the wrong thing; a stale value left behind
silently pins every later pod to an unreleased image.

## Phase detail

### 1 — `start.sh` and `up.sh`: the namespace block, the volume guard, the bounded hold

Five findings live inside twenty lines of `start.sh`, so they are fixed once, together (design.md
D1). `infra/up.sh` moves in the same commit because the volume guard has a client half and a pod
half and neither is meaningful alone (design.md D5).

- **`up.sh` refuses to create a pod when `RUNPOD_VOLUME_ID` is empty**, before the API call, and
  passes it into the container's environment so the entrypoint knows which volume to expect. This is
  where the guard actually bites: `mountpoint -q` does **not** work, because RunPod mounts the pod's
  own 20 GB volume disk at `volumeMountPath` when no network volume is attached, so the path exists
  and *is* a mountpoint — the wrong one (design.md D5). *(0009:R4, client half)*
- **`start.sh` refuses before preparing the namespace** if what it finds is not the volume it was
  told to expect — a free-space floor, not `mountpoint`. *(0009:R4, pod half)*
- **The `rm -rf` is guarded on its premise, not its proxy.** Refuse to delete `$MODELS_ROOT` unless
  it is empty or not a mountpoint, and abort with a clear message otherwise. Deleting a non-empty
  models tree is an explicit operator act, never a silent entrypoint step. *(0009:S4)*
- **The reachability hold covers namespace setup too**, not only the provisioning call. Wrap the two
  steps and guard the call once. *(0009:R8)*
- **The hold is bounded at 900 s** and writes a failure marker to **container disk**, not into the
  namespace — the namespace is exactly what may have failed. 3600 s is $0.74, more than twice the
  session ceiling (design.md D6). *(0009:S7)*
- **The comment stops calling the models tree empty.** The ComfyUI clone tracks
  `models/configs/*.yaml`; the `rm -rf` drops them knowingly, because the graph uses
  `CheckpointLoaderSimple`, which takes no config. Fix the comment, do not copy the configs
  (design.md D17). *(0009:R3)*

**Verify:** `bash -n start.sh infra/up.sh`; `make gate` green; new tests in `tests/test_infra.py`
bound to `model-provisioning:reachability:namespace-setup-is-held-open-too`,
`:the-hold-is-bounded-and-marked` and `:provisioning-requires-the-network-volume`; the existing
namespace test still passes unchanged.

### 2 — Pin ComfyUI's core to the commit `:v0.10-rc` was built from

`Dockerfile:16` clones ComfyUI's default branch head — the one unpinned link in the change whose
thesis was pinning, with both custom-node packs beside it already pinned to commits. *(0009:S5)*

Recover the commit from the image that produced v0.10's renders:

```
docker run --rm ghcr.io/alxb1t/isekai:v0.10-rc git -C /opt/ComfyUI rev-parse HEAD
```

Then `git clone` + `git checkout <sha>`, matching how its two neighbours in the same file are
already pinned. **Do not substitute upstream head** — the point is that this pin records what already
ran rather than importing an untested core (design.md D3). If the tag is gone from GHCR, halt.

Record in the CHANGELOG, in the same entry, that pinning the core **moves** the floating link rather
than removing it: `uv pip install -r requirements.txt` at `Dockerfile:20` and `:38` still resolve at
build time, so the image is not reproducible and this change does not claim it is (design.md D4).

**Verify:** the recovered SHA pasted into the phase's output; `docker build --check`; `make gate`
green; a test asserting the `Dockerfile` pins ComfyUI's core to a 40-hex commit, beside the existing
assertions on the two node packs.

### 3 — The provisioning guards move from the suite into the module

The four manifest checks have no caller outside `tests/test_manifest.py` — they are commit-time
assertions that cannot bite on a pod. These four findings put the rules where the values are used.

- **`plan` emits the already-resolved absolute target** and `decide` rejects a `dest` that is
  absolute or resolves outside the models root. `target="${MODELS_DIR}/${dest}"` is deleted from the
  driver, so the containment rule lives in one place (design.md D7). *(0009:S1)*
- **`decide` rejects a source that is not a pinned, whitespace-free URL**, applying `PINNED_SOURCE`
  where the value is used rather than only in the suite. *(0009:S6, second half)*
- **The driver reads the URL list into an array** — `IFS=$'\t' read -r -a` — instead of word
  splitting, which also removes the `# shellcheck disable=SC2086`. *(0009:S6, first half)*
- **An entry declaring no sources is refused by name**, not reported as "every source was rejected"
  with an empty reason list. *(0009:R7)*
- **The graph↔manifest binding keys on an explicit set of self-fetching class names**, not on a
  `*Preprocessor` suffix, and `InstantIDFaceAnalysis` joins it with the five antelopev2
  destinations. *(0009:R6)*

The plan-line format changes, so `land`, `scripts/download_models.sh` and both infra tests move in
this one commit.

**Verify:** `bash -n scripts/download_models.sh`; `docker build --check`; `make gate` green; new
tests bound to `model-provisioning:immutable-pins:an-escaping-destination-is-refused`,
`:a-malformed-source-is-refused-at-runtime`, `:an-entry-with-no-sources-is-refused` and
`model-provisioning:namespace:self-fetching-nodes-are-bound-by-name`.

### 4 — `workflow.py`: three stated ceilings

A short-side rule places no bound on the other axis, and a header field is an unverified number
(design.md D8). *(0010: R6, S1, S5)*

| Ceiling | Value |
|---|---|
| Long side of the computed target | 4096 |
| A header-declared dimension | 65535 |
| Bytes read while walking a header | 4 MiB |

Each refuses with `sys.exit`, naming the file and the limit, in the style of the existing
unreadable-header exit. **Do not clamp** the target instead of refusing — a clamped target no longer
preserves the aspect ratio and would squash the photo the way the orientation rule exists to prevent.

**Verify:** `make gate` green; new tests bound to
`workflow-injection:working-resolution:an-extreme-aspect-ratio-is-refused`,
`:an-out-of-range-header-dimension-is-refused` and `:an-unbounded-header-walk-is-refused`; the
existing orientation and deep-header tests still pass unchanged.

### 5 — CI enforces the `latest` protection it documents

`tags: ghcr.io/alxb1t/isekai:${{ inputs.tag || 'latest' }}` interpolates an unvalidated
`workflow_dispatch` string under a header comment asserting that a manual run "can never clobber the
image a rollback would reach for". *(0009:R5, 0009:S2 — one site, two stations.)*

Validate before use rather than after the fact: a first step that fails unless the input matches
`^[A-Za-z0-9._-]+$` and is not `latest`, assigning the validated value to a step output the build
step references, so `inputs.tag` is never interpolated into `tags` directly. The pattern also rejects
the newline that `docker/build-push-action`'s newline-separated `tags` input would otherwise honour
from a `gh workflow run` or REST dispatch.

Update the dispatch default, which still names `v0.9-rc`, two versions stale.

**Verify:** `make gate` green; the workflow parses (`gh workflow view build-image.yml` or an
equivalent YAML parse); phase 6's dispatch is itself the live test of the guard — it must accept
`v0.11-rc` and reject `latest`.

### 6 — Publish `:v0.11-rc`, then ⚠️ **GPU · HALT** — the smoke test and the loader probe

Everything the pod can invalidate is built (design.md D2). Nothing after this phase changes what the
pod ran.

**First, off the clock.** Dispatch the CI build for `:v0.11-rc` and confirm it succeeded. Then build
the four probe inputs with a script committed to this change's `probe/`, taking source and
destination as arguments so no path outside this repository is tracked. The inputs are **not
committed**; their dimensions and SHA-256 go in `probe/README.md` (design.md D14):

- **(a) landscape** — a portrait cropped to roughly 832×554. First time short-side rounding runs on
  the height axis.
- **(b) above the working scale** — the 1248×1824 asset cropped to a *different* aspect, e.g.
  1248×1400. Uncropped it is the same aspect as the 832×1216 photo v0.10 rendered and would compute
  to the identical 1024×1472 target, proving nothing.
- **(c) rotated JPEG** — a portrait rotated 90° so its pixels are stored landscape, saved as JPEG,
  with an APP1 segment declaring Orientation 6 spliced in using `tests/images.py`'s existing EXIF
  helper.
- **(d) plain JPEG control** — the same portrait as JPEG with no EXIF, so a failure on (c) is
  attributable to the tag rather than to the codec.

**Then, on the clock.** Set `RUNPOD_IMAGE` to `:v0.11-rc` in `.env`, announce, `infra/up.sh`.

1. Confirm from the container log that the volume mounted and the manifest verified — 15 entries,
   16.5 GiB, no fetch.
2. **The loader probe first** — seconds, no GPU. Send a two-node `LoadImage` → `SaveImage` graph over
   the same HTTP API for (c) and for a PNG carrying an `eXIf` Orientation chunk, and record the saved
   files' dimensions. This is what settles the rotated case, because `run.json` records the same
   dimensions whether or not the loader transposed (design.md D11). It is also what phase 7 consumes,
   so it runs before the render budget is spent.
3. **Four renders**, `convert.py <photo>` with `--variations 1` and one fixed `--seed` across all
   four.
4. `scp` the renders, the `run.json` files and the probe output off the pod, into this change's
   `probe/`. **The pod's disk is ephemeral; only the models volume persists.**
5. `infra/down.sh`. Confirm the pod is gone through the RunPod MCP and **record what it returned**.
6. Clear `RUNPOD_IMAGE` from `.env`.

**Acceptance — all machine-checkable, none by eye:**

- Each of the four runs exits 0.
- Each run's rendered dimensions equal the target `working_resolution` computes from that file's
  header. (b)'s target is a number no prior run produced.
- The loader probe's saved dimensions state, for each codec, whether `LoadImage` at the pinned commit
  applies EXIF `Orientation`.
- Session under 24 minutes; teardown confirmed with the MCP's response recorded.

**The CHANGELOG entry states what this does not establish** (design.md D10): nothing about identity,
fidelity or quality; **not** that renders are unchanged from v0.10, because no v0.10 PNG baseline was
kept and the dependency closure was re-resolved at build even though the core is pinned to the commit
v0.10 booted; **not** the volume guard or the bounded hold, both suite-bound and unexercised on a
pod; and nothing about mutation, since each photo ran at one variation.

**If the smoke test fails**, the version halts. Fix, dispatch a new `-rc`, and run a **second**
session at its own ceiling. Do not ship a `start.sh` rewrite a pod has demonstrated is broken.

### 7 — The PNG `eXIf` question, answered by phase 6's probe

Found while planning this change, not exported by either converge pass — so this version's content is
the twenty findings **plus one**, and the record says so (design.md D12).

`_png_dimensions` reads IHDR and stops. PNG can carry an `eXIf` chunk that Pillow reads and
`ImageOps.exif_transpose` acts on. Every input this project has ever rendered is a PNG.

**Two legitimate outcomes**, decided by phase 6's probe and not by reading `nodes.py`:

- **The probe shows PNGs are transposed** → fix `_png_dimensions` to honour the orientation the same
  way the JPEG path does, with a scenario under
  `workflow-injection:working-resolution:orientation-is-honoured` covering both codecs, and a spec
  delta appended to this change.
- **The probe shows they are not** → **no code change.** Adding an `eXIf` read would introduce the
  very mismatch v0.10 closed, in the opposite direction. Record in `design.md` that the codecs differ
  and why the parser is right to differ with them.

**Verify:** the probe output quoted in the phase's own output; `make gate` green; if the fix lands, a
test bound to the scenario; if it does not, no test and a design note.

### 8 — The trust root: WAI's digest is derived, not transcribed

`WAI_SHA256` exists three times — `scripts/derive_manifest.py`, `tests/test_manifest.py` and the
emitted `scripts/models.json` — and all three compare against copies of the same value a human typed,
so the transcription itself is unverified. `derive_manifest.py`'s own docstring claims the manifest is
"derived, never transcribed". *(0010:S4)*

Fetch it from Civitai's public API for the model version, like every other digest, so the human leaves
the loop. Record the URL and the date in `design.md`. The residual is unchanged and stated: Civitai is
still the trust root, publishes no signature, and WAI has no first-party host. **Do not record
BLAKE3** — verifying it would need a wheel the runtime rule forbids, and a field nothing reads is a
one-entry registry (design.md D13).

**Verify:** `python scripts/derive_manifest.py` leaves `scripts/models.json` **byte-identical** —
`git diff --exit-code scripts/models.json`. A diff is a halt and a finding, not a file to commit.
`make gate` green. The value was pre-verified against the API while this change was cut and agrees
exactly, bytes included, so a diff here means something moved upstream.

### 9 — The record: the 1152, the pose grid, the probe artifacts, the exemption label

All prose, one commit. Everything is recorded **forward** — `0010-illustrious-base` is archived, and
an archived change is a record of what was decided then (design.md D15).

- **The unreconciled 1152.** `0010`'s proposal says the scale targets a short side of 1152;
  `WORKING_SCALE = 1024` shipped, under a comment calling 1024 "the floor MistoLine's card names".
  One of the two readings is wrong. Record the reading and **admit it is unverified** — which one is
  right is a rendering question, and rendering questions wait for the evaluator. Do not re-test it.
  *(0010:R4)*
- **The pose grid.** Fold the corrected `scale-precedes-every-consumer` scenario into the change's
  `workflow-injection` delta — already written — and make the matching edit in `README.md`, whose
  line 65 carries the same false sentence. A preprocessor's internal working resolution is a separate
  dial; `DWPreprocessor` stays at 512 (design.md D9). *(0010:R5)*
- **The probe artifacts.** Note in `probe/README.md` that two `run.json` files can be byte-identical
  because the seed stream does not depend on the photo, and make the README table the authoritative
  tie between each input, its computed target and its rendered dimensions. *(0010:R8)*
- **The exemption label.** `spec_exempt("structural: pins the dials the phase-5 probe chose")`
  describes a by-eye value pin as structural, which is the opposite of what it is. Reword to what it
  is, e.g. `spec_exempt("preference, not a scenario: holds the dials design.md D9 records as
  by-eye")`. No behaviour changes. *(0010:R7)*

**Verify:** `make gate` green; `openspec validate 0011-converge-paydown --strict` passes;
`grep -rn '1152' --exclude-dir=archive .` returns nothing outside this change's own record;
`grep -n 'structural' tests/test_workflow_injection.py` no longer matches the dial-pin exemption. The
wording itself is reviewed, not command-checked — that is stated rather than dressed up as a check.
</content>
