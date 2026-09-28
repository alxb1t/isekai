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

### Changed

- `0.1.0` to `0.13.0` rewritten terse: Keep a Changelog sections only, and each heading from `0.7.0` names its
  change (0038 D1, D2, D3).
- `0.14.0` to `0.22.3` rewritten the same way; the `0.22.3` re-pin table goes (0038 D1, D2, D3).

## [0.26.0] - 2026-09-28

### Security

- **The ComfyUI transport ignores an exported proxy and bounds every wait.** Requests go through the client's own
  `OPENER` at a 60 s timeout and a render gives up at 600 s, each refused transient; a prompt id that is not a
  string is refused permanent (0037 design D1–D3).
- **An upload's boundary is random and in no part, its names are escaped, and an endpoint's error text keeps
  printable characters only** (0037 design D4, D5).
- **The review surface refuses a damaged draft, approved sheet, caption or tag list by name**, with the command
  that rewrites it, rather than failing with a server error; a draft update whose fields are not lists of strings
  is refused naming the field, and nothing is saved (0037 design D6).
- **A run's frame must name its photograph with one plain filename, and carry its name and digest**, or the run
  is refused naming `run.json`; a frame can no longer point a run at another file on the machine (0037 design D7).
- **A render session's watchdog polls its session and ends with it, its tunnel keeps host keys in a file of its
  own, removed at teardown, and its checks reach the tunnel with `--noproxy '*'`** (0037 design D8, D9, D11).
- **One metered session proved the boundaries end to end**: with a dead `http_proxy` exported, both flows rendered
  on a real pod with no refusal, and the RunPod MCP confirmed no pod left (0037 design D10).

### Fixed

- **The review surface's damage refusals name a fix that works.** A damaged approved sheet names the file to
  restore, since no command rewrites one and `review` refuses the same damage; every other command names
  `--runs <root>` when the surface serves a runs root that is not the default (0037 design D6).
- **A pasted remedy survives a runs root holding a space.** The review surface's damage commands and `compare`'s
  not-a-batch refusal shell-quote the root they name (0037 design D6).
- **A run whose photograph is a symbolic link is refused** naming `run.json` and its remedy, so a planted run can
  no longer serve or upload a file outside itself under a plain name (0037 design D7).

## [0.25.1] - 2026-09-27

### Changed

- **No intimate tag, rating term or per-tag count from the operator's sheets stays in tracked prose.** Archived
  `0018`, `0020`, `0021` and `0025` and earlier entries here are edited to describe what they quoted — a stated
  exception to the archive's freeze and this file's append-only rule (0036 design D1).
- **`tools/derive_field_map.py`'s comments follow, and no code moves.** The false "load-bearing" comment now says
  `PRECEDENCE` picks the winner the counts do (0036 design D2).
- **D33 records that isekai restricts no content; the operator answers for what renders** (0036 design D4).
- **`docs/pins.md` stops overstating the reader's and the image's pins.** The reader alias's template and
  the image's build tools join *Not pinned*, and a leftover pod-image record's borrowed pin joins *where it
  stops* (0036 design D5).
- **The teardown and port messages name the right fix.** A lost create and a failed teardown route through
  `.runpod_pod_id` and `infra/down.sh`; the port refusal stops only an earlier session's tunnel. The
  teardown test skips `echo` lines, so it still reads the call (0036 design D6).
- **`summon-anime-wai`'s graph placeholder is `photo.jpeg`, re-pinned in place.** The `LoadImage` `image` held
  a real photograph's filename, which `build_graph` overwrites before any submission, so no submitted graph
  moves; a new test holds that. `summon-anime-wai` →
  `96c605821e68a8ac2f1c7a60807cfcfb4c3658ae4112cc84d21a00bf39f3e698` (0036 design D7).

## [0.25.0] - 2026-09-27

### Added

- **`compare`, a new verb** (`0035` design D2): `python -m isekai compare <batch>` writes `compare.html` into
  the batch directory — each run's photograph beside each flow's renders under its latest approval, each render
  with its positive prompt and the captions in a row below, linked relative and never embedded — and prints only
  its path, so an agent hands it over unread. A flow that reads the photograph sits beside it: `summon`, then
  `conjure`.
