# Tasks — 0009-pinned-provisioning

## Progress

- [x] 1 — The manifest: eleven entries, pinned and hashed, and the helper that re-derives them
- [x] 2 — The provisioning module: the policy, the injected fetcher, the offline tests
- [x] 3 — Port the downloader: the shell becomes a thin driver, and the image carries what it needs
- [x] 4 — Bind the graph to the manifest, including what the graph never names
- [x] 5 — The annotator redirect: 386 MB moves onto the volume
- [x] 6 — The namespace: one mount, one symlink, every node
- [x] 7 — The docs: `README.md` and `CLAUDE.md` describe a pinned stack
- [ ] 8 — ⚠️ **GPU · HALT** — inventory the existing volume, run by the operator
- [ ] 9 — ⚠️ **GPU · HALT** — provision a new volume by script alone, render, then destroy the old

## The per-phase ritual

Every phase, without exception:

1. **Test-first where there is logic.** Phase 7 is prose and has none; phases 1–6 do. Red → green.
2. **Run each phase's stated verification — run it, never summarize it.** The commands are named in the phase
   detail below. Paste real output.
3. **Gate green before the commit** — `make gate`, which runs the five commands in `.minions/minions.toml`'s
   `gate` array, in order. A phase that leaves the gate red is not done. **Never weaken the gate to pass**;
   halt instead. Phases 3, 5 and 6 touch shell and the image, so they additionally run `bash -n` on every
   changed script and `docker build --check`.
4. **Append that phase's entry under `## [Unreleased]` in `CHANGELOG.md`**, in the style of the entries already
   there, using `### Added` / `### Changed` / `### Removed` headings.
5. **Check the box** in the `## Progress` list above, in that phase's own commit. The first unchecked entry is
   the current phase; that is how the loop reads this file.
6. **One commit per phase**, staged **by name**, carrying the trailer `Change: 0009-pinned-provisioning`
   **contiguous** with `Co-Authored-By:` — no blank line between them, or git stops parsing the trailer block.

**The test count moves up in this change.** v0.8 ends at 87. Every scenario in
`specs/model-provisioning/spec.md` declares `Layers: unit` and gains at least one bound test; no existing test
is deleted, because no existing behaviour changes.

**Two phases spend real money and both are HALT phases.** `CLAUDE.md` grants spend authority to the phase, not
to the agent: a pod goes up only for a phase marked ⚠️ GPU here, `infra/up.sh` creates it, `infra/down.sh` tears
it down, and teardown is confirmed through the RunPod MCP with what it returned recorded. The ceiling is
**45 minutes and ~$0.30 per pod session**. The operator brings the pod up in both phases (design.md D12).

**Nothing is destroyed before phase 9's render is green.** Phase 8 only reads. The old volume stays a complete
rollback until the last task of phase 9, and that ordering is the change's whole safety argument (design.md
D11).

**Phases 1–7 need no pod and no network beyond phase 1's derivation.** If the environment cannot reach Hugging
Face during phase 1, that is a halt with a named cause, not a reason to hand-write a digest.

## Phase detail

### 1 — The manifest: eleven entries, pinned and hashed, and the helper that re-derives them

`scripts/download_models.sh` today names seven sources, pins none of them, and omits four more files that the
graph's preprocessors fetch for themselves. This phase produces the data that fixes both, and the tool that
produced it — so a future upgrade is a re-run, not eleven manual lookups (design.md D15 for the location).

**The eleven entries.** Seven existing: `cagliostrolab/animagine-xl-4.0`, `InstantX/InstantID` ×2 (ip-adapter
and the identity ControlNet), `DIAMONIK7777/antelopev2` (five ONNX files),
`TTPlanet/TTPLanet_SDXL_Controlnet_Tile_Realistic`, `xinsir/controlnet-openpose-sdxl-1.0`,
`TheMistoAI/MistoLine`. Four new: `yzd-v/DWPose/yolox_l.onnx`,
`hr16/DWPose-TorchScript-BatchSize5/dw-ll_ucoco_384_bs5.torchscript.pt`, and
`lllyasviel/Annotators/{sk_model.pth,sk_model2.pth}` — the last two are fetched **unconditionally** by
`LineArtPreprocessor` regardless of the graph's `coarse: "disable"`, so both are entries.

