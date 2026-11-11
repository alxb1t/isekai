# The tattoo edit — tasks

The phases: the registry, the ink, the request, the session, the image's files, the pod proof, the docs. The image's files and the pod proof are a person's.

## Progress

- [x] 1 — Registry · moderate
- [x] 2 — Ink · hard
- [x] 3 — Request · hard
- [x] 4 — Session · hard
- [ ] 5 — Model and image **HUMAN**
- [ ] 6 — Proof on a pod **HUMAN · METERED**
- [ ] 7 — Docs · moderate

## 1 — Registry

- [x] 1.1 Add `isekai/foundation/edit.py` per [D1](design.md#d1): `EDITS_DIR`, `load_edit`, `tracked_edits`, `edit_digest` and the manifest's refusals, stdlib only; its tests in `tests/test_flow.py` carry `edit_load` in their names.
  Verify: `uv run pytest tests/test_flow.py -k edit_load` passes.
- [x] 1.2 Add `edits/tattoo-wai/edit.json` with the keys and values of [D2](design.md#d2), and `edits/tattoo-wai/graph.json`, the prototype's graph, its node ids named by `nodes`; tests carry `edit_tracked` and hold `checkpoint`, `controlnet` and `union_type` equal to what the graph names.
  Verify: `uv run pytest tests/test_flow.py -k edit_tracked` passes.
- [x] 1.3 Pin `tattoo-wai` in `tests/test_flow.py` by an `EDIT_PINNED` entry held equal to `edit_digest`, with a test carrying `edit_changelog` that each digest is in `CHANGELOG.md`, which the phase's bullet satisfies; the pin test carries `edit_pinned`.
  Verify: `uv run pytest tests/test_flow.py -k edit_pinned` passes.
- [x] 1.4 Add `EDITS_DIR` to the anchors `tests/test_package_paths.py` pins, so it resolves inside the repository.
  Verify: `uv run pytest tests/test_package_paths.py -k EDITS_DIR` passes.
- [x] 1.5 Hold the phase's tests together in one run.
  Verify: `uv run pytest tests/test_flow.py -k "edit_load or edit_tracked or edit_pinned"` passes.

## 2 — Ink

- [x] 2.1 **HALT CHECK** Pillow and numpy are declared, so the extraction adds no dependency.
  Verify: `git grep -n "numpy==" pyproject.toml` prints the pin.
- [x] 2.2 Add `config/ink.json` and `isekai/shared/ink.py` per [D3](design.md#d3): `extract_ink` computes the skin's envelope, the layer as the photograph over it, bare skin white, the stretch by `floor`; Pillow and numpy imported inside the functions; tests in `tests/test_ink.py` carry `ink_extract`.
  Verify: `uv run pytest tests/test_ink.py -k ink_extract` passes.
- [x] 2.3 Extend `isekai/shared/ink.py` with the outline as the layer's alpha, neutral, and depth as a power of the Multiply factor, each default by its input and each overridable; tests carry `ink_flags`.
  Verify: `uv run pytest tests/test_ink.py -k ink_flags` passes.
- [x] 2.4 Add the `ink` verb to `isekai/interface/cli.py`: `<image> <out>`, `--outline`, `--neutral`/`--no-neutral`, `--depth` refused outside the range at parse time, the layer written atomically; add `ink` last in `VERBS` and in the tuple of verbs that take no `photos` positional, and last in `EXPECTED_VERBS` with its argv in the per-verb table of `tests/test_pipeline_cli.py`; tests carry `ink_verb`.
  Verify: `uv run pytest tests/test_ink.py -k ink_verb` passes.
- [x] 2.5 Hold that the entry point's import graph reaches no wheel and the layers hold.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_layers.py` passes.
- [x] 2.6 Hold the phase's tests under the acceptance's selector.
  Verify: `uv run pytest tests/test_ink.py -k ink` passes.

## 3 — Request

- [x] 3.1 Add to `isekai/foundation/artifacts.py` the kind `EDIT_FILE` and its `EditRecord`, and to `isekai/foundation/run.py` the names of an edit's files and the parse of an edit image's path ([D5](design.md#d5)); tests in `tests/test_edit.py` carry `edit_names`.
  Verify: `uv run pytest tests/test_edit.py -k edit_names` passes.
- [x] 3.2 Add `isekai/shared/tattoo.py` per [D4](design.md#d4): the ink as composite over render, the darkness, the mask grown and feathered, the control, Pillow and numpy imported inside the functions; tests carry `edit_derive`.
  Verify: `uv run pytest tests/test_edit.py -k edit_derive` passes.
- [x] 3.3 Extend `isekai/shared/tattoo.py` with the refusals of [D4](design.md#d4), each naming its fix, and the near-black rule; tests carry `edit_refuse`.
  Verify: `uv run pytest tests/test_edit.py -k edit_refuse` passes.
- [x] 3.4 Extend `isekai/shared/tattoo.py` with the crop box: the mask's box plus the margin, widened, grown, the sampling size; tests carry `edit_crop`.
  Verify: `uv run pytest tests/test_edit.py -k edit_crop` passes.
- [x] 3.5 Add `isekai/pipeline/edit.py` with the request ([D5](design.md#d5)): the composite kept as RGB pixels, composite then record written, the seed drawn, the overrides marked, the chain's next `k`, a refusal writing nothing, Pillow imported inside the functions; tests carry `edit_request`.
  Verify: `uv run pytest tests/test_edit.py -k edit_request` passes.
- [x] 3.6 Add the `edit` verb's request form to `isekai/interface/cli.py`: `<edit> <render> --composite`, `--denoise`, `--strength`, `--lines`, `--seed`, an untracked edit refused naming the tracked ones, no endpoint used; add `edit` after `ink` in `VERBS`, in the tuple of verbs that take no `photos` positional and in `EXPECTED_VERBS`, with its argv in the per-verb table of `tests/test_pipeline_cli.py`; tests carry `edit_verb`.
  Verify: `uv run pytest tests/test_edit.py -k edit_verb` passes.
- [x] 3.7 Hold that the verb table, the entry point's imports and the layers stand with the new verbs and modules.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_layers.py` passes.

## 4 — Session

- [x] 4.1 Move `_submit` as `submit_and_wait`, with `_history`, `read_runtime` and `_first_device`, from `isekai/pipeline/generate.py` to `isekai/boundary/comfy/prompt.py`, exported by `isekai/boundary/comfy/__init__.py`, and `graph_digest` to `isekai/foundation/flow.py` ([D6](design.md#d6)); point `isekai/interface/cli.py`, `isekai/interface/render.py`, `tests/test_generate.py`, `tests/test_artifact_bytes.py` and `tests/stages.py` at their new places, and `generate.py` at `submit_and_wait`.
  Verify: `git grep -n submit_and_wait isekai/pipeline/generate.py` prints the call.
- [x] 4.2 Extend `isekai/pipeline/edit.py` with `sample`: re-derive the crops, upload them, patch `graph.json` from `edit.json` and the record, submit, wait; a rejected graph leaves the request pending and names the discard; tests in `tests/test_edit.py` carry `edit_sample`.
  Verify: `uv run pytest tests/test_edit.py -k edit_sample` passes.
- [x] 4.3 Extend `isekai/shared/tattoo.py` and `sample` with the stitch and the lines ([D6](design.md#d6)): the crop scaled to its box, blended by the mask over the composite, multiplied by one minus `lines` of the darkness; the record completed first, the image written last; tests carry `edit_stitch`.
  Verify: `uv run pytest tests/test_edit.py -k edit_stitch` passes.
- [x] 4.4 Add the `--pending` form to the `edit` verb in `isekai/interface/cli.py`: `<run-id>/<flow>` cells, `--server`, `--progress json`; with no client it derives and checks each pending edit and rents nothing; tests carry `edit_pending`.
  Verify: `uv run pytest tests/test_edit.py -k edit_pending` passes.
- [x] 4.5 Add `per_edit_s` 30 to `config/render.json` and the edits to the estimate in `isekai/interface/render.py`: `Timing`, the recorded edit durations, `estimated`, `quote` ([D7](design.md#d7)); tests in `tests/test_render.py` carry `edit_limit`.
  Verify: `uv run pytest tests/test_render.py -k edit_limit` passes.
- [x] 4.6 Run the pending edits in the session of `isekai/interface/render.py` per [D7](design.md#d7): cells less each `--without`, checked free before the pod, run after the renders, a session of edits alone allowed, a request running none; its tests open `tests/test_edit_session.py`.
  Verify: `uv run pytest tests/test_edit_session.py` passes.
- [x] 4.7 Hold that the listings and the evaluator's runs skip an edit, and make `isekai/interface/run_view.py` read an edit's files in a group ([D8](design.md#d8)); tests in `tests/test_edit_session.py` carry `edit_listing`, and one in `tests/test_run_view.py` the unread list.
  Verify: `uv run pytest tests/test_edit_session.py -k edit_listing` passes.
- [x] 4.8 **HALT CHECK** A group holding an edit's file is no group of failure records alone, which is why a discard takes the edits first; a test in `tests/test_edit_session.py` carrying `edit_group` holds it.
  Verify: `uv run pytest tests/test_edit_session.py -k edit_group` passes.
- [x] 4.9 Make `discard_render` in `isekai/pipeline/generate.py` delete every edit of the seed before it tests the group, add the edit stage's discard to `isekai/pipeline/edit.py`, and let `_discard` in `isekai/interface/cli.py` take an edit's path ([D9](design.md#d9)); tests carry `edit_discard`.
  Verify: `uv run pytest tests/test_edit_session.py -k edit_discard` passes.
- [x] 4.10 Pay `0111·R6`: add `(image.parent / "7.render.json").is_file()` to the assert after the lock in the refusal test of `tests/test_pipeline_cli.py`, so the render's record stays beside its image and thumbnail.
  Verify: `git grep -nF '7.render.json").is_file()' tests/test_pipeline_cli.py` prints the assert's line.
- [x] 4.11 Hold the phase's tests under the acceptance's selector.
  Verify: `uv run pytest tests/test_edit_session.py -k "edit and (render or discard)"` passes.

## 5 — Model and image

- [x] 5.0 In `tools/derive_manifest.py` look up WAI's Civitai file (version 2883731) by its new name `WAI-Nsfw-Illustrious-17.safetensors`, keeping the dest `checkpoints/waiIllustriousSDXL_v170.safetensors`, and drop the `mogaru99/waiIllustriousSDXL_v170` mirror, which answers 401.
  Verify: `git grep -L mogaru99 tools/derive_manifest.py` prints the file's path.
- [x] 5.1 Read the promax revision with `curl -s https://huggingface.co/api/models/xinsir/controlnet-union-sdxl-1.0`, whose `sha` field is it; in `tools/derive_manifest.py` add after `OPENPOSE` a constant `PROMAX` holding that sha, and after the openpose `Spec` one for `controlnet/union-promax/diffusion_pytorch_model_promax.safetensors` with the source `Source("xinsir/controlnet-union-sdxl-1.0", PROMAX, "diffusion_pytorch_model_promax.safetensors")`.
  Verify: `git grep -n union-promax tools/derive_manifest.py` prints the spec's dest.
- [x] 5.2 Run `uv run python -m tools.derive_manifest`, which rewrites `config/models.json` with the entry `controlnet/union-promax/diffusion_pytorch_model_promax.safetensors`, its SHA-256 and its size.
  Verify: `git grep -n diffusion_pytorch_model_promax config/models.json` prints the entry's dest line.
- [x] 5.3 In `isekai/boundary/provision.py` add to `SELF_FETCHING_MODELS`, under the nodes that fetch nothing, the entries `"DifferentialDiffusion": ()`, `"LoadImageMask": ()`, `"SetLatentNoiseMask": ()` and `"SetUnionControlNetType": ()`, in the dict's sorted order.
  Verify: `git grep -n SetUnionControlNetType isekai/boundary/provision.py` prints its entry.
- [x] 5.4 In `tests/test_manifest_binding.py` add tests carrying `edit` in their names that load `edits/tattoo-wai/graph.json` with `json.loads` and assert `undeclared_files(graph_model_files(graph), manifest) == []` and `unclassified_node_classes(graph) == []`, marked `@pytest.mark.spec("edit:models:the-edits-files-are-declared")` and `@pytest.mark.spec("edit:models:a-class-absent-from-the-mapping-fails")`, the second also adding a node of an unknown class and asserting it is named.
  Verify: `uv run pytest tests/test_manifest_binding.py -k edit` passes.
- [x] 5.5 In `isekai/boundary/pod_start.py` delete from `shm_type`'s docstring the clause `the last line wins, as a later mount shadows an earlier one` (`0060·R5`), and end the sentence before it with `.` where it now ends with `;`, at `under the directory.`
  Verify: `git grep -L "the last line wins" isekai/boundary/pod_start.py` prints the file's path.
- [x] 5.6 In `isekai/boundary/pod_start.py` replace `os.statvfs(pod.shm)` with `os.statvfs(pod.memory)` in the memory check (`0060·R6`), and in `tests/test_pod_start.py` key the fake's `figures` on the memory directory's path, `pod.memory`, where it keys on `pod.shm`.
  Verify: `git grep -n "statvfs(pod.memory)" isekai/boundary/pod_start.py` prints the line.
- [x] 5.7 In `isekai/boundary/pod_start.py` replace the comment's `inside the ~$0.30 per-session ceiling.` with `inside the session's limit, its quote's.` (`op·pod-start-comment`).
  Verify: `git grep -L "0.30" isekai/boundary/pod_start.py` prints the file's path.
- [x] 5.8 Run `uv run python -m tools.image_record`, which prints the record, and copy each changed value into `files` of `config/image.json`.
  Verify: `uv run pytest tests/test_infra.py -k record` passes.
- [ ] 5.9 Push the branch with `git push origin 0119-the-tattoo-edit`, dispatch `gh workflow run build-image.yml --ref 0119-the-tattoo-edit -f tag=v0.79-rc1`, read the run's id with `gh run list --workflow build-image.yml --limit 1`, and wait with `gh run watch` on that id.
  Verify: `gh run list --workflow build-image.yml --limit 1` prints the run completed.
- [ ] 5.10 Check the run summary's build record equals `files` of `config/image.json`, then copy the tag `v0.79-rc1` and the digest into `config/image.json`, and the digest into `image` of `gpunit.toml`.
  Verify: `git grep -n v0.79-rc1 config/image.json` prints the tag line.
- [ ] 5.11 Hold the record and the digest equal to the tree, and the pod start's tests green on the edits.
  Verify: `uv run pytest tests/test_infra.py tests/test_pod_start.py -k "digest or record or pod_start"` passes.

## 6 — Proof on a pod ⚠️ GPU

- [ ] 6.1 Announce the session to the person: at most 20 minutes, at most $0.90 an hour, and the volume for the window. List the collections' runs roots with `ls -d .data/*/runs` and take one holding an approval short of one image.
  Verify: `ls -d .data/*/runs` prints the runs root taken.
- [ ] 6.2 On the person's go, run `uv run --env-file .env gpunit volume up --yes`, then `uv run python -m isekai render <that runs> --limit 1200`; read the collection's `log.txt` for `host key verified`, no `no CA store`, promax fetched and verified, and the render's image downloaded.
  Verify: `git grep -n "host key verified" CHANGELOG.md` prints the phase's bullet, which records the lines read.
- [ ] 6.3 Tear down: the session deletes the pod on its exit; confirm with the RunPod MCP that no gpunit-isekai pod is listed, and on the person's word run `uv run --env-file .env gpunit volume down`; write "no gpunit-isekai pod" and what the MCP returned in the phase's bullet.
  Verify: `git grep -n "no gpunit-isekai pod" CHANGELOG.md` prints the phase's bullet.

## 7 — Docs

- [ ] 7.1 Add D51 to `docs/decisions.md` after D50 per [D11](design.md#d11): an edit is one flat directory, `edit.json` and `graph.json`, pinned by its digest, named `<what>-<base>`, its image written beside its source.
  Verify: `git grep -n D51 docs/decisions.md` prints its heading.
- [ ] 7.2 Amend in `docs/decisions.md` D50 (a render's deletion takes its edits and their chain), D36 (a session renders and edits), D29 (a tattoo is added by an edit after the flow; the flows carry no ink) and D14 (an edit is not a flow), each by one sentence.
  Verify: `git grep -n "not a flow" docs/decisions.md` prints the D14 sentence.
- [ ] 7.3 In `docs/data-flow.md` scope the line *img2img is a closed avenue*: an edit encodes a render, never the photograph, so composition still comes from noise, and describe `ink`, `edit` and the session's edits where the verbs are.
  Verify: `git grep -n "encodes a render" docs/data-flow.md` prints the sentence.
- [ ] 7.4 Add `docs/edit-tattoo.md`, the Krita-first guide, `isekai ink` its first step, the composite, `isekai edit`, `isekai render`, the overrides and `isekai discard`, with no path of the operator's notebook, and link it from `README.md`.
  Verify: `git grep -n edit-tattoo.md README.md` prints the link.
- [ ] 7.5 Name the new files and edges in `docs/modules.md`, `isekai/shared/README.md`, `isekai/pipeline/README.md` and `isekai/boundary/README.md`: the shared maths, the edit stage, the transport helpers' new home.
  Verify: `git grep -n "prompt.py" isekai/boundary/README.md` prints the line.
