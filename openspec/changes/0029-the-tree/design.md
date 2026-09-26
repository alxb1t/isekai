# Design — 0029 the tree

How `scripts/`, the evaluator, `probe/` and the licence record reach their new places without changing what a
run does. **Verdict: `feasible`.** Every file, symbol and line below was re-checked at `main` `c6d18a4`.

## Context

- **The project is not installed.** `uv.lock` records `isekai` as `source = { virtual = "." }`, with no build
  backend. `isekai` imports only from the repository root: the working directory, or pytest's
  `pythonpath = [".", "scripts"]` (`pyproject.toml:207`). A script run as `python evaluation/x.py` puts
  `evaluation/` on `sys.path` and loses `isekai`; `python -m …` from the root keeps it.
- **The derivers find `manifest.py` because it sits beside them** (`scripts/derive_manifest.py`,
  `derive_vocabulary.py`, `derive_eval_manifest.py`: `from manifest import …`). Pytest and `ty` see `scripts/`
  through `pythonpath` and `[tool.ty.environment] extra-paths = ["scripts"]` (`pyproject.toml:204`).
  `scripts/derive_field_map.py:58` and `scripts/derive_eval_manifest.py:46` insert the repository root on
  `sys.path`.
- **Anchors into `scripts/`:** `provision.MANIFEST_PATH` and `VOCABULARY_MANIFEST_PATH`
  (`isekai/boundary/provision.py:26-37`), `field_map.FIELD_MAP_PATH` (`isekai/shared/field_map.py:55-57`),
  `eval_models.EVAL_MANIFEST_PATH` (`isekai/evaluation/eval_models.py:29-31`), and each deriver's sibling
  `MANIFEST_PATH` (`derive_manifest.py:47`, `derive_vocabulary.py:53`, `derive_eval_manifest.py:50-51`).
  `tests/test_package_paths.py:44-58` pins the provision and evaluation anchors; `tests/test_field_map.py:103` pins the directory name.
- **`field_map.json` records its own path**: `"name": "scripts/field_map.json"`, a literal at
  `scripts/derive_field_map.py:633`. Every sheet records that name with the file's digest.
- **The image** copies `scripts/download_models.sh` and `scripts/models.json` into `/opt/isekai/scripts/`
  (`Dockerfile:78-81`); `start.sh:121` calls the copy; `provision.py`, copied to
  `/opt/isekai/isekai/boundary/`, finds its manifest by its own anchor. Every merge to `main` rebuilds
  `:latest`, which `infra/up.sh` boots.
- **Printed commands naming `scripts/`:** `VOCABULARY_REMEDY` (`isekai/shared/vocabulary.py:37`),
  `FIELD_MAP_REMEDY` (`isekai/shared/field_map.py:61`), `READER_REMEDY` (`isekai/pipeline/caption.py:93`),
  `TAGGER_REMEDY` (`isekai/pipeline/tagging.py:102`), and `derive_field_map.py --help`.
- **The evaluator:** `isekai/evaluation/` (`evaluate.py`, `eval_backends.py`, `ciede2000.py`,
  `eval_models.py`, `labels.py`), the root `evaluate.py` (its CLI), `baseline/` (code, data and records; no
  images). The root `evaluate.py` and `isekai/evaluation/evaluate.py` would collide at
  `evaluation/evaluate.py`. `labels.GitOrdering._first_commit_time` (`isekai/evaluation/labels.py:104-118`)
  runs `git log --diff-filter=A` without `--follow`.
- **`tests/test_layers.py:23`'s scope list** — `("isekai", "probe", "scripts", "evaluate.py")` — **skips a
  missing path silently** (`_sources`, `:44-50`); its evaluation rule is keyed on `isekai.evaluation`
  (`:101-108`), and `_imports` (`:69`) keeps only `isekai` imports.
- **`probe/`** has one live user, its own `tests/test_probe.py`. Its measurement — `LoadImage` transposes a PNG
  carrying an `eXIf` Orientation — is recorded in `openspec/changes/archive/0011-converge-paydown/design.md`.
- **The licence record** `scripts/eval_licences.md` is read by `tests/test_vocabulary_manifest.py:189-213`,
  bound to `model-provisioning:licences:vocabulary-terms-are-recorded`; `CLAUDE.md:155-156` states its rule.
