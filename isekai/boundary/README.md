# `boundary/` — everything that leaves this process

A hosted model, a rented GPU, a download. Each file is one way out, and this is
where a way out belongs.

**It is not yet where every way out lives.** Three sit outside this directory
today: `evaluation/labels.py` spawns `git`, `interface/ui/bundle.py` spawns
`npm`, and `interface/ui/app.py` binds a port. Moving them behind this boundary
is the better repository and is filed rather than done — a documentation release
that quietly refactors is two changes wearing one name (`0024` design.md D6).

## Files

| file | does | reaches |
|---|---|---|
| `comfy_types.py` | the `ComfyTransport` Protocol and the workflow/image types — the network boundary's shape, with no network in it | nothing |
| `comfy_client.py` | upload · submit · poll · retrieve, over `urllib` | the rented GPU |
| `multipart.py` | builds one multipart body; internal to the transport | nothing |
| `ollama.py` | one POST to a local runtime, and the classification of what comes back | the hosted model, over HTTP to localhost |
| `provision.py` | plan → verify → land: the manifest reader, the byte check, the skip/abort/fetch policy | a download, on the pod |
| `wd14.py` | the local tagger: a digest-verified ONNX session, the label index whose file order names its neurons, and the scored list it emits | a 467 MB file on disk, and nothing else |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `comfy_types.py` | `comfy_client.py`, `foundation/flow.py`, `interface/cli.py`, `interface/wiring.py`, `pipeline/generate.py` | `tests/conftest.py`, `tests/fakes.py`, `tests/test_generate.py`, `tests/test_image.py`, `tests/test_infra.py`, `tests/test_manifest_binding.py` |
| `comfy_client.py` | `interface/wiring.py` | `probe/loader_probe.py` |
| `multipart.py` | `comfy_client.py` | `tests/test_multipart.py` |
| `ollama.py` | `pipeline/caption.py`, `pipeline/tagging.py` | `tests/test_ollama.py` |
| `provision.py` | `wd14.py`, `evaluation/eval_models.py`, `shared/vocabulary.py` | `../../evaluate.py`, `tests/conftest.py`, `tests/test_eval_manifest.py`, `tests/test_flow.py`, `tests/test_infra.py`, `tests/test_manifest.py`, `tests/test_manifest_binding.py`, `tests/test_package_paths.py`, `tests/test_provision.py`, `tests/test_tagging.py`, `tests/test_vocabulary_manifest.py`, `tests/test_wd14.py` |
| `wd14.py` | `interface/cli.py`, `interface/wiring.py`, `pipeline/tagging.py` | `tests/stages.py`, `tests/test_resume.py`, `tests/test_tagging.py`, `tests/test_wd14.py` |

> `provision.py` is not on `python -m isekai`'s import graph, so the stdlib-only
> runtime rule is untouched either way.
>
> **`wd14.py` is**, and it is the only module in the package that touches the
> `tagging` extra. Every one of its imports from that extra -- `onnxruntime`,
> `numpy`, `Pillow` -- is **function-local**, which keeps the `-S` guard green;
> `tests/test_wd14.py` asserts none of them sits at module scope. It reaches no
> network at all, which makes it the one file here that is a boundary to a *file*
> rather than to a host.
>
> **`ollama.py` is now the only way out of this process to a model.** There was a
> second, `claude_cli.py`, and the isolation law that kept the two apart was the
> reason this note existed. v0.22 deleted that file with the arm it served, so
> there is no second transport to be isolated from -- and nothing in the gate
> would catch one being reintroduced. What makes that visible is that there is no
> registry to add an entry to: a second reader is a second adapter, in review.

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
