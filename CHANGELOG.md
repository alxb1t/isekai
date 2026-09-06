# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).

> **On this record's provenance.** This file was **backfilled during v0.7**, from the git
> history, after eleven phases and three releases had already shipped without it. Entries are
> reconstructed from commit messages and diffs; **anything the log does not support is not
> written here.** From v0.7 on, an entry is appended per phase under `## [Unreleased]` and cut
> at release, as the project's change contract requires.
>
> Two gaps in the record, stated rather than smoothed over:
>
> - **There is no 0.5.0.** The history goes v0.4 (2026-08-04) directly to v0.6 (2026-08-15).
>   No tag, branch or commit references a v0.5, so the version was skipped rather than lost.
> - **0.4.0 and 0.6.0 were never tagged.** They are real, completed, merged versions and are
>   recorded as releases here; their dates are their last commit rather than a tag date.
>   Tags `v0.1`–`v0.3` also use the two-part form that predates the current release contract.
>
> `0.7.0`'s heading is cut here, in the commit that completes the work; the annotated `v0.7.0`
> tag is the release act and is created against **this** commit, so the four places the
> version line lives — proposal, changelog, `pyproject.toml`, tag — all name the same thing.

## [Unreleased]

### Added

### Fixed

- **Three real plumbing failures, found on the renders already on disk, before any pod was created.**
  Running the scorer against `outputs/final/`'s ten 1024-canvas PNGs cost nothing and paid for itself
  three times. This is what ordering the metered session *last* is for.
  - **StyleID returned a `ModelOutput`, not a tensor.** `get_image_features` gives a bare tensor in
    transformers 4.x and a `BaseModelOutputWithPooling` in 5.x, whose `pooler_output` is the same
    already-projected vector. Both are now accepted, and a shape that is neither refuses loudly —
    because the extra declares `transformers>=4.49` and a silent change here would surface as a cosine
    over the wrong axis rather than as an error.
  - **DWPose is top-down, fixed at batch five, and emits SimCC rather than heatmaps.** It was being
    handed a whole image at batch one, which raises — so the axis correctly reported its own absence,
    for entirely the wrong reason. It now uses the person detector that was already pinned but never
    called, repeats the crop to fill the traced batch of five, and decodes `(5, 133, 576)` x-logits
    against `(5, 133, 768)` y-logits over 133 whole-body keypoints.
  - **`yolox_l.onnx` emits undecoded predictions.** Its `(1, 8400, 85)` output carries per-anchor
    offsets, not coordinates; reading columns 0–3 as pixels produced a confident-looking box in
    entirely the wrong place, and the pose read inside it came back as 133 keypoints every one of which
    fell under confidence. Found by looking at the value ranges rather than the shapes — the columns
    were negative. The standard YOLOX grid/stride decode is now done here, over a letterboxed input
    rather than a stretched one, because the model was trained that way.
  - **After the three: the scorer runs to completion on both directories, all five axes reporting.**
    No claim is made about the numbers — the dials moved six ways per render and these are the wrong
    subjects. What was proven is the plumbing.
- **`ty check` is green whether or not the extra is installed.** `eval_backends.py`'s unresolvable
  imports are scoped with a `[[tool.ty.overrides]]` block rather than per-line `ty: ignore` comments,
  which cannot be right in both environments: absent the extra they are load-bearing, present it they
  are "unused directive" warnings, and ty exits non-zero on warnings. `make gate` must not depend on
  what the operator happens to have synced. Every other check still applies to that file, which is how
  a genuine `invalid-return-type` on `OnnxSession.run` was caught and fixed — `onnxruntime` returns a
  `Sequence`, not a `list` — rather than suppressed.

### Added

- **`evaluate.py`, a second entry point beside `convert.py` and never on its import graph.** Four axes
  over a canvas the photograph and the render provably share: face (StyleID, plus ArcFace tagged
  falsify-only), pose (PCK), hair colour (CIEDE2000), and a face-location guard. It is deliberately not
  a subcommand — a subcommand would put the `[eval]` extra one misplaced import away from breaking
  `convert.py`'s `dependencies = []`.
- **Every rule the scorer applies is stdlib-only and therefore tested in CI with the stack absent.**
  `isekai/evaluate.py` holds the canvas, the guard, the refusals and the report and imports nothing
  third-party; the models arrive through Protocols that `isekai/eval_backends.py` implements. That is
  the same seam `ComfyTransport` is under, for the same reason — 47 tests over the scorer's behaviour
  run offline against fakes.
- **The canvas comes from the injector, and a mismatched render is refused naming both sizes.**
  `canvas_for` calls `working_resolution` and `image_dimensions` rather than restating the rule, and
  the photograph's pixels are transposed for a rotating EXIF tag **before any region is parsed** — the
  header parser returns dimensions, and `LoadImage` transposes both codecs, so a photograph parsed
  upright against transposed pixels would place every region wrong with all four numbers still looking
  plausible. The canvas is settled before any model is asked anything, which a test asserts.
- **Regions come from the photograph only.** The render is sampled inside the photograph's own mask and
  never handed to a parser — a human parser is trained on photographs and its behaviour on a drawing is
  unknown. A region under a **measured area floor** refuses naming itself and its area, rather than
  reporting a number derived from too few pixels; the per-class accuracy filter is not here, because it
  would have discarded classes on someone else's test-set numbers.
- **The guard computes both methods on every run** — box IoU and landmark-centroid alignment — and
  names which one was authoritative. Which one ships is decided by measurement in phase 8, not by
  argument. A failed guard refuses every region axis naming the guard as the cause, while the pose axis,
  which needs no region, still reports: a guard failure does not deprive the operator of the
  measurements it does not invalidate.
- **Absence is its own field and never a low score.** `face_detected` and `render_face_detected` are
  separate from every value, a pose reader that read nothing reports its own absence rather than a
  zero, and low-confidence keypoints are dropped and counted rather than scored at a guessed
  coordinate.
- **A cross-base comparison refuses per axis, not globally.** The embedding axes refuse with the reason
  in the record while colour, area and keypoints still report. **A run recording no base is treated as
  unknown rather than as matching** — the case this exists for is an old manifest that predates the
  provenance keys, where assuming a match would compare across bases silently.
- **The report emits no combined score, no verdict and no percentage.** One JSON record per render and
  one table per run; every column states its direction and whether it is absolute or relative; the run,
  the base and the image are named so a table read months later can be attributed. Every claim the
  numbers do **not** support is printed beside them, including that no axis isolates one dial.
- **CIEDE2000 is implemented in-tree and checked against Sharma, Wu & Dalal (2005)'s own 34-pair
  reference table**, to four decimals, plus symmetry and the neutral-chroma cases. That table was
  constructed to catch exactly the discontinuities an implementation gets wrong, which makes it a
  stronger check than trusting a transitive dependency — and it keeps scipy, networkx and imageio out
  of the lock for one closed-form function of six numbers.
- **The `[eval]` extra is five packages and CI never installs it.** `torch` and `transformers` are
  unavoidable rather than convenient: StyleID publishes only a `CLIPModel` safetensors and the DWPose
  artifact `models.json` pins is a TorchScript `.pt`. `onnxruntime` (MIT) carries the region parser and
  the anime-face detector. The gate array stays five commands and `convert.py` keeps
  `dependencies = []`.
- **`ultralytics` is absent from `pyproject.toml`, from `uv.lock` and from the scorer's import graph**,
  asserted by three tests rather than left to a licence review nobody runs. Verified with the whole
  extra installed: it is not importable.
- **The stdlib guard uses `-S`, and the AST fallback was not needed.** `design.md` D12 left the
  mechanism open because `-S` inside a uv venv was unverified. It was verified here, both ways: `-S`
  leaves no site-packages on `sys.path`, `import convert` succeeds under it, and `import pytest` fails
  under it — so the guard is falsifiable rather than passing for the wrong reason.
- **`run.json` becomes a provenance record, not only a reproduction one.** It recorded `seed`,
  `variations`, `seeds` and `overrides`, and so could not name the photograph, the graph, the base or
  the resolution — the two batches in `outputs/final/` are identifiable only from this file's prose,
  and a baseline nothing can identify is not a baseline. It now also records the input photograph's
  SHA-256, the base checkpoint the graph loads, the resolved working resolution, and a `renders` list
  carrying, per variation, the image it was written to, its sampler seed, a digest of **the graph as
  submitted**, and the dial values that graph actually carried.
- **The dials are recorded per variation, not once**, because under jitter every variation carries its
  own and a single record would be a lie about all but one of them. They are read off the submitted
  graph rather than reconstructed from the seed and the overrides — reconstructing them would mean
  re-deriving the mutator in order to read it. The three ControlNet strengths are keyed by node id,
  since they are tuned differently and "tile, pose, lineart" is an ordering nothing in the graph
  states.
- **The photograph is recorded as a digest and never as pixels.** A digest of a face is not a face, so
  the rule that derived faces are not committed is untouched — and the digest is exactly what makes an
  uncommitted input checkable rather than merely trusted, as `probe/README.md` already does.
- **Keys are added and none removed**, so a manifest written by an earlier version stays readable and
  a reader written against the old shape keeps working; a test holds that. The digest helper is
  spelled in `pipeline.py` rather than imported from `isekai.provision`, which has one: that module is
  deliberately off `convert.py`'s import graph, and importing it for four lines would put it on.
- **A render with the graph's own dials is possible for the first time.** `pipeline.run` called
  `mutate` unconditionally on every variation, and `mutate` moves six dials at once — `denoise`,
  `cfg`, `ip_weight` and all three ControlNet strengths — so **nothing this repository has ever
  rendered differs from its neighbour in one thing**, and "same subject, one thing moved" was not a
  claim it could make. `run` gains `fixed_dials` and the CLI gains `--fixed-dials`, **off by default**,
  so every existing invocation behaves exactly as it did.