- **`infra/render.sh`, one whole render session** (`0035` design D3): it assembles every prompt before renting,
  then runs `up.sh`, opens the tunnel, waits at most 300 s for ComfyUI and renders each `<flow>=<count>`. A
  trap set before `up.sh` tears the pod down and closes the tunnel on every exit, error and signal.
- **The flow skills, `run-flows` and `compare-renders`** (`0035` design D1, D4, D6): an agent runs a batch of
  photographs to the comparison page from exact commands, stopping for "approved" and for the go, and
  reads counts rather than runs. A test fails when a command a skill names stops parsing. `CLAUDE.md`'s pod rule
  now also accepts the operator's explicit go, and names the record files to delete after a confirmed teardown.

- **Proved by the operator using `run-flows`** (`0035` design D7): 5 photographs through both flows to
  `compare.html` — 10 of each stage's files, 5 approvals and 5 renders per flow, 0 refusals, one pod session of
  about 13 minutes torn down by `render.sh`, and the RunPod MCP found no pod left. Evidence in the change's
  `acceptance.md`.

### Fixed

- **onnxruntime no longer connects to Microsoft, and `tag` no longer exits 134** (`0035` design D5): loading it
  opened an HTTPS connection for its telemetry, whose teardown at exit could abort a `tag` that had written
  everything. `ORT_DISABLE_TELEMETRY=1` is set before every import of it; 0 of 40 runs aborted or left loopback.
- **`render.sh`'s own refusals reach the batch's log** (`0035` design D3): they went to stderr alone, which
  `run-flows` step 4 discards before reading `log.txt`, so a wait past 300 s, a recorded pod or a taken port
  showed the agent an exit 1 with no reason. `refuse()` now appends its line to the log as well, once the runs
  root is checked; a text check in `tests/test_infra.py` holds it.
- **A render session halts at the pod ceiling, and a second interrupt no longer cuts its teardown short**
  (`0035` design D3): nothing stopped a session at `CLAUDE.md`'s 45 minutes, and the teardown reset `INT` and `TERM`
  to their defaults, so a second Ctrl-C killed `down.sh` mid-DELETE and left the pod billing. A watchdog started
  before `up.sh` now refuses at 44 minutes, stops the command in flight and exits through the trap, keeping the
  renders written; the teardown ignores `INT`, `TERM` and `HUP`, and the trap covers `HUP`. `render.sh`'s refusals
  for an empty runs root and a taken port name a command to paste. Text checks in `tests/test_infra.py` hold both.
- **`run-flows` renders in the background, counts approved runs, and never reports a pod id** (`0035` design D1):
  step 4 was a foreground call longer than an agent's command limit, so a timeout could cut the teardown short; it
  now runs in the shell tool's background mode and waits for the exit. Step 3 counted approval files, so a run
  approved twice hid one approved never; it counts runs. A failed render's log tail drops the lines naming the pod
  or its address, and the skill's Never list forbids reporting them.
- **`compare` marks a directory no tracked flow names instead of refusing the page** (`0035` design D2): one run
  holding work from a flow since renamed failed the whole batch's page; that column now reads *not a tracked flow*.
  Its refusal of a directory with no `runs/` names a `python -m isekai tag` command to paste, and joins the suite's
  check that every printed command parses.

## [0.24.1] - 2026-09-27

### Changed

- **`up.sh` creates on RunPod's REST v2** (`0034` design D1, D2, D4): v1 retires on 2026-11-15. Each type in
  `RUNPOD_GPU_TYPE` is tried in order, since v2 places one per call; the poll waits for `ssh.direct`, and a
  failed read is *not yet*, so the 420 s teardown always runs. A failed call prints its `problem+json`.
- **`down.sh` deletes on REST v2** (`0034` design D3, D5): only a 204 tears down; a 404 keeps the record files
  and asks for the RunPod MCP's confirmation, since a wrong key gets one too. A test fails if any script under
  `infra/` names the retired v1 host; the README's pod diagram names v2's calls.
