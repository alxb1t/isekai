# Design — 0011-converge-paydown

## Context

See `proposal.md` — *Why*. The state this design starts from:

- Twenty findings sit `open` across four converge documents, all non-blocking, all re-anchored to
  `52bbcd4` while planning this change. **None is moot at HEAD.** The round-1 line numbers in those
  documents predate `88a5d59` and `503e9cf` and are not to be trusted; every item was located afresh.
- Two of the round-2 notes are load-bearing for the approach. `0009:S1` records that
  `entries_with_missing_keys`, `sources_on_a_mutable_ref`, `entries_without_a_digest` and
  `mirror_entries_without_an_alternate` have **no caller outside `tests/test_manifest.py`** — they are
  commit-time assertions, so a guard added beside them would still leave the pod unguarded.
  `0009:S6` records that the driver's word split is contained by a `wget` argument-parsing accident
  rather than by design.
- `isekai/workflow.py` and `isekai/cli.py` run **on the operator's machine**, not on the pod. The
  image carries only `start.sh`, `scripts/download_models.sh`, `scripts/models.json`,
  `isekai/provision.py` and the `Dockerfile` itself. This is what makes the phase order in D2
  possible.
- The one metered session is bounded by this repository's guardrail. The two numbers in it are not
  independent: at the RTX 4090 secure on-demand rate of **$0.74/hr** (checked while planning this
  change; v0.10 recorded $0.72/hr), **~$0.30 is reached at 24 minutes**. 45 minutes is the halt, not
  the plan.

## Goals / Non-Goals

**Goals:**

- Close all twenty exported findings, plus the one this change's planning found (D12), each bound to
  a scenario where it is behaviour and to prose where it is a record.
- Move every guard from where it is asserted to where it bites — `up.sh` before the pod exists,
  `decide`/`plan` on the pod — rather than adding a fifth commit-time check beside four that no
  runtime code calls.
- Exercise, on a pod, the input shapes v0.10's CHANGELOG explicitly named as untested, and return
  from that session able to state precisely what it established and what it did not.

**Non-Goals:**

- **No render change.** `workflows/pipeline.json` is not edited. Not the register, not a dial, not a
  ControlNet strength, not `DWPreprocessor`'s resolution (D9).
- **No reproducible image.** Pinning ComfyUI's core does not achieve that, and this change does not
  attempt the dependency closure (D4).
- **No evaluator, and no by-eye judgement.** v0.10 was declared the last version permitted to settle
  anything by eye. Every acceptance criterion here is a command or a comparison of numbers (D11).
- **No attestation improvement.** D13 removes a human from a transcription; it does not give WAI a
  signature it does not publish. `0009:S3` stays on the unscheduled track.

## Decisions

### D1 — All twenty in one version, and why the alternative loses

The alternative was two versions: infrastructure (`start.sh`, CI, the Dockerfile pin, the digest)
then correctness (`workflow.py`, the change record, the exemption label). It is rejected, but not on
the argument first offered for it.

That argument — that the items overlap by file — holds for **exactly one group**. Five findings sit
inside twenty lines of `start.sh`, so fixing them singly would have each pass rewrite the last. It
does **not** hold across the proposed split: `build-image.yml`, `Dockerfile:16`, `derive_manifest.py`,
`workflow.py`, the change record and the exemption label touch six disjoint files sharing no line.
And "the same defect from two sides" is an argument for one *commit*, which one version does not buy
and two versions do not prevent.

What actually settles it is cost against benefit. The split's real benefit is feedback from the pod
before the paper work is done — and **D2 obtains that by reordering, at no structural cost**. The
split's cost is two release boundaries, two changelog cuts and two archive folds for twenty nits.
So: one version, reordered.

### D2 — Nine phases, with the metered session sixth

Only phases 1–3 change the image; `workflow.py` is laptop-side and the re-derived manifest is
byte-identical (D13), so neither can affect what the pod runs.