- **A held run still draws its own sampler seed per variation**, because otherwise it would be one
  render billed N times. The seed draw is split out of `mutate` as `draw_seed` and stays the *first*
  draw `mutate` makes, so a held run and a jittered run from the same run seed carry the **same**
  sampler seeds and differ in the jitter alone — which makes the two directly comparable rather than
  merely both reproducible. An override still applies under `--fixed-dials`: holding the dials means
  not jittering *around* the base, never ignoring the base the user set.
- **`cn_strength` becomes settable.** The identity node's second dial — the keypoint route, beside
  `ip_weight`'s embedding route — sat at 0.5 in the graph and was referenced nowhere else in the tree:
  not in `apply_overrides`, not in `mutate`, not in any test. It joins `apply_overrides` and the CLI as
  `--cn-strength`, range-checked at parse time in zero-to-one like its neighbours. It is set on
  `ApplyInstantIDAdvanced` and **never** on a `ControlNetApplyAdvanced`, which is a different dial that
  happens to share a word — setting it there would move pose and structure while claiming to move
  identity, and a test asserts every ControlNet strength is untouched.
- **`cn_strength` is pinned** beside `PROBE_DENOISE` and `PROBE_IP_WEIGHT`, so a silent re-tune becomes
  a deliberate test edit. Unlike those two it was never *chosen* by anybody — it is the value the graph
  arrived with — so the pin records where the baseline was rendered rather than a preference. **0.5 is
  unsearched: this version makes it searchable and deliberately does not search it**, because searching
  a dial with the same renders that validate the instrument would leave neither result clean.
- **Every model the evaluator will load is pinned, before a line of scorer code exists.**
  `scripts/eval_models.json` — twelve entries, each with an immutable-revision URL, a SHA-256 and a
  byte count — is a **sibling** of `scripts/models.json` and never a section of it: that file is what
  the pod provisions **the graph** from, and these run locally on the operator's machine. It is
  *derived*, not transcribed, by `scripts/derive_eval_manifest.py`, under the same rule its sibling is
  under: re-running it must leave the file byte-identical.
- **Three destinations are copied out of the graph's manifest byte for byte** —
  `insightface/models/antelopev2/glintr100.onnx` and the two DWPose artifacts. For `glintr100` that is
  load-bearing rather than tidy: the scorer's ArcFace has to be the artifact the generator injects
  identity *with*, or the whole claim about self-grading would be a claim about two different models.
  `shared_entries_that_differ` compares whole entries, not just digests, so the two files cannot drift
  apart unnoticed — a matching digest beside diverged sources would mean the same bytes arriving from
  different places, which is exactly the drift the copy exists to prevent.
- **`isekai/eval_models.py`**, the gate every scorer axis will reach its weights through. It refuses
  three ways: an artifact the manifest does not declare, an entry whose sources are not pinned
  revisions, and bytes on disk that do not hash to the pin — the last naming the file, the expected
  digest and the computed one, because a human reading a mismatch is deciding whether a pin is stale
  or a file has been swapped, and two of the three do not answer that. The pin check runs even though
  nothing is fetched: an entry pointing at `resolve/main/` says nothing about which bytes those were.
  Nothing here knows about an axis, and it stays off `convert.py`'s import graph.

### Notes

- **Every licence was read on 2026-09-06 and recorded in `scripts/eval_licences.md`**, each with the
  URL it was read at and quoted verbatim from the source. **None forbids this use.**
- **DWPose was the one entry left open, and it closes clean: Apache-2.0.** So the pose axis is
  unthreatened on licence grounds, and the contingency where it would have reported its own absence
  rather than a zero is not needed.
- **The conflict this version was cut believing in does not exist.** StyleID's CC BY-SA 4.0 is on
  **the website** — footer boilerplate from the academic project-page template it is built on. The
  repository and the model card agree with each other: *"StyleID is released for non-commercial
  research use."* The adjacent clause, *"Do not use FFHQ-derived data for biometric human
  recognition"*, governs the **dataset** and not the encoder; it is recorded because it is adjacent,
  not because it binds.
- **Four artifacts are non-commercial research and are carried as recorded deviations** — StyleID,
  `segformer_b2_clothes` (NVIDIA Source Code License, inherited from SegFormer), and `glintr100`, whose
  restriction this project has been shipping since v0.9 because InsightFace's library is MIT and its
  weights are not. **Stated rather than discovered later: if this project ever became commercial, all
  four would bite at once, and retroactively against a baseline already in git.** There is no
  mitigation beyond knowing it. The rule that survives is the load-bearing half — **a model whose
  licence is restrictive may not be the sole carrier of an axis**; StyleID ships beside ArcFace or not
  at all.
- **The AGPL detector was replaced, because the artifact the design named does not exist.** The plan
  was to load `Fuyucchi/yolov8_animeface` (AGPL-3.0) through `onnxruntime` and never import
  `ultralytics`, so that no AGPL *code* is combined with this Apache-2.0 public repository. Checked on
  2026-09-06: that repository publishes **no ONNX at all** — its Hugging Face tree and its sole GitHub
  release both carry only `yolov8x6_animeface.pt` — so the mechanism had nothing to point at.
  Exporting the `.pt` ourselves was rejected: it needs `ultralytics` installed and yields an artifact
  with no upstream revision to pin. Pinned instead: **`deepghs/anime_face_detection`,
  `face_detect_v1.4_s`, MIT** — a published ONNX, which **dissolves** the copyleft problem instead of
  routing around it, and which keeps the guard measurable both ways rather than collapsing it to one
  method. Recorded residual, not relied on silently: deepghs's MIT tag is their own declaration over
  weights trained with `ultralytics` tooling, and Ultralytics asserts AGPL over such weights — an
  assertion about *weights*, which this repository distributes none of and links no code from.
- **A pre-v0.12 `run.json` is refused by name, not guessed at.** Both directories in `outputs/final/`
  were rendered before the provenance record existed, and the scorer says exactly what it lacks — no
  `photo_sha256`, so the photograph supplied cannot be confirmed; no `base`; no `renders` — and exits
  1. Guessing would be worse than refusing: a comparison against the wrong photograph produces four
  plausible numbers and no way to notice one of them is about somebody else.
- **All twelve pinned eval artifacts were fetched and verified against `scripts/eval_models.json`**
  before anything was scored. Every digest matched.
- **No scorer code, no axis and no render change.** This phase pins artifacts and records licences;
  `workflows/pipeline.json`, `scripts/models.json` and the `Dockerfile` are untouched, no image is
  rebuilt and no volume is re-provisioned.

## [0.11.0] - 2026-09-06

### Fixed

- **The capacity floor is raised clear of the container disk as well as the volume disk.** Moving the
  floor from free space to capacity widened the passing set, and one wrong disk entered it: the case
  the pod-side guard exists for at all is the one `up.sh` cannot see — the volume id is set and the
  mount silently failed — where `/runpod-volume` falls through to the container overlay, whose backing
  disk is `containerDiskInGb: 30` (`infra/up.sh`). `avail` on that overlay, already carrying the
  image, was far under the old 20 GiB floor and refused; `size` reports ~27.9 GiB regardless of what
  the image occupies, and passed. The floor is now **40 GiB**, derived against both wrong disks —
  20 GB volume disk ≈ 18.6 GiB, 30 GB container overlay ≈ 27.9 GiB — and against the right one, the
  80 GB network volume ≈ 74.5 GiB. It is one measurement still, not two: the rejected alternative was
  a second free-space check beside it. The error text now names what it measured and which two
  ephemeral disks a reading that small means. `design.md` D5 and D5a and `tasks.md` are reworded off
  the free-space mechanism they still described.
- **A manifest destination is held to the same whitespace rule as a source, and one that resolves to
  the models root itself is refused rather than crashed on.** `resolve_dest` is the single site the
  containment rule is enforced at, and it had two holes: a `dest` containing `\n` or `\t` survived
  `normpath` into the tab-delimited plan line, where an embedded newline starts a fresh record whose
  target is absolute and whose URL never meets `PINNED_SOURCE` — that check lives in `decide`, which
  an injected record bypasses; and a `dest` normalising to `"."` (`"."`, `"./"`, `"a/.."`) raised
  `IndexError` off `PurePosixPath(".").parts` being empty, instead of returning `None` as the
  function's own contract says. `plan` additionally refuses to emit any target carrying `\n` or `\t`,
  which covers the half of the target that comes from `MODELS_DIR` rather than from the manifest.
- **The header-walk refusal names the codec that gave up.** `_HeaderTooDeep`'s message was
  JPEG-worded — "no frame header" — but the PNG chunk walk raises it too, from two places, so an
  operator handed a corrupt PNG was told the file lacks a structure PNG does not have. The exception
  now carries its codec and the message renders it, still naming the file and the byte budget.
- **`civitai_file` returns the digest alone.** Its size was read with a subscript where every sibling
  read uses `.get` with a `SystemExit`, so a record omitting `sizeKB` aborted derivation with a raw
  `KeyError` — for a number the one call site discarded and the manifest never used, its `bytes`
  coming from Hugging Face. Dropped rather than defended.
- **The probe's JPEG segment walk no longer indexes past the end of the file.** `segments()` read the
  marker's code byte having tested only that the marker byte itself was in range, so a JPEG ending on
  a lone `0xFF` raised `IndexError`. A file that ends there has no segment left to report.
