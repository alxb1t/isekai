# Design — 0053 the evaluation mechanism

How a cohort on disk becomes two counts: the ground truth, the ranking, the encoder, the record, the entry point,
the pins and the deletion. **Verdict: feasible-with-caveats** — every piece is small and held by a test; the two
caveats are the detector on anime faces, probed on renders already on disk, and the deletion's edit to this
change's own delta, which the binding checker forces.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`20ef5a7`):

- **The entry point:** `evaluation/__main__.py:85-105` wants `photo_sha256`, `base` and `renders` from `run.json`
  (`:111`); `sys.exit` inside the render loop (`:181`); the records written after it (`:185-190`).
- **A current run:** the frame writes `schema`, `id` and `photo.sha256` (`isekai/foundation/run.py:376-386`; `Run`
  `:231`, `frame` `:251`, `open_run` `:346`). Renders are `<flow>/outputs/<NNN>/<seed>.png` beside
  `<seed>.render.json` (`isekai/pipeline/generate.py:476`, `:515`, `:527`; `SIDECAR` `:271`). `rendered`
  (`isekai/interface/run_view.py:175`) lists each flow's seeds from filenames. A batch is `<batch>/runs/<id>/`
  (`isekai/interface/compare_view.py:37`), the shape `infra/render.sh <runs> <flow>=<count>` fills (`:5`, `:34-37`).
- **No current render exists:** `find .data -name '*.render.json'` prints nothing; `.data/v0.30.1/runs/*/` hold
  `photo.png` and `summon-anime-wai/outputs/001/<seed>.png` with sidecars under the older name. `.inputs/` does
  not exist (`.gitignore:28`).
- **The dials are the flow's:** `ip_weight` and `identity_cn_strength` are read at `generate.py:388-389` from
  `flows/summon-anime-wai/flow.json:26-27`; the CLI has no override.
- **The manifest machinery:** `isekai/boundary/provision.py` — `PINNED_SOURCE` accepts a Hugging Face `resolve/<40
  hex>/` URL alone (`:49-51`), `resolve` (`:311`) verifies a digest under the models root. `evaluation/eval_models.py`
  — `EVAL_MANIFEST_PATH` (`:29`), `SHARED_WITH_THE_GRAPH` (`:36-40`), `RECOGNIZER` (`:43`), `shared_entries_that_differ`
  (`:52-71`). `tools/derive_eval_manifest.py` derives the file from `SPECS` (`:91`) with `PUBLISHERS` (`:49-53`); the
  gate's `drift` target runs it (`Makefile:26`, `:30`). `tools/manifest.py` — `Source` (`:84`), `Spec` (`:96`),
  `published_digest` reads the LFS object id (`:118`).
- **The ONNX pattern:** `isekai/boundary/wd14.py` — `silence_onnxruntime` (`:174`), `OnnxSession.__init__` (`:394-402`)
  imports `onnxruntime` inside the constructor and opens on `CPUExecutionProvider`.
- **The dependencies:** `onnxruntime==1.29.0`, `numpy==2.5.3`, `Pillow==12.3.0` (`pyproject.toml:43-45`); `[eval]`
  (`:78-82`) with its comment (`:50-77`); the ruff override (`:162`); the `ty` override (`:180-184`).
- **The encoders on Hugging Face, first-party:** `opencv/face_detection_yunet` at `3cc26e7f1014a5ee5d74a42acee58bafc9d0a310`
  holds `face_detection_yunet_2023mar.onnx`, LFS `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`,
  232589 bytes; `opencv/face_recognition_sface` at `3d7082438a6e4551e840c9b2bb60b71e8da4b524` holds
  `face_recognition_sface_2021dec.onnx`, LFS `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`,
  38696353 bytes — the digest of the untracked `models/opencv_face/sface.onnx` on this machine, read with
  `shasum -a 256`.
- **The spec:** `openspec/specs/evaluation/spec.md` — `## Purpose` (`:3-7`), *Source* and *Tests* (`:9-13`), nine
  requirements (`:17`, `:51`, `:72`, `:98`, `:116`, `:143`, `:171`, `:205`, `:239`).
