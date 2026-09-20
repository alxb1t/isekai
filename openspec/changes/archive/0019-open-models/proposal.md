---
version: v0.19
---

## Why

**This pipeline cannot run without an Anthropic subscription, and the models that would free it have
already been measured.** JoyCaption Beta One at ① and Qwen3-8B at ② ran end to end in the v0.13
prototype, on Ollama, on the operator's own machine — `prototype/joycaption.py` and `prototype/router.py`
still hold the request bodies, the pinned sampling and the refusal text. **Nothing about the open stack
is speculative; what is missing is the wiring.**

**The seam they need was built before they existed.** `Reader` and `Sorter` are Protocols with an offline
double each. `Reading` and `Sorting` already carry `implementation`, `models` and an unused
`pinned: bool`. `output_shape(schema)` already emits the JSON Schema Ollama's `format` field takes, and
`answers_from()` already falls back to `json.loads(text)` — **which is exactly the path an Ollama
response takes**, since it returns its JSON in the body rather than in a separate field. The v0.16 flow
registry made a flow a frozen directory the manifest fully describes, so a second implementation is a
**directory plus one optional key**, not an axis through every path-building line.

**Now, because v0.20 compares the two arms and cannot compare what does not run.** The review UI shipped
the version before this one, which matters more than it looks: [evidence] shows the stages fail in one
direction only — a colour ① did not resolve cannot be recovered by ②, and ③ is the only thing that
absorbs a reader regression. **v0.19 deliberately claims nothing about which arm is better.** Its whole
goal is that the open arm runs at all, and that no path through it can reach Claude.

## What Changes

- **`flows/summon-open-v1/`** — one new flow, **five files as every tracked flow is**. `graph.json` and
  `schema.json` are **byte-identical copies** of `summon-v1`'s; `flow.json` adds one `hosted` block; both
  briefings are **authored for the open models**.
- **`scripts/joycaption.Modelfile`** — the `ollama create` recipe the reader's name refers to, committed
  because it was never in the repository and cannot be reconstructed from it. **Beside `models.json` and
  `download_models.sh`, not inside the flow**: a sixth file in a flow directory would mean editing the
  structural requirement that a flow is five flat files, to house a file nothing reads.
- **`hosted: {implementation, reader, sorter}`** — a new **optional** top-level manifest key. **Not
  `models`**, which is already required and holds twelve pinned ComfyUI render weights. `hosted` names
  what ① and ② call; `models` names what the GPU loads. **Absent means the Claude adapter — today's
  behaviour — so neither incumbent flow is edited and `manifest_version` stays `2`.**
- **`load_flow` refuses any manifest key it does not know**, naming it. The loader already refuses a
  missing key, a mismatched flow name, an absent sibling and a missing node role; an unknown key is that
  same shape. **It closes the one path by which a misspelled `hosted` block would silently run Claude.**
- **`boundary/ollama.py`** — a new transport: a module-level `HOST`, one `POST` over stdlib `urllib`, an
  injectable `Transport` protocol, and its own failure classification. **It imports nothing from
  `boundary/claude_cli.py`.**
- **`OllamaReader` in `pipeline/caption.py` and `OllamaSorter` in `pipeline/sheet.py`**, beside the Claude
  adapters and the doubles they share a Protocol with. ① sends the photograph's bytes base64 and **no
  schema**; ② sends the prose, `format`, `think: false` and a repeat penalty.
- **`wiring` becomes a resolver.** `Wiring.reader` and `Wiring.sorter` become
  `Callable[[Flow], Reader] | None`, backed by two registries keyed by the manifest's own
  `implementation` string. **An unknown key is a refusal naming what this build carries; nothing is
  constructed until a flow asks.** The resolution moves inside `cli.py`'s per-flow loop, where it was
  hoisted above it.
- **No fallback, and it is tested rather than argued.** An unreachable host, an uncreated model, an
  unknown implementation and a missing `hosted` block are **four refusals**. The suite runs the open flow
  with `claude_cli.spawn` and `require_binary` monkeypatched to raise, so any Claude path turns the test
  red rather than passing vacuously.
