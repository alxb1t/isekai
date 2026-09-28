# Changelog

Notable changes, per [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0/).

A version's heading names its change: `## [0.25.0] - 2026-09-27 · 0035-the-flow-skills`. A bullet is one change
an operator notices, in 1–3 short lines — what changed and why — ending with its design id, `(0035 D2)`. It holds
no figure, file:line reference or pod id; a re-pinned flow's bullet names its new digest.

## [Unreleased]

## [0.29.0] - 2026-09-28 · 0041-the-right-machine

### Security

- A pod is created only beside a models volume large enough for the manifest, and with its libraries' telemetry
  and update checks off, so the machine rendering a likeness reports to no one (0041 D3, D4).
- `up.sh` checks a pod's host key against the fingerprint the pod printed, and keeps it for the strict tunnel; a
  mismatch, or no fingerprint in time, refuses and tears the pod down, so only the pod gets a photograph
  (0041 D1, D2).
- The privacy principles enter `docs/principles.md`, and `docs/decisions.md` records that renders stay on a pod
  and that the pod's operator is a trust boundary, accepted knowingly (0041 D5).
- One session rendered both flows through the checked host key and the strict tunnel, on a pod created with
  its telemetry switches set (0041 D6).

## [0.28.0] - 2026-09-28 · 0040-the-pod-image

### Security

- The image ships no SSH host key: each boot makes an Ed25519 key, serves with it alone and prints its fingerprint.
  ComfyUI writes only to memory and saves no metadata, and holds on too little memory; the environment now installs
  before the node clones (0040 D1, D2, D3, D4).

### Changed

- A pod boots image `v0.28-rc1`, built on request from this version's tree, so it carries the key and memory
  changes (0040 D5).
- One session on `v0.28-rc1` rendered both flows, a rotated photograph upright among them: the pod made its own
  host key, ComfyUI wrote to memory, and no render carried a text chunk (0040 D6).

## [0.27.0] - 2026-09-28 · 0039-the-photo-metadata

### Security

- A photograph can be stripped to the blocks that decode its pixels, colour profile and orientation, by a byte
  walk that never re-encodes; one it cannot walk to its end is refused (0039 D1, D2, D5).
- The render uploads the stripped photograph under its name, and the run's copy keeps its bytes; the transport
  takes a name and bytes (0039 D3, D4).
- A JFIF or Adobe header is cut to its fixed fields, so a thumbnail never leaves, and assembly walks the photograph,
  even under a prompt already on disk, so one the strip refuses is refused before any pod boots (0039 D1, D5).

## [0.26.1] - 2026-09-28 · 0038-the-changelog

### Changed

- Every version rewritten terse: Keep a Changelog sections only, each heading from `0.7.0` naming its change, and
  the preamble holding the rules only (0038 D1, D2, D3, D5).
- `CLAUDE.md` states the changelog's rules, no code, doc or README cites it, and `tests/test_changelog.py` holds
  both (0038 D6, D7, D8).

## [0.26.0] - 2026-09-28 · 0037-the-boundaries

### Security

- The ComfyUI transport ignores an exported proxy and bounds every wait; a malformed prompt id is refused
  (0037 D1, D2, D3).
- An upload's boundary is random and its names escaped, and an endpoint's error text keeps printable characters
  only (0037 D4, D5).
- The review surface refuses a damaged draft, sheet, caption or tag list by name, with a shell-quoted fix that
  works under any runs root, and refuses a malformed draft update (0037 D6).
- A run's frame names its photograph by one plain filename and carries its digest, and the photograph may not be
  a symbolic link (0037 D7).
- A render session's watchdog ends with it, its tunnel keeps its own host keys, and its checks bypass any proxy
  (0037 D8, D9, D11).

## [0.25.1] - 2026-09-27 · 0036-the-prose

### Changed

- No intimate tag, rating term or per-tag count from the operator's sheets stays in tracked prose; the archive and
  this file are edited, a stated exception (0036 D1).
- `docs/decisions.md` D33 records that isekai restricts no content; the operator answers for what renders
  (0036 D4).
- `docs/pins.md` stops overstating the reader's and the image's pins (0036 D5).
- The teardown and port messages name the right fix (0036 D6).
- `summon-anime-wai`'s graph placeholder is `photo.jpeg`, re-pinned in place; no submitted graph moves.
  `summon-anime-wai` → `96c605821e68a8ac2f1c7a60807cfcfb4c3658ae4112cc84d21a00bf39f3e698` (0036 D7).