- **Tests:** `tests/test_evaluate.py`, `tests/test_labels.py`, `tests/test_ciede2000.py`, `tests/eval_fakes.py` bind
  or support the requirements the deletion removes. `tests/test_eval_manifest.py` binds `pinned-artifacts`;
  its `recognizer-matches-the-generators-pin` tests (`:162-191`) assert the pin the deletion inverts.
  `tests/test_wd14.py:371-375` imports `eval_backends` for the telemetry check (`:377-396`).
  `tests/test_vocabulary_manifest.py:24` and `tests/test_package_paths.py:25`, `:58-60`, `:105` import `eval_models`,
  which stays. `tests/test_spec_bindings.py` — `unknown` (`:150`): a `spec` marker naming a key the effective spec
  lacks fails the gate, and `effective` (`tests/specs.py:28`) applies an active delta's `REMOVED` and `MODIFIED`.
- **Docs naming the sub-system:** `README.md:313-314`, `:383-385`; `docs/modules.md:74`; `docs/decisions.md:269-275`
  (D22); `docs/principles.md:252` (the last section, *Privacy*); `evaluation/README.md`.
- **The cohort's maker:** `synthetic_portraits` has `--identity`, ten identity specs and a face screen. Nothing is
  generated.

## Goals / Non-Goals

**Goals:** a current batch scorable; two counts with chance over a cohort; an encoder the generator does not use;
every render a row; the table re-derived from the record; the old evaluator gone.