```
1  start.sh + up.sh        image    0009 R3 R4 R8 S4 S7
2  Dockerfile pin          image    0009 S5
3  provisioning guards     image    0009 R6 R7 S1 S6
4  workflow.py ceilings    laptop   0010 R6 S1 S5
5  CI                      —        0009 R5 S2
6  ⚠️ GPU smoke test       —        renders + loader probe
7  PNG eXIf                laptop   decided by phase 6's probe
8  trust root              —        0010 S4
9  record + spec + label   —        0010 R4 R5 R7 R8
```

Phases 1–3 are what the image contains, 4 is what the renders exercise, and 5 is what publishes the
image — so all five must precede 6. Nothing after 6 can change what the pod ran, which is what makes
the position safe. Three phases now sit after the pod has spoken, so a failed smoke test wastes five
phases rather than eight.

*Alternative considered:* the metered phase last, as the ninth. Rejected — it maximises the work at
risk from the one gate that can invalidate it.

### D3 — The ComfyUI core is pinned to the commit `:v0.10-rc` was built from

`0009:S5` asks for a pin. Pinning to upstream's head today would import an untested core into a
repair version and make "does the core alone shift output at a fixed seed?" a live question this
change cannot answer. Pinning to what `:v0.10-rc` built from makes the pin a **record of what already
ran**: those are the renders v0.10 shipped.

The recovery is free and offline of any GPU —
`docker run --rm ghcr.io/alxb1t/isekai:v0.10-rc git -C /opt/ComfyUI rev-parse HEAD`. The tag was
confirmed still present in GHCR while planning this change (`docker manifest inspect` returned its
manifest), so the route is available; if it were not, phase 2 halts rather than substituting head.

Bumping the pin forward is a separate, later, deliberate act that must carry its own evidence — a
render comparison at a fixed seed, which needs a baseline this project does not currently keep
(D10).

*Alternatives:* upstream head (imports an untested change); no pin, with a design note (leaves the
one unpinned link in the change whose thesis was pinning).

### D4 — What stays unpinned, said out loud

`Dockerfile:20` and `:38` run `uv pip install -r requirements.txt` against ComfyUI's and the
preprocessor pack's own requirement files. Both resolve at build time and neither is version-locked.
So **pinning the core moves the floating link rather than removing it**: after phase 2 the core is
fixed and its dependency closure is not, and two builds of an identical tracked `Dockerfile` still
differ.

This change does not fix that. Locking both closures is a new tracked artifact, a new derive-and-verify
step and a build that cannot be validated without a full image rebuild — a change with its own
proposal. What this change does is **refuse to let the pin imply more than it delivers**: the
CHANGELOG names the closure as the remaining unpinned surface and `## Open Questions` names it as the
next pinning target.

### D5 — The volume guard belongs in `up.sh`; the pod-side guard is defence in depth

`0009:R4` describes `mkdir -p "$MODELS_NAMESPACE"` creating the namespace on container disk when the
network volume did not mount, then downloading 16.5 GiB onto storage that dies at teardown. Its
suggested fix is `mountpoint -q /runpod-volume`.

**That fix does not work.** RunPod's pod-create schema defaults `volumeInGb` to 20 and mounts the
pod's own volume disk at `volumeMountPath` when no network volume is attached. So a pod created with
an empty volume id boots with `/runpod-volume` present and *being* a mountpoint — the wrong one.
`mountpoint -q` passes and 16.5 GiB lands on a 20 GB ephemeral disk.

The guard therefore goes where it costs nothing to trip: **`infra/up.sh` refuses to create a pod when
`RUNPOD_VOLUME_ID` is empty**, and passes it into the container so the entrypoint knows which volume
to expect. The pod-side check remains as defence in depth for the case the client cannot see — id
set, mount silently failed — with a free-space floor as the discriminator rather than
`mountpoint`.

The consequence is recorded rather than hidden: **the pod-side guard ships suite-bound and
unexercised on a pod.** Exercising it would mean deliberately defeating the client check that phase 1
adds, in order to test a configuration this repository no longer produces. `up.sh` also cannot be
overridden from the environment for this purpose — it does `set -a; source ./.env` *after* the
caller's environment, so `.env` wins.