- **BREAKING — none.** Every existing verb, flag, artifact shape, manifest and committed digest is
  unchanged. `summon-v1` and `conjure-v1` are byte-identical.
- **Deliberately not in this version**, each with its disposal recorded: provisioning · digest
  verification · `pinned: true` · the blind-model check · seed matching across flows · decline detection
  at ② · the licence read · the comparison campaign itself · `conjure-open-v1` · briefing tuning ·
  Claude's `--model`/`--effort` · the `CliFailure` → `ModelFailure` rename. **None of the twelve blocks
  running the open flow**, which is the test each was held to.

## Capabilities

### New Capabilities

None. **Every behaviour here is an existing capability gaining a second implementation or a new refusal**,
which is the point: the seam was built for this.

### Modified Capabilities

- `caption`: the reader seam gains a second implementation, and an open flow refuses rather than
  substituting one. The absence licence is **unchanged and deliberately so** — it is what stopped a reader
  confabulating, and it applies to both arms.
- `sheet`: the sorter seam gains a second implementation, and the shape constraint the requirement already
  states is carried by a different field on a different transport.
- `image-generation`: the manifest gains one optional key and refuses keys it does not know. **The
  structural requirement that a flow is five flat files is unchanged** — which is why the `ollama create`
  recipe lives in `scripts/`.
- `cli`: the reader and sorter are resolved **per flow** rather than once per invocation, and four new
  refusals name their own remedy.

## Impact

| | |
|---|---|
| **`flows/summon-open-v1/`** | new — **five files**, as every tracked flow is. `graph.json`, `schema.json` byte-identical copies; `flow.json` + `hosted`; two authored briefings |
| **`scripts/joycaption.Modelfile`** | new — the `ollama create` recipe, recovered at build time from the operator's live model because it was never committed |
| **`isekai/boundary/ollama.py`** | new — `HOST`, `post`, `Transport`, the classification. Stdlib `urllib` only, as `comfy_client.py` already is |
| **`isekai/pipeline/caption.py`** | `+ OllamaReader`. `ClaudeReader`, `FakeReader`, `Reader`, `Reading` and `caption()` **untouched** |
| **`isekai/pipeline/sheet.py`** | `+ OllamaSorter`. `output_shape`, `answers_from`, `fill` and `sheet()` **untouched** |
| **`isekai/foundation/flow.py`** | `hosted` parsed into a `Hosted` value on `Flow`; unknown keys refused. `MANIFEST_VERSION` **stays 2** |
| **`isekai/interface/wiring.py`** | two registries; `reader`/`sorter` become `Callable[[Flow], …] \| None`, the shape `vocabulary` already has |
| **`isekai/interface/cli.py`** | the resolution moves inside the flow loop, two sites. `_seam` unchanged |
| **`tests/test_flow.py`** | one `PINNED` entry — the designed cost of adding a flow — plus the unknown-key and `hosted.implementation` assertions |
| **dependencies** | **none added.** `dependencies = []` holds, and the `-S` stdlib guard is what proves it. **The photograph is base64-encoded from its own bytes, unresized**, because PIL is in the `eval` extra and the adapter is reachable from `isekai.__main__` |
| **system dependency** | **Ollama, and the operator installs it and creates both models by hand** — the recipe is `scripts/joycaption.Modelfile`. The repository's third system dependency after `claude` and `node`, and `require_binary()` is the refusal shape it copies — applied to a port rather than a `PATH` entry |
| **not touched** | `generate.py`, `review.py`, `run.py`, `claude_cli.py`, `shared/*`, `run_view.py`, the UI, the evaluation sub-system, both incumbent flows and their committed digests — **verified by `git grep`, not assumed** |
| **money** | **one metered phase.** ①② run on localhost and cost nothing. The acceptance renders one photograph through the open flow: **one pod session, ceiling 45 minutes and ~$0.30.** Every other phase is free |