**Two constants come from the sibling project** rather than being re-derived, because they name the same
repository and the same file this project already pulls unpinned: `InstantX/InstantID` at
`57b32dfee076092ad2930c71fd6d439c2c3b1820`, and that revision's digest for `ip-adapter.bin` (design.md D2).

**Each entry carries** a destination path, a SHA-256, and an **ordered list of sources**, each addressing an
immutable revision. Entries whose primary source is a third-party mirror — antelopev2 and both DWPose repos —
carry at least one alternate (design.md D10). The manifest header records the date the pins were taken.

**Derive, do not transcribe.** The helper reads each source's published metadata and emits the manifest; the
committed file is its output. Hugging Face publishes the SHA-256 as the LFS object id and in the
`x-linked-etag` response header, so no artifact is downloaded to learn its digest.

**Tests:** the manifest parses, every entry has the required keys, no source resolves a mutable ref, every
entry carries a well-formed 64-hex digest, and every third-party-primary entry carries an alternate. Each
assertion is proven against a deliberately malformed fixture entry first.

**Verification:**
- `uv run pytest tests/test_manifest.py -q` — green, and each new test bound with `@pytest.mark.spec`
- re-run the helper and `git diff --exit-code scripts/models.json` — no drift between tool and committed data
- `make gate` — exit 0

**Closes:** `model-provisioning:immutable-pins:no-source-resolves-a-mutable-ref` ·
`…:every-entry-carries-a-digest` · `…:third-party-artifact-carries-an-alternate`.

### 2 — The provisioning module: the policy, the injected fetcher, the offline tests

The trust boundary is a *decision*, and this phase makes it one that `pytest` can reach (design.md D14). For
each manifest entry the module returns exactly one of:

- **skip** — the file is present and its digest matches;
- **abort** — the file is present and its digest does not match. It is **not deleted**: the volume is shared
  with another project, and a file this run did not write is not this run's to remove (design.md D4, D9);
- **fetch** — the file is absent, or the source's published digest disagreed with the manifest, in which case
  the next declared source is offered instead.

After a fetch, the module verifies the downloaded bytes and only then lands them at the destination, so a
failed or interrupted transfer never occupies the final name.

The **fetcher is an injected seam**, and a fake one is what makes all of this offline — the same argument, and
the same shape, as `FakeComfyClient` in `tests/`. Verification itself is `hashlib` and nothing else: no
dependency is added, and nothing here enters `convert.py`'s import graph.

**Tests:** matching bytes pass; mismatched bytes fail with a message naming the file, the expected digest and
the computed one; a present-and-matching file is verified rather than skipped by name; a present-and-mismatched
file aborts and **still exists afterwards**; an interrupted fetch leaves no file at the destination; a
pre-flight mismatch rejects that source without transferring and offers the next; a source publishing no digest
proceeds to download and post-verify rather than being trusted.

**Verification:**
- `uv run pytest tests/test_provision.py -q` — green
- `uv run pytest -q` — the full suite still offline and deterministic
- `make gate` — exit 0

**Closes:** `model-provisioning:byte-verification:mismatched-bytes-are-rejected` ·
`…:a-present-file-is-verified-not-skipped` · `…:a-failed-download-never-lands` ·
`…:a-present-file-that-fails-is-not-deleted` ·
`model-provisioning:preflight:published-digest-mismatch-aborts-before-transfer`.

### 3 — Port the downloader: the shell becomes a thin driver, and the image carries what it needs