- **Proved on one metered boot** (`0034` design D7): `up.sh` created and polled on v2, one `conjure` render,
  `down.sh` tore down on 204, and the RunPod MCP found the pod gone — 6 min 46 s, about $0.08. Evidence in
  the change's `acceptance.md`.
- **The poll is one guarded read, and an empty GPU list is refused** (`0034` design D2): after the metered
  boot, the simplify pass folded the poll's three reads into one `read … < <(curl | jq) || true`, checked
  offline against the `ssh.direct` shapes on bash 3.2 and 5.2 and not re-booted; `up.sh` refuses a
  `RUNPOD_GPU_TYPE` naming no type before any create.
- **Every RunPod call is bounded and keeps the key off `argv`**: `up.sh` and `down.sh` call curl through one
  `api` helper, `--max-time 30`, with the bearer header read from a file descriptor, so a stalled read cannot
  hold the poll past its 420 s teardown and no process listing shows the key.
- **A create whose outcome is unknown says a pod may exist** (`0034` design D4): a transport failure is
  reported as HTTP 000 rather than a silent exit, and on 000, a 5xx or a 201 with no `.id`, `up.sh` exits 1
  telling the operator to check the RunPod MCP's `list-pods` before re-running. A 400 still tries the next
  type. `down.sh`'s 404 refusal names the `rm` of both record files once the pod is confirmed gone.

## [0.24.0] - 2026-09-27

### Changed

- **CI and the toolchain pinned** (`0033` design D1): every workflow action by commit SHA, the runner
  `ubuntu-24.04`, Node `22.23.3`, and uv `0.12.19` in CI and in `pyproject.toml`'s `required-version`.
- **The image is built on request, from pinned inputs, into a locked environment** (`0033` design D2): the
  base and uv by digest; `image/` a uv project `tools/derive_image_project.py` derives, installed by
  `uv sync --locked`, with `onnxruntime-gpu` alone; `build-image.yml` dispatch-only, reporting its digest.
- **A boot prints when each step begins**: `start.sh` stamps each step in UTC, `up.sh` the pod's creation and
  its mapped :22.
- **The first image built on request**: `ghcr.io/alxb1t/isekai:v0.24-rc1`, digest
  `sha256:d6f12d02b1fb6b0d2c4c6d0505c70193202c647d57c27b7e1235845427dbb500`, recorded in the change's
  `acceptance.md`; `build-image.yml`'s digest step is a block scalar, so the workflow parses.
- **BREAKING — a pod boots only the digest `config/image.json` pins** (`0033` design D3): `RUNPOD_IMAGE` and
  its `:latest` default are gone; `up.sh` writes the booted reference to `.runpod_pod_image`, which
  `down.sh` removes on 204. Local compose builds are tagged `isekai:local`.
- **The reader's model is checked before its first call** (`0033` design D4): `config/reader.json`, derived by
  `tools/derive_reader.py`, pins the JoyCaption model and projector per alias; `caption` and `tag` refuse,
  spending no attempt, a model no entry pins or one Ollama built from other files. The caption's and hosted
  tags' producers now record `pinned: true` and both files' digests.
- **Every artifact records what shaped it** (`0033` design D5, D6): the sampling `options` on the caption and
  hosted tags, the wd14 `floor` (carried into the sheet), `flow_digest` on the sheet, prompt and render,
  `sheet` on the prompt and render in place of the render's `sheet_version`, the booted `image`, `pinned`
  and the endpoint's `runtime` on the render, and the sheet's `schema_document` and `field_map` on the
  draft and approval. Every new key is optional under version 1, so existing runs still read.
- **The record in `docs/`** (`0033` design D7): D6 checks the reader's model, D28 pins the image by digest in
  `config/image.json`, and D32 states when a run file's version moves; the principles' pinning gap shrinks
  to `apt`, and the README provisions the reader with `download_models.sh config/reader.json`.
- **Accepted on one metered pod session** (`0033` design D8): six photographs through both flows, twelve
  renders on `v0.24-rc1` by digest, 17 m 58 s at $0.72/hr ≈ $0.22, teardown confirmed through the RunPod
  MCP. Every record present on every artifact; the renders judged a success by eye.
