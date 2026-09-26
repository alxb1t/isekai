# Tasks — 0029 the tree

Guards first, then each directory moves once — `config/`, `tools/`, `evaluation/` — then the removals and the
docs ([D13](design.md#d13)).

## Progress

- [x] 1 — Guards: a missing scope path fails, and the image's layout is tested
- [x] 2 — `config/`: the files the pipeline reads
- [ ] 3 — `tools/`: the derivers and the operator's scripts, run as modules
- [ ] 4 — `evaluation/`: the sub-system leaves the package
- [ ] 5 — Removals: the licence record and `probe/`
- [ ] 6 — The docs follow the tree

Line numbers are `c6d18a4`'s; find each site by the text it names.

## 1 — Guards: a missing scope path fails, and the image's layout is tested

- [x] 1.1 **HALT CHECK** — `scripts/` holds the files [D13](design.md#d13) distributes, and no others.
  Verify: `git ls-files scripts | sed 's#scripts/##' | tr '\n' ' '` prints `derive_eval_manifest.py derive_field_map.py derive_manifest.py derive_vocabulary.py download_models.sh eval_licences.md eval_models.json field_map.json joycaption.Modelfile manifest.py models.json typecheck_ui.sh vocabulary.json `.
- [x] 1.2 Make `tests/test_layers.py`'s `_sources` fail on a scope path that does not exist, with the twin `test_a_scope_path_that_does_not_exist_fails`, per [D8](design.md#d8).
  Verify: `grep -c '^def test_a_scope_path_that_does_not_exist_fails(' tests/test_layers.py` prints `1`.
- [x] 1.3 Add [D5](design.md#d5)'s image tests, each with a twin over a broken `Dockerfile` text, to `tests/test_infra.py`, against today's layout.
  Verify: `grep -c -e '^def test_every_file_the_image_copies_exists(' -e '^def test_the_entrypoint_runs_the_provisioner_the_image_copies(' -e '^def test_the_manifest_the_provisioner_reads_is_copied_where_it_looks(' tests/test_infra.py` prints `3`.

## 2 — `config/`: the files the pipeline reads

- [x] 2.1 `git mv` `scripts/models.json`, `scripts/vocabulary.json`, `scripts/field_map.json` and `scripts/joycaption.Modelfile` into `config/`.
  Verify: `ls config | tr '\n' ' '` prints `field_map.json joycaption.Modelfile models.json vocabulary.json `.
- [x] 2.2 Re-anchor `provision.MANIFEST_PATH`, `VOCABULARY_MANIFEST_PATH`, `field_map.FIELD_MAP_PATH` and the derivers' manifest paths to `config/`, and re-pin `tests/test_package_paths.py`, per [D8](design.md#d8).
  Verify: `git grep -n -e '"scripts" / "models.json"' -e '"scripts" / "vocabulary.json"' -e '"scripts" / "field_map.json"' -e '("scripts", "models.json")' -e '("scripts", "vocabulary.json")' -e 'parent / "models.json"' -e 'parent / "vocabulary.json"' -- isekai scripts tests` prints nothing.
- [x] 2.3 Record `config/field_map.json` as the table's name and re-derive it; follow it in `tests/test_field_map.py:63`, `:103`, `:130`, `:134`, per [D4](design.md#d4).
  Verify: `grep -c '"name": "config/field_map.json"' config/field_map.json scripts/derive_field_map.py | paste -sd' ' -` prints `config/field_map.json:1 scripts/derive_field_map.py:1`.
- [x] 2.4 Copy `config/models.json` to `/opt/isekai/config/models.json` in the `Dockerfile`, and run `docker build --check .`, per [D5](design.md#d5).
  Verify: `grep -c 'COPY config/models.json /opt/isekai/config/models.json' Dockerfile` prints `1`.
- [x] 2.5 Point every remaining path to a moved file at `config/` — the Modelfile remedies, `VOCABULARY_REMEDY`'s manifest argument, the tests [D3](design.md#d3) and [D8](design.md#d8) name, and the comments.
  Verify: `git grep -n -e 'scripts/joycaption' -e 'scripts/vocabulary.json' -e 'scripts/models.json' -e 'scripts/field_map.json' -- isekai tests scripts Dockerfile start.sh` prints nothing.

## 3 — `tools/`: the derivers and the operator's scripts, run as modules

- [ ] 3.1 `git mv` the derivers, `manifest.py`, `download_models.sh` and `typecheck_ui.sh` from `scripts/` into `tools/`, and add `tools/__init__.py`, per [D1](design.md#d1).
  Verify: `ls tools | grep -v __pycache__ | tr '\n' ' '` prints `__init__.py derive_eval_manifest.py derive_field_map.py derive_manifest.py derive_vocabulary.py download_models.sh manifest.py typecheck_ui.sh `.
- [ ] 3.2 Make every import in `tools/` absolute, delete the `sys.path` inserts, and re-flow `manifest.py:31` (`v0.22.2 review/R12`), per [D1](design.md#d1), [D11](design.md#d11).
  Verify: `grep -l -e '^from manifest import' -e 'sys.path.insert' tools/*.py` prints nothing.
- [ ] 3.3 Set `pyproject.toml`'s `pythonpath`, `extra-paths` and `known-first-party` per [D1](design.md#d1), and follow the moved modules in the tests [D8](design.md#d8) names.
  Verify: `grep -c '"scripts"' pyproject.toml tests/test_layers.py | paste -sd' ' -` prints `pyproject.toml:0 tests/test_layers.py:0`.
- [ ] 3.4 Run the browser typecheck from `tools/` in the `Makefile`, and add [D6](design.md#d6)'s `derive` target; follow the path in `.github/workflows/ci.yml:22`.
  Verify: `make -n gate | grep -c 'bash tools/typecheck_ui.sh'` prints `1`, and `make -n derive | grep -c 'python -m tools.derive_'` prints `4`.
- [ ] 3.5 Copy `tools/download_models.sh` to `/opt/isekai/tools/` in the `Dockerfile`, call it there from `start.sh:121`, and run `docker build --check .`, per [D5](design.md#d5).
  Verify: `grep -c '/opt/isekai/scripts' Dockerfile start.sh | paste -sd' ' -` prints `Dockerfile:0 start.sh:0`.
- [ ] 3.6 Give `VOCABULARY_REMEDY` and `FIELD_MAP_REMEDY` [D3](design.md#d3)'s commands, with every deriver's usage line and the tests that assert them.
  Verify: `git grep -n -e 'scripts/download_models' -e 'scripts/derive_' -e 'scripts/manifest' -e 'scripts/typecheck' -- isekai tests tools Dockerfile start.sh Makefile .github` prints nothing.

## 4 — `evaluation/`: the sub-system leaves the package

- [ ] 4.1 `git mv` `isekai/evaluation/` to `evaluation/`, `evaluate.py` to `evaluation/__main__.py`, `baseline/` to `evaluation/baseline/`, and `scripts/eval_models.json` to `evaluation/`; add `evaluation/baseline/__init__.py`. [D1](design.md#d1), [D2](design.md#d2).
  Verify: `test ! -e isekai/evaluation/evaluate.py && test ! -e evaluate.py && test ! -e baseline/README.md && test -f evaluation/__main__.py && test -f evaluation/eval_models.json && test -f evaluation/baseline/__init__.py && echo ok` prints `ok`.
- [ ] 4.2 Import `evaluation` where `isekai.evaluation` stood — in `evaluation/`, `tools/derive_eval_manifest.py`, `isekai/foundation/refusal.py`'s docstring and the tests [D8](design.md#d8) names; `EVAL_MANIFEST_PATH` becomes a sibling path.
  Verify: `git grep -n 'isekai.evaluation' -- '*.py'` prints nothing.
- [ ] 4.3 Point `pyproject.toml`'s ruff per-file ignore, `ty` override and comments at `evaluation/`, and add `evaluation` to `known-first-party`.
  Verify: `grep -c 'isekai/evaluation' pyproject.toml` prints `0`.
- [ ] 4.4 Add `--follow` to `GitOrdering._first_commit_time`, with `test_a_moved_file_keeps_its_first_added_time` in `tests/test_labels.py`, per [D7](design.md#d7).
  Verify: `grep -c -e '"--follow"' evaluation/labels.py` prints `1`, and `grep -c '^def test_a_moved_file_keeps_its_first_added_time(' tests/test_labels.py` prints `1`.
- [ ] 4.5 Key `tests/test_layers.py`'s evaluation rule on the top-level `evaluation`, keep it in `_imports`, extend the cycle check to `evaluation/`, and set the scope to `("isekai", "probe", "tools", "evaluation")`, per [D8](design.md#d8).
  Verify: `grep -c '"isekai.evaluation"' tests/test_layers.py` prints `0`, and `grep -c 'FRONT_DOOR_SCOPE = ("isekai", "probe", "tools", "evaluation")' tests/test_layers.py` prints `1`.

## 5 — Removals: the licence record and `probe/`

- [ ] 5.1 Delete `scripts/eval_licences.md`, the licence tests, `LICENCES_PATH` and `_section_naming` in `tests/test_vocabulary_manifest.py`, `CLAUDE.md:155-156`, and the comments naming it, per [D10](design.md#d10).
  Verify: `git ls-files scripts | wc -l | tr -d ' '` prints `0`, and `git grep -n -e eval_licences -e LICENCES_PATH -- ':!CHANGELOG.md' ':!openspec'` prints nothing.
- [ ] 5.2 Delete `probe/` and `tests/test_probe.py`; re-point `evaluation/eval_backends.py`'s citation, `isekai/boundary/README.md:31`, the layer scope and its front-door twin, and `tests/images.py`'s helpers, per [D9](design.md#d9).
  Verify: `git ls-files probe tests/test_probe.py | wc -l | tr -d ' '` prints `0`, and `git grep -n 'probe/' -- isekai evaluation/eval_backends.py tests tools` prints nothing.

## 6 — The docs follow the tree

- [ ] 6.1 Rewrite `README.md`'s commands and layout per [D12](design.md#d12).
  Verify: `grep -c -e 'scripts/' -e 'python evaluate.py' README.md` prints `0`.
- [ ] 6.2 Follow the tree in `docs/data-flow.md`, `docs/decisions.md`, `docs/modules.md`, `isekai/README.md` (with `v0.22.5 review/R3`'s promise), the group READMEs and `evaluation/README.md`'s links, per [D11](design.md#d11), [D12](design.md#d12).
  Verify: `git grep -n -e 'scripts/' -e 'isekai/evaluation' -e '\.\./\.\./evaluate\.py' -- docs isekai/README.md 'isekai/*/README.md' evaluation/README.md` prints nothing.
- [ ] 6.3 Edit the preambles of `evaluation`, `field-map`, `model-provisioning` and `tagging` under `openspec/specs/`; the evaluation *Source* names `isekai/boundary/provision.py` (`v0.22.5 review/R5`).
  Verify: `grep -c -e 'scripts/' -e 'isekai/evaluation' openspec/specs/evaluation/spec.md openspec/specs/field-map/spec.md openspec/specs/model-provisioning/spec.md openspec/specs/tagging/spec.md | paste -sd' ' -` prints `openspec/specs/evaluation/spec.md:0 openspec/specs/field-map/spec.md:0 openspec/specs/model-provisioning/spec.md:0 openspec/specs/tagging/spec.md:0`.
- [ ] 6.4 Correct `pyproject.toml:54` and `evaluation/baseline/README.md:196`, and give `evaluation/baseline/`'s usage lines and `.gitignore:19` the new paths, per [D11](design.md#d11).
  Verify: `grep -c 'The eval tests skip there' pyproject.toml` prints `0`, and `grep -c 'isekai/evaluate.py' evaluation/baseline/README.md` prints `0`.
- [ ] 6.5 No live file names `scripts/` but the history [D12](design.md#d12) keeps.
  Verify: `git grep -n 'scripts/' -- ':!CHANGELOG.md' ':!openspec/changes' ':!openspec/specs/image-generation/spec.md' ':!isekai/foundation/run.py'` prints nothing.
