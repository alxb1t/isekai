# `boundary/` — everything that leaves this process

A hosted model, a rented GPU, a download. Each file is one way out, and nothing
outside this directory opens a socket or spawns a binary.

## Files

| file | does | reaches |
|---|---|---|
| `claude_cli.py` | one locked-down model invocation, one envelope back | the hosted model, over its CLI |
| `comfy_types.py` | the `ComfyTransport` Protocol and the workflow/image types — the network boundary's shape, with no network in it | nothing |
| `comfy_client.py` | upload · submit · poll · retrieve, over `urllib` | the rented GPU |
| `multipart.py` | builds one multipart body; internal to the transport | nothing |
| `ollama.py` | one POST to a local runtime, and the classification of what comes back | the hosted model, over HTTP to localhost |
| `provision.py` | plan → verify → land: the manifest reader, the byte check, the skip/abort/fetch policy | a download, on the pod |
| `wd14.py` | the local tagger: a digest-verified ONNX session, the label index whose file order names its neurons, and the scored list it emits | a 467 MB file on disk, and nothing else |

## Imported by

| file | inside `isekai/` | outside |
|---|---|---|
| `claude_cli.py` | `pipeline/caption.py`, `pipeline/sheet.py` | `tests/test_caption.py`, `tests/test_sheet_stage.py`, `tests/test_package_paths.py`, `tests/test_run_directory.py` |
| `comfy_types.py` | `comfy_client.py`, `foundation/flow.py`, `interface/cli.py`, `interface/wiring.py`, `pipeline/generate.py` | five test modules |
| `comfy_client.py` | `interface/wiring.py` | `probe/loader_probe.py` |
| `multipart.py` | `comfy_client.py` | `tests/test_multipart.py` |
| `ollama.py` | `pipeline/caption.py`, `pipeline/sheet.py` | `tests/test_ollama.py` |
| `provision.py` | `evaluation/eval_models.py`, `shared/vocabulary.py`, `wd14.py` | `../../evaluate.py`, ten test modules |
| `wd14.py` | `pipeline/tagging.py`, `interface/cli.py`, `interface/wiring.py` | `tests/test_wd14.py`, `tests/stages.py` |

> `provision.py` is not on `python -m isekai`'s import graph, so the stdlib-only
> runtime rule is untouched either way.
>
> **`wd14.py` is**, and it is the only module in the package that touches the
> `tagging` extra. Every one of its three imports -- `onnxruntime`, `numpy`,
> `Pillow` -- is **function-local**, which is what keeps the `-S` guard green;
> `tests/test_wd14.py` asserts none of them sits at module scope. It reaches no
> network at all, which makes it the one file here that is a boundary to a *file*
> rather than to a host.
>
> **`ollama.py` imports nothing from `claude_cli.py`.** It is the weaker half of
> the isolation law and named here anyway: the edge that matters is the call
> graph, because `pipeline/caption.py` imports nine names from `claude_cli` for
> `ClaudeReader` and every flow traverses that file. The suite is what proves an
> open flow reaches none of them.

> Files and importers only. What a seam *is*, and what could replace it, is the
> design record's; neither restates the other.