- **D27 corrected**: a network volume reports its storage cluster's capacity (≈ 2.2 PiB), so the 20 GB
  `isekai-models` passes `start.sh`'s 40 GiB floor. The known break it recorded was never true.

- **`docs/pins.md`, the operating guide to the pins** (`0033` design D10): what each pin buys and where it
  stops, where each is declared and checked, how each is moved, and what stays open. `tests/test_docs.py`
  holds every repository path it names to exist.

## [0.23.0] - 2026-09-26

### Changed

- **BREAKING — a flow's manifest declares `"tagger": true | false`** (`0032` design D1): a required
  boolean, refused naming the key when absent or not a boolean, and `MANIFEST_VERSION` moves 3 → 4.
- **Both flows re-pinned in place, format only**: each manifest gains `"tagger": true` and version 4, and
  each graph's `filename_prefix` becomes its flow's id, so the image is unchanged and `flow_graph_sha256`
  moves. `summon-anime-wai` → `039a1a80f2b43069e8e1bffcc4e1665417c4aa73e1c2f40fca783379c351669b`;
  `conjure-anime-wai` → `f2bd3202079b1288068aed7ccf57e2b6b0e3b9a1db037973b4be99f83bf22a1f`.
- **BREAKING — `caption` writes the prose only; a new `tag` verb writes both tag lists** (`0032` design
  D2): WD14 first, then the JoyCaption tags, each refusal collected on its own, so neither tagger's failure
  costs the other its list and the sheet's input no longer waits on Ollama. `tag` refuses a flow whose
  manifest declares `"tagger": false`; `--new-version` re-produces only what its own verb writes; the
  sheet's remedies name `tag`.
- **A flow that declares no tagger gets a sheet with every field empty** (`0032` design D3): `sheet()` takes
  a required `tagged` keyword from the composition root, reads no list when it is false, and records an
  `empty` producer with no model and no `from`. A `sheet-empty` golden pins its bytes.
- **The review surface shows a missing caption with the command that writes it** (`0032` design D4): the
  input payload carries `caption_command`, built by the server, and the caption panel shows *no caption*
  and the command. The approval-race test's waits are bounded and asserted, so a regression fails rather
  than hangs.
- **The record** (`0032` design D5): D1 is now *Stage ① is two independent verbs*, and D31 records that a
  flow declares whether it is tagged. The data flow, the READMEs and `CLAUDE.md` draw ① as `tag` and
  `caption` side by side; the manifest's key lists name `tagger`; `cli.py`'s docstring and the `cli` and
  `sheet` spec preambles name the verbs rather than count them.
- **Accepted on one synthetic portrait** (`0032` phase 6, `acceptance.md`): both flows run `tag`, `caption`,
  `sheet` and `ui`; with Ollama stopped, `tag` writes WD14 and refuses only the JoyCaption lists; `sheet`
  before `tag` refuses naming `tag`. The known native abort at exit is confirmed to kill the process (exit
  134, after every write); it is recorded, not fixed.

## [0.22.9] - 2026-09-26

### Fixed

- **v0.22.8's families, finished** (`0031` design D1): an endpoint answer in the wrong shape is refused
  permanent, and a history that is not an object no longer polls forever; every missing or wrong-typed key
  the `review`, `approve` and `sheet` stages read from a draft, an approval, a sheet or a tag list is
  refused by name, though the review surface's own reads of those files are not yet; a damaged `run.json`
  names a remedy that works, offering the photograph again by its path; approval takes the draft lock, so
  an autosave cannot write after it.
- **Approval never guesses a draft unedited**: a source sheet that is gone is refused rather than read as
  unedited, and a damaged one (missing its `fields`, not valid JSON, or declaring another version) names a
  fix that keeps it: a new sheet and a fresh copy, or, for a re-opened draft, deleting the draft to keep the
  approval. No sheet number is freed for reuse.

### Changed

- **The retry rule is stated once**, in `run._spent`, which `exhausted` and `check_budget` share; an AST
  test holds that every `write(` passes an annotated artifact; a `draft-saved` golden pins `save_draft`'s
  rewrite; a `ty: ignore` and an unused fixture go (`0031` design D2). `require` refuses a key of a shape
  its noun table lacks rather than raising; the approval-race twin no longer waits on a timing window; the
  missing-key tests are bound to the scenarios they prove rather than the batch one.