## [0.25.0] - 2026-09-27 · 0035-the-flow-skills

### Added

- `compare` verb: writes `compare.html`, each photograph beside its flows' renders, and prints its path (0035 D2).
- `infra/render.sh`: one render session that assembles first, rents, renders each flow, halts at the pod ceiling,
  and tears down on every exit (0035 D3).
- The `run-flows` and `compare-renders` skills: an agent runs a batch to the comparison page, stopping for the
  approval and the go, and never reports a pod id (0035 D1, D4, D6).

### Fixed

- onnxruntime's telemetry is disabled, so `tag` no longer connects out or aborts at exit (0035 D5).

## [0.24.1] - 2026-09-27 · 0034-runpod-rest-v2

### Changed

- `up.sh` creates and `down.sh` deletes on RunPod's REST v2, trying each GPU type in order (0034 D1, D2, D3).
- Only a 204 tears down; a 404 keeps the record files and asks for the RunPod MCP's confirmation (0034 D5).
- Every RunPod call is bounded and reads its key from a file descriptor, never `argv` (0034).
- A create whose outcome is unknown says a pod may exist, and names the check (0034 D4).

## [0.24.0] - 2026-09-27 · 0033-pin-and-record

### Added

- `docs/pins.md`: what each pin buys, where it is declared and checked, and how it moves (0033 D10).

### Changed

- CI and the toolchain are pinned: actions by commit, the runner, Node and uv (0033 D1).
- The image is built on request from pinned inputs into a locked environment, and reports its digest (0033 D2).
- BREAKING: a pod boots only the digest `config/image.json` pins; `RUNPOD_IMAGE` goes (0033 D3).
- `caption` and `tag` refuse a reader model that no entry in `config/reader.json` pins (0033 D4).
- Every artifact records what shaped it: sampling options, floor, flow digest, sheet, image and runtime
  (0033 D5, D6).
- A boot prints when each step begins (0033).

## [0.23.0] - 2026-09-26 · 0032-the-tag-verb

### Changed

- BREAKING: a flow's manifest declares `"tagger": true | false`, and `MANIFEST_VERSION` moves to 4 (0032 D1).
- Both flows re-pinned in place, format only. `conjure-anime-wai` →
  `f2bd3202079b1288068aed7ccf57e2b6b0e3b9a1db037973b4be99f83bf22a1f` (0032 D1).
- BREAKING: `caption` writes the prose only, and a new `tag` verb writes both tag lists (0032 D2).
- A flow that declares no tagger gets a sheet with every field empty (0032 D3).
- The review surface shows a missing caption with the command that writes it (0032 D4).

## [0.22.9] - 2026-09-26 · 0031-the-backlog

### Changed

- The retry rule is stated once, in `run._spent`, and the drifted documentation is corrected (0031 D2, D3).

### Fixed

- An endpoint answer in the wrong shape is refused permanent, and a history that is not an object no longer polls
  forever (0031 D1).
- A key the `review`, `approve` or `sheet` stage reads from a run file is refused by name when missing or mistyped
  (0031 D1).
- Approval takes the draft lock, and never guesses a draft unedited from a missing or damaged source (0031 D1).
- A damaged `run.json` names a remedy that works (0031 D1).

## [0.22.8] - 2026-09-26 · 0030-the-defects

### Fixed

- An unreadable run file is refused by name, with a remedy that deletes it, and `show` marks it (0030 D1, D5).
- A failure record's attempt is the highest recorded plus one, so a deleted record is never overwritten (0030 D2).
- One definition of the current draft: a stale draft neither re-opens an input nor is approved (0030 D1, D4).
- The transport's failure carries its kind: a 4xx is permanent, a 5xx or a closed tunnel transient (0030 D3, D6).
- Every printed stage command names its run, so a pasted remedy acts (0030 D1, D2).

## [0.22.7] - 2026-09-26 · 0029-the-tree

### Changed

- The files the pipeline reads move to `config/`, and the derivers and operator scripts to `tools/`
  (0029 D1, D3, D4).
- The evaluator is a top-level `evaluation/`, run as `python -m evaluation` (0029 D1, D2).
- `make derive` re-runs every deriver in dependency order (0029 D6).
- The image's paths are checked statically (0029 D5).

### Removed

