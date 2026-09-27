# Tasks — 0033 pin and record

CI first, then the image and its rc build, the pin, the reader, the records and the docs; the acceptance runs
the whole flow last, with every pin in place ([D8](design.md#d8)).

## Progress

- [x] 1 — CI and the toolchain
- [x] 2 — The image: inputs by digest, a locked environment, built on request
- [x] 3 — 🛑 **HUMAN** — push the branch and dispatch the rc build
- [x] 4 — The pin: `config/image.json`, `up.sh` boots it
- [x] 5 — The reader: `config/reader.json`, the model checked before its first call
- [x] 6 — The records
- [ ] 7 — The record in `docs/`
- [ ] 8 — 🛑 **HUMAN · METERED · HALT** — the acceptance: the whole flow, both flows, every pin in place

Line numbers are `801ffec`'s; find each site by the text it names.

## 1 — CI and the toolchain

- [x] 1.1 **HALT CHECK** — the workflows use major tags, and no uv version is pinned.
  Verify: `cat .github/workflows/ci.yml .github/workflows/build-image.yml | grep -c -E 'uses: [^@]+@v[0-9]+$'` prints a number above `0`, and `grep -c 'required-version' pyproject.toml` prints `0`.
- [x] 1.2 ⛔ Ask the operator to upgrade this machine's uv to 0.12.19, then add `[tool.uv] required-version = "==0.12.19"` to `pyproject.toml`; re-lock `uv.lock` only if `uv lock --check` fails, per [D1](design.md#d1).
  Verify: `uv --version | cut -d' ' -f2` prints `0.12.19`, and `grep -c 'required-version = "==0.12.19"' pyproject.toml` prints `1`.
- [x] 1.3 In both workflows, pin every `uses:` to its commit SHA with the release in a comment, set `runs-on: ubuntu-24.04`, give `astral-sh/setup-uv` `version: "0.12.19"` and Node an exact `22.x.y`, per [D1](design.md#d1).
  Verify: `cat .github/workflows/ci.yml .github/workflows/build-image.yml | grep -c -e 'ubuntu-latest' -e "node-version: '22'"` prints `0`, and `cat .github/workflows/ci.yml .github/workflows/build-image.yml | grep -c -E 'uses: [^@]+@v[0-9]+$'` prints `0`.

## 2 — The image: inputs by digest, a locked environment, built on request

- [x] 2.1 **HALT CHECK** — the image installs from requirement files, with CPU `onnxruntime` beside them.
  Verify: `grep -c 'uv pip install -r' Dockerfile` prints `2`, and `grep -c 'onnxruntime==1.20.1' Dockerfile` prints `1`.
- [x] 2.2 Write `tools/derive_image_project.py`, add it to the `Makefile`'s `derive` with `image/` in its closing `git diff --stat`, and run it to write `image/pyproject.toml`, `image/uv.lock` and `image/.python-version`, per [D2](design.md#d2).
  Verify: `test -f image/uv.lock && grep -c '"onnxruntime' image/pyproject.toml` prints `1`, and `grep -c 'derive_image_project' Makefile` prints `1`.
- [x] 2.3 In the `Dockerfile`, name the base and uv by digest, copy `image/pyproject.toml`, `image/uv.lock` and `image/.python-version` one by one, set `UV_PROJECT_ENVIRONMENT`, and run `uv sync --locked` in place of `uv venv` and every `uv pip install`, per [D2](design.md#d2); `docker build --check .` passes.
  Verify: `grep -c -e 'uv pip install' -e 'uv venv' Dockerfile` prints `0`, and `grep -c '@sha256:' Dockerfile` prints `2`.
- [x] 2.4 Make `.github/workflows/build-image.yml` dispatch-only with a required tag that is not `latest`, give the build step an `id`, and write its digest to the job summary, per [D2](design.md#d2).
  Verify: `grep -c -e '^  push:' -e 'branches:' .github/workflows/build-image.yml` prints `0`, and `grep -c 'outputs.digest' .github/workflows/build-image.yml` prints `1`.
- [x] 2.5 Print `date -u` before each step of `start.sh`, and the UTC times `infra/up.sh` created the pod and saw port 22 mapped, per [D2](design.md#d2); keep `tests/test_infra.py`'s `start.sh` checks (`:184`, `:252`) green.
  Verify: `grep -c 'date -u' start.sh` prints a number above `4`.
- [x] 2.6 In `tests/test_infra.py`, test `pod-image:build:only-a-request-builds`, `pod-image:build:inputs-are-named-by-digest`, `pod-image:build:the-environment-is-locked` and `pod-image:boot:each-step-is-timestamped`.
  Verify: `grep -c -e 'pod-image:build:' -e 'pod-image:boot:each-step-is-timestamped' tests/test_infra.py` prints `4`.

## 3 — 🛑 **HUMAN** — push the branch and dispatch the rc build

- [x] 3.1 ⛔ **HALT.** Ask the operator to push `v0.24_pin_and_record`, run `gh workflow run build-image.yml --ref v0.24_pin_and_record -f tag=v0.24-rc1`, and give the digest from the job summary. Record it as the first line of `openspec/changes/0033-pin-and-record/acceptance.md`: `Image: ghcr.io/alxb1t/isekai:v0.24-rc1@sha256:<digest>`.
  Verify: `grep -c '^Image: ghcr.io/alxb1t/isekai:v0.24-rc1@sha256:[0-9a-f]\{64\}$' openspec/changes/0033-pin-and-record/acceptance.md` prints `1`.

## 4 — The pin: `config/image.json`, `up.sh` boots it

- [x] 4.1 **HALT CHECK** — `up.sh` boots an image the environment can override.
  Verify: `grep -c 'RUNPOD_IMAGE' infra/up.sh` prints a number above `0`.
- [x] 4.2 Write `config/image.json` with phase 3's digest; `infra/up.sh` boots `<image>@<digest>` and writes `.runpod_pod_image`; `infra/down.sh` removes it on 204; drop `RUNPOD_IMAGE` and `.env.example:15-18`; add `.runpod_pod_image` to `.gitignore`; tag compose builds `isekai:local`, per [D3](design.md#d3).
  Verify: `cat infra/up.sh .env.example docker-compose.yml | grep -c -e 'RUNPOD_IMAGE' -e ':latest'` prints `0`, and `grep -c '^.runpod_pod_image$' .gitignore` prints `1`.
- [x] 4.3 In `tests/test_infra.py`, test `pod-image:boot:the-pinned-digest-is-booted`, `pod-image:boot:no-override` and `pod-image:boot:the-booted-image-is-recorded`; keep `up.sh`'s checks (`:105`, `:112`, `:298`, `:313`, `:320`, `:401`) green.
  Verify: `grep -c 'pod-image:boot:' tests/test_infra.py` prints `4`.

## 5 — The reader: `config/reader.json`, the model checked before its first call

- [x] 5.1 **HALT CHECK** — no reader manifest exists, and nothing reads Ollama's record of a model.
  Verify: `test -f config/reader.json; echo $?` prints `1`, and `grep -c -F '.ollama/' isekai/boundary/ollama.py` prints `0`.
- [x] 5.2 Write `tools/derive_reader.py` through `tools/manifest.py` and run it to write `config/reader.json`, with `aliases` and `concedo` as its publisher; add it to the `Makefile`'s `derive` and `tests/test_derivation.py`'s `DERIVERS`, per [D4](design.md#d4).
  Verify: `grep -c '"joycaption-beta-one-q4k"' config/reader.json` prints `1`, and `grep -c 'derive_reader' Makefile` prints `1`.
- [x] 5.3 Add `provision.READER_MANIFEST_PATH` and `Manifest`'s `NotRequired` `aliases` to `isekai/boundary/provision.py`, the anchor to `tests/test_package_paths.py`, and point `config/joycaption.Modelfile`'s comment at the manifest, per [D4](design.md#d4).
  Verify: `grep -c 'READER_MANIFEST_PATH' tests/test_package_paths.py` prints a number above `0`, and `grep -c 'e8ae55dd07e61d541ab741d6ed63e7810192cea65d7ef8cda69b2a99fb06dc15' config/joycaption.Modelfile` prints `0`.
- [x] 5.4 In a new `tests/test_reader_manifest.py`, test `each-model-names-its-model-and-projector`, `every-flow-model-is-pinned` and `driver-provisions-the-manifest` under `model-provisioning:reader:`, and extend `test_the_vocabulary_appears_only_in_its_own_manifest` (`tests/test_vocabulary_manifest.py:122`) to the reader's manifest.
  Verify: `grep -c 'model-provisioning:reader:' tests/test_reader_manifest.py` prints `3`.
- [x] 5.5 In `isekai/boundary/ollama.py`, add the check [D4](design.md#d4) describes — a constant root, injectable, memoised per model — and call it in `OllamaReader.read` and `OllamaTagger.tag` before `ask`; `Reading` and `Tagging` carry the verified `artifacts` and `pinned=True`.
  Verify: `grep -c 'registry.ollama.ai' isekai/boundary/ollama.py` prints `1`.
- [x] 5.6 Test `caption:reachability:an-unpinned-build-is-refused`, `caption:reachability:an-unpinned-model-is-refused` and the first-call scenario's *no record read* in `tests/test_caption.py`, and `tagging:independence:an-unpinned-hosted-model-costs-no-local-list` in `tests/test_tagging.py`; point `tests/test_caption.py:402-416` and `tests/test_pipeline_cli.py`'s real-reader tests (`:375`, `:404`, `:416`, `:427`) at a fixture root.
  Verify: `grep -c -e 'an-unpinned-build-is-refused' -e 'an-unpinned-model-is-refused' tests/test_caption.py` prints `2`.
- [x] 5.7 Record `artifacts` and `pinned` in the caption's and hosted tags' producers (`isekai/pipeline/caption.py:249-259`, `isekai/pipeline/tagging.py:349-359`), with `caption:provenance:a-verified-model-is-pinned` and `tagging:provenance:the-hosted-tagger-declares-its-pin`; reword `tagging.py:242-247` and `:316-318`, per [D4](design.md#d4).
  Verify: `grep -c 'caption:provenance:a-verified-model-is-pinned' tests/test_caption.py` prints `1`, and ``grep -c 'record `pinned: false`' isekai/pipeline/tagging.py`` prints `0`.

## 6 — The records

- [x] 6.1 **HALT CHECK** — no pipeline stage records a floor or a flow digest.
  Verify: `cat isekai/pipeline/sheet.py isekai/pipeline/generate.py isekai/pipeline/tagging.py | grep -c -e 'flow_digest' -e '"floor"'` prints `0`.
- [x] 6.2 In `isekai/foundation/artifacts.py`, add every key [D5](design.md#d5) names as `NotRequired`, and make `Render`'s `sheet_version` `NotRequired`, per [D6](design.md#d6); test `run-directory:schema:an-added-record-key-is-optional` in `tests/test_run_directory.py`.
  Verify: `grep -c 'flow_digest: NotRequired' isekai/foundation/artifacts.py` prints `3`.
- [x] 6.3 Record `options` in the caption and tags producers and `floor` in the wd14 producer, and carry `floor` into the sheet's producer when the list records one, per [D5](design.md#d5); test `caption:provenance:the-options-are-recorded`, `tagging:provenance:options-and-floor-are-recorded` and `sheet:output:sheet-carries-the-floor`.
  Verify: `grep -c 'sheet:output:sheet-carries-the-floor' tests/test_sheet_stage.py` prints `1`.
- [x] 6.4 Give `sheet()` a required `flow_digest` keyword, passed by `isekai/interface/cli.py` and `tests/stages.py`, and record it in the sheet; test `sheet:output:sheet-names-its-flow-digest`, per [D5](design.md#d5).
  Verify: `grep -c 'sheet:output:sheet-names-its-flow-digest' tests/test_sheet_stage.py` prints `1`.
- [x] 6.5 Record `flow_digest` and `sheet` in the prompt and the render, stop writing the render's `sheet_version`, and say *by approval* in `run_view.rendered`'s docstring, per [D5](design.md#d5); in `tests/test_generate.py`, test `image-generation:provenance:the-flow-digest-and-the-sheet-are-recorded` with differing numbers, and rebind `:423-437` and `:531` to the renamed scenarios.
  Verify: `grep -c 'outputs-carry-the-approval' tests/test_generate.py` prints `1`, and `grep -c '"sheet_version":' isekai/pipeline/generate.py` prints `0`.
- [x] 6.6 Add `system_stats()` to `ComfyTransport`, `ComfyClient` (a `GET` under `_reported`) and `tests/fakes.py`'s `FakeComfyClient`, with `comfy-transport:runtime:the-report-is-read-through-the-seam` in `tests/test_generate.py`, per [D5](design.md#d5).
  Verify: `cat isekai/boundary/comfy/contract.py isekai/boundary/comfy/client.py tests/fakes.py | grep -c 'def system_stats'` prints `3`.
- [x] 6.7 Give `render()` required `image` and `runtime` keywords, called after `if not wanted`; `cli._generate` reads `.runpod_pod_image` (an anchor in `tests/test_package_paths.py`) and passes a thunk memoised per session; test `a-pinned-pod-is-recorded`, `an-unrecorded-endpoint-is-unpinned` and `a-complete-batch-reads-no-report` under `image-generation:runtime:`, and adapt `tests/test_generate.py:740-903`, per [D5](design.md#d5).
  Verify: `grep -c 'image-generation:runtime:' tests/test_generate.py` prints `3`.
- [x] 6.8 Carry `schema_document` and `field_map` from the sheet into the draft and from the draft into the approval in `isekai/pipeline/review.py`, with `review:copy:the-sheet-records-are-carried` in `tests/test_review.py`, per [D5](design.md#d5).
  Verify: `grep -c 'review:copy:the-sheet-records-are-carried' tests/test_review.py` prints `1`.
- [x] 6.9 Re-capture the goldens each added key moves — `caption`, `tags`, `wd14`, `sheet`, `sheet-empty`, `draft`, `draft-saved`, `approved`, `prompt` and `render` under `tests/golden/` — and no byte beyond those keys.
  Verify: `cat tests/golden/sheet.json tests/golden/prompt.json tests/golden/render.json | grep -c '"flow_digest"'` prints `3`.

## 7 — The record in `docs/`

- [ ] 7.1 In `docs/decisions.md`, rewrite D6 and D28 and add D32, per [D7](design.md#d7).
  Verify: `grep -c '^### D32 · ' docs/decisions.md` prints `1`, and `grep -c 'config/image.json' docs/decisions.md` prints a number above `0`.
- [ ] 7.2 Shrink `docs/principles.md`'s pinning list (`:184-187`) to the apt gap and empty its records line (`:237-239`); in `README.md`, replace the by-hand GGUF fetch (`:279-281`) with the provisioning command and name `config/image.json`; name `.runpod_pod_image` in `CLAUDE.md`; add `config/reader.json` and `tools/derive_reader.py` to the `model-provisioning` spec's Source line, per [D7](design.md#d7).
  Verify: ``grep -c 'its moving `latest` tag' docs/principles.md`` prints `0`, and `grep -c 'download_models.sh config/reader.json' README.md` prints a number above `0`.

## 8 — 🛑 **HUMAN · METERED · HALT** — the acceptance: the whole flow, both flows, every pin in place

**Ceiling: 45 minutes and ~$0.30 for the pod session.** The pod goes up only through `infra/up.sh`, and down
through `infra/down.sh` in the same session; the RunPod MCP confirms it gone. **A synthetic portrait, never a
real person's photograph.** Every command and what it printed goes into `acceptance.md`, with no absolute path.

- [ ] 8.1 ⛔ **HALT.** Ask the operator to grow `isekai-models` to 45 GB in the RunPod console, for a synthetic portrait and a `--runs` root, and for an explicit go that quotes the ceiling; record the go as `Go: <date>` in `acceptance.md`.
  Verify: `grep -c '^Go: ' openspec/changes/0033-pin-and-record/acceptance.md` prints `1`.
- [ ] 8.2 The free half, for both flows: `bash tools/download_models.sh config/reader.json`, then `tag`, `caption`, `sheet`, and `ui` to review and approve; record each artifact's pins and records — both digests and `pinned: true` on the caption and tags, `floor`, `flow_digest`, and the approval's `schema_document` and `field_map`.
  Verify: `grep -c -e 'isekai tag --flow' -e 'isekai caption --flow' -e 'isekai sheet --flow' openspec/changes/0033-pin-and-record/acceptance.md` prints a number above `2`.
- [ ] 8.3 ⚠️ **METERED.** `bash infra/up.sh`, then `generate` with `--count 2` for `conjure-anime-wai` and `--count 1` for `summon-anime-wai`, then `bash infra/down.sh`, and the RunPod MCP confirms the pod gone; record the boot's timestamps, each render's `image`, `pinned`, `runtime`, `flow_digest` and `sheet`, and a judgement of the renders by eye.
  Verify: `grep -c -e '"pinned": true' -e 'pod gone' openspec/changes/0033-pin-and-record/acceptance.md` prints a number above `1`.
- [ ] 8.4 Close D27's known break in `docs/decisions.md` now that the volume clears the floor, and record the volume's size in `acceptance.md`.
  Verify: ``grep -c 'the floor `start.sh` declares is larger than the real volume' docs/decisions.md`` prints `0`.
