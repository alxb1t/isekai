# Tasks — 0102 the one briefing

The config, then the flows, then the record, per [design](design.md). Paths are from the repository root.

## Progress

- [x] 1 — The config
- [ ] 2 — The flows
- [ ] 3 — The record

## 1 — The config

- [x] 1.1 Copy the briefing, per [D1](design.md#d1): `cp flows/summon-anime-wai/caption.briefing.md config/caption.briefing.md`.
  Verify: `git hash-object config/caption.briefing.md` prints `3fe95d1859f333e59745fe3e5359e0cbab7dda2c`.
- [x] 1.2 Write `config/caption.json` as [D1](design.md#d1) states.
  Verify: `uv run python -c 'import json; print(json.load(open("config/caption.json")))'` prints `{'briefing': 'caption.briefing.md', 'model': 'joycaption-beta-one-q4k'}`.
- [x] 1.3 Write `isekai/foundation/caption_config.py` per [the loader](design.md#the-loader), its module docstring
  saying what it reads and that the config is the library's, not a flow's ([D2](design.md#d2)).
  Verify: `uv run python -c 'from isekai.foundation.caption_config import load_caption_config as c; print(c().model, c().briefing_path.name)'` prints `joycaption-beta-one-q4k caption.briefing.md`.
- [x] 1.4 In `tests/test_caption.py`, add `test_the_config_is_loaded_with_the_model_and_briefing_it_names`, bound to
  `caption:selection:the-config-names-the-model`, writing its config and briefing under `tmp_path`.
  Verify: `uv run pytest tests/test_caption.py -k config_is_loaded` exits 0.
- [x] 1.5 In `tests/test_caption.py`, add `test_a_config_declaring_no_model_is_refused` and
  `test_a_config_model_that_is_not_a_non_empty_string_is_refused` over `[None, "", "   ", 3, [], {}]`, both bound to
  `caption:selection:an-absent-or-empty-model-is-refused`, each asserting the refusal names `model`.
  Verify: `uv run pytest tests/test_caption.py -k 'config_declaring or config_model'` exits 0.
- [x] 1.6 In `tests/test_caption.py`, add `test_a_config_carrying_an_unknown_key_is_refused` (`caption:selection:an-unknown-key-is-refused`)
  and `test_a_config_naming_no_briefing_beside_it_is_refused` over `["absent.md", "sub/caption.briefing.md", 3]`
  (`caption:selection:an-absent-briefing-is-refused`), each asserting the refusal names the key, the value or the file.
  Verify: `uv run pytest tests/test_caption.py -k 'config_carrying or config_naming'` exits 0.
- [x] 1.7 In `tests/test_package_paths.py`, add `caption_config.CAPTION_CONFIG_PATH` to `ANCHORS`, suffix
  `("config", "caption.json")`, id `caption_config.CAPTION_CONFIG_PATH`; in its module docstring, "a schema and a
  briefing are a flow's" → "a schema is a flow's".
  Verify: `uv run pytest tests/test_package_paths.py -k CAPTION_CONFIG_PATH` exits 0.
- [x] 1.8 In `isekai/interface/wiring.py`, per [D3](design.md#d3), `reader_for` and `hosted_tagger_for` run
  `load_caption_config().model`. Their docstrings and the comment above them name `config/caption.json` where they
  name the manifest's `model`, and `reader_for`'s says it reads nothing from `flow`, as `tagger_for`'s does.
  Verify: `grep -nF 'flow.model' isekai/interface/wiring.py` prints nothing.
- [x] 1.9 In `isekai/interface/cli.py`'s caption step, `briefing_path=flow.caption_briefing_path` →
  `briefing_path=load_caption_config().briefing_path`; in the comment above it, the sentence opening "One command
  naming two flows on two models" → "A reader that refuses refuses for this flow alone."
  Verify: `grep -n 'two flows on two models' isekai/interface/cli.py` prints nothing.
- [x] 1.10 In `isekai/interface/cli.py`, the `--flow` comment's "its briefing, its schema, its graph and its dials" →
  "its schema, its graph and its dials"; the docstring that resolves the flows, "its briefing, its schema and its
  dials" → "its schema and its dials".
  Verify: `grep -n 'its briefing' isekai/interface/cli.py` prints nothing.
- [x] 1.11 In `isekai/foundation/flow.py`, delete `Flow`'s `model: str` field, `model=named,` in `load_flow`'s
  return, the `caption_briefing_path` property, and the comment from ``# What `model` names`` through
  ``# this one**.``, both its paragraphs. `load_flow`'s model value check stays until 2.1 ([D4](design.md#d4)).
  Verify: `git grep -nE 'flow\.model|caption_briefing_path' isekai` prints nothing.
- [x] 1.12 In `isekai/pipeline/caption.py`'s module docstring, per [D8](design.md#d8): "the flow names the model it
  runs" → "`config/caption.json` names the model it runs"; "the flow's manifest declares the alias" through "gives
  each its own" → "the config declares the alias, which `interface/wiring.py` resolves for every flow".
  Verify: `grep -nE 'the flow names the model|gives each its own' isekai/pipeline/caption.py` prints nothing.
- [x] 1.13 In `isekai/pipeline/caption.py`, `caption`'s docstring: "because the briefing it was produced under is
  part of that flow's frozen directory" → "as every stage's artifact is (D17)", and its next sentence ends at "read
  it twice".
  Verify: `grep -n 'frozen directory' isekai/pipeline/caption.py` prints nothing.
- [x] 1.14 In `isekai/pipeline/tagging.py`'s module docstring, "the alias the flow's manifest names in its `model`
  key" → "the alias `config/caption.json` names".
  Verify: `grep -n 'manifest names in its' isekai/pipeline/tagging.py` prints nothing.
- [x] 1.15 In `isekai/boundary/wd14.py`'s module docstring, "the alias the flow's manifest names" through "so it
  runs for every flow" → "the alias `config/caption.json` names, for every flow"; "a string in a frozen manifest"
  through "a claim a flow makes about itself" → "a string in `config/caption.json`".
  Verify: `grep -nE 'manifest names in its|frozen manifest' isekai/boundary/wd14.py` prints nothing.
- [x] 1.16 In `tests/stages.py`, `CAPTION_BRIEFING = FLOW.caption_briefing_path` → `CAPTION_BRIEFING = load_caption_config().briefing_path`;
  in its module docstring, "A briefing is part of a flow, so `caption` and `sheet` are handed the path they read it
  from" → "`caption` is handed the path of the briefing it reads".
  Verify: `grep -n 'part of a flow' tests/stages.py` prints nothing.
- [x] 1.17 In `tests/stages.py`, the module docstring's first line, "The two stages that read a briefing, bound to
  the one tracked flow's copies." → "The stages the suite drives, bound to the one tracked flow."; `caption`'s
  docstring, "under `summon-anime-wai`'s standing instructions" → "under the caption config's standing instructions".
  Verify: `grep -nE "flow's copies|summon-anime-wai.s standing" tests/stages.py` prints nothing.
- [x] 1.18 In `tests/test_compare.py`, drop `briefing_path=load_flow(flow).caption_briefing_path,` from the `caption`
  call, `tests/stages.py`'s default taking its place; `load_flow`'s import stays, `:92` reads it.
  Verify: `grep -n 'caption_briefing_path' tests/test_compare.py` prints nothing.
- [x] 1.19 In `tests/test_flow.py`, delete `test_a_flow_declaring_a_model_is_loaded_with_it` and
  `test_the_tracked_flows_each_declare_the_model_they_are_meant_to_run`; rename the briefings test per
  [Tests](design.md#tests), dropping `flow.caption_briefing_path` from its paths.
  Verify: `grep -nE 'caption_briefing_path|image-generation:model:flow-declares' tests/test_flow.py` prints nothing.
- [x] 1.20 In `tests/test_generate.py`'s `_fewer_roles_flow`, `"model": source.model,` → `"model": "a-reader",`.
  Verify: `grep -n 'source.model' tests/test_generate.py` prints nothing.
- [x] 1.21 In `tests/test_pipeline_cli.py`, rename `_two_models` to `_flows_a_and_b`, its manifests keeping the
  source's own `model`, its docstring "Return a flows root holding `flow-a` and `flow-b`, copies of
  `summon-anime-wai`."; in `_caption_with_one_refusing`, drop `models=(flow.model,)`.
  Verify: `grep -n '_two_models' tests/test_pipeline_cli.py` prints nothing.
- [x] 1.22 In `tests/test_pipeline_cli.py`, the unreachable-model test resolves `reader_for(load_flow("summon-anime-wai"))`
  and runs `OllamaReader(model=READER, …)`; its docstring, "What a manifest can still get wrong" → "What the config
  can still get wrong"; the section heading's "the flow names the model" → "the config names the model".
  Verify: `grep -nE 'the flow names the model|What a manifest' tests/test_pipeline_cli.py` prints nothing.
- [x] 1.23 In `tests/test_pipeline_cli.py`, rename the manifest-model test per [Tests](design.md#tests), resolving
  `reader_for(load_flow("summon-anime-wai"))`: `isinstance(reader, OllamaReader)` and `reader.model == load_caption_config().model`; it and the implementation
  test above it bind `caption:selection:the-config-names-the-model`. Then delete `_flow_declaring`.
  Verify: `grep -nE '_flow_declaring|caption:selection:the-flow-names-the-model' tests/test_pipeline_cli.py` prints nothing.
- [x] 1.24 In `tests/test_pipeline_cli.py`, replace the two-models test with `test_one_command_resolves_every_flow_on_the_configured_model`,
  bound to `cli:resolution:one-command-one-model`: for each flow `_flows_a_and_b` holds, `reader_for` gives an
  `OllamaReader` whose `model` is `load_caption_config().model`.
  Verify: `grep -nE 'flow\.model|one-command-two-models' tests/test_pipeline_cli.py` prints nothing.
- [x] 1.25 In `tests/test_tagging.py`, rename the hosted-tagger tests per [Tests](design.md#tests), bound to
  `tagging:independence:the-hosted-tagger-runs-the-readers-model`, keeping their `isinstance` checks and asserting
  the tagger's model is `load_caption_config().model`; their docstrings say the config names it, not the flow.
  Verify: `grep -nE 'flow\.model|the-hosted-tagger-runs-the-flows-model' tests/test_tagging.py` prints nothing.
- [x] 1.26 In `tests/test_reader_manifest.py`, rename the flow-model test per [Tests](design.md#tests), bound to
  `model-provisioning:reader:the-caption-model-is-pinned`, asserting `load_caption_config().model` is
  `"joycaption-beta-one-q4k"` and in `reader_manifest["aliases"]`; drop the `isekai.foundation.flow` import.
  Verify: `grep -nE 'every-flow-model-is-pinned|foundation.flow import' tests/test_reader_manifest.py` prints nothing.
- [x] 1.27 In `tests/test_reader_manifest.py`'s module docstring, "A flow names its reader by an alias" →
  "`config/caption.json` names the reader by an alias".
  Verify: `grep -n 'A flow names its reader' tests/test_reader_manifest.py` prints nothing.
- [x] 1.28 In `tests/test_caption.py`, rename the flow's-own-directory test per [Tests](design.md#tests), bound to
  `caption:inputs:briefing-comes-from-the-config`: `BRIEFING_PATH.parent == FLOW.path` →
  `BRIEFING_PATH == load_caption_config().briefing_path`.
  Verify: `grep -n 'caption:inputs:briefing-comes-from-the-flow' tests/test_caption.py` prints nothing.
- [x] 1.29 In `tests/test_caption.py`, `test_the_readers_artifact_names_ollama_and_the_model_that_ran`'s marker,
  `caption:selection:the-flow-names-the-model` → `caption:selection:the-config-names-the-model`.
  Verify: `grep -n 'caption:selection:the-flow-names-the-model' tests/test_caption.py` prints nothing.
- [x] 1.30 In `tests/test_caption.py`, the second-flow test's comment, "its briefing is part of its own frozen
  directory, so it cannot inherit a reading written to answer a different question" → "written under its own flow".
  Verify: `grep -n 'frozen directory' tests/test_caption.py` prints nothing.
- [x] 1.31 In `tests/test_caption.py`, `tests/test_run_directory.py` and `tests/golden/caption.json`,
  `flows/summon-anime-wai/caption.briefing.md` → `config/caption.briefing.md`; the golden's `sha256` stays.
  Verify: `git grep -n 'flows/summon-anime-wai/caption.briefing.md' tests` prints nothing.
- [x] 1.32 In `isekai/foundation/README.md`, add a `caption_config.py` row to `## Files` and to `## Imported by` (inside: `interface/cli.py`,
  `interface/wiring.py`; outside: `tests/stages.py`, `tests/test_caption.py`, `tests/test_package_paths.py`, `tests/test_pipeline_cli.py`,
  `tests/test_reader_manifest.py`, `tests/test_tagging.py`); `refusal.py`'s importers gain it; `flow.py`'s lose `tests/test_reader_manifest.py`.
  Verify: `grep -c '^| .caption_config.py. |' isekai/foundation/README.md` prints `2`.
- [x] 1.33 In `isekai/README.md`'s table, the `foundation/` row's files gain `` · `caption_config.py` `` after `` `flow.py` ``.
  Verify: `grep -c 'caption_config.py' isekai/README.md` prints `1`.
- [x] 1.34 In `isekai/interface/wiring.py`'s `Wiring` comments, "the flow decides which implementation runs, so" through
  "false for one of them." → "a resolver per flow refuses for that flow alone, and constructs nothing until a flow asks.";
  "on the one key the reader also reads, because" through "about itself." → "on the model the reader runs, the one `config/caption.json` names."
  Verify: `grep -nE 'the flow decides which|claim the flow makes' isekai/interface/wiring.py` prints nothing.
- [x] 1.35 In `isekai/boundary/ollama.py`'s refusals at `:270` and `:354`, "this flow declares" → "`config/caption.json` names".
  Verify: `grep -n 'this flow declares' isekai/boundary/ollama.py` prints nothing.
- [x] 1.36 In `tests/fakes.py` and `tools/derive_reader.py`, "The alias every tracked flow names" → "The alias `config/caption.json` names";
  in `tests/test_resume.py`'s comment, "and a resolver because the flow names the model it runs" → "and a resolver because it is resolved per flow".
  Verify: `git grep -nE 'every tracked flow names|because the flow names the' -- tests tools` prints nothing.
- [x] 1.37 In `isekai/interface/wiring.py`'s `hosted_tagger_for` docstring, "The manifest carries no separate tagger name" through
  "says once." → "`config/caption.json` names that model once, for both."; "It is not optional. `model` is required, so there is
  no flow whose manifest leaves this unresolvable --" → "It is not optional: it resolves for every flow --".
  Verify: `grep -nE 'already says once|model. is required' isekai/interface/wiring.py` prints nothing.
- [x] 1.38 In `tests/test_tagging.py`, the parametrized hosted-tagger test's docstring → one line, "Every flow's hosted tagger
  runs the model `config/caption.json` names."; the other's first line, "on the key the reader also reads" → "on the reader's model".
  Verify: `grep -nE 'unrepresentable|on the key the reader' tests/test_tagging.py` prints nothing.
- [x] 1.39 **HALT CHECK** — a caption written under `config/caption.briefing.md` equals the golden byte for byte: the
  briefing's bytes, and so the prompt, did not move.
  Verify: `uv run pytest tests/test_artifact_bytes.py -k caption` exits 0.

## 2 — The flows

- [ ] 2.1 In `isekai/foundation/flow.py`, per [D4](design.md#d4): `MANIFEST_VERSION = 4` → `MANIFEST_VERSION = 5`;
  delete `"model",` from `REQUIRED` and `load_flow`'s model value check, from `# The value, not only its presence.`
  through its `raise Refusal`; above `KNOWN`, delete the sentence opening "The model `model` names".
  Verify: `grep -n '"model"' isekai/foundation/flow.py` prints nothing.
- [ ] 2.2 In `isekai/foundation/flow.py`, the misspelling examples: "`modl` is caught" → "`taggr` is caught", and
  "names `model` -- a key the operator did not misspell --" → "names `tagger` -- not the key the operator wrote --".
  Verify: `grep -n 'modl' isekai/foundation/flow.py` prints nothing.
- [ ] 2.3 In `isekai/foundation/flow.py`, delete `CAPTION_BRIEFING_NAME`, and `SIBLINGS = (GRAPH_NAME, SCHEMA_NAME)`.
  Verify: `grep -n 'CAPTION_BRIEFING_NAME' isekai/foundation/flow.py` prints nothing.
- [ ] 2.4 In `isekai/foundation/flow.py`, per [D8](design.md#d8): "the graph, the schema or the briefing" → "the graph
  or the schema"; "the schema and the briefing outside" → "the schema outside"; "the briefing decides the caption,
  the caption decides the sheet" → "the schema decides the sheet"; " and in the briefing that names it" → deleted.
  Verify: `grep -ni 'briefing' isekai/foundation/flow.py` prints nothing.
- [ ] 2.5 In each `flows/<id>/flow.json`, `"manifest_version": 4,` → `"manifest_version": 5,`, and delete the line
  `"model": "joycaption-beta-one-q4k",`.
  Verify: `git grep -nE '"model": "|"manifest_version": 4' flows` prints nothing.
- [ ] 2.6 `git rm flows/conjure-anime-wai/caption.briefing.md flows/control-anime-wai/caption.briefing.md
  flows/summon-anime-wai/caption.briefing.md flows/summon-flat-anime-wai/caption.briefing.md
  flows/summon-semireal-anime-wai/caption.briefing.md flows/summon-vivid-anime-wai/caption.briefing.md`.
  Verify: `git ls-files -- 'flows/*/caption.briefing.md'` prints nothing.
- [ ] 2.7 In `tests/test_flow.py`, drop `CAPTION_BRIEFING_NAME`'s import; `len(SIBLINGS) == 3` →
  `len(SIBLINGS) == 2` and `(GRAPH_NAME, SCHEMA_NAME, CAPTION_BRIEFING_NAME)` → `(GRAPH_NAME, SCHEMA_NAME)`; rename the
  control's files test per [Tests](design.md#tests), deleting its `CAPTION_BRIEFING_NAME` assertion.
  Verify: `grep -n 'CAPTION_BRIEFING_NAME' tests/test_flow.py` prints nothing.
- [ ] 2.8 In `tests/test_flow.py`, rename `_holds_the_subjects_schema_and_briefing` and the flat and look tests that
  call it per [Tests](design.md#tests); the new-file test's comment, "the schema and the briefing inside the flow" →
  "the schema inside the flow".
  Verify: `grep -nE 'schema_and_briefing|schema and the briefing' tests/test_flow.py` prints nothing.
- [ ] 2.9 In `tests/test_flow.py`, delete the no-model, the not-a-non-empty-string and the `models` collision tests
  named in [Tests](design.md#tests); in `test_every_key_this_build_reads_is_required`, `MANIFEST_VERSION == 4` →
  `MANIFEST_VERSION == 5` and `"model" in REQUIRED` → `"model" not in REQUIRED`.
  Verify: `grep -nE 'image-generation:model:|collides_with_a_real_key' tests/test_flow.py` prints nothing.
- [ ] 2.10 In `tests/test_flow.py`, `_misspelled` pops `"tagger"` and its docstring says "whose tagger key"; rename the
  misspelled test per [Tests](design.md#tests), over `["taggr", "Tagger", "tagger_on"]`, bound to
  `image-generation:manifest:a-misspelled-key-is-refused`; the heading `the model key, and the allowlist` → `the allowlist`.
  Verify: `grep -nE 'a-misspelled-model-key-is-refused|whose model key' tests/test_flow.py` prints nothing.
- [ ] 2.11 In `tests/test_generate.py`'s `_fewer_roles_flow`, delete `"model": "a-reader",` and the comment above it,
  and copy `SCHEMA_NAME` alone in place of the loop over `(SCHEMA_NAME, CAPTION_BRIEFING_NAME)`; drop that import.
  Verify: `grep -n 'CAPTION_BRIEFING_NAME' tests/test_generate.py` prints nothing.
- [ ] 2.12 Re-pin each flow in `tests/test_flow.py`'s `PINNED`, per [D5](design.md#d5), to the digest
  `uv run python -c 'from isekai.foundation.flow import manifest_digest as d, tracked_flows as t; [print(f, d(f)) for f in t()]'`
  prints for it; `test_a_re_pin_leaves_a_record_a_later_reader_can_find` passes once the phase's CHANGELOG entry names each.
  Verify: `uv run pytest tests/test_flow.py -k 'not a_re_pin_leaves_a_record'` exits 0.
- [ ] 2.13 In `tests/golden/prompt.json`, `tests/golden/render.json`, `tests/golden/sheet.json` and
  `tests/golden/sheet-empty.json`, `"flow_digest"`'s value → `summon-anime-wai`'s new digest from 2.12.
  Verify: `git grep -n 96c605821e68a8ac2f1c7a60807cfcfb4c3658ae4112cc84d21a00bf39f3e698 tests` prints nothing.
- [ ] 2.14 **HALT CHECK** — every golden is written byte for byte with only the flow digest moved.
  Verify: `uv run pytest tests/test_artifact_bytes.py` exits 0.

## 3 — The record

- [ ] 3.1 In `docs/decisions.md`, per [D6](design.md#d6): D14's bold line, "`schema.json`, `caption.briefing.md` — and
  it shares nothing" → "`schema.json` — and it shares nothing"; D14's `Made by:` gains `` `0102` ``.
  Verify: `grep -n 'caption.briefing.md' docs/decisions.md` prints nothing.
- [ ] 3.2 In `docs/decisions.md`, D6's bold line, "and the model a flow names is checked against" → "and the model
  `config/caption.json` names is checked against"; D6's `Made by:` gains `` `0102` ``.
  Verify: `grep -n 'the model a flow' docs/decisions.md` prints nothing.
- [ ] 3.3 In `README.md`'s banner, "The flow's manifest names the one model it runs, in a required `model` key, and
  every tracked flow names the same one." → "`config/caption.json` names the one model it runs, for every flow.";
  "the flow names it and nothing verifies" → "`config/caption.json` names it and nothing verifies".
  Verify: `grep -n 'required .model. key' README.md` prints nothing.
- [ ] 3.4 In `README.md`, "the flow supplies the briefing it reads and the schema it fills against" → "the flow
  supplies the schema it fills against"; "the flow is what supplies its briefing, its schema, its graph and its
  dials" → "the flow is what supplies its schema, its graph and its dials".
  Verify: `grep -nE 'supplies (its|the) briefing' README.md` prints nothing.
- [ ] 3.5 In `README.md`'s tree, `flow.json`'s comment loses "model, "; delete the `caption.briefing.md` line under
  `flows/summon-anime-wai/`, `schema.json` taking `└──`; under `config/`, above `joycaption.Modelfile`, add `caption.json`
  ("the reader's model and its briefing") and `caption.briefing.md` ("the standing instructions every photograph is read under").
  Verify: `grep -n 'inputs, vocabulary, model, tagger' README.md` prints nothing.
- [ ] 3.6 In `docs/data-flow.md`, "supplies the briefing a stage reads, the schema it fills against" → "supplies the
  schema a stage fills against"; in `isekai/pipeline/README.md`, "supplies the briefing it reads, the schema it fills
  against" → "supplies the schema it fills against".
  Verify: `git grep -n 'supplies the briefing' docs isekai` prints nothing.
- [ ] 3.7 In `docs/pins.md`'s table, below the reader's files row, add `| the caption briefing | git, and its sha256 in every caption |
  `config/caption.briefing.md` | the gate: `tests/golden/caption.json` holds its sha256 |`.
  Verify: `grep -c 'config/caption.briefing.md' docs/pins.md` prints `1`.
- [ ] 3.8 **HALT CHECK** — the delta validates against the specs as this phase leaves them.
  Verify: `openspec validate 0102-the-one-briefing --strict` exits 0.