- **The pod-side volume guard measures capacity, which is what it is trying to prove, rather than
  free space.** The 20 GiB floor was read off `df -k --output=avail` while its error text claimed to
  have proved *identity* — "this is not network volume ${RUNPOD_VOLUME_ID}". Free space on a
  correctly-attached volume is whatever this project's 16.5 GiB of models plus the second project
  sharing that volume have left of it, so the guard was coupled to fill level and degraded
  monotonically as the volume filled. A warm boot on which every manifest entry would `SKIP` — a pod
  that needed to download nothing — would have been refused, written the failure marker and billed
  the whole 900 s hold. The floor is now on `--output=size`: total capacity discriminates the pod's
  own 20 GB ephemeral disk from the network volume whatever either currently holds, and the message
  says what is measured. Free space is not checked at all; if it ever should be, it is a second check
  with its own message, which is why it is not smuggled into this one.
- **A PNG declaring an `eXIf` chunk longer than the header budget is refused by name.** The chunk
  walk seeks over every payload but one: the `eXIf` branch called `read(length)` on the raw uint32 out
  of the chunk header, bounded by nothing. `MAX_HEADER_BYTES` is tested at the top of the loop and
  that branch returns before the next iteration, so a chunk declaring 0xFFFFFFFF asked for a 4 GiB
  read whose `MemoryError` neither `except` clause catches — a traceback instead of the refusal that
  names the file and the budget. It was the fourth ceiling in a phase whose subject was stating the
  three the header parse left open. The length is now checked against the budget before the read, and
  a chunk that overruns it raises the same `_HeaderTooDeep` the other ceilings do rather than
  truncating to a silently wrong orientation.

- **A rotated PNG is measured as it will be loaded, in the codec every input this project has ever
  used.** v0.10 closed this for JPEG and left PNG open, because `_png_dimensions` read IHDR and
  stopped. PNG can carry an `eXIf` chunk holding the same TIFF stream JPEG's APP1 does, and the
  phase-6 loader probe measured the pinned build rather than reasoning about it: a portrait PNG
  tagged Orientation 6 came back from `LoadImage` as **1216×832**, transposed, against an untagged
  control that did not move. Injection was therefore measuring such a file as its header states while
  the loader handed the graph the transposed pixels — and `ImageScale` runs with `crop: "disabled"`,
  so the photo would be squashed non-uniformly into the wrong frame and the distorted face fed to
  InstantID, the VAE encoder and all three preprocessors at once. Exactly the defect v0.10 called
  blocking, in the branch that was not fixed. The parser now walks the PNG's chunks to the pixel data
  looking for `eXIf`, and both codecs share one TIFF orientation reader rather than each having its
  own. The scenario the fix is bound to now names both codecs, because the mismatch is a property of
  the loader and not of the container.

### Added

- **The base checkpoint's digest is derived from its publisher's own record, not transcribed.**
  `derive_manifest.py`'s docstring claimed the manifest is "derived, never transcribed" while the one
  digest that matters most was a constant a human typed — and it is the entry where the digest is not
  merely a check on the transfer but the **whole trust root**, because WAI has no first-party host
  and every source is a mirror. It existed in three places that compared against each other, which
  cross-checks the copying and not the value. The deriver now fetches it from Civitai's public
  model-version record (`https://civitai.com/api/v1/model-versions/2883731`, read 2026-09-06), like
  every other digest, and holds the mirrors against that. The parse is a pure function so the suite
  checks it offline; only the fetch touches the network.

  The residual is unchanged and stated: **Civitai is still the trust root**, it publishes no
  signature, and the digest is computed by the platform after upload — an independent cross-check of
  the mirrors, not an attestation by the author. **BLAKE3 is deliberately not recorded** although the
  same API publishes it: verifying it would need a wheel the stdlib-only runtime rule forbids, and a
  field nothing reads is the same smell as a one-entry registry. The hand-written copy in the suite
  stays, on purpose — it is the *offline* anchor the gate holds, and an anchor that fetches is not
  one.
- **CI enforces the `latest` protection its own header comment claims.** `build-image.yml` asserted
  that a manual run "can never clobber the image a rollback would reach for" while interpolating an
  unvalidated `workflow_dispatch` string straight into `tags` — so a dispatch naming `latest` did
  exactly that, and a newline in the input would have been honoured as a second tag by
  `docker/build-push-action`'s newline-separated `tags` field, which a `gh workflow run` or a REST
  dispatch can supply. A first step now fails unless the input matches `^[A-Za-z0-9._-]+$` and is not
  `latest`, and assigns the validated value to a step output the build step reads, so the raw input
  is never interpolated into `tags` at all. The dispatch default, still `v0.9-rc` two versions on,
  now names `v0.11-rc`.
- **Three stated ceilings on measuring a photo, each a refusal rather than a clamp.** The short-side
  rule bounds one axis and says nothing about the other, and a header field was an unverified number
  until something bounded it. The computed target's **long side** is capped at 4096 — 4:1 at a 1024
  short side, past any real photo, and 1024×4096 is already a heavy SDXL allocation. A
  **header-declared dimension** is capped at 65535, which JPEG's own two-byte frame field already
  enforces, so both codecs now refuse the same input. The **marker walk** stops after 4 MiB, so a
  file whose frame header sits arbitrarily deep is refused rather than read to its end. Each names
  the file and the limit. None clamps: a clamped target no longer preserves the aspect ratio, and
  would squash the photo the way the orientation rule exists to prevent.
- **A pod is refused before it is created if it was not told which network volume to use.**
  `infra/up.sh` now checks `RUNPOD_VOLUME_ID` before the create call and passes it into the
  container, so the entrypoint is told which volume to expect rather than inferring it. The failure
  this prevents — the full 16.5 GiB model stack downloaded onto storage that dies at teardown —
  renders correctly, bills fully, and is discovered only on the next metered session. The suggested
  pod-side fix, `mountpoint -q`, does **not** work: RunPod defaults `volumeInGb` to 20 and mounts the
  pod's own volume disk at `volumeMountPath` when no network volume is attached, so the path exists
  and *is* a mountpoint — the wrong one. The entrypoint therefore keeps a second check as defence in
  depth, with a free-space floor above what that 20 GB disk could ever report as the discriminator.
- **The provisioning guards moved from the suite into the module, where they can bite on a pod.**
  Four manifest checks had no caller outside `tests/test_manifest.py`: they constrain the manifest
  this repository tracks, and constrain nothing about a manifest the module is handed on the pod —
  which is what joins a destination onto the filesystem and hands a URL to a transfer. `decide` now
  refuses, before any byte moves and naming the entry, a destination that is absolute or resolves
  outside the models root, a source that is not a pinned URL free of whitespace, and an entry that
  declares no sources at all. The last is refused **by name** rather than reported as "every source
  was rejected" with an empty reason list: an entry that offered nothing and an entry whose every
  offer was refused are different failures with different fixes.
- **The plan line carries the already-resolved destination.** `provision.py` resolves it once and
  `scripts/download_models.sh` no longer assembles `"${MODELS_DIR}/${dest}"`, so a manifest-controlled
  field can no longer reach a path join and the containment rule has exactly one site. The resolution
  is lexical, because the models root on the pod *is* a symlink onto the namespace.
- **The driver reads its sources as an array rather than word-splitting a string.** `IFS=$'\t' read
  -r -a` makes the sources a list from the moment the line is read, so a source's own shape cannot
  change how many arguments `wget` is given. The `# shellcheck disable=SC2086` that made the split
  legal is gone with it — the suppression was the marker, and the split was contained only by an
  argument-parsing accident.
- **The graph↔manifest binding keys on an explicit set of class names, not a `*Preprocessor`
  suffix.** A suffix rule binds the nodes spelled that way and silently passes the ones that are not:
  `InstantIDFaceAnalysis` fetches the whole antelopev2 pack and matches no pattern at all. The
  mapping is now a census of every class the shipped graph uses, so a node added to the graph fails
  the check until someone answers whether it fetches for itself, and the five antelopev2 destinations
  are bound to the node that fetches them.
- **The provisioning hold is bounded and leaves a marker.** A provisioning abort used to hold the pod
  open with `tail -f /dev/null` — reachable, but reporting as running and healthy while it billed
  indefinitely. It now holds for 900 s (~$0.19 at the rate this project runs on, inside the ~$0.30
  per-session ceiling) and writes a failure marker to **container disk**, never into the models
  namespace: the namespace is exactly the thing that may have failed, and a marker a broken volume
  prevents you from writing does not make the failure legible.

### Changed

- **ComfyUI's core is pinned to a commit — the last unpinned link in the change whose thesis was
  pinning.** `Dockerfile` cloned the default branch head while both custom-node packs beside it were
  already pinned, so an image rebuilt a month later ran a different inference engine with no record
  that it had. The pin is `250b2e9551a7bc7a8ebb5beb07e0fecd2983e04a`, **recovered from
  `ghcr.io/alxb1t/isekai:v0.10-rc` itself** rather than taken from upstream today: it is a record of
  what already ran, so the core is not a new variable. Bumping it forward is a separate, deliberate
  act that must carry a render comparison at a fixed seed.
- **The reachability hold covers preparing the namespace, not only fetching into it.** Creating the
  namespace and relinking the models root now sit inside the same guarded step as the download, so a
  failure there reports and holds instead of terminating the entrypoint — which under `set -e` took
  the SSH daemon with it and left no way in. Preparing the volume is provisioning by any reading a
  human would give the word; the guarantee is about provisioning and not about one of its steps.
- **The `rm -rf` of the models root is guarded on its premise rather than on its proxy.** What made
  the delete safe was that the tree is the image's own, on container disk; the check was that the
  path is not yet a symlink. A non-empty tree someone has mounted there is a real models tree, and
  the entrypoint now refuses rather than deleting it. Deleting one is an explicit operator act.