- **The drifted documentation, corrected** (`0031` design D3): the README names the vocabulary step the
  gate needs, the group READMEs name `artifacts.py` and its importers, `docs/modules.md` says only a run
  file's JSON goes through `write`, the principle names a file to delete by its full path or by its path in
  the run, the tools' `--help` names `python -m <module>`, and the sheet budget's comment says it does not
  bind.

## [0.22.8] - 2026-09-26

### Fixed

- **An unreadable run file is refused by name**: not valid JSON, not an object, or a `schema` that is not
  an object. The remedy deletes the file before re-running its stage; the run's frame reads through the
  same check, and `show` marks such a file instead of parsing it (`0030` design D1, D5).
- **A failure record's attempt is the highest recorded plus one**, so a deleted record never lets the next
  overwrite a later one. A budget refusal names the record by its path in the run, and a refusal after a
  record that refuses the next run says to delete it, with the run id in the command (`0030` design D2, D3).
- **One definition of the current draft**, `review.current_draft`: a draft below the approval is stale, so
  it neither re-opens an input nor is approved, and `approve` on an approved flow writes nothing. A lock
  orders overlapping draft updates; a draft without `fields` or an approval without `sheet` is refused
  (`0030` design D1, D4).
- **The transport's failure carries its kind**: `Unreachable` becomes `TransportFailure`. A 4xx or an
  unreadable answer is recorded permanent, a 5xx or a closed tunnel transient; a failed upload is recorded,
  and a malformed history refused. The render's sidecar is written before its image (`0030` design D3, D6).
- **Every printed stage command names its run**, so a pasted remedy acts rather than exiting 0 having done
  nothing; the guard parses each as printed. A refusal that pointed at `show` for an id names the runs
  root instead, and a non-string WD14 tag routes nowhere rather than raising (`0030` design D1, D2).
- **`docs/principles.md` drops the known breaks this release closes** and names the tests that now hold
  them; *Only a front end composes* gains `load_vocabulary`'s break (`0030` design D7).

## [0.22.7] - 2026-09-26

### Changed

- **A layer-test scope path that does not exist fails the scan** rather than narrowing it silently
  (`0029` design D8).
- **The image's paths are held statically.** `tests/test_infra.py` checks every `COPY` source exists,
  the entrypoint runs a provisioner the image copies, and the manifest lands where `provision.py`'s
  anchor looks (`0029` design D5).
- **The files the pipeline reads live in `config/`**: `models.json`, `vocabulary.json`, `field_map.json`
  and `joycaption.Modelfile`. The anchors, the image's manifest copy and the printed remedies follow;
  `field_map.json` records `config/field_map.json`, so new sheets record a new name and digest for the
  same fields (`0029` design D3, D4, D5).
- **The derivers and the operator's scripts live in `tools/`, a package run from the root**:
  `uv run python -m tools.derive_field_map`, `bash tools/download_models.sh`. The `sys.path` hops and
  `extra-paths` go; the image and the remedies follow (`0029` design D1, D3, D5).
- **`make derive` re-runs every deriver in dependency order**, beside `gate` and outside it
  (`0029` design D6).
- **The evaluator is a top-level `evaluation/` beside the package it measures.** `isekai/evaluation/`,
  the root `evaluate.py` (now `evaluation/__main__.py`), `baseline/` and `eval_models.json` move into
  it; it runs as `uv run --extra eval python -m evaluation` (`0029` design D1, D2).
- **The label ordering follows a moved file**: `GitOrdering` runs `git log --follow`, so moving the
  labels keeps their first-added time (`0029` design D7).
- **The layer test keys its evaluation rule on the top-level `evaluation`**, and its cycle check covers
  `evaluation/` (`0029` design D8, `v0.22.5 review/R3`).
- **The docs follow the tree**: `README.md`'s commands and layout, `docs/`, the package and group
  READMEs, `evaluation/`'s READMEs and usage lines, and the spec preambles name `config/`, `tools/` and
  `evaluation/`. Two false claims are corrected: no eval test skips in CI, and the guard is pinned in
  `evaluation/evaluate.py` (`0029` design D11, D12, `v0.22.5 review/R5`).