*Alternative considered:* a second pod created with an empty volume id, ~3 min and ~$0.04. Rejected
on the above: it tests a state the repository will no longer create, and reaching it means editing a
real volume id out of `.env` on the clock with a stale blank as the failure mode.

### D6 — The hold is bounded at 900 s and the marker goes on container disk

`0009:S7` observes that the reachability hold turned a pod that died in seconds into one that holds
indefinitely, billing, with `sshd` up and no workload — and reporting as healthy. Its suggested bound
is `exec sleep 3600`. **3600 s is $0.74**, more than twice this repository's per-session ceiling; a
bound that itself exceeds the ceiling does not answer the argument that made it a finding.

**900 s ≈ $0.19** — longer than any inspection anyone would perform on a billed pod, and inside the
$0.30 wall on its own.

The marker goes to container disk, not into `$MODELS_NAMESPACE`: the namespace is exactly the thing
that may have failed, and a marker that a failing volume prevents you from writing does not make the
failure legible.

### D7 — `plan` emits a resolved absolute target; containment is checked where it resolves

`0009:S1` offers two shapes and calls the second better: a containment predicate in `decide`, or
`plan` emitting the already-resolved target so the shell joins nothing. They are not alternatives —
`plan` can only emit a resolved target if something resolved it, and that resolution is where the
containment check belongs. Both, then: the check in `decide`, the resolved path on the plan line,
and `target="${MODELS_DIR}/${dest}"` deleted from the driver.

This also shrinks `0009:S6`: with no path assembled in the shell, a manifest-controlled field can no
longer reach one. `S6`'s own two halves both land — the array read (`read -r -a`, which removes the
`shellcheck disable=SC2086`) **and** the runtime source-shape check, because doing one and not the
other leaves `provision.py` half-guarded in the phase whose subject is guards.

The plan-line format changes, so `land`, the driver and both infra tests move in one commit.

### D8 — Three stated ceilings, three numbers

| Ceiling | Value | Why this number |
|---|---|---|
| Long side | **4096** | 4:1 at a 1024 short side — past any real photo, and 1024×4096 is already a heavy SDXL allocation |
| Header dimension | **65535** | What JPEG's format already enforces, so both codecs refuse the same input and the spec can say so |
| Header walk | **4 MiB** | A camera's EXIF + thumbnail + ICC + XMP is a few hundred KiB; generous without being unbounded |

Each refuses by naming the file and the limit, in the style of the existing unreadable-header exit.

*Alternative considered:* only the long-side cap, on the reasoning that it bounds the render target
whatever the header claimed. Rejected — it does not bound the *parse*, so `0010:S5`'s measured 16.8 s
refusal on a 100 MB file survives, and it would report an aspect-ratio problem for a file whose real
defect is a nonsense dimension.

### D9 — `DWPreprocessor` at 512: the sentence is corrected, not the graph

`0010:R5` offers two options — set it to 1024, or record in `design.md` that a preprocessor's
internal resolution is a separate axis. Neither is taken, because the finding understates the
problem. The shipped living spec says "no control hint is registered against a different one"
(`workflow-injection:working-resolution:scale-precedes-every-consumer`, and the same sentence in
`README.md`). `DWPreprocessor` carries `resolution: 512` where tile and lineart carry 1024. **The
sentence is false as written**, and the test bound to that scenario checks image links only, so the
false clause is unenforced.

Setting it to 1024 measurably changes the render — a rendering question, and by this change's own
rule rendering questions wait for the evaluator. So the spec sentence is narrowed to what the suite
proves (every consumer receives the same scaled image), and the preprocessor's own working resolution
is named as a separate dial. `README.md` moves with it.

### D10 — What the smoke test may conclude, decided before it runs

The session runs **four renders at `--variations 1` with a fixed seed** — a landscape crop, a crop
above the working scale at an aspect no prior run produced, an EXIF-rotated JPEG, and a plain-JPEG
control — plus the loader probe of D11. One variation, because the criteria are dimensional and
structural: variations jitter dials, not dimensions.