- **A metered pod session exercised four input shapes v0.10 named as untested, and a loader probe
  settled a question exit codes cannot.** `probe/README.md` is the record. One session on
  `:v0.11-rc`, 9 min 33 s and ~$0.11 against a 45-minute, ~$0.30 ceiling; teardown confirmed through
  the RunPod MCP with its response recorded. All four renders exited 0, and each render's dimensions
  equal the target `working_resolution` computes from that file's own header — including 1536×1024,
  the first target produced by rounding on the **height** axis, and 1024×1152, an aspect no prior run
  produced. The pinned ComfyUI core was confirmed on the pod itself.

  **What the session did not establish is stated in the same breath**, in `probe/README.md` and here:
  nothing about identity, fidelity or quality, because no evaluator exists and none was run; **not**
  that renders are unchanged from v0.10, because the dependency closure was re-resolved at build and
  no v0.10 PNG baseline was kept, so there is nothing to diff against; **not** the volume guard and
  **not** the bounded hold, both of which ship suite-bound and were never reached on a healthy pod;
  and nothing about mutation, since each photo ran at one variation.

### Notes

- **The unreconciled 1152, recorded and left unverified.** v0.10's proposal says the working scale
  targets a short side of **1152**, on the reading that MistoLine's card requires *above* 1024;
  `WORKING_SCALE = 1024` shipped, under a comment calling 1024 "the floor MistoLine's card names".
  Two readings of one sentence, and one of them is wrong. The reading this repository runs on is
  1024, and every render it has ever shipped was made at it. **Which reading is right is a rendering
  question, so it waits for the evaluator and was not re-tested here** — nothing in this version
  should be read as saying the 1024 was validated. What changed is that the disagreement is written
  down where a reader following the version chain will hit it, rather than sitting unremarked between
  an archived proposal and a code comment. v0.10's own documents are not edited: an archived change
  records what was decided then.
- **The pose-grid sentence is corrected in both places it was written.** `workflow-injection`'s
  `scale-precedes-every-consumer` claimed "no control hint is registered against a different one",
  and `README.md` repeated it. It is false: `DWPreprocessor` derives its hint at `resolution: 512`
  where tile and lineart carry 1024, and the test bound to the scenario checks image links only — so
  the false clause was unenforced. The scenario is narrowed to what the suite proves, that every
  consumer is handed the same scaled image, with a preprocessor's own working resolution named as the
  separate dial it is. **The graph is unchanged**: moving that dial measurably changes the render, and
  rendering questions wait for the evaluator.
- **A `spec_exempt` label now says what it is.** `"structural: pins the dials the phase-5 probe
  chose"` described a by-eye value pin as structural, which is the opposite of what it is. It reads
  `"preference, not a scenario: holds the dials design.md D9 records as by-eye"`. No behaviour
  changes; the point is that a reader auditing the exemptions is told the truth about which ones are
  load-bearing.
- **Pinning the core moves the floating link rather than removing it, and this change does not claim
  otherwise.** `Dockerfile` still runs `uv pip install -r requirements.txt` against ComfyUI's own
  requirement file and against the preprocessor pack's, and neither is version-locked: both resolve
  at build time, so after this pin the core is fixed and its dependency closure is not, and two
  builds of an identical tracked `Dockerfile` still differ. **The image is not reproducible.** Locking
  both closures needs a new tracked artifact, a derive-and-verify step and a full rebuild to
  validate — its own change, and named here as the next pinning target.
- The comment above the models namespace no longer calls the tree it replaces empty. The ComfyUI
  clone tracks `models/configs/*.yaml`, so it is not; the delete drops them **knowingly**, because
  the graph uses `CheckpointLoaderSimple`, which takes no config. Copying them in would add a write
  at boot to be ordered against the new volume guard, and would restore a config dropdown only for
  loader classes this repository's one-path rule forbids ever using. The defect was a false comment,
  and the comment is what is fixed.
- **Both new guards ship suite-bound and unexercised on a pod.** Exercising the pod-side volume check
  would mean deliberately defeating the client check added beside it, in order to test a
  configuration this repository no longer produces; exercising the bounded hold would mean breaking
  provisioning on metered time. This is a real residual, and it is written down rather than smoothed
  over.

## [0.10.0] - 2026-09-05

### Fixed

- **A rotated phone photo is measured as it will be loaded, not as its header states.** ComfyUI's
  `LoadImage` applies the EXIF `Orientation` tag before any node sees the pixels, so for the ordinary
  case of a phone held upright the frame header's 4032x3024 is transposed to 3024x4032 by the time
  the graph has it. Injection computed its target from the untransposed pair and `ImageScale` runs
  with `crop: "disabled"`, which scales to the exact target rather than fitting to it — so the photo
  was squashed non-uniformly into a landscape frame, silently, and the distorted face was fed to
  InstantID, the VAE encoder and all three preprocessors at once. The header parser now reads the tag
  and swaps the pair on the four values that transpose.
- **A camera JPEG whose frame header sits past 64 KiB is read rather than refused.** The parser read
  a fixed 64 KiB prefix on the premise that the frame header is near the front; an EXIF segment
  carrying an embedded thumbnail may alone be 65 533 bytes, and cameras write ICC and XMP segments
  besides. Such a file walked off the end of the prefix and hard-exited with "cannot read the image
  dimensions from its header" — a well-formed photo reported as a defective one. The marker walk now
  runs against the open file, reading each segment's header and seeking over its payload, so it is
  bounded by the file rather than by a guess. Standalone markers and a segment length below 2 are
  now rejected in the same pass, both of which previously stepped the walk into a payload where
  arbitrary bytes could be read back as a frame header.

### Added

- **The publisher-stated digest of a mirror-only artifact is a spec'd requirement.** The base
  checkpoint's tie to the SHA-256 Civitai publishes was checked by the gate but bound to a scenario
  about digests being present, which it does not prove. `model-provisioning`'s immutable-pins
  requirement gains the case the base actually depends on — an artifact its publisher does not host
  is pinned to the digest the publisher states — and the one-checkpoint assertion is split into its
  own test against the one-path rule.

### Removed

- **Animagine XL 4.0 leaves the manifest.** It had been the rollback and the probe's comparison
  base since the WAI entry landed; with the swap proven, a declared checkpoint nothing renders with
  is a second path in everything but name, which this repository's one-path rule forbids
  (`design.md` D3). `cagliostrolab` leaves the `publishers` list with it. The manifest is now 15
  entries and 16.5 GiB, down from 16 and 23.0 GiB. **A re-provision after this point removes
  Animagine from the volume**, so rolling back to it means reverting the manifest, not just
  `ckpt_name`.

### Changed

- **`README.md` and `CLAUDE.md` describe an Illustrious base.** The path table and the "How it
  works" line name WAI-illustrious-SDXL v17.0, the working-resolution rule and the committed CLIP
  layer are written down, and the ControlNet stack is described as the strength-to-zero comparison
  left it — including that "changes the render" is not "improves the render", and that tile carries
  its publisher's animation disclaimer as a known deviation. `1girl`'s defect is recorded as
  **closed**, with the mechanism that closed it named: the identity node's face embedding, not a
  tagger. **Neither document makes any claim about identity or quality.**

### Notes

- **The path runs on WAI-illustrious-SDXL v17.0, at stated input resolutions.** Two photos of
  different aspect ratios through the unmodified `convert.py`, both exiting 0 and writing
  `0.png`–`4.png` plus `run.json`: 982×1559 rendered at **1024×1600** and 832×1216 at
  **1024×1472**, every variation. Each rendered dimension equals the target the injector computes
  from the photo's own header — the first live confirmation of the scale node on real files.
  Session 8 min 23 s at $0.72/hr = **$0.10**; teardown confirmed through the RunPod MCP (`get-pod`
  → 404 "pod not found", `list-pods` → 0 items). `RUNPOD_IMAGE` was cleared from `.env` afterwards.
- **What this version does not establish**, stated plainly because v0.8's Verified block implied a
  generality it never tested: **nothing** about identity, fidelity or quality — no evaluator exists
  and none was run; **not** that the chosen dials are good, let alone optimal; **not** that any
  ControlNet improves output, only that each retained one measurably changes it; **not** that the
  register improves anything. It also does not establish that the path runs at *any* resolution —
  both photos were portrait and both below the working scale, so a landscape input and a photo
  above 1024 on its short side remain untested on a GPU.
  What it establishes is that the path runs on WAI at the two stated input resolutions, and that a
  male photo yields a male-presenting output.

### Changed

- **The probe's verdicts are applied, and both are "no change to the graph".** The chosen
  `denoise` 0.65 and `ip_weight` 0.9 are the values already committed, and the tile ControlNet is
  kept because the strength-to-zero comparison found it strongly distinguishable from absent. They
  are now **pinned by the suite** rather than merely present, so the evaluator version inherits a
  baseline it can measure against and a silent re-tune becomes a deliberate test edit.
- **The stack walk is under test.** `KSampler.positive` may point at `ApplyInstantIDAdvanced`
  directly *or* through a stack of `ControlNetApplyAdvanced` nodes, so the encoder must be found by
  following the link and never by class lookup. The probe could have shortened that stack, which is
  exactly when the property would have broken unnoticed; a test now walks it end to end and asserts
  the hop count matches the number of ControlNets in the graph.
- **`scripts/models.json` is unchanged, so the image is not republished.** Nothing dropped out of
  the graph, so the manifest the pod provisions from still matches it and `:v0.10-rc` stays the
  image the final renders boot.

### Notes