Replace `scripts/download_models.sh` with the ported design (design.md D2, D3): it reads the manifest, asks the
module what to do with each entry, runs `wget` for whatever URL it is handed, and asks the module to verify and
land the result. Inline per-model variables and the `hf` CLI both go — every source is now a URL string the
manifest carries and the suite can inspect.

**The image must carry what the script now depends on.** The `Dockerfile` copies `start.sh` and
`scripts/download_models.sh` and nothing else; it must also copy the manifest and the module, or provisioning
arrives on the pod missing both (design.md D15).

**Verification:**
- `bash -n scripts/download_models.sh` — exit 0
- `git grep -n "hf download" -- scripts Dockerfile start.sh` — no hits
- `docker build --check .` — exit 0
- `git grep -n "COPY" Dockerfile` — shows the manifest and the module alongside the script
- `make gate` — exit 0

**Closes:** nothing on its own — phase 2 owns the behaviour; this phase is the driver that runs it on the pod.

### 4 — Bind the graph to the manifest, including what the graph never names

Half the binding is direct: every model filename appearing in `workflows/pipeline.json`'s node inputs must have
a manifest entry. The other half is the gap this whole change was found through — `LineArtPreprocessor` names
no file at all and downloads two — so a **tracked mapping from node class to the files that node fetches for
itself** carries the rest, and a graph containing such a node whose class is absent from the mapping fails
rather than passing silently (design.md D6).

The reverse direction is deliberately **not** asserted: the manifest legitimately carries artifacts no graph
field names, such as the antelopev2 pack that `InstantIDFaceAnalysis` resolves by directory.

**Verification:**
- `uv run pytest tests/test_manifest_binding.py -q` — green
- prove the check bites: temporarily remove one manifest entry and confirm the test fails; temporarily delete
  `LineArtPreprocessor` from the mapping and confirm the test fails; restore both and confirm green
- `make gate` — exit 0

**Closes:** `model-provisioning:manifest-completeness:graph-filename-has-an-entry` ·
`…:preprocessor-models-are-declared`.

### 5 — The annotator redirect: 386 MB moves onto the volume

`comfyui_controlnet_aux` writes annotator checkpoints to `<node dir>/ckpts` — the pod's **container disk**,
because the volume mounts elsewhere. That is 386 MB re-fetched from Hugging Face during the first render of
every pod, unpinned, on metered time. Set `AUX_ANNOTATOR_CKPTS_PATH` in the `Dockerfile` to a path inside the
project's models tree and point the four manifest destinations at it, so they become ordinary entries fetched
ahead of time (design.md D7).

**The pack's own log cannot confirm this.** It prints `Using ckpts path: …` from the config-derived value, not
from the environment override, so it will report the old path while writing to the new one. The
`CHANGELOG.md` entry for this phase must say so, because phase 9 confirms the redirect **on the filesystem**
and a future reader will otherwise reach for the log.

**Verification:**
- `uv run pytest tests/test_infra.py -q` — green, asserting the env var is set to a path inside the models tree
- `docker build --check .` — exit 0
- `make gate` — exit 0

**Closes:** `model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree`.

### 6 — The namespace: one mount, one symlink, every node

Move `infra/up.sh`'s `volumeMountPath` to `/runpod-volume` and add a single symlink in `start.sh` pointing
`/opt/ComfyUI/models` at `/runpod-volume/isekai`. Because `folder_paths.models_dir` is then itself inside the
namespace, **every** node resolves there — including the InstantID node and the Impact Subpack, which the
sibling project established live will ignore `extra_model_paths.yaml` and, unredirected, auto-download a broken
nested antelopev2 pack (design.md D8).

Artifacts shared with the sibling project are **duplicated, not shared** (design.md D9); nothing in this phase
reaches outside `/runpod-volume/isekai`.

