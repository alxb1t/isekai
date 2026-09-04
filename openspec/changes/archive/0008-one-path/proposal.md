---
version: v0.8
---

# Delete everything that is not the product

## Why

isekai renders a photo of a person as an anime image of **that same person**. Four selectable
model paths, two checkpoint families and a required `--prompt` flag are not that product — they
are the record of how the product was found. Three of the four paths exist only as history:
`qwen` preserves identity by instruction-edit, `animagine` renders from noise, `animagine-i2i`
drops the ControlNet stack. Every one of them is superseded by `animagine-i2i-cn`, and each one
still costs a workflow JSON, a fixture, a registry entry, a set of spec scenarios and a branch
in code that the surviving path never takes.

The `--prompt` flag is worse than redundant: it makes the single highest-leverage input to a
Danbooru-trained base a thing a human types differently every run. Identity is four axes — face,
hair, clothes, pose — and today the face rides on InstantID, the pose on OpenPose, and hair and
clothes ride on whatever was typed. A version that cannot say what prompt produced a render
cannot make a claim about identity at all.

Now, because the **next** version swaps the checkpoint. Every path, fixture, spec key and
workflow filename that survives into v0.9 is relocked against the new base. Deleting the three
dead paths afterwards means renaming and relocking them first, for nothing.

## What Changes

- **BREAKING** — `--model`, `--workflow` and `--prompt` are **removed**. `--prompt` was required;
  every existing invocation breaks. The whole required surface becomes
  `convert.py photo.jpg -o ./outputs`.
- **BREAKING** — `-o` changes meaning from an **output file** to an **output directory**.
  A run writes `<output-dir>/<UTC-timestamp>/0.png` … `4.png` plus a `run.json`. An `-o` naming
  an image file is rejected at parse time, so the old form fails loudly instead of creating a
  directory called `out.png`.
- The `qwen`, `animagine` and `animagine-i2i` paths are deleted — code, workflow JSON, fixtures,
  spec scenarios, and their entries in `scripts/download_models.sh`.
- The survivor is **renamed to nothing**: `workflows/pipeline.json`, `workflows/pipeline_ui.json`,
  `inject()`, and spec keys with no model segment. The next version replaces the base; a name
  that describes the base would be renamed twice.
- The **model registry is retired**. With one path there is no name to resolve, no injector to
  pair and no mutator to attach. `isekai/models.py` is deleted and the `model-registry`
  capability is removed from the living spec.
- The positive prompt becomes **graph configuration**, in the same category as `steps` and `cfg`.
  Its one piece of typed subject text — the pose tag `arms crossed`, which fights the OpenPose
  ControlNet that owns that axis — is removed. The rest of the string is committed and pinned by
  a test.
- `--variations` defaults to **5** and is capped at 25. Every variation's seed is derived
  uniformly from `--seed`; variation 0 loses its verbatim-seed exemption, whose only reason was
  back-compat with releases this change deletes.
- **Added:** timestamped run directories, and a `run.json` recording the seed, the five derived
  seeds and the dial values — so a run describes itself instead of depending on terminal
  scrollback.
- The spend rule in `CLAUDE.md` is rewritten: a metered phase no longer needs an explicit human
  "go"; teardown confirmed through the RunPod MCP replaces it, with a stated fallback and a
  stated ceiling.
- One **metered** phase closes the change: a live smoke test on a pod, one photo in, five renders
  out. It proves the path *runs*. It makes no claim about what it rendered.

## Capabilities

### New Capabilities

None. This change removes capability and narrows what remains.

### Modified Capabilities

- `model-registry`: **retired in full.** Every requirement is removed — name resolution, injector
  pairing and mutation pairing all describe a choice that no longer exists. The living spec goes
  from five capabilities to four.
- `cli`: model selection removed entirely; the prompt and workflow-override flags removed; the
  output flag becomes a directory with an extension guard; the variation count gains a default of
  five and a ceiling; the refusal of variations on a model with no mutator is removed with the
  models it protected.
- `workflow-injection`: prompt placement removed as a behaviour — the positive conditioning path
  is graph-committed, so there is nothing to place. Qwen-specific node-location and photo-wiring
  scenarios removed. What remains is photo wiring and unambiguous node location on one graph.
- `workflow-mutation`: the no-mutator, no-ControlNet-nodes, wired-dial and no-identity-node
  scenarios are removed — each described a graph this change deletes. Reproducibility gains
  uniform seed derivation and the run manifest.

`comfy-transport` is untouched: the network boundary does not know how many paths exist.

## Impact

- **Deleted:** `isekai/models.py`, `tests/test_model_dispatch.py`, `tests/fixtures/`,
  `workflows/qwen-image-edit.json`, `workflows/qwen-image-edit.reference.json`,
  `workflows/animagine-instantid.json`, `workflows/animagine-i2i.json`,
  `openspec/specs/model-registry/`.
- **Renamed:** `workflows/animagine-i2i-cn.json` → `workflows/pipeline.json`;
  `workflows/animagine-i2i-cn_ui.json` → `workflows/pipeline_ui.json`;
  `inject_animagine` → `inject`.
- **Signature change:** `pipeline.run` loses its `inject`, `prompt` and `mutate` parameters and
  gains an output directory. `Injector` and `Mutator` disappear from `isekai/comfy_types.py`.
- **Dead branches removed:** `overrides.py`'s no-identity-node path, `mutate.py`'s wired-dial
  guard and subgraph-id ordering, `find_node`'s unused `title` parameter, and
  `tests/test_variations.py`'s v0.4 byte-identity assertion.
- **Docs:** `README.md` (model table, quickstart, status line) and `CLAUDE.md` (the additive-models
  invariant, the registry seam, the model list, the spend rule) both become false and are
  rewritten.
- **Dependencies:** none added. The runtime stays stdlib-only.
- **Cost:** the build is $0 and entirely local. One phase is metered — a single pod session,
  capped at 45 minutes and roughly $0.30.