### Removed

- **The licence record `scripts/eval_licences.md`**, its tests and its `CLAUDE.md` rule; the
  requirement leaves the `model-provisioning` spec. The AGPL guards stay (`0029` design D10).
- **`probe/`**, v0.11's loader probe, with `tests/test_probe.py`; its measurement stays recorded in
  the archived `0011-converge-paydown` design (`0029` design D9).

## [0.22.6] - 2026-09-26

### Changed

- **Every run file kind's bytes are pinned before the shapes move.** `tests/golden/` holds one file per
  kind, written by today's writers; `tests/test_artifact_bytes.py` compares them byte for byte, and
  its tripwire lets no module outside `foundation/artifacts.py` call `write_json` or `envelope`
  beyond an exact allowlist of today's writers (`0028` design D8, D9).
- **`isekai/foundation/artifacts.py` is the run directory's contract.** It declares each kind's shape
  and its producer's as a `TypedDict`, each kind's name and version as an `Artifact` descriptor, one
  typed `read` and `write`, and `DanbooruTag`; `write_json` moves into it (`0028` design D1-D4).
- **The frame and the error record are written through the contract.** `open_run` writes `RUN_FILE`;
  `record_failure` takes a typed `Failure` and writes `ERROR_FILE`, so every recorded failure carries a
  `stage` and a `detail` (`0028` design D4, D11).
- **The caption and both tag lists are written through the contract.** WD14's `Scored.tag` is a
  `DanbooruTag`, and the tagger's pins are typed `DigestRecord`s (`0028` design D5, D6).
- **The sheet, the review draft and the approved sheet are read and written through the contract.**
  `route` takes only `DanbooruTag`s; `review` reads its origin with one typed read per branch
  (`0028` design D5, D5a, D6).
- **The prompt and the render sidecar are read and written through the contract**, so no module
  outside `foundation/artifacts.py` writes a run file by hand (`0028` design D5, D9).
- **`SCHEMA_VERSION`, `envelope` and `read_artifact` are retired.** The review UI and
  `scripts/derive_field_map.py` read through `read`; the tests read and write valid files through the
  contract, and `tests/stages.py` writes WD14 tags in production's spelling (`0028` design D7, D10).
- **The docs name the contract.** `docs/principles.md` holds the shapes with the golden test and the
  tripwire where it said *not yet*; `docs/modules.md`, `docs/data-flow.md` and the foundation README
  name `artifacts.py`; the tripwire's empty allowlist is deleted (`0028` design D12).

## [0.22.5] - 2026-09-25

### Changed

- **The gate and the encoder window are each declared once.** The `Makefile` is the gate's one
  declaration; `.minions/minions.toml` is deleted and `.minions/` ignored whole. The review UI reads
  the window from the token budget the server sends (`0027` design D1, D2).
- **The layers, the principles' *held by* names and the vocabulary checks are held by tests.**
  `tests/test_layers.py` scans every import, with an exact allowlist of the edges still to move;
  `tests/test_principles.py` resolves each named test; a missing vocabulary fails the checks that
  read it unless `ISEKAI_VOCABULARY=absent`, which CI sets (`0027` design D3–D5).
- **`foundation` imports nothing above it.** `atomic_write.py` moves from `shared/` to `foundation/`,
  and the `Workflow` graph type from `boundary/comfy_types.py` to `foundation/flow.py`, which owns
  the graph (`0027` design D6).
- **Pin verification is `boundary/provision.py`'s.** `resolve`, `entry_for` and their exceptions move
  there from `evaluation/eval_models.py`, and `resolve` takes its manifest. `wiring.load_vocabulary`
  verifies the vocabulary; `shared/vocabulary.py`'s `load` only reads it (`0027` design D7, D8).
- **The ComfyUI transport is `boundary/comfy/`**, a package with a front door. The client turns a
  network error into `Unreachable` itself, word for word; the CLI's `_Reporting` wrapper is gone.
  `probe/loader_probe.py` now receives `Unreachable` rather than a raw `URLError` (`0027` design D9).