- The licence record `scripts/eval_licences.md` and its requirement; the AGPL guards stay (0029 D10).
- `probe/`, the loader probe (0029 D9).

## [0.22.6] - 2026-09-26 · 0028-the-file-shapes

### Changed

- `isekai/foundation/artifacts.py` is the run directory's contract: each file kind's shape, name and version, with
  one typed `read` and `write` (0028 D1, D2, D3, D4).
- Every run file is read and written through the contract, and golden files pin each kind's bytes
  (0028 D5, D8, D9).

### Removed

- `SCHEMA_VERSION`, `envelope` and `read_artifact` (0028 D7).

## [0.22.5] - 2026-09-25 · 0027-the-seams

### Changed

- The `Makefile` is the gate's one declaration; `.minions/minions.toml` goes (0027 D1).
- The review UI reads the encoder window from the server's token budget (0027 D2).
- `tests/test_layers.py` holds that imports point down, and `foundation` imports nothing above it (0027 D3, D6).
- Pin verification belongs to `boundary/provision.py`, and the ComfyUI transport is `boundary/comfy/`
  (0027 D7, D9).
- The approval state moves from the review UI into `pipeline/review.py` (0027 D11).

## [0.22.4] - 2026-09-25 · 0026-architecture-in-the-repo

### Changed

- Code, tests and spec preambles say what the code does; no behaviour changes (0026 D1).
- `docs/` holds the architecture: `principles.md`, `decisions.md` and `modules.md`, with `docs/arc/` flattened in
  (0026).
- `CLAUDE.md` keeps only process, and imports `docs/principles.md` (0026 D8).
- `README.md` stops restating the architecture and links `docs/` (0026 D10).

## [0.22.3] - 2026-09-23 · 0025-running-the-flow

### Changed

- The negative prompt is quality-only and lives in the flow alone; each graph's negative node is emptied, and both
  flows are re-pinned (0025 D1, D2).
- `dependencies = []` retires: the tagger's and the UI's stacks are declared, so the gate stops removing them
  (0025 D3).
- The `-S` guard is narrowed, and falsified against a declared dependency (0025 D4).
- `## Quickstart` is rewritten as `## Running a flow` (0025 D5).

### Fixed

- The re-pin record test can fail for a re-pin (0025 D2).
- The tagger's refusal names `uv sync`, not a removed extra (0025 D3).

## [0.22.2] - 2026-09-22 · 0024-the-documents

### Added

- `docs/arc/`, where the architecture is drawn: the module graph and the data flow (0024 D3, D4).
- Scenarios for the behaviour `0.22.1` shipped unbound, repaying its `spec_exempt` markers (0024 D7).

### Changed

- Every claim the repository makes about itself is checked against the tree, and quantities leave the docs
  (0024 D1, D2, D6).
- `CLAUDE.md` holds agent instructions only; how the system works moves to `docs/arc/` (0024 D3).
- An input re-opened with `review --new-version` is editable on the surface again (0024 D5).

### Removed

- `isekai/README.md`'s edge table: `docs/arc/` owns the module graph (0024 D4).

## [0.22.1] - 2026-09-22 · 0023-backlog-paydown

### Changed

- `num_ctx` is pinned in both hosted option maps (0023 D8).

### Removed

- The `vite` dev-server proxy, which the `Host` guard turned into a trap (0023 D3).

### Fixed

- A manifest missing a dial its roles read, or naming a node its graph lacks, is refused at load (0023 D4).
- An unreachable endpoint is recorded `transient`; rendering's budget stays one (0023 D11).
- One flow's malformed sheet, or one unreadable photograph, no longer costs the rest of the batch (0023 D1).
- An overlapping draft `PUT` answers `409`, and approve stops when the write it waits for was refused (0023 D6).
- Every command a refusal prints is one the parser accepts (0023 D1).
- The UI bundle is rebuilt when anything it is built from changes, and the build is bounded in time (0023 D1).
- The hosted tag panel shows each tag once (0023 D7).

### Security

- The review surface validates `Host` and `Origin` on every request (0023 D3).

## [0.22.0] - 2026-09-22 · 0022-one-arm

### Changed

- BREAKING: `summon-anime-wai` and `conjure-anime-wai` replace the three flows; a flow's name carries its base
  (0022 D5, D6).
- BREAKING: the `hosted` block goes; a required top-level `model` replaces it, and `MANIFEST_VERSION` moves to 3
  (0022 D1, D2, D4).
