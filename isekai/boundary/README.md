# `boundary/` — everything that leaves this process

A hosted model, a rented GPU, a download. Each file is one way out, and this is
where a way out belongs.

**It is not yet where every way out lives.** Some sit outside this directory
today: `interface/ui/bundle.py` spawns `npm`, and `interface/ui/app.py` binds a
port. Moving them behind this boundary is the better repository and is filed rather than done — a documentation release
that quietly refactors is two changes wearing one name (`0024` design.md D6).

## Files

| file | does | reaches |
|---|---|---|
| `comfy/__init__.py` | the ComfyUI transport's front door: `ComfyTransport`, `ComfyClient`, `Image`, `TransportFailure`, `unread` | nothing |
| `comfy/contract.py` | the `ComfyTransport` Protocol, the image type, `TransportFailure`, which carries its kind, and `unread`, the permanent failure for an answer in a shape this build does not read — the network boundary's shape, with no network in it | nothing |
| `comfy/client.py` | upload · submit · poll · retrieve · the server's own report, over `urllib`, never through a proxy and never past `TIMEOUT`; every failure it meets is raised as a `TransportFailure`: a 4xx or an unreadable answer permanent, a 5xx, a closed tunnel or a timeout transient | the rented GPU |
| `comfy/multipart.py` | builds one multipart body; private to the package | nothing |
| `ollama.py` | one POST to a local runtime, the classification of what comes back, and the check that a model is built from the files `config/reader.json` pins | the hosted model, over HTTP to localhost; Ollama's model records on disk |
| `provision.py` | plan → verify → land: the manifest reader, the byte check, the skip/abort/fetch policy, and `resolve`, which returns a pinned artifact's path only once its bytes are verified | a download, on the pod |
| `wd14.py` | the local tagger: a digest-verified ONNX session, the label index whose file order names its neurons, and the scored list it emits | a 467 MB file on disk, and nothing else |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `comfy/` | `interface/cli.py`, `interface/wiring.py`, `pipeline/generate.py` | `tests/fakes.py`, `tests/stages.py`, `tests/test_generate.py`, `tests/test_resume.py` |
| `comfy/multipart.py` | `comfy/client.py` | `tests/test_multipart.py` |
| `ollama.py` | `pipeline/caption.py`, `pipeline/tagging.py` | `tests/conftest.py`, `tests/fakes.py`, `tests/test_caption.py`, `tests/test_ollama.py`, `tests/test_pipeline_cli.py`, `tests/test_tagging.py` |
| `provision.py` | `ollama.py`, `wd14.py`, `interface/wiring.py` | `evaluation/__main__.py`, `evaluation/cohort.py`, `evaluation/eval_models.py`, `evaluation/face.py`, `evaluation/recall.py`, `tests/conftest.py`, `tests/fakes.py`, `tests/test_cohort.py`, `tests/test_eval_manifest.py`, `tests/test_evaluation_cli.py`, `tests/test_flow.py`, `tests/test_infra.py`, `tests/test_manifest.py`, `tests/test_manifest_binding.py`, `tests/test_package_paths.py`, `tests/test_provision.py`, `tests/test_reader_manifest.py`, `tests/test_recall_cli.py`, `tests/test_sheet_schema.py`, `tests/test_tagging.py`, `tests/test_vocabulary_manifest.py`, `tests/test_wd14.py`, `tools/derive_manifest.py`, `tools/derive_reader.py`, `tools/derive_vocabulary.py`, `tools/manifest.py` |
| `wd14.py` | `interface/cli.py`, `interface/wiring.py`, `pipeline/tagging.py` | `evaluation/face.py`, `evaluation/recall.py`, `tests/stages.py`, `tests/test_recall.py`, `tests/test_recall_cli.py`, `tests/test_resume.py`, `tests/test_sheet_stage.py`, `tests/test_tagging.py`, `tests/test_vocabulary_manifest.py`, `tests/test_wd14.py` |

> `provision.py` is on `python -m isekai`'s import graph, through `ollama.py`'s
> check of the reader's manifest. It imports only the standard library, so the
> module-scope import rule holds.
>
> **`wd14.py` is**, and it touches the tagger's stack; `evaluation/face.py`
> touches it too, off that graph. Every one of `wd14.py`'s imports of it --
> `onnxruntime`, `numpy`, `Pillow` -- is **function-local**, which keeps the `-S`
> guard green. They are declared dependencies as of v0.22.3, so one moved to
> module scope resolves silently; that guard and `tests/test_wd14.py`'s source
> scan catch it. `wd14.py` reaches no network at all, which makes it the one file
> here that is a boundary to a *file* rather than to a host. `onnxruntime` itself
> connects to Microsoft when it loads, so `silence_onnxruntime()` sets its switch
> first, for both sessions (0035 design D5).
>
> **`ollama.py` is now the only way out of this process to a model.** There was a
> second, `claude_cli.py`, and the isolation law that kept the two apart was the
> reason this note existed. v0.22 deleted that file with the arm it served, so
> there is no second transport to be isolated from -- and nothing in the gate
> would catch one being reintroduced. What makes that visible is that there is no
> registry to add an entry to: a second reader is a second adapter, in review.

> Files and importers only. What a component *is* is
> [`docs/principles.md`](../../docs/principles.md)'s, and the choices in force are
> [`docs/decisions.md`](../../docs/decisions.md)'s; neither restates the other.