- **The approval state is the pipeline's.** `Status` and `state(directory)` move, unchanged, from the
  review UI's `Batch` into `pipeline/review.py`; `run_view.py` asks `run.is_approved`; the unused
  `review.is_complete` is deleted (`0027` design D11).
- **The docs follow the code.** `docs/modules.md` draws the new graph and `docs/principles.md` names
  `tests/test_layers.py` where it held *not yet*; the `comfy-transport` and `run-directory` preambles
  name the moved modules; the layer test's allowlist is deleted (`0027` design D10, D12).

## [0.22.4] - 2026-09-25

### Changed

- **The sweep: code, tests and spec preambles say what the code does.** Docstrings, comments,
  the `caption` and `sheet` help text, the parser's description and `pyproject.toml` lose retired
  mechanisms, *"the only"* claims and counts (`0026` design D1, S1–S30). No behaviour changes.
- **`docs/` holds the architecture.** `principles.md`, `decisions.md` (with D29 and D30, the product
  scope) and `README.md` are written from `0026`'s payload; `docs/arc/` is flattened into `docs/`, its
  false claims corrected, and `modules.md` gains how the components interact.
- **`CLAUDE.md` keeps only process and imports `docs/principles.md`.** Its design rules move to `docs/`;
  the change id is the next free number; it gains what a patch may hold, and the notebook and
  demo-subject rules (`0026` design D8).
- **The group READMEs point at `docs/principles.md` and `docs/decisions.md`** instead of *"the design
  record"*, which named nothing in the repository (`0026` design D9).
- **`README.md` stops restating the architecture.** `## The path` becomes `## Architecture`, a link to
  `docs/`; the intro, the caption notes and the gate's mirrors say what the code does (S43–S46, D10).

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

- `isekai/boundary/ollama.py`: open models behind a local Ollama read and sort, with no `claude` needed
  (0019 D1, D5).
- A flow may declare the models its first two stages call, and `flows/summon-open-v1/` does (0019 D2, D3).
- An unreachable host or an absent model refuses without spending an attempt (0019 D9).
- A manifest key this build does not read is refused by name (0019 D12).

### Fixed

- The photograph is never sent through the environment's `http_proxy` (0019 D4).
- A connection dropped mid-answer is classified rather than ending the batch (0019 D9).

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
- An autosave racing an approve no longer loses the last correction (0018 D13).

## [0.17.0] - 2026-09-18 · 0017-conjure

### Added

- `flows/conjure-v1/`: a render from the sheet alone, no photograph, added without code (0017 D1, D2, D3).
- Its schema is chosen by vocabulary depth, and its dials are `summon`'s less the identity ones (0017 D4, D6).

### Fixed

- Both `conjure-v1` briefings stop eliciting attributes the vocabulary cannot hold (0017 D5).

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

- The package becomes group directories, each with a `README.md`; the CLI moves to `interface/cli.py`
  (0015 D2, D3, D11).
- `show.py` becomes `run_view.py`, `photo.py` becomes `image.py`, and `write_atomically` is its own module
  (0015 D4, D6).
- The repository-root anchors are pinned by a test before anything moves (0015 D7).

### Fixed

- The image and the provisioning driver follow `provision.py` into `boundary/` (0015).

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
- `run.json` records the photograph's digest, the base, the working resolution, and each variation's seed, graph
  digest and dials (0012 D4).
- `--fixed-dials` renders at the graph's own dials, and `--cn-strength` sets the identity node's keypoint dial
  (0012 D3, D6).
- The evaluator's models are pinned in `scripts/eval_models.json`, a sibling of the graph's manifest, with every
  licence recorded (0012 D16, D18).
- The guard ships box IoU as its authoritative method, chosen by measuring both (0012 D9).

### Changed

- The anime-face detector is `deepghs/anime_face_detection`, MIT: the AGPL one named publishes no ONNX (0012 D19).

### Fixed

- `run.json` records the pod image and the ComfyUI commit, bounded to printable ASCII, and the report reads them
  (0012 D14).
- The pose reader's crop, normalisation and channel order match its published reference pipeline (0012).

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
