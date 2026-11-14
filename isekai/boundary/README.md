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
| `comfy/__init__.py` | the ComfyUI transport's front door: `ComfyTransport`, `ComfyClient`, `Image`, `TransportFailure`, `unread`, `submit_and_wait`, `read_runtime` | nothing |
| `comfy/contract.py` | the `ComfyTransport` Protocol, the image type, `TransportFailure`, which carries its kind, and `unread`, the permanent failure for an answer in a shape this build does not read — the network boundary's shape, with no network in it | nothing |
| `comfy/client.py` | upload · submit · poll · retrieve · the server's own report, over `urllib`, never through a proxy and never past `TIMEOUT`; every failure it meets is raised as a `TransportFailure`: a 4xx or an unreadable answer permanent, a 5xx, a closed tunnel or a timeout transient | the rented GPU |
| `comfy/multipart.py` | builds one multipart body; private to the package | nothing |
| `comfy/prompt.py` | the helpers a stage submits a graph with: `submit_and_wait` queues one graph, waits for its history and returns the image's bytes, `read_runtime` returns the versions the server reports and its first device; the render and the edit share them, so neither stage imports the other | the rented GPU, over the transport it is handed |
| `gpu.py` | `read_env`, the `.env` file read into the session's environment; `bounds`, what `gpunit.toml` bounds; `open_session`, gpunit's session stopping at the session's limit; `Seams`, what a session reaches through; and `Volume`, the window volume and `.gpunit/` through gpunit's verbs; `run_gpunit`, a gpunit verb whose lines reach `say` as they come, and its `GpunitExit`, the exit with the last `refused:` line `refused_line` reads; gpunit is imported inside each | the rented GPU, through gpunit |
| `ollama.py` | one POST to a local runtime, the classification of what comes back, the check that a model is built from the files `config/reader.json` pins, and the probe a job asks before it starts | the hosted model, over HTTP to localhost; Ollama's model records on disk |
| `pod_start.py` | the pod's start, run as the image's command: the volume, the models link, `provision.py fetch`, the memory checks, then `exec` into ComfyUI; stdlib only | the pod's volume and memory, and `provision.py` as a process |
| `pose.py` | the placement's pose: `Pose`, the `PoseFinder` seam, `verified_paths` for the detector's and the estimator's digest-verified files, and `OnnxPoseFinder`, which reads one person's box and the body's keypoints with their scores on the CPU; `open_pose` makes it; `onnxruntime`, numpy and Pillow are imported inside its functions | two files on disk, and nothing else |
| `provision.py` | decide → transfer → verify → land: the manifest reader, the byte check, the skip/abort/fetch policy, `fetch`, which walks each entry's sources, and `resolve`, which returns a pinned artifact's path only once its bytes are verified | a download, on the laptop and on the pod |
| `sam2.py` | the placement's segmenter: `prepare` for the encoder's input, the `Segmenter` seam, `Embedding`, whose `mask` runs the decoder for a prompt, and `OnnxSegmenter`, which encodes an image once, on the CPU; `open_segmenter` makes it from the members `unpack` verified; `onnxruntime`, numpy and Pillow are imported inside its functions | two files on disk, and nothing else |
| `unpack.py` | a zip entry's members, each landed by its declared destination and verified: `Member` and `ZipEntry`, `unpack_members`, `fetch` and its `python -m isekai.boundary.unpack fetch` command, `member_for` and `resolve_member`, and the placement manifest's path and its fetch command; it leaves `provision.py` unedited, which the pod image copies | a download through `provision`, then the archive on disk |
| `wd14.py` | the local tagger: a digest-verified ONNX session, the label index whose file order names its neurons, and the scored list it emits | a 467 MB file on disk, and nothing else |

## Imported by

**Derived.** `uv run python -m tools.derive_imported_by` writes this table from the import graph of `tools/import_graph.py`, the one the layer guards read, and a test re-derives it. It names importers in `isekai/`, `evaluation/` and `tools/`, never a test.

| file | inside `isekai/` | outside |
|---|---|---|
| `comfy/` | `gpu.py`, `interface/render.py`, `interface/verbs/common.py`, `interface/verbs/edits.py`, `interface/verbs/generate.py`, `interface/wiring.py`, `pipeline/edit.py`, `pipeline/generate.py` | — |
| `comfy/multipart.py` | `comfy/client.py` | — |
| `comfy/prompt.py` | `comfy/__init__.py` | — |
| `gpu.py` | `interface/render.py`, `interface/ui/app.py`, `interface/ui/billing.py`, `interface/ui/jobs.py`, `interface/wiring.py` | — |
| `ollama.py` | `interface/wiring.py`, `pipeline/caption.py`, `pipeline/tagging.py` | — |
| `pod_start.py` | `interface/render.py` | — |
| `pose.py` | `interface/wiring.py`, `pipeline/proposing.py` | — |
| `provision.py` | `ollama.py`, `pose.py`, `sam2.py`, `unpack.py`, `wd14.py`, `interface/wiring.py` | `evaluation/__main__.py`, `evaluation/cohort.py`, `evaluation/eval_models.py`, `evaluation/face.py`, `evaluation/recall.py`, `tools/derive_manifest.py`, `tools/derive_reader.py`, `tools/derive_vocabulary.py`, `tools/manifest.py` |
| `sam2.py` | `interface/wiring.py`, `pipeline/proposing.py` | — |
| `unpack.py` | `pose.py`, `sam2.py`, `interface/wiring.py` | `tools/derive_placement.py`, `tools/manifest.py` |
| `wd14.py` | `pose.py`, `sam2.py`, `interface/cli.py`, `interface/wiring.py`, `pipeline/tagging.py` | `evaluation/face.py`, `evaluation/recall.py` |

> `interface/render.py` imports `pod_start.py` for the hold its limit's floor is
> above; the image runs it as a file.

> `provision.py` is on `python -m isekai`'s import graph, through `ollama.py`'s
> check of the reader's manifest. It imports only the standard library, so the
> module-scope import rule holds.
>
> **`wd14.py` is**, and it touches the tagger's stack; `evaluation/face.py`
> touches it too, off that graph. Every one of `wd14.py`'s imports of it --
> `onnxruntime`, `numpy`, `Pillow` -- is **function-local**, which keeps the `-S`
> guard green. They are declared dependencies as of v0.22.3, so one moved to
> module scope resolves silently; that guard and `tests/test_wd14.py`'s source
> scan catch it. `wd14.py` reaches no network at all, and with `pod_start.py` is one
> of the two files here that open no connection: a boundary to a *file* rather than
> to a host. `pod_start.py` reaches the network only through `provision.py fetch`,
> run as a process. `onnxruntime` itself
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