- **The v0.10 probe ran on a pod and its results are recorded** in
  `openspec/changes/0010-illustrious-base/probe/`. WAI provisioned alongside Animagine at boot from
  the manifest, verified: 6,938,040,682 bytes, exactly the count the manifest declares. Session
  18 min 27 s at $0.72/hr = **$0.22**, inside the 45-minute / ~$0.30 ceiling; teardown confirmed
  through the RunPod MCP (`get-pod` → 404 "pod not found", `list-pods` → 0 items).
- **Every ControlNet is kept.** A strength-to-zero comparison at a fixed seed, with no mutation and
  every other dial held, asked one falsifiable question per ControlNet: does the conditioning reach
  the sampler at all? Tile is **strongly** distinguishable from absent — hair length, garment and
  framing all change — and OpenPose and MistoLine are distinguishable subtly. None is
  indistinguishable, so none is deleted, **including tile**, which `design.md` D7 named as the
  likely deletion and left to the comparison to decide. TTPlanet's own card disclaimer — "no comic,
  animation application are promised", recommended strength 0.9 against the 0.2 this graph runs —
  is therefore recorded against it as a **known deviation**, not resolved. This establishes only
  that each retained ControlNet measurably *changes* the render, never that it improves it.
- **`denoise` 0.65 and `ip_weight` 0.9 are chosen — a preference, not a measurement.** Found by eye
  against one photo at a fixed seed, over three denoise points and one ip_weight point. They are
  the values already in the graph: they were tuned on Animagine with no reason to expect they would
  transfer, so this is a real search with a null result. **Chosen is not best**, and the search was
  coarse — four renders inside a 25-minute budget.
- **The gender check passes.** A male-presenting input photo, at the new register with `1girl`
  removed and a fixed seed, produced an unambiguously male-presenting output. This is the one
  falsifiable acceptance criterion the register change gets and it could have failed. One photo is
  an existence proof that the identity embedding supplies the axis, not a rate.
- **The first thing to check next version.** As `design.md` D4 predicted, dropping `realistic,
  photorealistic` from the negative removed a push away from the photograph, and these outputs read
  as semi-realistic digital painting rather than flat anime screencap. Recorded as a finding for
  the evaluator version, not as a reason to reinstate a gender tag.

### Added

- **`ghcr.io/alxb1t/isekai:v0.10-rc` is published**, and it is the image both metered phases boot.
  The pod provisions from the manifest baked into whatever image it runs, and `:latest` is v0.9's
  — so a pod on `:latest` would provision v0.9's manifest and never fetch the checkpoint the graph
  now names. No `Dockerfile` change was needed: `ImageScale` and `CLIPSetLastLayer` are core
  ComfyUI, so this is a rebuild rather than a change. `:latest` is deliberately **not** touched;
  CI publishes it from a push to `main` and nowhere else, and the manual dispatch requires a tag
  and names it "never `latest`", precisely so a pre-release build cannot clobber the image a
  rollback reaches for. The tag becomes v0.10's on merge, by the mechanism that already exists
  (`design.md` D8). `RUNPOD_IMAGE` is set in the untracked `.env` and is cleared after the last
  metered phase, since a stale value would silently pin every later pod to an unreleased image.

### Changed

- **BREAKING — the base is WAI-illustrious-SDXL v17.0, and the register is its publisher's.** The
  positive is the content tags with WAI's own ladder appended last, where every published sample
  puts it; the negative is the publisher's own short form. WAI's page warns that too many quality
  tags and over-long negative prompts *reduce* image quality, so taking its positive while keeping
  v0.8's eighteen-token negative would have taken half the guidance and ignored the half stated as
  a warning (`design.md` D4). One consequence, recorded rather than absorbed: `realistic,
  photorealistic` is gone from the negative, which removes a push *away* from the photograph on a
  product whose whole subject is a photograph — if renders come back more photographic than v0.8's,
  that is the first place to look. Both literals stay pinned by equality, so changing either is a
  deliberate test edit.
- **The graph stops CLIP at the second-to-last layer.** Every one of WAI v17's published sample
  images carries `clipSkip: 2` and none of the publisher's prose mentions it, so a graph without a
  `CLIPSetLastLayer` ships a configuration the publisher never tested while looking identical to
  one that does (`design.md` D6). Both text encoders take their CLIP through it — routing only the
  positive would condition the two halves against different text towers. The value is pinned like
  the prompt: configuration, not a dial.

### Removed

- **`1girl` is out of the committed positive; `solo` stays.** `solo` is what does the Danbooru
  mode-selection work, while `1girl` additionally asserted a gender that the identity node's face
  embedding already carries — so that axis now belongs to a mechanism already in the graph rather
  than to a tagger that does not exist (`design.md` D5). This closes the defect v0.8 recorded and
  named a later version as the owner of. **It is not yet demonstrated**: whether a male photo
  yields a male-presenting output is this version's one falsifiable acceptance criterion for the
  register change, and it is checked on a pod, not here.

### Notes

- The negative carries one tag beyond the publisher's quoted short form: `nsfw`, which the same
  model page instructs users to add to filter its four safety-rating tags. On a product that
  converts photographs of real people, omitting an instruction the publisher gives by name would
  be a defect rather than fidelity to the quote.

### Added

- **The photo is scaled to a working resolution before any node reads it.** An `ImageScale` node
  sits between the image loader and every consumer — the latent encoder, the identity node and all
  three ControlNet preprocessors — so one pixel grid feeds the whole graph and no control hint is
  registered against a different one. Previously the render happened at whatever size the input
  happened to be, so "the path runs" was a claim about the photos that were tried.
- **`isekai.workflow` derives the render target from the photo's own header.** `image_dimensions`
  parses JPEG and PNG headers directly — stdlib only, nothing new enters `convert.py`'s import
  graph — and `working_resolution` preserves aspect, puts the short side at 1024 and rounds both
  dimensions to a multiple of 64, in **both** directions, so a small photo is scaled up as well as
  a large one down. A short side rather than a pixel budget: at a fixed megapixel count the short
  side moves with the aspect ratio, so a wide photo would land below MistoLine's floor while a
  squarer one cleared it, and nothing in the run would say so (`design.md` D2). An unreadable or
  truncated header stops the run naming the file; there is no default size, because a silently
  wrong resolution is a wrong render rather than an error.

### Changed

- **`inject` takes the photo's local path.** No node available to this pipeline can derive a target
  from the image it is given, so the dimensions are computed by injection and written into the
  scale node. The path is passed from the `input_path` `pipeline.run` already holds, so it stays an
  argument rather than becoming state.

### Added

- **WAI-illustrious-SDXL v17.0 is declared in the manifest**, alongside Animagine rather than in
  place of it. The bytes come from pinned Hugging Face mirror revisions — WAI has no first-party
  Hugging Face repo — and the digest verified against them is **the SHA-256 Civitai itself
  publishes** for the model version, checked mechanically by `derive_manifest.py` against the
  digest the primary mirror serves. That is what makes a mirror a CDN rather than a trust root:
  the digest is the acceptance test, so any host serving matching bytes is equally acceptable
  (`design.md` D1). Six byte-identical alternates are declared, so v0.9's fallback walking has
  somewhere to go if the primary disappears mid-version. Two things the record deliberately does
  **not** claim: the byte count discriminates nothing, since every published WAI version reports
  the identical one, and Civitai's digest is computed by the platform after upload — an
  independent cross-check of the mirrors, not a signature by the model's author. Civitai's own
  download is **not** declared as a source: `provision.py` accepts only a Hugging Face
  `resolve/<40-hex>/` URL, and widening that for one entry would weaken the no-mutable-ref check
  to buy availability six mirrors already supply.
- **Animagine's entry stays.** It is the rollback and the probe's comparison base until the swap
  is proven, and the graph↔manifest binding runs one way, so an extra entry is legal. It is
  removed in this change's final phase (`design.md` D3). Nothing is removed here.

## [0.9.0] - 2026-09-05

### Changed

- **The ordered fallback list is now walked at transfer time, not only at pre-flight.** A FETCH
  plan line carries every source that survived the pre-flight, in the manifest's order, and the
  driver walks them: a dead mirror or bytes that fail verification advance to the next source, and
  only exhausting all of them aborts the entry. Previously the plan named a single URL, so the one
  failure the alternates existed for — a mirror that has gone away, which the pre-flight cannot
  distinguish from "publishes no digest" — aborted the pod boot with the alternate untouched
  (`design.md` D16).
- **A provisioning abort now holds the pod open instead of stopping the container.** `start.sh`
  guards the provisioning call; on failure it prints the reason and `exec`s a foreground hold with
  `sshd` still alive, ComfyUI not started and nothing deleted. Under `set -e` the non-zero exit
  previously killed PID 1 and took the SSH daemon with it, so the file the abort policy leaves "on
  disk for a human to inspect" was unreachable and every re-boot died at the same line
  (`design.md` D17).
- **The stack now provisions from the manifest alone, and the unchanged path renders off it.**
  One pod, 23.3 minutes of wall clock, on a volume created empty for this purpose. All 15 entries
  were fetched from their pinned `resolve/<sha>/` URLs and SHA-256 verified before landing; the
  volume ended holding **exactly the manifest and nothing else** — 15 files, 16.51 GiB, every size
  byte-identical to its declared `bytes`, zero `.partial` files, zero unexpected extras. Then
  `convert.py` rendered the untouched Animagine path: exit 0, `0.png`–`4.png` and `run.json`.
  Cost: 23.3 minutes at the pod's quoted $0.72/hr is ~$0.28, and RunPod's billing aggregate had
  not settled at the time of writing — it still reported the pre-session figure. The operator
  raised this session's ceiling to ~$0.48 in advance; the wall-clock figure is inside it.
  **What this establishes is exactly two things**: that the stack is reproducible from a pinned
  manifest, and that the unchanged path renders from a volume whose entire contents were placed
  by the script. It establishes **nothing** about identity, fidelity, quality or the base —
  `ckpt_name` is still Animagine XL 4.0 and the graph, the CLI and the transport are untouched.