**It may conclude:** the path runs end to end at four input shapes v0.10 did not test; each render's
dimensions equal the target injection computes from that file's header; and what ComfyUI's
`LoadImage` at the pinned commit does with an EXIF `Orientation` on each codec.

**It may not conclude, and the CHANGELOG says so:**

- Nothing about identity, fidelity or quality. No evaluator exists and none was run.
- **Not that renders are unchanged from v0.10.** The core is pinned to the commit v0.10 booted, so
  the core is not a variable — but the dependency closure was re-resolved at build (D4), and **no
  v0.10 PNG baseline was kept** (the probe directory holds `run.json` files only), so there is
  nothing to diff against. Render equivalence is unestablished and stays that way.
- Not the volume guard and not the bounded hold, both of which ship suite-bound and unexercised on a
  pod (D5, D6).
- Nothing about mutation, since each photo ran at one variation.

The second bullet is the honest form of the question "must the CHANGELOG name the core pin as an
unmeasured variable?" — after D3 the core is not the variable. Its closure is.

### D11 — The loader probe, because exit 0 cannot prove the rotated case

The rotated-JPEG case has no machine-checkable criterion as posed. If `LoadImage` did **not**
transpose, the graph would receive landscape pixels and the scale node — which scales to the exact
target rather than fitting to it — would squash them into the portrait target. `run.json` records
**the same dimensions either way**. Exit 0 and a dimension match are consistent with both the working
and the broken case. The only strong signals would be an eyeball, which this change forbids itself,
or InstantID failing on a sideways face, which is real but probabilistic.

So the session sends a **two-node graph — `LoadImage` → `SaveImage`, no diffusion — over the same
HTTP API and compares the saved file's dimensions**. Transposed gives one pair, untransposed the
other. It tests the loader directly rather than the parser, costs seconds and no GPU, and settles
D12 in the same act by sending a PNG carrying an `eXIf` chunk through the identical graph.

That probe graph lives in this change's `probe/` directory, never in `workflows/`, so the one-path
rule is untouched. Its output is saved to `probe/` alongside the renders, because phase 7 depends on
it.

### D12 — The PNG `eXIf` item, and why it waits for the probe

Found while planning this change, not exported by either converge pass — so this change's content is
twenty findings **plus one**, and saying "the twenty" would be false.

PNG can carry an `eXIf` chunk; Pillow's `Image.getexif()` reads it and `ImageOps.exif_transpose` acts
on it. `_png_dimensions` reads IHDR and stops. If `LoadImage` transposes PNGs, this is the same
defect v0.10 called blocking, in the codec branch that was not fixed — and **every input this project
has ever rendered is a PNG**.

It is scheduled at phase 7, *after* the pod, because if the probe says PNGs are not transposed then
the correct action is **no fix**: adding an `eXIf` read would introduce the very mismatch v0.10
closed, in the opposite direction. Phase 7 therefore has two legitimate outcomes — the fix with its
scenario, or a design note recording that the codecs differ and why the parser is right to differ
with them. Deciding it by reading `nodes.py` would establish what Pillow is *asked* to do, not what
the pinned build does.

### D13 — The trust root is derived, not transcribed — and it was verified before this was cut

`0010:S4`'s suggested fix is to spell the constant once so three files cannot drift. That removes a
transcription risk that a single re-derive also removes, while leaving `derive_manifest.py`'s own
"derived, never transcribed" claim false for the one entry where it matters most.

Civitai's public API returns per-file `hashes.SHA256` for a model version. `derive_manifest.py`
already fetches over the network for every other entry, so this one joins them and the human leaves
the loop. The residual is unchanged and stated: Civitai is still the trust root, publishes no
signature, and WAI has no first-party host.

**Verified while planning this change**, so phase 8 carries no discovery risk and forces no image
rebuild:

```
transcribed WAI_SHA256   f116b0c78ff441467b0cdc8f1936e1ed18ea31e9997c7b132b1b8db533f0bd04
Civitai API  SHA256      F116B0C78FF441467B0CDC8F1936E1ED18EA31E9997C7B132B1B8DB533F0BD04   ✓
models.json  bytes       6938040682   =   API sizeKB × 1024                                  ✓
```