- `CliFailure` becomes `StageFailure`, and the shared run names move to `foundation/run.py` (0022 D12, D13).

### Removed

- The `claude` arm: `isekai/boundary/claude_cli.py`, both reader registries and `tests/test_isolation.py`
  (0022 D16, D18).
- `sheet.briefing.md`, from every flow (0022 D9).

## [0.21.0] - 2026-09-21 · 0021-sheet-from-the-tagger

### Added

- `field-map`: one authored table giving each tag one primary field, checked at load (0021 D4, D9, D19).
- `scripts/derive_field_map.py`, an offline authoring aid for the table (0021 D15).
- A read-only field cheatsheet on `Option+Space`, served by `GET /api/fields`, and `Option+F` for the photograph
  (0021 D11, D13, D14).

### Changed

- The sheet comes from the local tagger's list through the field map; an absent `wd14/` refuses naming `caption`
  (0021 D5, D21, D24).

### Removed

- Both sorters, the free-text mapping cascade and their scenarios (0021 D20, D23).

## [0.20.0] - 2026-09-21 · 0020-readable-caption

### Added

- `caption` also writes a local WD14 tag list and a hosted JoyCaption one, beside the prose (0020 D1, D7, D8).
- `isekai/boundary/wd14.py`, the local tagger behind a `tagging` extra, verifying its pinned digests first
  (0020 D9, D17, D19).
- The review surface shows the caption a sentence to a block, with both tag lists beneath (0020 D2, D10, D13).
- The gate type-checks the browser half, and CI restores its toolchain (0020 D22).

### Changed

- The hosted tag list is filtered to the vocabulary before it reaches the page (0020 D29).

### Fixed

- `isekai ui` rebuilds a stale bundle (0020 D28).

## [0.19.0] - 2026-09-20 · 0019-open-models

### Added

- `isekai/boundary/ollama.py`: open models behind a local Ollama read and sort, with no `claude` needed and no
  proxy in between (0019 D1, D4, D5).
- A flow may declare the models its first two stages call, and `flows/summon-open-v1/` does (0019 D2, D3).
- An unreachable host or an absent model refuses without spending an attempt (0019 D9).
- A manifest key this build does not read is refused by name (0019 D12).

## [0.18.0] - 2026-09-19 · 0018-review-ui

### Added

- `isekai ui <ids…> --flow F`: stage ③ in a browser, a Vue app served by FastAPI beside the CLI (0018 D1, D2, D8).
- Editing with autosave, undo, a keyboard model, tag autocomplete and a token budget per field (0018 D4).
- Approval is terminal in the browser, and a run manifest sums up the batch (0018 D5).
- The bundle is built on demand, and a `ui` extra pins the server stack (0018 D12).

### Changed

- Each living spec gains `## Purpose` (0018 D9).

### Fixed

- The run-root containment guard compares directories, not path text (0018 D10).

## [0.17.0] - 2026-09-18 · 0017-conjure

### Added

- `flows/conjure-v1/`: a render from the sheet alone, no photograph, added without code (0017 D1, D2, D3).
- Its schema is chosen by vocabulary depth, and its dials are `summon`'s less the identity ones (0017 D4, D6).

## [0.16.0] - 2026-09-17 · 0016-flow-registry

### Added

- `--flow` is required and repeatable on every stage verb, resolved against `flows/` before a run opens (0016 D6).

### Changed

- BREAKING: a flow is flat files with an eight-key `flow.json` that pins its models by digest (0016 D1, D3, D4).
- BREAKING: the run layout is input above flow, and the sheet stage writes one sheet per flow (0016 D5, D6).
- BREAKING: the run id's separator is an underscore (0016 D10).
- `validate` moves to `shared/fields.py`, and no stage imports another (0016 D8).

### Fixed

- A manifest declaring the photograph on one side only is refused at load (0016 D9).
- Resume no longer assumes a render is a PNG (0016 D11).

## [0.15.0] - 2026-09-17 · 0015-arc-alignment

### Changed

- The package becomes group directories, each with a `README.md`; the CLI moves to `interface/cli.py`, and
  `provision.py`, which the image follows, to `boundary/` (0015 D2, D3, D11).
- `show.py` becomes `run_view.py`, `photo.py` becomes `image.py`, and `write_atomically` is its own module
  (0015 D4, D6).