- **The skip path was proven on the warm volume, in the same session.** Re-running the driver
  printed `skip (present, verified)` for all 15 — each one re-hashed off the volume and compared,
  not accepted by name. That is the case a pinned manifest exists for and the one a
  download-path-only check would never reach.
- **The annotator redirect was confirmed on the filesystem, and the log did contradict it** —
  exactly as `design.md` D7 warned. `comfyui_controlnet_aux` printed
  `Using ckpts path: /opt/ComfyUI/custom_nodes/comfyui_controlnet_aux/ckpts`, its pre-override
  value, while `/proc/<pid>/environ` on the running ComfyUI showed
  `AUX_ANNOTATOR_CKPTS_PATH=/opt/ComfyUI/models/annotator_ckpts` and all four checkpoints sat on
  the volume under it. Trusting the log would have produced the wrong conclusion. Note also that
  the variable reads **empty in an SSH session**, because a login shell does not inherit Docker
  `ENV`; only the container's main process does, which is why `/proc` is the check and not `echo`.
- **The 80 GB volume was destroyed**, after and only after that render. Confirmed through the
  RunPod MCP: `204` on delete, absent from the volume list, `404 network volume not found` on
  lookup. The replacement is 40 GB, sized from both projects' manifests (~27.3 GiB together).

### Removed

- **`ghcr.io/alxb1t/isekai:latest` was not touched by this phase.** The metered pod ran
  `:v0.9-rc`, published by a manual CI run, and the two tags resolve to different digests — so the
  image a rollback would reach for is still the released v0.8 one.

### Added

- **The 62 GB models volume was inventoried, and nothing on it is unaccounted for.** One pod,
  read-only, 6.6 minutes of wall clock; teardown confirmed through the RunPod MCP, which returned
  an empty pod list and `404 pod not found` for the pod's id. On cost the two available figures
  disagree and both are recorded rather than one being chosen: 6.6 minutes at the pod's quoted
  $0.72/hr is $0.08, while RunPod's daily aggregate reports $0.19 of pod GPU for the day, and the
  per-pod hourly breakdown had not settled at the time of writing. Either figure is inside the
  ceiling. 48 files, 55.85 GiB, classified
  exhaustively:

  | class | files | size | |
  |---|---|---|---|
  | placed by this project's script | 11 | 16.15 GiB | every non-annotator entry of the v0.9 manifest |
  | placed by the sibling project | 10 | 10.81 GiB | nested one level deeper, under `models/` |
  | orphaned Qwen weights | 4 | 28.89 GiB | removed from the script by v0.8, never from disk |
  | staging and cache leftovers | 23 | ~1 KB | the `.hf` tree, three `.cache/huggingface` trees, one 0-byte `.partial` |
  | **unaccounted for** | **0** | **—** | **the gate on phase 9's destroy** |

  Both projects' scripts are pinned and checksummed, so everything the first two classes hold is
  re-downloadable; the remaining 28.89 GiB answers to nothing.
- **The annotator gap is confirmed empirically.** All four annotator checkpoints —
  `yolox_l.onnx`, `dw-ll_ucoco_384_bs5.torchscript.pt`, `sk_model.pth`, `sk_model2.pth` — are
  **absent from the volume**. They were being re-fetched to container disk on every pod's first
  render, exactly as the proposal argued from reading the graph.
- **The antelopev2 pin is confirmed from the volume itself.** The leftover cache tree names
  `ba0c3e10f4548361eb9a63265d87ce1140ab5a05` — the same DIAMONIK7777 revision the manifest pins,
  recorded independently by a download this change did not make.
- **The volume was extended from 62 GB to 80 GB** by the operator during this phase, so the
  "98% full" pressure recorded in `proposal.md` is relieved. It does not change the plan: the
  volume is still replaced rather than pruned, because pruning proves nothing about the manifest.
- **Correction to `proposal.md` and `design.md`: the two repositories' `.env` files do *not*
  disagree.** Both name the same volume id, and it is the account's only volume. What differs is
  the **key name** — this repo uses `RUNPOD_VOLUME_ID`, the sibling `RUNPOD_NETWORK_VOLUME_ID` —
  which is almost certainly what was mistaken for a stale id. There is no stale id to reconcile;
  phase 9 still updates both.
- **Phase 9's open question is answered.** Both manifests together are ~27.3 GiB
  (this project 16.5 GiB across 15 entries, the sibling 10.8 GiB), so the new volume needs
  roughly 40 GB for comfortable headroom — half of what the current one now carries, once the
  orphaned Qwen weights are gone.

- **`README.md` and `CLAUDE.md` describe a pinned stack.** The weights line now says the stack is
  provisioned from a pinned, checksummed manifest and that the volume is namespaced per project;
  the layout gains `scripts/models.json`, `scripts/derive_manifest.py` and `isekai/provision.py`;
  the pod-lifecycle diagram shows the `/runpod-volume` mount and the namespace symlink.
  `CLAUDE.md` records that the living spec goes to five capabilities when `model-provisioning` is
  archived, and that `provision.py` is not in `convert.py`'s import graph, so the stdlib-only
  runtime rule is untouched. **No claim is made about identity, quality or the base** — this
  version changed none of them. The five-command gate array is unchanged.

- **The volume mounts at `/runpod-volume` and the models directory is one symlink into this
  project's namespace.** `infra/up.sh`'s `volumeMountPath` moves off `/opt/ComfyUI/models`, and
  `start.sh` points `/opt/ComfyUI/models` at `/runpod-volume/isekai`. Because
  `folder_paths.models_dir` is then itself inside the namespace, **every** node resolves there —
  including the InstantID node and the Impact Subpack, which ignore `extra_model_paths.yaml` and,
  unredirected, auto-download a broken nested antelopev2 pack. One symlink also makes a scratch
  namespace and a rollback the same operation.
- **The volume is shared, so nothing here reaches outside `/runpod-volume/isekai`.** Artifacts
  the sibling project also uses are duplicated rather than shared: at $0.07/GB/month that is
  about 32¢/month, and it keeps this project's manifest describing bytes this project's pins
  control.

- **`AUX_ANNOTATOR_CKPTS_PATH` moves 386 MB of annotator checkpoints onto the volume.**
  `comfyui_controlnet_aux` writes them to `<node dir>/ckpts` — the pod's container disk, which
  does not survive the pod — so `yolox_l.onnx`, `dw-ll_ucoco_384_bs5.torchscript.pt`,
  `sk_model.pth` and `sk_model2.pth` were re-fetched from Hugging Face, unpinned, during the
  first render of every pod, on metered time. Redirected onto the models tree they are ordinary
  manifest entries, fetched and verified ahead of time. The pack reads the variable as
  `os.getenv(NAME, default)`, so the environment wins over its own `config.yaml`.
- **⚠️ The pack's own log cannot confirm this.** It prints `Using ckpts path: …` from the
  *config-derived* value, not from the override, so it will report the old path while writing to
  the new one. Confirmation is a directory listing on the pod, never a log line. A future reader
  will otherwise reach for the log and conclude the redirect failed.

### Added

- **The graph and the manifest are bound by a test.** Every model filename `pipeline.json` names
  in a node's input must have a manifest entry, matched against the tail of a destination so
  `instantid/diffusion_pytorch_model.safetensors` and `openpose/diffusion_pytorch_model.safetensors`
  stay two files rather than one. This is the only mechanism that would have caught the annotator
  gap, and the only one that stops it reopening when v0.10 edits the graph.
- **A tracked mapping from node class to the files that node fetches for itself**
  (`PREPROCESSOR_MODELS`), carrying the half of the binding the graph cannot supply.
  `LineArtPreprocessor` names no file and downloads two. A graph containing a preprocessor whose
  class is absent from the mapping **fails** rather than passing silently — an unmapped
  preprocessor is an unknown quantity, not a safe default. An empty tuple is a real answer:
  `TilePreprocessor` fetches nothing, and `DWPreprocessor` names its two files in its own inputs.
  The reverse direction is deliberately not asserted — the manifest legitimately carries the
  antelopev2 pack, which `InstantIDFaceAnalysis` resolves by directory and no graph field names.

### Changed

- **`scripts/download_models.sh` is a thin driver over the manifest.** It asks
  `provision.py` for a plan, runs `wget` for whatever URL it is handed, and asks the module to
  verify and land the result. Every entry is decided before any byte moves, so a mismatch on a
  warm volume stops the run instead of surfacing halfway through a 6.9 GB transfer. The inline
  per-model shell variables are gone — every source is now a URL string the manifest carries and
  the suite can inspect.
- **The image carries provisioning's three files, not one.** The `Dockerfile` copied only the
  script; it now also copies `scripts/models.json` and `isekai/provision.py`, preserving their
  relative layout because the module resolves the manifest relative to itself. `start.sh` invokes
  the driver at its new path.
- **`wget` is installed in the image.** The previous downloader used the `hf` CLI, so the image
  never needed it; the ported one does, and the image shipped `curl` alone.
- **Pre-flight does not follow the redirect.** `resolve/<sha>/<path>` answers 302 and carries
  `x-linked-etag` on *that* response — the CDN it points at does not repeat it — so following the
  redirect loses the header and silently degrades every entry to post-download verification. All
  fifteen entries were confirmed live to pre-flight and match.

### Removed

