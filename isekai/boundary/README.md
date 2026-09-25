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
| `comfy_types.py` | the `ComfyTransport` Protocol and the image type — the network boundary's shape, with no network in it | nothing |
| `comfy_client.py` | upload · submit · poll · retrieve, over `urllib` | the rented GPU |
| `multipart.py` | builds one multipart body; internal to the transport | nothing |
| `ollama.py` | one POST to a local runtime, and the classification of what comes back | the hosted model, over HTTP to localhost |
| `provision.py` | plan → verify → land: the manifest reader, the byte check, the skip/abort/fetch policy, and `resolve`, which returns a pinned artifact's path only once its bytes are verified | a download, on the pod |
| `wd14.py` | the local tagger: a digest-verified ONNX session, the label index whose file order names its neurons, and the scored list it emits | a 467 MB file on disk, and nothing else |

## Imported by

**Named, not counted.** A count in this column has gone stale in every group here
at least once; a list of names cannot.

| file | inside `isekai/` | outside |
|---|---|---|
| `comfy_types.py` | `comfy_client.py`, `interface/cli.py`, `interface/wiring.py`, `pipeline/generate.py` | `tests/fakes.py` |
| `comfy_client.py` | `interface/wiring.py` | `probe/loader_probe.py` |
| `multipart.py` | `comfy_client.py` | `tests/test_multipart.py` |
| `ollama.py` | `pipeline/caption.py`, `pipeline/tagging.py` | `tests/test_ollama.py` |
| `provision.py` | `wd14.py`, `evaluation/eval_backends.py`, `evaluation/eval_models.py`, `interface/wiring.py` | `../../evaluate.py`, `tests/conftest.py`, `tests/test_eval_manifest.py`, `tests/test_flow.py`, `tests/test_infra.py`, `tests/test_manifest.py`, `tests/test_manifest_binding.py`, `tests/test_package_paths.py`, `tests/test_provision.py`, `tests/test_tagging.py`, `tests/test_vocabulary_manifest.py`, `tests/test_wd14.py` |
| `wd14.py` | `interface/cli.py`, `interface/wiring.py`, `pipeline/tagging.py` | `tests/stages.py`, `tests/test_resume.py`, `tests/test_tagging.py`, `tests/test_wd14.py` |

> `provision.py` is not on `python -m isekai`'s import graph, so the module-scope
> import rule is untouched either way.
>
> **`wd14.py` is**, and it touches the tagger's stack; `evaluation/eval_backends.py`
> touches it too, off that graph. Every one of `wd14.py`'s imports of it --
> `onnxruntime`, `numpy`, `Pillow` -- is **function-local**, which keeps the `-S`
> guard green. They are declared dependencies as of v0.22.3, so one moved to
> module scope resolves silently; that guard and `tests/test_wd14.py`'s source
> scan catch it. `wd14.py` reaches no network at all, which makes it the one file
> here that is a boundary to a *file* rather than to a host.
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