- The repository-root anchors are pinned by a test before anything moves (0015 D7).

## [0.14.0] - 2026-09-15 · 0014-delete-the-old-path

### Added

- The target ceiling is restored to the surviving render path (0014 D4).
- `--runs` refuses a root inside the working tree (0014 D7).
- `infra/up.sh`'s readiness wait is bounded, and tears the pod down on timeout (0014 D10).

### Changed

- `.data/` is the one root anything is generated into; `outputs/` is gone (0014 D7).
- `isekai/workflow.py` becomes `isekai/photo.py`, without injection (0014 D3).

### Removed

- BREAKING: the old render path, `convert.py` and its CLI; `python -m isekai` is the one entry point (0014 D1).
- The model artifacts only the old graph used, from the manifest (0014).

## [0.13.0] - 2026-09-15 · 0013-walking-skeleton

### Added

- `python -m isekai`, a second entry point with the verbs `caption`, `sheet`, `review`, `approve`, `generate` and
  `show`; `convert.py` is untouched (0013 D1, D2).
- The run directory, `.data/runs/<photo-id>/`: the photograph copied in, artifacts numbered and never overwritten,
  and a failure recorded beside its artifact with its kind (0013 D4, D5, D14).
- `caption` reads a photograph into prose, and `sheet` sorts the prose into a versioned schema mapped onto the tag
  vocabulary, both through a locked-down `claude -p` (0013 D6, D8).
- `review` copies a sheet into a draft, and `approve` validates the draft and renames it, recording whether a human
  edited it (0013 D3).
- `generate` renders an approved sheet through a flow under `flows/`, declared and pinned by equality; the prompt is
  assembled locally before any endpoint (0013 D12, D13).
- The tag vocabulary is provisioned from its own pinned manifest, and one module derives every manifest (0013 D9,
  D10).

### Removed

- The absent-models preflight: no endpoint lists a volume, so it could only give a false guarantee (0013 D15).

### Fixed

- `outputs/` and `.inputs/` are gitignored again, held by a test (0013 D14).
- `generate` assembles the whole batch before renting, renders only with `--server`, and refuses a run approved for
  nothing (0013).
- The sorting briefing's examples use the vocabulary's spellings, so `count` and `gaze` map to tags (0013).
- `infra/up.sh` sends the GPU preference as a list, not one enum value (0013).

## [0.12.0] - 2026-09-07 · 0012-identity-evaluator

### Added

- `evaluate.py`, a second entry point off `convert.py`'s import graph: face, pose and hair-colour axes and a
  face-location guard, which rank and never grade (0012 D1, D5, D12).
- `run.json` records the photograph's digest, the base, the working resolution, the pod image, the ComfyUI
  commit, and each variation's seed, graph digest and dials (0012 D4, D14).
- `--fixed-dials` renders at the graph's own dials, and `--cn-strength` sets the identity node's keypoint dial
  (0012 D3, D6).
- The evaluator's models are pinned in `scripts/eval_models.json`, a sibling of the graph's manifest, with every
  licence recorded (0012 D16, D18).
- The guard ships box IoU as its authoritative method, chosen by measuring both (0012 D9).

### Changed

- The anime-face detector is `deepghs/anime_face_detection`, MIT: the AGPL one named publishes no ONNX (0012 D19).

## [0.11.0] - 2026-09-06 · 0011-converge-paydown

### Added

- `infra/up.sh` refuses a pod with no network volume named, and the pod checks its volume's capacity (0011 D5).
- A provisioning abort holds the pod for a bounded time and leaves a failure marker on container disk (0011 D6).
- Measuring a photo refuses past stated ceilings on the target, a header dimension and the header walk (0011 D8).
- `provision.py` refuses an escaping destination, an unpinned source and an empty entry before any byte moves
  (0011 D7).
- The base checkpoint's digest is derived from Civitai's record, not transcribed (0011 D13).
- CI refuses a manual image tag that is `latest` or malformed (0011).

### Changed

- ComfyUI's core is pinned to the commit the release-candidate image ran (0011 D3, D4).
- The graph↔manifest binding keys on a census of node classes, not a name suffix (0011).

### Fixed

- A rotated PNG is measured as the loader transposes it, as a JPEG already was (0011 D11, D12).
- The pose-grid sentence is corrected: `DWPreprocessor` works at its own resolution (0011 D9).

## [0.10.0] - 2026-09-05 · 0010-illustrious-base