- **Line numbers are `c6d18a4`'s.** A builder re-resolves each by the text it names.

## Goals / Non-Goals

**Goals**

- Every file in `scripts/` lives in `config/`, `tools/` or `evaluation/`, and `scripts/` is gone.
- The evaluator is a top-level `evaluation/` that imports `isekai`, and `isekai` never imports it.
- Every tool runs one way: as a module from the repository root.
- The image's layout is the repository's, held by a test.

**Non-Goals**

- Any change to what a run writes, beyond `field_map.json`'s recorded name ([D4](#d4)).
- Any evaluator behaviour but [D7](#d7).
- A metered boot.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | tools and the evaluator run as modules from the root, with absolute imports | the project is virtual; only `-m` from the root keeps `isekai` importable | keeping the `sys.path` hops |
| [D2](#d2) | the root `evaluate.py` becomes `evaluation/__main__.py` | the root `evaluate.py` and the rules module collide | renaming the rules module |
| [D3](#d3) | the printed commands name the new paths and shapes | a remedy must be a command this build has | leaving `scripts/` in a remedy |
| [D4](#d4) | `field_map.json` records `config/field_map.json` | a record names where the file is | keeping a path that no longer exists |
| [D5](#d5) | the image mirrors the repository, held by static tests | a merge rebuilds `:latest`, and no boot can prove it | a bespoke image layout |
| [D6](#d6) | `make derive` runs the derivers in dependency order | one command re-derives every derived file | a target per deriver |
| [D7](#d7) | `GitOrdering` follows a renamed file | the move would falsify the labels' evidence | moving the labels unguarded |
| [D8](#d8) | the tests that assume the old tree are rewritten; a missing scope path fails | a stale scope list narrows a check with no failure | editing only the paths |
| [D9](#d9) | `probe/` is deleted | no live code uses it; its result is recorded | moving it into the archive |
| [D10](#d10) | the licence record is deleted, and its requirement removed | licences are out of scope for now | keeping a record nothing maintains |
| [D11](#d11) | the backlog rows this move reaches are paid | each is one line in a file this change edits | leaving them for the backlog patch |
| [D12](#d12) | the docs follow the tree | a doc naming `scripts/` is false the moment it goes | a docs sweep in a later change |
| [D13](#d13) | phases: guards, `config/`, `tools/`, `evaluation/`, removals, docs | each directory moves once, under guards that hold every move | one phase |
| [D14](#d14) | a patch | it meets every condition `CLAUDE.md` states | a minor |

### D1

**Tools and the evaluator run as modules from the repository root.**

- `tools/` and `evaluation/` are packages: `tools/__init__.py` and `evaluation/baseline/__init__.py` hold a
  docstring; `evaluation/__init__.py` is `isekai/evaluation/__init__.py`, moved.
- Imports are absolute: `from tools.manifest import …`, `from evaluation.evaluate import …`. The `sys.path`
  inserts at `derive_field_map.py:58` and `derive_eval_manifest.py:46` go.
- `pyproject.toml`: `pythonpath = ["."]`; `extra-paths = ["scripts"]` goes; `known-first-party` becomes
  `["isekai", "tools", "evaluation"]`.
- **Shell scripts stay shell scripts**: `bash tools/download_models.sh`, `bash tools/typecheck_ui.sh`. Both
  find the root from their own directory (`download_models.sh:25-26`, `typecheck_ui.sh:19`), at the same
  depth as today.

### D2

**`evaluate.py` becomes `evaluation/__main__.py`**, run as `uv run --extra eval python -m evaluation <run>/
--photo <photo>`. The rules keep `evaluation/evaluate.py`. `evaluation/baseline/`'s tools run as
`uv run --extra eval python -m evaluation.baseline.build_subjects` and `…build_contact_sheets`.

### D3

**The printed commands:**

| constant | before | after |
|---|---|---|
| `VOCABULARY_REMEDY` | `bash scripts/download_models.sh scripts/vocabulary.json` | `bash tools/download_models.sh config/vocabulary.json` |
| `FIELD_MAP_REMEDY` | `uv run python scripts/derive_field_map.py` | `uv run python -m tools.derive_field_map` |
| `READER_REMEDY`, `TAGGER_REMEDY` | `ollama create {model} -f scripts/joycaption.Modelfile` | `ollama create {model} -f config/joycaption.Modelfile` |

Each is asserted by a test that follows it: `tests/test_caption.py:462`, `tests/test_vocabulary_manifest.py:282`,
`:294`, `tests/test_resume.py:356`. `derive_field_map.py`'s docstring, which `--help` prints, and each deriver's
usage line name the module form.

### D4

**`field_map.json`'s recorded name becomes `config/field_map.json`.** The literal at
`scripts/derive_field_map.py:633` changes and the table is re-derived, so the file's bytes and the digest new
sheets record change; its `revision` (`3`) and every field do not. `tests/test_field_map.py:63`, `:130`, `:134`
use the name as fixture data and follow it.

### D5

**The image mirrors the repository's layout.**

- `Dockerfile:78-81`: `config/models.json` → `/opt/isekai/config/models.json`, `tools/download_models.sh` →
  `/opt/isekai/tools/download_models.sh`. `start.sh:121` calls `/opt/isekai/tools/download_models.sh`.
  `provision.py`'s anchor then resolves inside the image with no change of its own.
- **Three static tests in `tests/test_infra.py`**, each with a twin over a broken `Dockerfile` text:
  `test_every_file_the_image_copies_exists`,
  `test_the_entrypoint_runs_the_provisioner_the_image_copies` (the path `start.sh` calls is a COPY destination),
  `test_the_manifest_the_provisioner_reads_is_copied_where_it_looks` (`/opt/isekai/` plus
  `provision.MANIFEST_PATH` relative to the repository is a COPY destination). `spec_exempt`.
- **`docker build --check .`** runs in the phase that edits the `Dockerfile`, as `CLAUDE.md` asks of
  image-as-code phases.

### D6

**`make derive`**, beside `gate` in the `Makefile`, runs in this order and stops at the first failure:

```
uv run python -m tools.derive_manifest        # network — writes config/models.json
uv run python -m tools.derive_eval_manifest   # network — reads config/models.json
uv run python -m tools.derive_vocabulary      # network — writes config/vocabulary.json
uv run python -m tools.derive_field_map       # needs the provisioned vocabulary
git diff --stat -- config/ evaluation/eval_models.json
```

`make` names the failing command. It is not part of the gate.

### D7

**`GitOrdering._first_commit_time` runs `git log --follow --diff-filter=A`.** A test in `tests/test_labels.py`
commits a file, moves it with `git mv` in a later commit, and asserts the first-added time is the first
commit's. The requirement *Human labels are collected blind and pairwise* already demands it: the labels must
be shown recorded before the scores.

### D8

**The tests that assume the old tree are rewritten.**

- `tests/test_layers.py`: `FRONT_DOOR_SCOPE` names the tree as it stands in each phase, ending at
  `("isekai", "tools", "evaluation")`; **`_sources` fails on a path that does not exist**; the evaluation rule is
  keyed on the top-level `evaluation`, and `_imports` keeps it; the cycle check covers `evaluation/`. Each
  change keeps its twin.
- `tests/test_package_paths.py`: the anchors re-pin to `("config", …)` and `("evaluation", "eval_models.json")`,
  and the twin no longer assumes every anchor sits under `isekai/`.
- `tests/test_field_map.py:103` pins `config`.
- Tests that read a moved file by path follow it: `tests/test_eval_manifest.py:188`, `tests/test_flow.py:142`,
  `tests/test_sheet_schema.py:151`, `tests/test_infra.py:149`, `tests/test_vocabulary_manifest.py:55`.
- Tests that import a moved module follow it: `tests/test_derivation.py:14-19`, `tests/test_manifest.py:9`,
  `tests/test_field_map.py` (`derive_field_map`), `tests/eval_fakes.py:14-15`, `tests/test_ciede2000.py:3`,
  `tests/test_eval_manifest.py:22`, `tests/test_evaluate.py:6`, `:683-685`, `tests/test_labels.py:9`,
  `tests/test_package_paths.py:31`, `tests/test_vocabulary_manifest.py:33`.

### D9

**`probe/` is deleted** with `tests/test_probe.py`.

- `isekai/evaluation/eval_backends.py:121`'s citation of `probe/README.md` re-points to
  `openspec/changes/archive/0011-converge-paydown/design.md`.
- `isekai/boundary/README.md:31` loses `probe/loader_probe.py`; `tests/test_layers.py`'s front-door twin
  (`:320-325`) builds its breaking module under `tools/` instead.
- `tests/images.py`'s `exif_tiff` and `png_chunk`, public for the probe (`:138`), become private: nothing else
  imports them.

### D10

**The licence record is deleted, and its requirement removed** ([specs/](specs/model-provisioning/spec.md)).

- `scripts/eval_licences.md`; `tests/test_vocabulary_manifest.py`'s licence tests (`:189-213`), `LICENCES_PATH`
  (`:50`) and `_section_naming`; `CLAUDE.md:155-156`.
- The comments that point at it: `isekai/evaluation/eval_backends.py:12`, `:180`.
- **The AGPL guards stay**: `tests/test_evaluate.py:650-690` keep `ultralytics` out of the dependencies, the
  lockfile and the scorer's imports.

### D11

**The backlog rows this move reaches:**

- **`v0.22.2 review/R12`** — `manifest.py:31`'s orphan line is re-flowed as the file moves.
- **`v0.22.5 review/R3`** — the cycle check covers `evaluation/`, and `isekai/README.md:33-38` stops promising
  "the subpackage cycles and why each one exists".
- **`v0.22.5 review/R5`** — the evaluation preamble's *Source* names `isekai/boundary/provision.py`.
- Two claims found false on the way: `pyproject.toml:54` (*"The eval tests skip there"* — none skips) and
  `baseline/README.md:196` (`isekai/evaluate.py`, a path that never existed).

### D12

**The docs follow the tree:** `README.md` (the commands at `:98`, `:272`, `:278`, `:298`; the layout at
`:311-348`; `:385`), `docs/data-flow.md:131`, `docs/decisions.md:52`, `:97`, `docs/modules.md`'s evaluation
lines, the group READMEs that name a moved file, `isekai/README.md`'s evaluation row and anchor list, the
evaluation README's relative links, the spec preambles of `evaluation`, `field-map`, `model-provisioning` and
`tagging`, and `.github/workflows/ci.yml:22`. `openspec/specs/image-generation/spec.md:424` stays: it says
where a file went at v0.19, which is history.

### D13

**Phases**, each green alone:

```
1 guards      _sources fails on a missing path · the image tests (D5), against today's layout
2 config/     models, vocabulary, field map, Modelfile · anchors · field_map.json's name · Dockerfile, the manifest copy ·
              the Modelfile remedies
3 tools/      the derivers + manifest.py as modules · download_models.sh, typecheck_ui.sh ·
              Makefile, make derive · start.sh, Dockerfile · pyproject · the remaining remedies · R12
4 evaluation/ isekai/evaluation/, evaluate.py, baseline/, eval_models.json · pyproject · --follow ·
              the layer test's evaluation rules and cycle check (R3)
5 removals    the licence record · probe/
6 docs        D12 · R5 · the false claims · scripts/ gone
```

### D14

**This is a patch.**

| condition | met because |
|---|---|
| no format version moves | no run file's kind or version changes; `MANIFEST_VERSION` is untouched |
| a behaviour fix is required by an existing requirement | `--follow` is required by *Human labels are collected blind and pairwise* |
| nothing deprecates a verb or a flag | no `isekai` verb or flag changes; the tools' invocation is not a verb of `python -m isekai` |
| nothing changes the product | a sheet's fields, the prompt and the image are unchanged; a new sheet's field-map *record* names the new path |

**The requirement leaves as a `REMOVED` delta**, the first removal in a patch: the patch conditions forbid
adding a requirement, not removing one.

## Dependencies

None.

## Risks / Trade-offs

- **The rebuilt `:latest` is never booted before a pod uses it.** → The static tests and `docker build
  --check` hold the paths; the operator's backlog tracks the first boot as its live proof.
- **A fresh `git log --follow` can mis-follow a file whose content was rewritten in the move.** → The move is
  `git mv` with no content change.
- **The printed commands change shape, not just directory.** → Each is asserted by a test, and every one names
  a command this build has.
- **A scope list silently narrowed a check once.** → [D8](#d8) makes a missing path fail.

## Verdict

**`feasible`.** A reorganisation under guards: the image and the layer tests fail on a stale path, every
printed command is asserted, and the one behaviour fix is one flag its requirement demands.
