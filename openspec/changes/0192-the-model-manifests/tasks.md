# The model manifests — tasks

The model openers take their manifest's path, `unpack.main` takes its fetcher, and the row of `unpack` leaves the patch ratchet.

## Progress

- [ ] 1 — The openers · moderate
- [ ] 2 — The fetcher and the ratchet row · moderate
- [ ] 3 — The documents · moderate

## 1 — The openers

- [ ] 1.1 **HALT CHECK** the ratchet stands where the wiring's version left it, and the pose finder takes no manifest yet.
  Verify: `git grep -n -e "^PATCHED_ROWS = 18" -e "^def verified_paths(models_dir: Path = DEFAULT_MODELS_DIR)" -- tests/test_ratchets.py isekai/boundary/pose.py` prints a line for each pattern.
- [ ] 1.2 In `tests/test_wd14.py`, add `import json` and, after `_planted`, add `def _declared(models_dir: Path, manifest: Manifest) -> Path:`, which writes `json.dumps(manifest)` to `models_dir / "vocabulary.json"` and returns that path, per [D3](design.md#d3).
  Verify: `git grep -n -F "def _declared(models_dir: Path, manifest: Manifest) -> Path:" -- tests/test_wd14.py` prints one line.
- [ ] 1.3 In `tests/test_wd14.py`, in `test_the_model_is_verified_and_not_only_the_label_index`, `test_a_half_whose_bytes_do_not_match_its_digest_stops_the_stage` and `test_both_halves_present_and_matching_resolve_to_their_two_paths`, delete the patch of `"load_manifest"` and the `monkeypatch` parameter, and pass `manifest=_declared(tmp_path, manifest)` to `verified_paths`. The tripwire cases keep their patches. No assertion changes.
  Verify: `uv run pytest tests/test_wd14.py -k "verified_and_not_only or half_whose_bytes or both_halves_present"` exits 1, on the unexpected keyword.
- [ ] 1.4 In `tests/test_wd14_runtime.py`, import `_declared` beside `_planted`. In `test_a_graph_whose_bytes_differ_from_its_pin_is_never_opened` and `test_the_session_opens_the_verified_path_on_the_cpu`, delete the patch of `"load_manifest"` and pass `manifest=_declared(tmp_path, manifest)` to `open_session`. `monkeypatch` stays: `_stubbed` takes it. No assertion changes.
  Verify: `uv run pytest tests/test_wd14_runtime.py -k "never_opened or verified_path_on_the_cpu"` exits 1, on the unexpected keyword.
- [ ] 1.5 In `tests/test_vocabulary_manifest.py`, make `_declaring_none(tmp_path)` return the path of its copy and delete its `monkeypatch` parameter and the patch of `"VOCABULARY_MANIFEST_PATH"`. In `test_an_undeclared_artifact_is_refused`, type `load` as `Callable[..., object]`, delete the `monkeypatch` parameter, and call `load(tmp_path / "models", manifest=manifest)`. No assertion changes.
  Verify: `uv run pytest tests/test_vocabulary_manifest.py -k undeclared_artifact_is_refused` exits 1, on the unexpected keyword.
- [ ] 1.6 In `tests/test_pose.py`, make `_provisioned(tmp_path)` return `(models, manifest)`, annotated `tuple[Path, Path]`, and delete its `monkeypatch` parameter and the patch of `"PLACEMENT_MANIFEST_PATH"`. Each of its callers unpacks `models, manifest = _provisioned(tmp_path)`, passes `manifest=manifest` to `verified_paths` or `open_pose`, and drops a `monkeypatch` parameter nothing else reads. Drop `unpack` from the `isekai.boundary` import. No assertion changes.
  Verify: `uv run pytest tests/test_pose.py -k "pose_verified or pose_cpu"` exits 1, on the unexpected keyword.
- [ ] 1.7 In `tests/test_sam2.py`, make `_provisioned(tmp_path)` return `(models, manifest)` as in 1.6, and pass `manifest=manifest` to `open_segmenter` in its callers, each unpacking the pair and dropping a `monkeypatch` parameter nothing else reads. Drop `unpack` from the `isekai.boundary` import. No assertion changes.
  Verify: `uv run pytest tests/test_sam2.py -k sam_open` exits 1, on the unexpected keyword.
- [ ] 1.8 In `isekai/boundary/wd14.py`, give `verified_paths` and `open_session` the keyword `manifest: Path | None = None` after `*`, as [D1](design.md#d1) gives them. `verified_paths` reads `source = VOCABULARY_MANIFEST_PATH if manifest is None else manifest`, loads `declared = load_manifest(source)`, passes `declared` to `resolve` and `entry_for` and `source` to `undeclared`; `open_session` passes `manifest=manifest` on. Each docstring gains one sentence for the keyword.
  Verify: `git grep -n -F "manifest: Path | None = None" -- isekai/boundary/wd14.py` prints a line for each function.
- [ ] 1.9 In `isekai/interface/wiring.py`, give `load_vocabulary` the keyword `manifest: Path | None = None` after `*`, with the same `source` and `declared` as 1.8: `source` goes to `undeclared`, `declared` to `resolve` and `entry_for`.
  Verify: `git grep -n -F "manifest: Path | None = None" -- isekai/interface/wiring.py` prints one line.
- [ ] 1.10 In `isekai/boundary/pose.py`, import `PLACEMENT_MANIFEST_PATH` beside `PLACEMENT_REMEDY` and `provision` alone from `isekai.boundary`. Give `verified_paths` and `open_pose` the keyword `manifest: Path = PLACEMENT_MANIFEST_PATH` after `*`: `verified_paths` loads `declared = provision.load_manifest(manifest)` and passes it to `provision.resolve`; `open_pose` passes `manifest=manifest` on.
  Verify: `git grep -n -F "manifest: Path = PLACEMENT_MANIFEST_PATH" -- isekai/boundary/pose.py` prints a line for each function.
- [ ] 1.11 In `isekai/boundary/sam2.py`, import `PLACEMENT_MANIFEST_PATH` beside `PLACEMENT_REMEDY` and give `open_segmenter` the keyword `manifest: Path = PLACEMENT_MANIFEST_PATH` after `*`. It loads `declared = provision.load_manifest(manifest)` and passes it to `unpack.resolve_member`.
  Verify: `git grep -n -F "manifest: Path = PLACEMENT_MANIFEST_PATH" -- isekai/boundary/sam2.py` prints one line.
- [ ] 1.12 No file of the package reads `unpack.PLACEMENT_MANIFEST_PATH` through the module any more.
  Verify: `git grep -n -F "unpack.PLACEMENT_MANIFEST_PATH" -- isekai` prints nothing.
- [ ] 1.13 In `tests/mutants.json`, re-point `BD-1` and `BD-10b` per [D6](design.md#d6): `BD-1`'s find and replace read `resolve(dest, models_dir, declared)` and `entry_for(declared, dest)` where they read `manifest`, and `BD-10b`'s find and replace read `verified_paths(models_dir, manifest=manifest)`.
  Verify: `git grep -n -F -e "resolve(dest, models_dir, declared)" -e "verified_paths(models_dir, manifest=manifest)" -- tests/mutants.json` prints a line for the find and the replace of each.
- [ ] 1.14 Run the cases of every file the phase touched, and the structure tests.
  Verify: `uv run pytest tests/test_wd14.py tests/test_wd14_runtime.py tests/test_vocabulary_manifest.py tests/test_pose.py tests/test_sam2.py tests/test_propose.py tests/test_ui_propose.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_spec_bindings.py` exits 0.
- [ ] 1.15 Lint what the phase changed.
  Verify: `uv run ruff check isekai/boundary isekai/interface/wiring.py tests/test_wd14.py tests/test_wd14_runtime.py tests/test_vocabulary_manifest.py tests/test_pose.py tests/test_sam2.py` exits 0.
- [ ] 1.16 Replay the standing mutants over the edited files; `BD-1` and `BD-10b` find their lines.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.

## 2 — The fetcher and the ratchet row

- [ ] 2.1 **HALT CHECK** `unpack.main` takes no fetcher yet, and the ratchet still lists the row.
  Verify: `git grep -n -e "^def main(argv: list\[str\]) -> int:" -e "^    .isekai\.boundary\.unpack.: [0-9]" -- isekai/boundary/unpack.py tests/test_ratchets.py` prints a line for each pattern.
- [ ] 2.2 In `tests/test_provision_unpack.py`, in `test_unpack_cli_fetches_the_manifest_it_names_into_the_models_dir`, delete the patch of `"HuggingFaceFetcher"` and the `monkeypatch` parameter, and pass its lambda to `unpack.main` as `fetcher=`. Its `spec_exempt` text reads `structural: the command line is fetch over the fetcher it is given and a named manifest`. No assertion changes.
  Verify: `uv run pytest tests/test_provision_unpack.py -k fetches_the_manifest_it_names` exits 1, on the unexpected keyword.
- [ ] 2.3 In `tests/test_provision_unpack.py`, add `import inspect` and, after that case, add `test_unpack_cli_defaults_to_the_hugging_face_fetcher` marked `@pytest.mark.spec_exempt("structural: the command line fetches over Hugging Face unless a test gives its own")`, per [D7](design.md#d7). It asserts the default of `fetcher` in `inspect.signature(unpack.main).parameters` is `unpack.HuggingFaceFetcher`.
  Verify: `uv run pytest tests/test_provision_unpack.py -k defaults_to_the_hugging_face` exits 1, on the missing parameter.
- [ ] 2.4 In `isekai/boundary/unpack.py`, give `main` the keyword `fetcher: Callable[[], Fetcher] = HuggingFaceFetcher` after `*`, as [D2](design.md#d2) gives it, and call `fetcher()` in place of `HuggingFaceFetcher()`.
  Verify: `git grep -n -F "fetcher: Callable[[], Fetcher] = HuggingFaceFetcher" -- isekai/boundary/unpack.py` prints one line.
- [ ] 2.5 No test patches a name of `unpack` any more: no line holds `unpack, "`.
  Verify: `git grep -n -F 'unpack, "' -- tests` prints nothing.
- [ ] 2.6 In `tests/test_ratchets.py`, delete the row `"isekai.boundary.unpack": 3,` from `PATCHED_MODULES`, per [D4](design.md#d4).
  Verify: `git grep -n -e "^    .isekai\.boundary\.unpack.: [0-9]" -- tests/test_ratchets.py` prints nothing.
- [ ] 2.7 In `tests/test_ratchets.py`, set `PATCHED_ROWS = 17`.
  Verify: `git grep -n -e "^PATCHED_ROWS = 17" -- tests/test_ratchets.py` prints one line.
- [ ] 2.8 Run the cases of every file the phase touched, and the structure tests.
  Verify: `uv run pytest tests/test_provision_unpack.py tests/test_provision.py tests/test_vocabulary_manifest.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_spec_bindings.py` exits 0.
- [ ] 2.9 Lint what the phase changed.
  Verify: `uv run ruff check isekai/boundary/unpack.py tests/test_provision_unpack.py tests/test_ratchets.py` exits 0.

## 3 — The documents

- [ ] 3.1 In `docs/principles.md`, replace the *Known breaks* bullet under *A component is a contract*, which holds `so is every name of a module`, with the bullet [D5](design.md#d5) gives, word for word.
  Verify: `git grep -n -F "so is every name of a module" -- docs/principles.md` prints nothing.
- [ ] 3.2 Each module `PATCHED_MODULES` still lists is named in that bullet, which says each `stays for` one reason, as [D5](design.md#d5) names them.
  Verify: `git grep -o -F -e "stays for" -e "boundary/ollama.py" -e "boundary/provision.py" -e "boundary/wd14.py" -e "evaluation/face.py" -e "foundation/run.py" -e "interface/cli.py" -e "interface/render.py" -e "interface/ui/__init__.py" -e "interface/ui/events.py" -e "interface/ui/library.py" -e "pipeline/edit.py" -e "pipeline/generate.py" -e "pipeline/importing.py" -e "pipeline/review.py" -e "pipeline/tattoos.py" -e "shared/chain.py" -e "shared/ink.py" -- docs/principles.md` prints each path.
- [ ] 3.3 Run the documents' tests.
  Verify: `uv run pytest tests/test_principles.py tests/test_docs.py tests/test_ratchets.py` exits 0.
