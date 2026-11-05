# Design — 0102 the one briefing

The briefing and the model move from each flow to `config/caption.json`, read by a loader in `isekai/foundation/`;
then the flows drop them and are re-pinned, format only. **Verdict: feasible.**

## Context

Each `flows/*/caption.briefing.md` is the blob `3fe95d18`, and each `flows/*/flow.json` declares
`"model": "joycaption-beta-one-q4k"`. `isekai/foundation/flow.py` holds the briefing as a sibling
(`CAPTION_BRIEFING_NAME`, `SIBLINGS`, `Flow.caption_briefing_path`) and the model as a required key (`REQUIRED`,
`Flow.model`, the value check in `load_flow`). `isekai/interface/wiring.py`'s `reader_for` and `hosted_tagger_for`
build from `flow.model`; `isekai/interface/cli.py`'s caption step passes `flow.caption_briefing_path`.

A caption records its briefing as `{path, sha256}` (`instructions_record`, `isekai/foundation/run.py:809`). Nothing
reads the path back: `isekai/interface/run_view.py:122-126` prints the sha, caption resume asks only whether a
caption exists (`isekai/pipeline/caption.py:254-256`), and `artifacts.read` checks only the kind and version. So a
caption written under `config/caption.briefing.md` records a new path and the same sha256, and old captions read as
before.

`config/image.json` pins `isekai/boundary/provision.py` by digest (`tests/test_infra.py:290-294`), so a loader there
is an image rebuild. `config/reader.json` is not in that record; it stays untouched all the same.

## Goals / Non-Goals

**Goals:** one briefing and one model for the library, in `config/`; a flow that is `flow.json`, `graph.json` and
`schema.json`; the same briefing bytes and the same prompt; every flow re-pinned, format only.