- **The `hf` CLI dependency.** Sources are plain `resolve/<commit-sha>/` URLs fetched with
  `wget`. The cost is `hf`'s resumable, parallel transfer; the `.partial` discipline means an
  interrupted transfer restarts from zero rather than being trusted.

### Added

- **The provisioning policy, in `isekai/provision.py` and reachable by `pytest`.** For each
  manifest entry the module returns exactly one decision: **skip** (present and its digest
  matches), **abort** (present and it does not — and the file is *left on disk*, because the
  volume is shared and a file this run did not write is not this run's to remove), or **fetch**
  from a named source. A file already at its destination is hashed, never taken on its name:
  verification that ran only on the download path would leave a warm volume permanently
  unchecked, which is the case the digest exists for. `land()` verifies a transferred file and
  only then moves it into place, so an interrupted or tampered transfer never occupies the final
  name — the next run sees the file as absent rather than as present-and-trusted.
- **A pre-flight seam.** Hugging Face publishes a file's SHA-256 in the `x-linked-etag` response
  header, so a source whose published digest already disagrees with the manifest is rejected in a
  second rather than after a multi-gigabyte transfer, and the entry's next declared source is
  offered instead. This is an optimisation, never a check: a source that publishes nothing — or
  a header that cannot be read — degrades to download-and-post-verify, never to trust. The seam
  is injected and `FakeFetcher` is what keeps the suite offline, the same argument and the same
  shape as `FakeComfyClient`.
- **`scripts/models.json`, a pinned and checksummed manifest of every model artifact the
  shipped graph needs — fifteen files across eleven sources.** Each entry names a destination
  under the models tree, a SHA-256, and an ordered list of `resolve/<commit-sha>/` URLs, so a
  source addresses bytes that cannot move. Four of the entries are the annotator checkpoints
  `DWPreprocessor` and `LineArtPreprocessor` fetched for themselves at graph-execution time —
  386 MB that nothing in this repository named, and that every fresh pod re-downloaded onto
  ephemeral disk during a metered render. `LineArtPreprocessor` fetches both `sk_model.pth` and
  `sk_model2.pth` unconditionally, regardless of the graph's `coarse: "disable"`, so both are
  declared.
- **`scripts/derive_manifest.py`, the helper that produced it.** Digests are *derived*, never
  transcribed: Hugging Face publishes each LFS object's SHA-256 as its object id, so no artifact
  is downloaded to learn its digest, and every alternate source is cross-checked against its
  primary at derivation time. Revisions are data in the helper rather than resolved from a
  branch, so re-running it is byte-identical — `git diff --exit-code scripts/models.json` is the
  check that the tool and the committed data have not diverged.
- **`isekai/provision.py`, the manifest's reader and its offline checks** — no source resolves a
  mutable ref, every entry carries a well-formed SHA-256, and every entry whose primary source is
  a mirror rather than the artifact's publisher declares an alternate. Each check is proven
  against a deliberately malformed entry as well as against the tracked file. The module is
  stdlib-only (`json`, `re`, `pathlib`) and is not in `convert.py`'s import graph.

## [0.8.0] - 2026-09-04

### Removed

- **The `qwen`, `animagine` and `animagine-i2i` paths.** All three are superseded by
  `animagine-i2i-cn`, which alone preserves identity, composition and pose. Gone with them:
  `workflows/qwen-image-edit.json`, `workflows/qwen-image-edit.reference.json`,
  `workflows/animagine-instantid.json`, `workflows/animagine-i2i.json`, their test fixtures,
  `inject_qwen`, and the four Qwen downloads in `scripts/download_models.sh`.
- **The `model-registry` capability.** Its three requirements — name resolution, injector
  pairing and mutation pairing — all describe a choice that no longer exists, so
  `openspec/specs/model-registry/` and `tests/test_model_dispatch.py` are deleted. The living
  spec goes from five capabilities to four.
- **Tests bound to the deleted paths**, including
  `test_run_without_overrides_is_byte_identical_to_v04`, which pinned v0.4's output for a path
  that is now gone, and the Qwen-only guards for a wired `cfg` dial and a graph with no identity
  node. Deleting them took the suite from v0.7's 114 tests to 81; the count going down is the
  work, not a weakened gate.
- **`tests/fixtures/`.** The fixtures were byte-identical copies of the shipped graphs with no
  drift check — a second thing to rename and a silent divergence waiting to happen.
  `tests/conftest.py` now loads `workflows/pipeline.json` directly.
- **`--model`, `--workflow` and `--prompt`.** The whole required surface becomes
  `convert.py photo.jpg`. `--prompt` was **required**, so this is **BREAKING** for every
  existing invocation: the positive prompt is now committed to the graph, which is what makes a
  render attributable. `--workflow` has no equivalent — edit `workflows/pipeline.json`.
- **Variation 0's verbatim-seed exemption.** Its stated reason was back-compat with releases
  this change deletes, and it left `--seed` with two meanings: a stream seed for variations
  1..N and a literal sampler seed for variation 0. **BREAKING**: `--seed 42` no longer
  reproduces v0.7's first render.
- **The conditioning trace in `inject`.** With no prompt to place, the walk from
  `KSampler.positive` to the first `CLIPTextEncode` has no caller. Its non-obvious insight —
  that the sampler's positive input may reach the encoder through a stack of ControlNet apply
  nodes, so it must be followed rather than looked up — is recorded in the change's `design.md`
  and in the `workflow-injection` capability header.
- **The model registry and every seam with nothing passing through it.**
  `isekai/models.py`, `Model` and `get_model` are deleted, and `Injector` and `Mutator` go with
  them from `isekai/comfy_types.py`. `pipeline.run` loses its `inject` and `mutate` parameters
  and imports them instead. `ComfyTransport` **stays** a parameter — `FakeComfyClient` is what
  makes the suite offline — and so does `workflow`, which keeps file I/O in the CLI. The rule
  this change learned: *a parameter is a seam only if something else is actually passed through
  it.*
- **Every branch with no reachable caller**: `overrides.py`'s silent no-op when a graph carries
  no `ApplyInstantIDAdvanced`, `mutate.py`'s wired-dial guard (it existed because Qwen wired
  `cfg`) and its `"102:14"` subgraph-id ordering, the `mutate is None` branch in `run`, and
  `find_node`'s `title` parameter — which no caller ever passed.
- **`arms crossed` from the committed positive prompt.** Pose is the OpenPose ControlNet's axis;
  a pose tag in the prompt competes with the mechanism that owns it. That is an architectural
  argument and needs no render to justify it — **this change makes no claim about what the graph
  now renders.**

### Changed

- **The surviving path is renamed to nothing.** `workflows/animagine-i2i-cn.json` →
  `workflows/pipeline.json`, `workflows/animagine-i2i-cn_ui.json` →
  `workflows/pipeline_ui.json`, `inject_animagine` → `inject`, and the one remaining `--model`
  value → `pipeline`. Every name available today describes the base or the technique, and v0.9
  replaces the base; the only name that version cannot invalidate is no name. The flag itself
  is then removed outright — see below.
- **Spec keys lose their model segment**:
  `workflow-injection:photo-wiring:controlnet-single-loader-across-stack` →
  `…:single-loader-fans-out`, and
  `workflow-injection:latent-init:img2img-inits-from-photo-below-one` →
  `…:inits-from-photo-below-one`.
- **BREAKING: `-o` names a directory, not a file**, defaulting to `./outputs`. A run writes
  `<output-dir>/<UTC instant>/0.png` … and a `run.json` beside them. An `-o` naming a file with
  an image extension is **rejected at parse time** — otherwise an upgrading caller silently gets
  a directory called `out.png`.
- **BREAKING: `--variations` defaults to 5**, capped at 25. Five renders to choose between is
  the product rather than an option; the ceiling exists because every variation is one billed
  GPU render, so an unbounded count bills a mistyped digit at GPU rates.
- **Every variation's seed is derived uniformly** from `--seed`, variation 0 included. The
  per-variation seed is still printed, and is now also recorded in `run.json`.
- `main()` resolves the run directory and hands the **resolved** path to `run`, which draws no
  clock of its own — which is what keeps the suite offline and deterministic.

### Added

- **Timestamped run directories and `run.json`.** The manifest records the seed the run was
  given, the per-variation seeds actually drawn and the dial values in force, so a run describes
  itself instead of depending on the operator still having the terminal it was printed to.
- **The positive prompt is pinned by equality** in the suite, and commented in
  `workflows/pipeline_ui.json` with the version that owns its register. "The string holds no
  subject text" has no mechanical form — a blacklist assertion is defeated silently by any
  rewrite — so equality makes every future prompt edit a deliberate test edit.
- **`README.md` and `CLAUDE.md` describe one path.** The four-row model table, `--model` and
  `--prompt` in the quickstart, and the "four selectable models" status line all go; the run
  directory layout is shown instead. `CLAUDE.md` retires the additive-models invariant — **"there
  is one path; a version may replace it, it may not add a second"** — and replaces the registry
  seam with the rule this change learned: *a parameter is a seam only if something else is
  actually passed through it.* The conditioning-trace insight the deleted code carried is
  preserved there by name.
- The `README.md` license line no longer claims to match a model license the repo does not ship;
  it states the repository's own licence and that weights are licensed by their publishers.
- **`CLAUDE.md`'s metered-work guardrail is rewritten.** Teardown confirmed through the RunPod
  MCP replaces the blanket "wait for an explicit human go". The new rule states all four things
  the old protocol got for free from a human being present: who **creates** (`infra/up.sh`), who
  **tears down** (`infra/down.sh` — teardown is the act), who **confirms** (the MCP — and
  confirmation is *not* the act), and what it **degrades to** when the MCP is unreachable (the
  human "go", unchanged, for the whole session). It carries a stated ceiling: **45 minutes,
  ~$0.30** per pod session. This is an authority *expansion* in an otherwise subtractive change,
  which is why it is its own entry rather than folded into the docs one.

