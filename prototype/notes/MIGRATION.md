# MIGRATION — what on `main` dies, what survives, what moves

**Round 5, N47. Written 2026-09-13.** The honest inventory behind **L18** — *the old flow is deleted,
not deprecated*. Written to be attacked in a grilling session and then cut into changes.

> **Nothing in `prototype/` is promoted as code.** This branch never merges. Every line reaches a
> release by being **restated inside a change** under `openspec/changes/<id>/`, per
> [`../../CLAUDE.md`](../../CLAUDE.md) § *How a change is cut here*. This note says *what* moves, not
> *how it gets there* — that is [`ROADMAP.md`](ROADMAP.md) (N48).

---

## 1 · The headline, and it is good news

```
   main today            152 scenarios · 6 capabilities · 9,251 lines of code+tests
        │
        ├─ SURVIVES      ≈92 scenarios   transport · provisioning · evaluation · CLI
        │                                 the expensive half, and it took versions to get right
        │
        └─ DIES          ≈60 scenarios   workflow-injection · workflow-mutation
                                          the half that encodes an architecture round 1 rejected
```

**The survivors are why the next version is affordable at all.** `ComfyTransport`, the manifest
discipline, `Refusal`, the offline-fake suite and the `-S` guard are not re-derivable cheaply, and none
of them is touched by the new architecture.

---

## 2 · What dies, and why deleting it costs nothing measurable

### `workflow-injection` — 23 scenarios, most of them false now

| requirement | fate |
|---|---|
| **The positive prompt is graph configuration** | **dies.** The prompt is assembled per flow from a reviewed sheet (**L10**) |
| **Latent initialisation from the photo** | **dies.** The from-noise flow is `EmptyLatentImage` at `denoise 1.0` |
| Node location on the one graph | **moves** — becomes a flow's own concern |
| Photo wiring into the one graph | **moves** — same |
| **The photo is scaled to a working resolution** | **survives.** Stdlib header parsing, aspect preserved, short side 1024, both dimensions on a 64 step |
| **The base's CLIP layer is committed to the graph** | **survives as a flow's dial** — clip skip −2 is WAI's, and undocumented in its prose |

### `workflow-mutation` — 44 scenarios, and **L4** kills six of eight requirements

**Dial jitter is gone.** A flow's dials are settled against its publisher's own recommendations and
confirmed by measurement (F25, F26, F35, F39); jittering them does not produce a variant of the flow, it
produces an untested flow, which **L3** forbids from being selectable.

**`draw_seed` survives and `mutate` does not.** They are already separate functions in
`isekai/mutate.py` — `draw_seed` draws a sampler seed and touches no dial, which is exactly **L4**.
**The seam was built before the law that needed it.**

### Why the deletion is a replacement rather than a loss

**`main`'s shipped path is the architecture round 1 rejected.** It is img2img — the photograph seeded
into the latent at `denoise < 1` — and **F24 established that taking the photograph *out* of the latent
is what removed the blur.** Round 1's `notile-d045` was that architecture tuned and its verdict was
*"rejected — too soft… median linework 0.0030 across ten portraits, ~10x below its own inputs."*

**So this is a measured-inferior architecture being replaced by a measured-better one**, which is what
*"a version may replace it"* was written to license.

---

## 3 · What survives, and it is the expensive half

| | scenarios | why it is untouched |
|---|---:|---|
| **`comfy-transport`** | 5 | **L7 wants provider-neutrality and it is already neutral** — HTTP to a host and a port, knowing nothing about who rents the machine. Hand-built multipart, polling, retrieval |
| **`model-provisioning`** | 22 | **L20/L21/L22 are extensions of it, not replacements.** Immutable revisions, digests before trust, source fallback, a failure that leaves the pod reachable |
| **`evaluation`** | 28 | **L15/L16 modify it; nothing in it is wrong.** `Refusal`, the IoU guard, PCK, per-axis claims, pinned-and-verified models, blind pairwise labels |
| **`cli`** | 30 | **Shape B extends it.** Range validation at parse time, provenance flags, the output-directory contract |