**Non-Goals:** a caption the flows share; any edit to `provision.py`, `config/reader.json` or the `Dockerfile`; a new
decision in `docs/decisions.md`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `config/caption.briefing.md` is `flows/summon-anime-wai/caption.briefing.md` copied byte for byte. `config/caption.json` is `{"briefing": "caption.briefing.md", "model": "joycaption-beta-one-q4k"}`, two-space indented, ending in a newline. `briefing` names a file beside `config/caption.json` | the same bytes give the same sha256 and the same prompt, so `tests/golden/caption.json` moves its path only | a briefing path from the repository root: a second spelling of one file |
| <a id="d2"></a>**D2** | A new module, `isekai/foundation/caption_config.py`, stdlib and `refusal.py` only, per [the loader](#the-loader) | the brief settles it in `foundation/`; `flow.py` reads a flow, and this is not one | a loader in `provision.py`: the pod image pins it; a function in `flow.py`: it keeps the briefing a flow's concern |
| <a id="d3"></a>**D3** | `reader_for(flow)` and `hosted_tagger_for(flow)` keep their `Flow` parameter and read nothing from it, as `tagger_for` already does; each runs `load_caption_config().model`. The caption step passes `briefing_path=load_caption_config().briefing_path`. Seams stay resolved per flow | a seam resolved per flow refuses for that flow alone (`cli:flow-selection:one-flows-refusal-leaves-the-others`), and every test double keeps its `lambda flow:` shape | a seam with no parameter: it changes every double and buys nothing |
| <a id="d4"></a>**D4** | `MANIFEST_VERSION` is 5. `REQUIRED`, and so `KNOWN`, lose `"model"`, and `load_flow`'s model value check goes. `SIBLINGS` is `(GRAPH_NAME, SCHEMA_NAME)`, and `CAPTION_BRIEFING_NAME` goes. Each `flow.json` declares `"manifest_version": 5` and no `"model"`; each `flows/*/caption.briefing.md` is deleted. Phase 1 drops `Flow.model` and `caption_briefing_path` while `load_flow` still checks `model`, so for one phase the key is checked and read by nothing | a format move is what the equality check exists for: a version 4 manifest is refused naming both versions. The order is the brief's: the config first, the re-pin last | `model` kept optional: `KNOWN == REQUIRED` rules out an optional key |
| <a id="d5"></a>**D5** | Every flow is re-pinned in place, format only: each new digest from `manifest_digest` into `PINNED`, and phase 2's CHANGELOG entry a bullet per flow naming its new digest. `summon-anime-wai`'s digest moves in the goldens that record it: `tests/golden/prompt.json`, `render.json`, `sheet.json`, `sheet-empty.json` | the freeze's price: `test_a_re_pin_leaves_a_record_a_later_reader_can_find` fails on a digest no entry carries, and `tests/test_changelog.py`'s `BULLET_LIMIT` keeps a bullet to 300 characters, so a bullet per flow, as `0090`'s was | a new identifier per flow: nothing a flow renders changes |
| <a id="d6"></a>**D6** | `docs/decisions.md`: D14's bold line loses `` `caption.briefing.md` ``; D6's bold line says "the model `config/caption.json` names" for "the model a flow names". Each `Made by:` gains `` `0102` `` | a decision in force is edited where it lives (`A7`); no new choice is made | a new decision for the config: D6 already decides how the model is checked |
| <a id="d7"></a>**D7** | A requirement whose scenario title changes is REMOVED and ADDED under a new title, per [the key moves](#the-key-moves) | `openspec validate --strict` refuses a MODIFIED block that "omits scenario(s) the current spec still has", and archive refuses to drop them; probed on a scratch copy of `openspec/` at `7fdbad24` | a stale scenario title kept to satisfy the validator |
| <a id="d8"></a>**D8** | A comment, docstring or refusal text that says a flow holds the briefing or names the model is rewritten in the phase that makes it false, each named in a task | a comment states what holds, in the present tense | one sweep at the end: phases 1 and 2 would commit false comments |

**D8's exceptions.** `isekai/boundary/provision.py:42`'s comment, "keyed by the alias a flow names", stays: the pod image pins that file by digest, so an edit is a rebuild. `load_flow`'s model refusal text, "a flow names the one model its reader and its hosted tagger run", stands through phase 1 and goes with the check in 2.1, per [D4](#d4).

### The loader

```python
CAPTION_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "caption.json"
)


@dataclass(frozen=True)
class CaptionConfig:
    model: str
    briefing_path: Path


def load_caption_config(path: Path = CAPTION_CONFIG_PATH) -> CaptionConfig: ...
```

It reads the JSON object and refuses with `Refusal`, in this order, each message naming `caption.json`:

```
a key other than briefing and model  ─▶ names the key, and the keys it reads
briefing or model absent             ─▶ names the key
model not a non-empty string         ─▶ names `model` and the value's repr; never str() it
briefing not a string, not a bare
  file name, or no file beside it    ─▶ names the value or the file
```

`briefing_path` is `path.parent / briefing`. `CAPTION_CONFIG_PATH` is anchored on the module's own `__file__`, so
`tests/test_package_paths.py`'s `ANCHORS` gains it.

### The key moves

| capability | old key | new key | test |
|---|---|---|---|
| `caption` | `caption:inputs:briefing-comes-from-the-flow` | `caption:inputs:briefing-comes-from-the-config` | `tests/test_caption.py` |
| `caption` | `caption:selection:the-flow-names-the-model` | `caption:selection:the-config-names-the-model` | `tests/test_pipeline_cli.py`; `tests/test_caption.py`, the loader test and `test_the_readers_artifact_names_ollama_and_the_model_that_ran` |
| `caption` | — | `caption:selection:an-absent-or-empty-model-is-refused`, `caption:selection:an-unknown-key-is-refused`, `caption:selection:an-absent-briefing-is-refused` | `tests/test_caption.py`, the briefing test over an absent file, a path and a non-string |
| `image-generation` | `image-generation:model:flow-declares-the-model-it-runs`, `image-generation:model:an-absent-model-is-refused`, `image-generation:model:an-empty-model-is-refused` | removed | — |
| `image-generation` | `image-generation:manifest:a-misspelled-model-key-is-refused` | `image-generation:manifest:a-misspelled-key-is-refused` | `tests/test_flow.py` |
| `cli` | `cli:resolution:one-command-two-models` | `cli:resolution:one-command-one-model` | `tests/test_pipeline_cli.py` |
| `tagging` | `tagging:independence:the-hosted-tagger-runs-the-flows-model` | `tagging:independence:the-hosted-tagger-runs-the-readers-model` | `tests/test_tagging.py` |
| `model-provisioning` | `model-provisioning:reader:every-flow-model-is-pinned` | `model-provisioning:reader:the-caption-model-is-pinned` | `tests/test_reader_manifest.py` |

`tests/test_spec_bindings.py` lets a marker name a living key or one an open delta adds (`nameable`), and demands no
key a delta removes, so each test re-binds in the phase that edits it.

## Tests

| layer | adds | removes |
|---|---|---|
| unit | `tests/test_caption.py`: the loader's tests, one for what it loads and one per refusal; `tests/test_package_paths.py`: one `ANCHORS` row | `tests/test_flow.py`: the model-key tests, and the rows `REQUIRED` and `SIBLINGS` no longer parametrise; `tests/test_pipeline_cli.py`: the two-models test, replaced |
| end-to-end | none | none |

Counted with `uv run pytest <file> --collect-only -q | tail -1` at `7fdbad24`, and as planned:

| file | at `7fdbad24` | planned |
|---|---|---|
| `tests/test_flow.py` | 112 | 99 |
| `tests/test_caption.py` | 41 | 53 |
| `tests/test_package_paths.py` | 12 | 13 |
| `tests/test_pipeline_cli.py` | 60 | 60 |
| the suite, `uv run pytest --ignore=tests/e2e --collect-only -q` | 1481 | 1481 |
| `tests/e2e`, `uv run pytest tests/e2e --collect-only -q` | 19 | 19 |

**Deleted or merged**, each mapped to the test that carries its assertion (`I16`):

| test | carried by |
|---|---|
| `tests/test_flow.py::test_a_flow_declaring_a_model_is_loaded_with_it` | `tests/test_caption.py::test_the_config_is_loaded_with_the_model_and_briefing_it_names`, `caption:selection:the-config-names-the-model` |
| `tests/test_flow.py::test_the_tracked_flows_each_declare_the_model_they_are_meant_to_run` | `tests/test_reader_manifest.py::test_the_model_the_caption_config_names_is_pinned`, which asserts `joycaption-beta-one-q4k` |
| `tests/test_flow.py::test_a_manifest_declaring_no_model_is_refused_naming_the_key` | `tests/test_caption.py::test_a_config_declaring_no_model_is_refused`, `caption:selection:an-absent-or-empty-model-is-refused` |
| `tests/test_flow.py::test_a_model_that_is_not_a_non_empty_string_is_refused`, every row | `tests/test_caption.py::test_a_config_model_that_is_not_a_non_empty_string_is_refused`, over the same values |
| `tests/test_flow.py::test_a_typo_that_collides_with_a_real_key_is_refused_for_the_absence` | `tests/test_flow.py::test_a_manifest_missing_a_declared_field_is_refused_naming_it`, `image-generation:manifest:invalid-manifest-names-the-field`: with no `model` key, `models` collides with nothing |
| `tests/test_flow.py::test_a_manifest_missing_a_declared_field_is_refused_naming_it[model]` | retired by [D4](#d4): `model` is not a key |
| `tests/test_flow.py::test_a_flow_missing_one_of_its_named_files_is_refused_naming_it[caption.briefing.md]` and `::test_editing_any_of_its_named_files_changes_the_digest[caption.briefing.md]` | retired by [D4](#d4): the briefing is not a flow's file; `tests/golden/caption.json`'s sha256 holds its bytes |
| `tests/test_pipeline_cli.py::test_one_command_over_two_flows_writes_two_artifacts_each_naming_its_own` | `tests/test_pipeline_cli.py::test_one_command_resolves_every_flow_on_the_configured_model`, `cli:resolution:one-command-one-model` |

**Rewritten in place**, same scenario, new name:

| file | before | after |
|---|---|---|
| `tests/test_caption.py` | `test_the_standing_instructions_come_from_the_flows_own_directory` | `test_the_standing_instructions_come_from_the_caption_config` |
| `tests/test_pipeline_cli.py` | `test_a_flow_resolves_to_a_reader_running_the_model_its_manifest_names` | `test_a_flow_resolves_to_a_reader_running_the_configured_model` |
| `tests/test_tagging.py` | `test_the_hosted_tagger_runs_the_model_the_flow_names` | `test_the_hosted_tagger_runs_the_configured_model` |
| `tests/test_tagging.py` | `test_each_flow_gets_a_hosted_tagger_on_the_model_its_own_reader_runs` | `test_each_flow_gets_a_hosted_tagger_on_its_readers_model` |
| `tests/test_reader_manifest.py` | `test_every_model_a_tracked_flow_declares_is_pinned` | `test_the_model_the_caption_config_names_is_pinned` |
| `tests/test_flow.py` | `test_a_misspelled_model_key_is_refused_naming_what_was_written` | `test_a_misspelled_key_is_refused_naming_what_was_written` |
| `tests/test_flow.py` | `test_the_schema_briefings_and_graph_each_flow_needs_are_in_its_directory` | `test_the_schema_and_graph_each_flow_needs_are_in_its_directory` |
| `tests/test_flow.py` | `test_a_control_holds_the_subjects_graph_schema_and_briefing` | `test_a_control_holds_the_subjects_graph_and_schema` |
| `tests/test_flow.py` | `_holds_the_subjects_schema_and_briefing` | `_holds_the_subjects_schema` |
| `tests/test_flow.py` | `test_a_flat_flow_holds_the_subjects_schema_and_briefing` | `test_a_flat_flow_holds_the_subjects_schema` |
| `tests/test_flow.py` | `test_a_look_holds_the_subjects_schema_and_briefing` | `test_a_look_holds_the_subjects_schema` |

## Moved since the brief

The brief cites `22291a5f`; every fact was re-checked at `7fdbad24`, after `0097`, `0098` and `0099` were released.
The code, test and spec facts stand. These moved, and the plan carries the value at `7fdbad24`:

- The flows' digests in `CHANGELOG.md` sit at `:107`, `:109`, `:116`, `:884`, `:1163`, `:1210`; the format-only
  re-pin precedent is at `:1209`.
- `provision.py`'s image pin is checked at `tests/test_infra.py:290-294`; `config/reader.json` is not in
  `config/image.json`'s record.
- `docs/decisions.md` gained D48 and an amended D36, below D14 and D6, whose lines stand. `0097` and `0098` are
  released, so no open version shares that file with this one.

## Dependencies

None.

## Risks / Trade-offs

- **A digest no CHANGELOG bullet carries fails `test_a_re_pin_leaves_a_record_a_later_reader_can_find`** → phase 2's
  entry names each new digest; sub-task 2.12's check sets that test aside until the entry is written, as `0090`'s
  re-pin did.
- **The goldens record `summon-anime-wai`'s flow digest** → sub-task 2.13 moves it, and 2.14's HALT CHECK holds
  every other byte.
- **The briefing leaves the freeze, so an edit to it moves no flow digest** → every caption records the briefing's
  sha256, and `tests/golden/caption.json` holds the committed bytes' digest, so an edit still fails the gate.
- **A caption's recorded briefing path changes** → nothing reads it back; the sha256 is unchanged.
- **For phase 1, `load_flow` checks a `model` nothing reads** → phase 2 deletes the key and the check together.

## Migration Plan

A flow directory of manifest version 4 is refused by this build, naming both versions. Old runs need nothing: their
captions read as before, and a new caption records `config/caption.briefing.md`.

## Verdict

**feasible.** Every file and symbol named exists at `7fdbad24`; the facts that moved are carried above, and none
changes a settled decision.