### Verified

- **The one path was run live on a GPU pod on 2026-09-04**, on our own image against the
  persistent models volume: `convert.py <photo>` exited 0 for two separate input photos, each
  writing `outputs/<UTC instant>/` with `0.png`–`4.png` and a `run.json` carrying five seeds.
  This records that the path **runs**; it makes no claim about fidelity, identity or quality,
  for which this repository still has no evaluator.

### Known defects

- **`1girl` fixes the gender of every input photo**, in a product whose input is "a photo of a
  person". `1girl, solo` is the Danbooru mode selector for this base rather than subject text,
  and an empty positive is not neutral on a Danbooru-trained checkpoint, so removing it would be
  a register decision. v0.8 changes no base and therefore decides no register: the defect is
  stated here and owned by **v0.9**, the version that can probe a replacement against real
  renders.

## [0.7.0] - 2026-09-01

Adoption of the OpenSpec SDD repository standard, plus the defects that adopting it exposed.

### Added

- **The spec tree.** `openspec/specs/` across five capabilities — `model-registry`,
  `workflow-injection`, `workflow-mutation`, `comfy-transport`, `cli` — as keyed scenarios
  describing behaviour the repo already shipped. 91 scenarios across 22 requirements.
- **The change tree.** `openspec/changes/` with `archive/`, and `0001-mf-standard` carrying
  all four artifacts. The zero spec delta is declared with `skip_specs: true` in a tracked
  `.openspec.yaml`, so `openspec validate --strict` passes.
- **Spec-to-test binding.** `spec` and `spec_exempt` markers registered in
  `[tool.pytest.ini_options]`, and every test bound to the scenario it proves — 117 bindings,
  zero unmarked tests.
- **A root `Makefile`** with a `gate` target mirroring the declared gate array command for
  command, so the gate a human types cannot drift from the one the orchestrator runs.
- **`.python-version`**, pinning the interpreter to 3.12.
- **`## How a change is cut here` in `CLAUDE.md`** — the change contract stated in-tree for
  the first time: the four artifacts, the id scheme, the authoring commands, the `Change:`
  trailer, the version line.
- **Docstrings and type annotations throughout `isekai/`**, under a widened ruff selection.
- **This file.**

### Changed

- **The gate config moved to `.minions/minions.toml`**, the one path the orchestrator reads;
  `.gitignore` now excludes `.minions/*` while re-including that single tracked file.
- **CI invokes `make gate`** rather than keeping a third copy of the command list, which had
  already drifted — it was running `ruff format --check` and `ruff check` without the `.` the
  array names.
- **Ruff lint selection widened** from ruff's default to `["E", "F", "I"]`, then to
  `["E", "F", "I", "D", "ANN"]`. Selecting `E` whole enables `E501` line-length; `D` and `ANN`
  add docstrings and annotations.
- **`CLAUDE.md` rewritten** onto the repo's in-tree contract, and then onto the standard's
  template.
- **`README.md` rewritten.** It had duplicate `Quickstart` and `Setup` sections, marked
  shipped files `(planned)`, named one model where four ship, and mentioned the gate nowhere.
- **`.env.example` is now path-free**, declaring shape only.

### Fixed

- **`--variations N` billed N identical renders** on `qwen` and `animagine`. Both are
  registered without a mutation seam, so the graph never varied and N paid renders produced
  one image. Now refused before the photo is uploaded.
- **`--seed` was validated and then silently discarded** on those same models.
- **`--variations 0` uploaded the photo, rendered nothing and exited 0.** Now rejected at
  parse time.
- **`mutate` crashed with a bare `TypeError` on a linked dial.** In ComfyUI API format an
  input may legally be a `[node_id, slot]` link, and `workflows/qwen-image-edit.json` drives
  `cfg` that way — so a documented flag combination died on a raw arithmetic error. Now stops
  with a message naming the dial and the node driving it.
- **`--denoise 0.0` was silently discarded**, the value being falsy rather than absent.
- **`ValueError` on subgraph node ids.** Node ordering used `sorted(key=int)`, which cannot
  parse an id like `102:14`; the repo ships a graph containing exactly that.
- **A stray `$` in the unknown-model exit message.**

## [0.6.0] - 2026-08-15

### Added

- **`isekai/overrides.py`** — an `apply_overrides` seam setting user-chosen base dial values
  by `class_type`, and `--denoise` `[0, 1]`, `--cfg` `[0, 30]`, `--ip-weight` `[0, 1]` on the
  CLI, with a bounded-float argparse type factory turning an out-of-range value into a clean
  exit. `pipeline.run` applies overrides per variation **before** `mutate`, so
  `--denoise X --variations N` jitters around `X` and `--seed` reproduces the set.
- **`.minions/minions.toml`** (as `minions.toml` at the root), first declaring the gate array.

### Changed

- **Jitter is base-relative.** `mutate` reads a node's current value as the base and draws
  `uniform(base ± δ)` instead of an absolute `uniform(lo, hi)` — denoise ±0.05, cfg ±0.5,
  ip_weight ±0.05, each clamped to its valid bound. At the baked defaults this is
  byte-for-byte identical to the previous behaviour, pinned by a characterization test.

## [0.5.0]

Skipped — see the note at the top of this file.

## [0.4.0] - 2026-08-04

### Added

- **The workflow-mutation seam.** `mutate(workflow, rng)`, separate from `inject_*`: sets the
  KSampler seed and bounded-jitters `denoise` / `cfg` / `ip_weight`. `random.Random` is
  dependency-injected, so randomized code is deterministically unit-tested.
- **`--seed` and `--variations`**, validated at the boundary. Each variation's seed is
  printed — the reproducibility contract.
- **The `animagine-i2i-cn` model** — `animagine-i2i` plus a tile / OpenPose / lineart
  ControlNet stack, with `comfyui_controlnet_aux` and the SDXL ControlNet weights pinned into
  the image.
- **A generalized injection trace.** `inject_animagine` now walks `.positive` to the first
  `CLIPTextEncode`, so it lands through a ControlNet chain of any depth and serves the whole
  InstantID family.
- **ControlNet strength jitter** — every `ControlNetApplyAdvanced` strength varies ±0.1 around
  its tuned baseline, in deterministic node-id order so a seed reproduces the whole graph. A
  no-op on graphs without ControlNet nodes.

### Changed

- The default `--model` is now `animagine-i2i`.

## [0.3.0] - 2026-07-31

### Added

- **The `animagine-i2i` model** — the Animagine + InstantID base as img2img, taking its latent
  init from the photo via `VAEEncode` at `denoise < 1`, so the photo's composition survives.
  `denoise` becomes the identity-versus-style dial.
- The real exported Animagine img2img workflow, with the test fixtures locked to it.

## [0.2.0] - 2026-07-31

### Added

- **Model dispatch.** `--model {qwen,animagine}`, built test-first: each model owns a workflow
  JSON and an injection strategy, resolved through a name-to-`Model` registry.
  `pipeline.run` takes the strategy as a parameter rather than hardcoding Qwen.
- **The `animagine` model** — Animagine XL 4.0 with InstantID and InsightFace, where identity
  is an injected signal (face embedding and keypoints) on a from-noise SDXL base. InstantID
  nodes and weights added to the image.
- **The test harness and the transport seam** — a `uv` project with pytest, and a fake client
  standing in for ComfyUI so the suite runs offline.
- The real exported Animagine + InstantID workflow, with the test fixtures locked to it.

## [0.1.0] - 2026-07-28

### Added

- **The headless conversion pipeline.** `convert.py`, a zero-dependency CLI (stdlib `urllib`
  only) that uploads a photo, injects photo and prompt into a ComfyUI workflow by node
  `class_type` / title, submits to `/prompt`, polls `/history` and downloads from `/view`.
- **The container environment as code.** A CUDA base image with `uv`, PyTorch and ComfyUI
  serving on `:8188`, no model weights baked in; a compose file for local GPU passthrough;
  CI publishing the image to GHCR; and `scripts/download_models.sh` fetching Qwen-Image-Edit.
- **SSH into the pod image**, so `ssh -L` can reach ComfyUI privately: `start.sh` installs the
  injected public key, starts `sshd`, then runs ComfyUI in the foreground.
- **On-demand pod lifecycle.** `infra/up.sh` creates a pod from the GHCR image with the models
  volume and SSH attached, polls for its address and prints the tunnel command;
  `infra/down.sh` deletes it so per-second billing stops.
- **Self-provisioning models on boot** — `start.sh` downloads weights idempotently before
  launching ComfyUI, so a fresh pod populates the volume without manual setup.
- The validated API-format Qwen-Image-Edit workflow, and the runbook to drive it.

### Fixed

- **Blackwell (sm_120) GPUs could not run the image.** cu124 kernels gave "no kernel image is
  available"; PyTorch is pinned to 2.8.0 / cu128, whose wheels ship sm_120 kernels.

[Unreleased]: https://github.com/alxb1t/isekai/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/alxb1t/isekai/compare/v0.3...v0.7.0
[0.6.0]: https://github.com/alxb1t/isekai/compare/dffdd63...bbe6924
[0.4.0]: https://github.com/alxb1t/isekai/compare/v0.3...dffdd63
[0.3.0]: https://github.com/alxb1t/isekai/compare/v0.2...v0.3
[0.2.0]: https://github.com/alxb1t/isekai/compare/v0.1...v0.2
[0.1.0]: https://github.com/alxb1t/isekai/releases/tag/v0.1