### Added

- An `ImageScale` node sizes the photo to a working resolution derived from its own header (0010 D2).
- A release-candidate image tag for metered phases; `:latest` stays the released one (0010 D8).

### Changed

- BREAKING: the base is WAI-illustrious-SDXL v17.0, fetched from mirrors and trusted by the digest Civitai
  publishes, with its publisher's prompts (0010 D1, D4).
- The graph stops CLIP at the second-to-last layer, as the publisher's samples do (0010 D6).
- The probe's dials and every ControlNet are kept, and the dials are pinned by the suite (0010 D7, D9).

### Removed

- `1girl` leaves the positive prompt; gender comes from the identity node's face embedding (0010 D5).
- Animagine XL 4.0 leaves the manifest once the swap is proven (0010 D3).

### Fixed

- A rotated JPEG is measured as the loader transposes it, and a deep frame header is read, not refused (0010 D2).

## [0.9.0] - 2026-09-05 · 0009-pinned-provisioning

### Added

- `scripts/models.json`, a pinned and checksummed manifest of every model the graph needs, derived by
  `scripts/derive_manifest.py` (0009 D5, D15).
- `isekai/provision.py` decides skip, fetch or abort per entry, hashes a file already present, and lands a transfer
  only once verified (0009 D4, D14).
- A test binds the graph to the manifest, including the files preprocessors fetch for themselves (0009 D6).

### Changed

- `scripts/download_models.sh` is a `wget` driver over the manifest, walking its fallback sources; the `hf` CLI goes
  (0009 D2, D3, D16).
- The volume mounts at `/runpod-volume`, and the models directory is one symlink into this project's namespace
  (0009 D8, D9).
- The annotator checkpoints move onto the volume, and a provisioning abort holds the pod open (0009 D7, D17).

## [0.8.0] - 2026-09-04 · 0008-one-path

### Changed

- BREAKING: one path, renamed to nothing: `workflows/pipeline.json`; `--model`, `--workflow` and `--prompt` go
  (0008 D1).
- BREAKING: `-o` names a directory; each run writes a timestamped one with its renders and a `run.json` (0008 D4).
- BREAKING: every variation's seed is derived from `--seed`, variation 0 included (0008 D5).
- The positive prompt is pinned by equality in the suite, and `arms crossed` leaves it (0008 D6, D7).
- `CLAUDE.md`'s metered-work rule names who creates, tears down and confirms, and when a human go is back (0008 D10).

### Removed

- The `qwen`, `animagine` and `animagine-i2i` paths, the registry, the fixtures and every idle seam (0008 D2, D3, D9).

## [0.7.0] - 2026-09-01 · 0001-mf-standard

### Added

- The OpenSpec tree, and `spec` and `spec_exempt` markers binding every test to a scenario (0001).
- A root `Makefile` with a `gate` target that CI runs, `.python-version`, and this file (0001).

### Changed

- The gate config moves to `.minions/minions.toml`, and `CLAUDE.md` and `README.md` are rewritten (0001).

### Fixed

- `--variations` no longer bills identical renders on a model with no mutation, and zero is refused (0001).
- `--seed` and `--denoise 0.0` are no longer discarded, and `mutate` refuses a linked dial by name (0001).

## [0.6.0] - 2026-08-15

### Added

- `--denoise`, `--cfg` and `--ip-weight`, range-checked and applied before the jitter.

### Changed

- The jitter is relative to each dial's base value.

## [0.4.0] - 2026-08-04

### Added

- `--seed` and `--variations`, through a mutation seam with an injected `random.Random`.
- The `animagine-i2i-cn` model: `animagine-i2i` with a tile, OpenPose and lineart ControlNet stack.

## [0.3.0] - 2026-07-31

### Added

- The `animagine-i2i` model: img2img from the photo, with `denoise` as the identity-versus-style dial.

## [0.2.0] - 2026-07-31

### Added

- `--model {qwen,animagine}`, the `animagine` model with InstantID, and a fake transport for an offline suite.

## [0.1.0] - 2026-07-28

### Added

- `convert.py`, a stdlib-only CLI that drives a ComfyUI workflow, and the container image CI publishes.
- Pods created and deleted by `infra/up.sh` and `infra/down.sh`, with models downloaded on boot.

### Fixed

- Blackwell GPUs run the image: PyTorch is pinned to a cu128 build.
