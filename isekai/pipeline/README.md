# `pipeline/` — the staged verbs

One file per stage, in the order a photograph passes through them. No stage reads
another's output directly: each is handed a path inside a run and hands back a
numbered artifact, and **no stage imports another** — the last such edge closed
when `validate` moved to `shared/fields.py`. `caption` and `tag` write the
photograph's description into `photo/`, once for every flow; every other stage is
per flow: the flow supplies the schema it fills against and the directory it
writes into ([D17](../../docs/decisions.md#d17--input-above-flow-below)).

**The verbs are `import` · `caption` · `tag` · `sheet` · `review` · `approve` · `draft` · `discard` · `generate` · `edit`.**
`importing.py` is `import`: it fills a collection's `sources/` and comes before every run. `edit.py` is `edit`: it
works on a finished render after `generate`, and writes its files beside the render's own
([D51](../../docs/decisions.md#d51--an-edit-is-one-flat-directory-pinned-by-its-digest)).
`tattoos.py` is no verb: it keeps the library's tattoos and makes the app's ink view, `preview` and `composite`, and
imports no stage ([D52](../../docs/decisions.md#d52--the-tattoo-library-is-kept-whole-until-a-tattoo-is-removed)).
`proposing.py` is no verb either: it proposes the pairs of stage 2 for the app and keeps nothing
([D54](../../docs/decisions.md#d54--automatic-pairs-run-on-the-operators-machine-and-are-kept-nowhere)).
`review.py` holds `review`, `approve` and the revision and draft writers serving `draft`;
`tagging.py` is `tag`: its two functions write
the two tag lists, each refusal collected on its own. `caption` and `tag` are
independent, and neither reads the other's output
([D1](../../docs/decisions.md#d1--stage--is-two-independent-verbs)).

## Files

| file | does | costs |
|---|---|---|
| `importing.py` | reads a file into staging — an upload in turn, by its open import's reader — cleans it to its pixels and orientation, verifies it, previews it, and commits the collection's `sources/` | free |
| `caption.py` | ① `caption`: turns a photograph into descriptive prose | a model call |
| `tagging.py` | ① `tag`: a scored tag list from a local ONNX session, then a raw one from a hosted model. **Neither is narrowed** — filtering is ②'s job | free, then a model call |
| `sheet.py` | ② routes the photograph's local tag list into the flow's schema's fields, through the authored table | free |
| `review.py` | ③ copies a sheet somewhere a human may correct it, then approves it | a human — the largest measured gain in the pipeline |
| `generate.py` | ④ assembles every prompt locally, then renders each against an endpoint, and discards one render | free, then **money** |
| `edit.py` | `edit`: requests an edit from a render and its composite, or with `request_placed` from a bake's composite and its placement record, and lists the pending ones, then samples a pending one over the transport and stitches it; discards an edit. It takes its transport helpers from `boundary/comfy/prompt.py` and its maths from `shared/tattoo.py`, and imports no stage | free to request and check, then **money** to sample |
| `proposing.py` | `propose`: the pairs stage 2 proposes from a photograph, a render and the tattoo's points on the photograph, as `Proposal(arm, pairs)`, none for no person and none for no usable bone; a `Proposer` holds the pose finder and the segmenter it is given. It reads no file, takes the pose from `boundary/pose.py`, the segmenter from `boundary/sam2.py` and its geometry from `shared/proposal.py`, and imports no stage | free |
| `tattoos.py` | the library's `.tattoos/<name>/` and its cuts under `.tattoos/.cuts/<digest>/<name>/`: keeps an upload upright and bounded, cuts a tattoo from a photograph, reads every name by the render's digest, removes a tattoo, saves and reads an outline with its tone and a tattoo's stage-1 pairs per photograph, makes the ink view on the outline's crop, the `preview` of a warp on a crop of its target and the `composite` over a whole render. It takes bytes and paths, takes its maths from `shared/chain.py`, `shared/ink.py` and `shared/tattoo.py`, and imports no stage; Pillow is imported inside its functions | free |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `importing.py` | `interface/cli.py`, `interface/ui/__init__.py`, `interface/ui/app.py`, `interface/ui/library.py` | `tests/test_importing.py` |
| `caption.py` | `interface/cli.py`, `interface/wiring.py` | `tests/stages.py`, `tests/test_caption.py`, `tests/test_generate.py`, `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`, `tests/test_run_view.py`, `tests/test_sheet_stage.py`, `tests/test_tagging.py`, `tests/test_ui.py`, `tests/test_ui_api.py` |
| `tagging.py` | `interface/cli.py`, `interface/wiring.py` | `tests/test_generate.py`, `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_run_view.py`, `tests/test_tagging.py`, `tests/test_ui_api.py` |
| `sheet.py` | `interface/cli.py`, `interface/drafting.py`, `interface/run_view.py`, `interface/ui/app.py` | `tests/stages.py`, `tests/test_run_view.py`, `tests/test_sheet_stage.py` |
| `review.py` | `interface/cli.py`, `interface/drafting.py`, `interface/render.py`, `interface/ui/app.py`, `interface/ui/library.py` | `tests/e2e/conftest.py`, `tests/e2e/test_review.py`, `tests/test_artifact_bytes.py`, `tests/test_generate.py`, `tests/test_render.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`, `tests/test_run_view.py`, `tests/test_ui.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py`, `tests/test_ui_library.py` |
| `edit.py` | `interface/cli.py`, `interface/render.py`, `interface/ui/app.py` | `tests/test_edit.py`, `tests/test_edit_placement.py`, `tests/test_edit_session.py` |
| `proposing.py` | `interface/wiring.py` | `tests/test_propose.py`, `tests/test_ui_propose.py` |
| `tattoos.py` | `interface/ui/app.py` | `tests/test_package_paths.py`, `tests/test_tattoo_library.py`, `tests/test_tattoo_placement.py`, `tests/test_ui_library.py`, `tests/test_ui_placement.py`, `tests/test_ui_tattoo.py` |
| `generate.py` | `interface/cli.py`, `interface/compare_view.py`, `interface/render.py`, `interface/run_view.py`, `interface/ui/app.py`, `interface/ui/library.py` | `tests/e2e/conftest.py`, `tests/test_artifact_bytes.py`, `tests/test_generate.py`, `tests/test_render.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`, `tests/test_run_view.py`, `tests/test_ui_api.py` |

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