**Non-Goals:** the batch itself and its committed figure; a control flow; hair, clothes or pose; a threshold; a
second encoder or seed; the cohort's generation; the root README's showcase; deleting the old models from `models/`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the cohort is `<dir>/<person>/<file>`; a run is its photograph's when the frame's `photo.sha256` equals the file's digest | the directory is the ground truth; a run is keyed by its bytes | a cohort manifest; a `person` key in the frame |
| [D2](#d2) | per render, rank the cohort by cosine; a photograph-level hit and a person-level hit with the source excluded; chance as expected hits | threshold-free, ground truth known, a copied pixel earns nothing on the second | a same-person threshold; AUC; an average cosine |
| [D3](#d3) | YuNet detects and lands five landmarks, SFace embeds the aligned 112×112 crop; both from `opencv`'s Hugging Face repositories, on onnxruntime; a numpy similarity transform and `PIL.Image.transform` align | independent of the generator's pins, Apache-2.0 and MIT, ONNX, SFace already measured on this task; no package added | `glintr100`, the adapter's own target; StyleID, torch and non-commercial; `opencv-python` for the warp |
| [D4](#d4) | one `evaluation.json` per batch, one table with a column per flow, re-derived from the record; a failure is a row | every render visible, the control arm drops in as a column later | a record per render; a table per flow |
| [D5](#d5) | `python -m evaluation <runs> --cohort <dir>` reads each `run.json` under `<runs>` through `Run`, each flow's seeds through `run_view.rendered`, writes `<runs>/../evaluation.json` and prints the table | the readers exist; the batch is what `render.sh` leaves | a `--flow` flag; parsing sidecars |
| [D6](#d6) | no package is added; `[eval]` and both overrides go; D22 says the evaluator adds no package to the runtime list | the isolation holds by construction; an empty extra is a config nothing reads | an empty `[eval]` |
| [D7](#d7) | D37 records the encoder's independence as a decision; `## Measurement` enters the principles with the tests that hold each | a choice about this evaluator is a decision; a rule every component follows is a principle | encoder independence as a principle |
| [D8](#d8) | the deletion is the last phase, and that phase adds `REMOVED` and `ADDED` to this change's delta as it deletes the tests | the binding checker fails a marker whose key an active delta removed, so the delta and the tests move together | `REMOVED` at the cut, which turns the gate red at the cut; deleting first |

### D1

**The cohort.** `cohort.py` holds `load_cohort(directory) -> Cohort`: every file directly under each sub-directory
is a `Photograph(person, path, sha256)`, the digest by `isekai.boundary.provision.digest_of`. A run is matched by
`run.frame["photo"]["sha256"]`; no match gives the outcome `outside the cohort`. A cohort photograph the detector
finds no face in refuses the whole scoring with `Refusal` naming the file, before any render is opened.

### D2

**The counts.** `rank(render_vector, gallery) -> list[Photograph]` sorts by cosine, descending. A photograph-level
hit: `ranked[0] is source`. A person-level hit: the first of `ranked` that is not `source` has `source.person`.
Chance is expected hits: per render `1 / N` and `(K_P - 1) / (N - 1)`, summed over the renders scored, printed to
one decimal: `2.1 / 18`. The record holds each render's `nearest` and `nearest_without_source` as photograph
paths relative to the cohort, never a cosine.

```
cohort.py   load_cohort · rank · hits · chance · record · table      stdlib + isekai.boundary.provision.digest_of
face.py     Detector · Encoder · align · embed                       onnxruntime · numpy · Pillow
__main__.py the runs, the flows, the seeds; calls the two above
```

### D3

**The encoder.** Two entries in `eval_models.json`, derived by `tools/derive_eval_manifest.py` from two `Spec`s with
`PUBLISHERS = ("opencv",)` and the revisions in *Context*: `opencv_face/face_detection_yunet_2023mar.onnx` and
`opencv_face/face_recognition_sface_2021dec.onnx`. `face.py` opens each through `resolve` and an
`onnxruntime.InferenceSession` on `CPUExecutionProvider`, after `silence_onnxruntime()`, the import inside the
constructor as `wd14.OnnxSession` does.

YuNet: input `[1, 3, 640, 640]` BGR float, no normalisation; the image letterboxed into 640 square; the three
strides' heads decoded with priors, scores thresholded at 0.6, NMS at 0.3, the highest-scoring box kept; its five
landmarks mapped back to image pixels. SFace: `align(image, landmarks)` solves the least-squares similarity
transform from the five landmarks to the 112×112 ArcFace template and warps with `PIL.Image.transform(AFFINE)`;
input `[1, 3, 112, 112]` RGB float, no normalisation, as OpenCV's `FaceRecognizerSF` swaps it before SFace; output 128-d, L2-normalised. The template:

```
(38.2946, 51.6963) (73.5318, 51.5014) (56.0252, 71.7366) (41.5493, 92.3655) (70.7299, 92.2041)
```

`embed(path) -> Vector | None`: `None` when no face is found. `__main__`-style entry `python -m evaluation.face
<image>…` prints one line per image, `face <x> <y> <w> <h>` or `no face`, for the probe in [tasks](tasks.md).

**Fallback, decided here and taken only if the probe fails:** the pinned `anime_face_detection/model.onnx` finds
the render's box, the crop is resized to 112×112 without alignment, and the photograph side keeps YuNet.

### D4

**The record and the table.** `evaluation.json`:

```
{"cohort": {"directory": "cohort", "people": ["p1", …], "photographs": 18},
 "encoder": {"detector": "<dest>", "encoder": "<dest>"},
 "flows": {"summon-anime-wai": {
    "rows": [{"person": "p1", "photograph": "p1/1.png", "run": "<id>", "seed": 123,
              "outcome": "hit" | "miss" | "no face found" | "not rendered",
              "nearest": "p1/1.png", "nearest_without_source": "p1/2.png",
              "photograph_hit": true, "person_hit": true}, …],
    "counts": {"photograph": {"hits": 15, "of": 18, "chance": 1.0},
               "person": {"hits": 14, "of": 18, "chance": 2.1}}}},
 "outside_the_cohort": ["<run id>", …]}
```

`table(record) -> str` prints the diagram in the delta: a row per flow, a chance row, then every row whose
outcome is not `hit`, named. A run with several renders of one flow contributes its first seed; the rest are
listed as `also rendered`. `outcome` is `hit` when both hits hold, `miss` when the face was found and either
missed; the two booleans keep the split.

### D5

**The entry point.** `main(argv)`: `runs` positional, `--cohort` required, `--models` defaulting to
`DEFAULT_MODELS_DIR`, `--flows` defaulting to `FLOWS_DIR`. It lists `runs/*/run.json`, opens each as `Run`, matches
it per D1, embeds every cohort photograph once (refusing per D1), then for each run and each `(flow, group, seeds)`
from `run_view.rendered` embeds `outputs/<group>/<seed>.png`, ranks per D2, and collects rows. A refusal from one
render is its row. It writes `runs.parent / "evaluation.json"` and prints `table`. Exit `0` with rows; `1` only on
a refusal of the cohort itself or an unreadable `runs`.

### D6

**No package.** `pyproject.toml`: the `[project.optional-dependencies]` table and its comment (`:50-82`) go; the
ruff `"evaluation/eval_backends.py"` line (`:162`) and the `[[tool.ty.overrides]]` block (`:180-184`) go; `uv lock`
re-derives `uv.lock`. D22 becomes: *Runtime dependencies are declared and pinned exactly. There is no optional
extra: the evaluator adds no package to the runtime list, and one it ever needs goes into an `[eval]` extra, never
into the pipeline's.* `README.md:313-314` says there is no extra; `:383-385` describe `evaluation/` as the cohort
evaluator.

### D7

**The decision and the principles.** The batch is the operator's, after this change ships; the record it writes
is committed by the change that publishes the figure, and `table` re-derives the table from it, which
`evaluation:table:the-table-re-derives-from-the-record` holds on a fixture record.

**D37 in `docs/decisions.md`:** *The evaluator's encoder shares no pin with the generator* — the adapter is trained
to satisfy the generator's recognizer, so a count on it is the adapter grading itself; held by the shares-no-pin
test; made by this change. **`## Measurement` in `docs/principles.md`**, after *Privacy*: *identity is a cohort
measurement* (held by the counts tests), *every render is a row* (held by the failure-is-a-row test), *a published
number ships with the code that computes it* (held by the re-derive test).

### D8

**The deletion, last.** The deletion phase removes `evaluate.py`, `eval_backends.py`, `ciede2000.py`, `labels.py`,
`baseline/`, `tests/test_evaluate.py`, `tests/test_labels.py`, `tests/test_ciede2000.py`, `tests/eval_fakes.py` and
the `recognizer-matches-the-generators-pin` tests; replaces `SHARED_WITH_THE_GRAPH`, `RECOGNIZER` and
`shared_entries_that_differ` with `DETECTOR`, `ENCODER` and `shared_with_the_graph(eval, graph) -> list[str]`, which
`__main__` refuses on when non-empty; drops the copied entries and the old `Spec`s from the deriver; re-points
`tests/test_wd14.py:371-375` at `evaluation.face`; rewrites `evaluation/README.md`; replaces `docs/modules.md:74`.

In the same phase, this change's `specs/evaluation/spec.md` gains `## REMOVED Requirements` for every
requirement the proposal lists as REMOVED, each with **Reason** and **Migration**, plus *Every model the scorer loads is pinned and verified*,
re-added as *Every model the evaluator loads is pinned and verified* minus its last SHALL sentence and its
`recognizer-matches-the-generators-pin` scenario — OpenSpec refuses a `MODIFIED` that drops a scenario; and the living spec's `## Purpose`, *Source* and *Tests* lines
are rewritten to the cohort evaluator.
`tests/test_spec_bindings.py` is why the delta moves with the tests: a `REMOVED` at the cut would make every old
marker name a key the effective spec lacks, and the gate would be red before the first phase.

## Dependencies

None. Two model artifacts, pinned in [D3](#d3), fetched by the existing provisioner on first use.

## Risks / Trade-offs

- **YuNet misses stylised faces** → the probe on `.data/v0.30.1` is a halt check; the fallback is decided in
  [D3](#d3).
- **The old evaluator goes before a batch has run the new one** → the probe, the tests and the delta are the
  proof here; the first batch is the operator's, and the old code stays in git.
- **The cohort is told apart by hair and skin, not faces** → the floor is chance alone until the control arm; the
  README's table says so in one line.
- **A Hugging Face repository drops its LFS object id** → `published_digest` raises and the deriver stops; the pins
  stay as derived at the cut.
- **The build edits the change's own delta** → one phase, one commit, `openspec validate --strict` re-run in it.

## Verdict

**feasible-with-caveats** — the cohort, the face and the entry point modules, the detector's and the encoder's
pins; the detector is probed on renders already on disk, and the deletion carries its own delta edit.