**And four seams survive that no scenario counts:**

- **The `Protocol` + lazy-import posture** (`eval_backends`) — **L1 is named after it.**
- **The `-S` subprocess guard** (`tests/test_evaluate.py:750`) with its own falsifiability test at `:769`.
- **`FakeComfyClient`** and a suite that reads the shipped graph rather than a fixture copy — the reason
  434 tests run offline.
- **The byte-identical manifest derivation**, which **L21** generalises to one shared deriver.

---

## 4 · What moves, and what it costs

| from | to | note |
|---|---|---|
| `isekai/workflow.py`'s **header parsing** | the orchestrator or a shared module | stdlib, exact, and **already handles EXIF orientation for both codecs** — `:315` transposes on the tag |
| `isekai/mutate.py`'s **`draw_seed`** | the generation layer | **L4**; `mutate` itself is deleted |
| `prototype/tagmap.py` | **the vocabulary module** | **L23** — its lifetime tracks the vocabulary, not the model |
| `prototype/sheet.py`'s **vocabulary check** | the vocabulary module | and **soften its message**: *"not a Danbooru tag"* overclaims; the honest statement is *not in WD14's prediction set* |
| `prototype/face_likeness.py` · `same_person.py` | the evaluation layer | N-way identification and the verification test (F41, F47) |
| `prototype/joycaption.py` | a VLM implementation | pinned bytes and two sight gates |
| `prototype/router.py` + `tagmap.py` | an LLM implementation + the vocabulary | the mapper splits from the harness |
| `prototype/styles/fromnoise-v1.json` | `flows/<id>/` | one graph, two derivations — `A` is `D` plus two nodes |

---

## 5 · Four things that must change, not merely move

**1 · `pipeline.run`'s exactly-one contract.** Its provenance calls
`find_node(class_type="ApplyInstantIDAdvanced")` under an **exactly-one** contract, and **flow `D` has
deleted that node.** `prototype/ablation.py` says outright it could not use `pipeline.run` for this
reason and refused to weaken the contract for a prototype. **This is a spec edit, not a code tweak.**

**2 · The sheet format.** Today a sheet embeds its assembled prompt and `sheet.py build` regenerates it
— the footgun where editing the prompt block gets silently overwritten. **L9 makes a sheet fields-only**,
which removes the class of error structurally. **Every sheet on disk is in the old format.**

**3 · Qwen3-8B is unpinned.** `ollama pull qwen3:8b` is a moving tag, violating
`model-provisioning`'s own *"every source is pinned to an immutable revision and a digest"*, on the layer
worth **9.6x**. **The precedent is in-tree**: JoyCaption is also Ollama-hosted and *is* pinned, because
its GGUF was fetched by revision, verified by digest, and `ollama create`d from that file.
**Hosting through Ollama is not the same as resolving through Ollama.**

**4 · The living spec is restructured, 6 capabilities → ~9.** **L17**, one per layer: `cli`,
`orchestration`, `caption`, `sheet`, `review`, `image-generation`, `comfy-transport`, `evaluation`,
`model-provisioning`. This cannot be done in one version without a change that touches everything, which
is **N48's** problem and not this note's.

---

## 6 · The one question this note deliberately does not answer

**Deleting the old flow does not require the whole new pipeline to exist in the same version.** A
version could delete the old path and land the generation layer with flow `A` alone, the sheet supplied
by hand while ①②③ are still being built — **and there would then be a window where `convert.py
photo.jpg` is not end-to-end.**

**Whether that window is acceptable is a roadmap decision**, and `decisions §4 probe` is the rule that
bears on it: *keep the old thing declared until the new one is proven; the irreversible act is a
version's last, never its first.* → [`ROADMAP.md`](ROADMAP.md) (N48).
