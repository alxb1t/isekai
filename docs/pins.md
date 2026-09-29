# Pins — why we pin, and how each pin is moved

Every input that shapes an output is fixed by a digest, a commit or an exact version, and it moves only by a
commit. The rule and its reason are [the pinning principle](principles.md#everything-that-shapes-an-output-is-pinned);
what each artifact records is [the records principle](principles.md#every-artifact-records-what-shaped-it). This
page is how the pins are held, and how each one is moved.

```
upstream release ──▶ nothing arrives by itself
                        │
        a change re-pins it on purpose ──▶ the gate, and a proof ──▶ commit
                                                                       │
                          every artifact records what shaped it ◀──────┘
```

## What pins buy

Each gain, and where it stops.

| gain | what it means here | where it stops |
|---|---|---|
| **identity** | every pod runs the same image bytes; every machine installs the same packages and model files | not the same pixels: the GPU, its driver and the host are not pinned, and [a seed reproduces the graph, not the pixels](decisions.md#d13--the-seed-reproduces-the-graph-not-the-pixels) |
| **integrity** | a file whose bytes differ from its pinned digest is refused | a digest proves the bytes are the pinned ones, not that they are benign; GGUF, safetensors and ONNX carry no code, which is what keeps a model inert |
| **supply chain** | a new or re-published release never arrives unasked; a moved action tag cannot run new code | a release compromised before it was pinned stays pinned |
| **comparable figures** | a figure names the configuration that produced it, and a later run can use the same one | only for runs recorded after the pins |
| **attribution** | each artifact records the files, options, floor, flow and image that shaped it | what is not pinned is recorded, not held; a render on another server, after a teardown that did not answer 204, borrows .runpod_pod_image's pin |
| **no silent drift** | every move is a commit — a new digest, a re-lock, a re-pin — so `git log` and `git bisect` find when an output changed | |
| **rollback** | an old image digest boots again | while the registry keeps it |
| **fail before paying** | a wrong or missing model is refused before a call or a paid render | |

**The price:** an update arrives only when someone re-pins it, builds break where a moving input would have
drifted, and verification costs time at provisioning and at boot.

## The inventory

Each pin: what fixes it, where it is declared, and when it is checked.

| pin | pinned by | declared in | checked |
|---|---|---|---|
| the pod image | digest | `config/image.json` | `infra/up.sh` boots only that digest and writes it to `.runpod_pod_image` |
| the image's base and uv | digest | `Dockerfile` | at build |
| the image's Python environment | a lock with every installed package's hash; Python by patch; the sdist builds' tools by hash | `image/pyproject.toml`, `image/uv.lock`, `image/.python-version` | `uv sync --locked` at build |
| ComfyUI and its custom nodes | git commit | `Dockerfile` | at build; `tests/test_infra.py` holds each clone to a commit |
| isekai's Python dependencies | a lock with every hash | `pyproject.toml`, `uv.lock` | `uv sync --locked`, the gate's first command |
| uv | exact version | `pyproject.toml`, `image/pyproject.toml`, `.github/workflows/ci.yml`, `Dockerfile` | every `uv` command |
| CI's actions, runner and Node | commit SHA; runner and Node by version | `.github/workflows/` | every run |
| the render models | sha256 at an immutable revision | `config/models.json` | on landing, and on every boot |
| the tag vocabulary and WD14 | sha256, one revision for both | `config/vocabulary.json` | on landing, and when the tagger opens |
| the reader's files | sha256 at an immutable revision | `config/reader.json` | on landing, and the Ollama alias's layers before its first call ([D6](decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model)) |
| the evaluator's models | sha256 at an immutable revision | `evaluation/eval_models.json` | when the evaluator resolves them |
| each flow | a digest of every file in it | `tests/test_flow.py` | the gate |

## Re-pinning

One recipe per pin. Each is a commit inside a change, and each change says what moved and why.

- **The pod image.** Push the branch, run `gh workflow run build-image.yml --ref <branch> -f tag=<vX.Y-rcN>`,
  and copy the digest from the job summary into `config/image.json`. A new digest is proved on a pod, in a
  metered phase, before it merges ([D28](decisions.md#d28--the-image-carries-code-the-volume-carries-weights)).
- **The base or uv.** Resolve the new reference with `docker buildx imagetools inspect <ref>`, write it with its
  digest into the `Dockerfile`, then rebuild the image.
- **The image's Python environment.** `make derive` runs `tools/derive_image_project.py`, which re-reads the
  upstream requirement lists at the commits the `Dockerfile` pins and re-locks `image/`. Review the diff of
  `image/uv.lock`, then rebuild the image.
- **ComfyUI or a custom node.** Move its commit in the `Dockerfile`, then `make derive` and rebuild. A new core
  changes output, so the change carries a render comparison.
- **isekai's dependencies.** `uv lock --upgrade-package <name>`, and review the diff of `uv.lock`.
- **uv.** Move `required-version` in `pyproject.toml`, `version:` in `.github/workflows/ci.yml`, and the
  `COPY --from` reference with its digest in the `Dockerfile`, then `make derive` carries it into
  `image/pyproject.toml`. `tests/test_infra.py` fails while any of them disagrees.
- **An action.** Replace its SHA and the release in its comment; `gh api repos/<owner>/<repo>/git/ref/tags/<tag>`
  resolves one.
- **A model manifest.** Move the revision constant in its deriver — `tools/derive_manifest.py`,
  `tools/derive_vocabulary.py`, `tools/derive_reader.py` — run `make derive`, and review the diff under
  `config/`. For the reader, then run `bash tools/download_models.sh config/reader.json` and
  `ollama create joycaption-beta-one-q4k -f config/joycaption.Modelfile`.
- **A flow.** A variant is a new flow; an abandoned configuration is re-pinned — update `PINNED` in
  `tests/test_flow.py` and name the new digest in `CHANGELOG.md`
  ([D14](decisions.md#d14--a-flow-is-one-flat-directory)).

## Not pinned

What stays open, and what stands in for it.

| input | why not | what stands in |
|---|---|---|
| apt packages in the image | versions leave the Ubuntu archive, so a pinned version breaks a later build | the image digest freezes them inside each image |
| the Ollama runtime | the operator installs it, outside the repository | the alias's model and projector layers are checked, and the caption and the hosted tags record both file digests |
| the pod's GPU, driver and host | RunPod assigns them | each render records the ComfyUI, Python and PyTorch versions the pod reports |
| macOS and Metal on the operator's machine | outside the repository | nothing yet |
| the reader alias's template, system prompt and parameters | the check compares the model and projector layers alone, and changing the rest needs write access to the operator's Ollama store | `config/joycaption.Modelfile`, from which the alias is built |

**A rebuild is not byte-identical**: apt is open, and insightface compiles from source. What reproduces exactly
is booting the same digest.

## When to re-pin

- **An advisory names a pinned version.** Re-pin to the fixed release, and prove it as its row above says.
- **A deliberate upgrade** — a model, ComfyUI, a dependency — for a reason the change states.
- **Never as routine.** Each re-pin is a change with its own proof: a render comparison for anything that
  shapes an image, and a metered phase for a new image digest.