The re-derive must leave `scripts/models.json` byte-identical, which is the manifest's own existing
invariant.

*Alternative considered:* recording BLAKE3 too, which the same API publishes. Rejected — it is not
in the standard library, so verifying it would need a wheel the runtime rule forbids, and recording
a field nothing reads is the same smell as a one-entry registry. Its existence is noted here as
something a human re-verifying by hand can cross-check.

### D14 — Probe inputs are constructed, not committed; the recipe is

None of the four inputs exists. The sibling project's portrait outputs are 832×1216 (the size v0.10
already ran) and 1248×1824; all are PNG and all portrait, so there is no landscape input and no JPEG
anywhere. They are built from those outputs:

- **landscape** — a crop of a portrait to roughly 832×554, so short-side rounding runs on the height
  axis for the first time.
- **above the working scale** — the 1248×1824 asset cropped to a different aspect (e.g. 1248×1400).
  Uncropped it is the *same* aspect as the 832×1216 photo v0.10 rendered, so it would compute to the
  identical 1024×1472 target and prove nothing beyond the direction of the scale.
- **rotated JPEG** — a portrait rotated 90° so its pixels are stored landscape, saved as JPEG, with
  an APP1 segment spliced in declaring Orientation 6. `tests/images.py`'s existing EXIF helper emits
  a correct big-endian TIFF IFD, so the segment is generated by code the suite already trusts. This
  is byte-for-byte what a phone writes, and `LoadImage` cannot tell who wrote the tag.
- **plain JPEG control** — the same portrait as JPEG with no EXIF, so a failure on the rotated case
  is attributable to the tag rather than to the codec, which this project has never fed to a pod.

They are **not committed**: this repository commits `run.json` artifacts and never inputs, v0.10 set
that precedent deliberately, and committing derived faces into a repository whose product is identity
preservation invites a confusion the README would then have to disclaim. Each fixture's dimensions
and SHA-256 go in `probe/README.md` so a re-run is verifiable, and the construction script — taking
source and destination as arguments, so no path outside this repository is tracked — is committed to
`probe/`.

*Alternative considered:* sourcing a real phone photo from the internet. Rejected on three counts: it
puts a stranger's face through a face-embedding pipeline without consent, it is not reproducible, and
it proves nothing the constructed file does not.

### D15 — The record is written forward, never backward

