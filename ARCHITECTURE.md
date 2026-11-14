# Architecture

A way into `docs/`, which is the one source: this page names the parts, and the links hold them. A photograph
of a person goes in and an anime image of that same person comes out, on open models and a rented GPU, one
staged verb at a time. [`docs/README.md`](docs/README.md) draws it.

## Layers

Imports point down; `tests/test_layers.py` holds that. [`docs/modules.md`](docs/modules.md) has the graph.

- **`interface`** — the CLI and the review UI; they compose. The CLI's verbs live in `interface/verbs/`, one row each.
- **`pipeline`** — the stages.
- **`boundary`** — every way to a model, the GPU or the network.
- **`shared`** — what the stages share: the vocabulary, the field map, image headers, and the placement's maths:
  the ink, the tattoo, the chain and the proposal's geometry.
- **`foundation`** — the run directory, the flow and the refusal, and what rides with them: the artifacts'
  contract, the edit registry, the caption config, the migration and the command text a refusal prints.

Evaluation is a separate sub-system beside the code it measures.

## Boundaries

- **The run directory** — the channel between stages: [`docs/data-flow.md`](docs/data-flow.md).
- **This machine and the pod** — a photograph crosses to be rendered, through `isekai render`, gpunit and an SSH
  tunnel: [D34](docs/decisions.md#d34--renders-stay-on-a-pod), [D36](docs/decisions.md#d36--a-render-session-is-isekai-render).
- **The local models** — JoyCaption through Ollama and WD14, both on this machine: [D5](docs/decisions.md#d5--one-arm),
  [D6](docs/decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model).
- **The browser and the UI** — the UI serves the loopback address and checks each request:
  [D24](docs/decisions.md#d24--the-review-ui-serves-only-this-machine).
- **The repository and a run** — a run holds a photograph, so it stays under an ignored root:
  [D18](docs/decisions.md#d18--runs-stay-out-of-what-git-tracks).

## Read next

| file | answers |
|---|---|
| [`docs/principles.md`](docs/principles.md) | the rules every component follows |
| [`docs/decisions.md`](docs/decisions.md) | the choices in force, and why |
| [`docs/modules.md`](docs/modules.md) | the layers, and which module imports which |
| [`docs/data-flow.md`](docs/data-flow.md) | the verbs, the stages, the run directory |
| [`docs/pins.md`](docs/pins.md) | what each pin buys, where it is declared, and how it is moved |