**Verification:**
- `bash -n infra/up.sh start.sh` — exit 0
- `uv run pytest tests/test_infra.py -q` — green, asserting the mount path and the symlink target
- `git grep -nE "1[a-z0-9]{9}|/Users/" -- . ':!.env' ':!openspec/changes/archive'` — no hits; no tracked file
  names a real volume id or an absolute path from this machine
- `make gate` — exit 0

### 7 — The docs: `README.md` and `CLAUDE.md` describe a pinned stack

`README.md`: the stack is provisioned from a pinned, checksummed manifest and the volume is namespaced per
project. Make **no** claim about identity, quality or the base — this version changed none of them.

`CLAUDE.md`: the living spec goes from four capabilities to five (`model-provisioning` joins at archive time,
which is `mf-release`'s act), and the layout section gains the manifest and the module. The five-command gate
array is unchanged and must stay so.

**Verification:**
- `git diff --stat README.md CLAUDE.md` — both touched
- `git grep -n "gate" .minions/minions.toml Makefile` — the array and the target still agree, command for
  command
- `make gate` — exit 0

### 8 — ⚠️ **GPU · HALT** — inventory the existing volume, run by the operator

**Announce, then stop.** The operator runs `infra/up.sh` with the existing volume attached. This phase only
**reads**; nothing is created, moved or deleted on the volume.

Record a full recursive listing with sizes, then tear down with `infra/down.sh` and confirm through the RunPod
MCP, recording what it returned. Classify every path found:

- placed by this project's script;
- placed by the sibling project's script (it nests under `<volroot>/models/`, one level deeper than this
  project's, which is why the two have not collided);
- orphaned — the four Qwen weights v0.8 removed from the script but never from disk, and the `.hf` staging
  tree the old `download()` never cleaned up;
- **unaccounted for.**

**This phase is the gate on the destroy.** Phase 9 may not begin until nothing unaccounted-for is
irreplaceable. Both projects' scripts are pinned and checksummed, so anything they declare is re-downloadable;
anything else is not.

Also determine which repository's `.env` names the live volume id — the account holds one volume and the two
files disagree, so one is already stale. Record the finding; **do not** transcribe the id into any tracked
file.

**Verification:** the listing and the classification are recorded in the phase's `CHANGELOG.md` entry ·
teardown confirmed through the MCP, with its response recorded.

### 9 — ⚠️ **GPU · HALT** — provision a new volume by script alone, render, then destroy the old

**Announce, then stop.** This phase is the change's acceptance criterion and its only irreversible act, in that
order.

1. Create the new volume in the **same data center** (a volume cannot move, and a pod cannot mount one from
   elsewhere), sized from both projects' manifests — design.md's first Open Question, answered here.
2. Operator runs `infra/up.sh` against the new volume. Provision it **with the script alone — no file placed
   by hand.** Confirm every entry was fetched and verified, and confirm **on the filesystem** that the
   annotator checkpoints landed inside the models tree rather than at the pack's default (phase 5 — the log
   will not tell you this).
3. Render the **unchanged** Animagine path: `convert.py <photo>` exits 0 and writes `0.png`–`4.png` plus
   `run.json`. Download the outputs before teardown — pod disk is ephemeral. Tear down with `infra/down.sh`
   and confirm through the MCP.
4. **Only now**: destroy the old volume, and update `RUNPOD_VOLUME_ID` in this repository's `.env` and in the
   sibling project's. Confirm through the MCP that the old volume is gone and record what it returned.

**Verification:**
- `convert.py <photo>` — exit 0, five images and a `run.json` in the run directory
- the provisioning log shows every entry fetched-and-verified, none skipped-unverified
- a directory listing on the pod shows the annotator checkpoints inside the models tree
- both teardown and the volume deletion confirmed through the MCP, with responses recorded

**The `CHANGELOG.md` entry must state what this version did not establish**: nothing about identity, fidelity,
quality or the base. It establishes exactly two things — that the stack is reproducible from a pinned manifest,
and that the unchanged path renders from a volume whose entire contents were placed by the script.