`0010:R4` (the proposal's 1152 against the shipped 1024), `R5` and `R8` all ask for a sentence in
`0010`'s own documents. `0010-illustrious-base` is **archived**, and an archived change is a record of
what was decided *then*; editing it to say what was decided later destroys the property that makes it
a record. All three are recorded in **this** change's `design.md` and CHANGELOG, which is what a
reader following the version chain will hit.

On `0010:R4` specifically: this change **records the reading and admits it is unverified**. The
proposal said a short side of 1152 because MistoLine's card requires above 1024; `WORKING_SCALE = 1024`
shipped, with a code comment calling 1024 "the floor MistoLine's card names". One of the two readings
is wrong, and which one is a **rendering** question — so it waits for the evaluator and is not
re-tested here.

### D16 — No register change, and why not even the tempting one

v0.10 recorded that dropping `realistic, photorealistic` from the negative left renders reading as
semi-realistic digital painting rather than flat anime screencap, and named it "the first thing to
check next version". It is not done here. It and the unmeasured quality ladder wait for the evaluator
version: v0.10 was declared the last version permitted to settle anything by eye, and changing a
register now moves the floor the evaluator is about to measure against.

### D17 — `0009:R3` corrects the comment rather than copying the configs

`rm -rf "$MODELS_ROOT"` deletes `models/configs/*.yaml` that the ComfyUI clone tracks, under a comment
calling the tree "empty". Copying them into the namespace would add a write at boot that then has to
be ordered against the new volume guard, and would restore a config dropdown only to loader classes
this repository's one-path rule forbids ever using. The graph uses `CheckpointLoaderSimple`, which
takes no config. The defect is a false comment; the comment is fixed.

### D18 — Verdict

**`feasible-with-caveats`.** Every item has a phase, a fix shape and a check. The caveats are three,
each written down rather than smoothed over: the volume guard and the bounded hold ship unexercised
on a pod (D5, D6); the image's Python dependency closure stays unpinned after the core is pinned
(D4); and no baseline exists against which render equivalence with v0.10 could be established (D10).

## Risks / Trade-offs

- **The smoke test fails and invalidates an earlier phase** → the version halts, is fixed, and a new
  `-rc` is dispatched for a **second** metered session. The ceiling is **per session**, so a re-run
  is a new session at ~$0.19, not an overrun of the first. `tasks.md` says so up front rather than
  discovering it on the clock.
- **`:v0.10-rc` becomes unavailable before phase 2 runs** → phase 2 halts. It must not substitute
  upstream head, which is the outcome D3 exists to avoid. The tag was confirmed present while this
  was written.
- **The re-derive in phase 8 does not reproduce `models.json` byte-for-byte** → halt. The manifest's
  own invariant is that a re-run leaves it identical; a diff means something changed upstream and is
  a finding, not a file to commit. Pre-verified in D13, so this is unlikely rather than unguarded.
- **The `latest` guard added in phase 5 rejects the phase 6 dispatch** → it fails loudly and free,
  before any pod. This is why CI is not hoisted earlier: the dispatch is the act that tests it.
- **Two guards ship unexercised** (D5, D6) → mitigated only by being stated, in the CHANGELOG and in
  the spec's own scenario text. This is a real residual and is not written as anything else.
- **The dependency closure stays unpinned** (D4) → mitigated by naming it rather than by letting the
  core pin imply reproducibility, and by recording it as the next pinning target.
- **The plan-line format change in D7 touches `land`, the driver and two infra tests** → one commit,
  moved together; the suite is offline and catches a partial move.
- **The metered session overruns** → hard halt at 45 minutes per the repository guardrail, with the
  session planned against 24. Budget: pod boot and image pull dominate; v0.10 rendered ten images in
  an 8m23s session including boot, so four renders and two probe calls are not the constraint.

## Migration Plan

No data migration. The volume is not re-provisioned: no manifest entry moves and `models.json` is
byte-identical, so the pod boots against the warm volume and verifies it.

The metered session, in order:

1. Announce, then `infra/up.sh` with `RUNPOD_IMAGE` set to `:v0.11-rc` in `.env` — `start.sh` and the
   `Dockerfile` both changed, so `:latest` would boot the wrong thing.
2. Confirm the volume mounted and the manifest verified from the container log before rendering.
3. The loader probe first (seconds, no GPU) — it is what phase 7 consumes, and a failure there should
   not be discovered after the render budget is spent.
4. Four renders, `--variations 1`, one fixed seed across all four.
5. `scp` the renders, the `run.json` files and the probe output off the pod. **The pod's disk is
   ephemeral; only the models volume persists.**
6. `infra/down.sh`, then confirm the pod is gone through the RunPod MCP and record what it returned.
7. Clear `RUNPOD_IMAGE` from `.env` — a stale value silently pins every later pod to an unreleased
   image.

Rollback: `:latest` is untouched until the release merges, so any pod created without `RUNPOD_IMAGE`
continues to boot the v0.10 image throughout.

## Open Questions

- **Locking the image's Python dependency closure** (D4). Deferred deliberately: it needs its own
  proposal, a new tracked artifact and a full image rebuild to validate. Named here as the next
  pinning target so the core pin is not read as more than it is.
- **Whether ComfyUI's core pin should ever be bumped forward, and on what evidence.** A bump needs a
  render comparison at a fixed seed, which needs a baseline this project does not keep. Recording one
  — the CLI writing its working resolution into `run.json`, and renders kept for comparison — is the
  evaluator version's call, as `0010:R8` already observed.
- **`0009:S3`** — six manifest entries have no publisher-controlled source. Argued and accepted in
  `0009`'s `design.md`, exported on the **unscheduled** track with a trigger rather than to a version.
  Not reopened here.
</content>
