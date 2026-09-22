# Tasks — 0022 one arm

## Progress

- [x] 1 — The split: five names to `foundation/run.py`, the arm still working
- [x] 2 — The flow set, the loader and the arm, together
- [ ] 3 — The documents and the spec delta
- [ ] 4 — ⚠️ **HUMAN · METERED** — the acceptance, both flows, the same photographs

## The per-phase ritual

1. **Run each sub-task's stated verification — run it, never summarize it. Paste real output.**
2. **Gate green before the commit** — `make gate`, the commands in `.minions/minions.toml`'s `gate` array,
   in order. **Never weaken the gate to pass**; halt and say so.
3. A `CHANGELOG.md` entry under `## [Unreleased]`, appended in that phase's own commit.
4. The phase's box ticked in `## Progress` above, in that phase's own commit.
5. **One commit per phase**, staged **by name**, carrying `Change: 0022-one-arm` contiguous with the
   `Co-Authored-By:` line.
6. **Every new test carries a binding** — `@pytest.mark.spec("<key>")` naming the scenario it proves, or
   `@pytest.mark.spec_exempt("<reason>")` if it is genuinely structural.

**`design.md` is authoritative.** Where the tree disagrees with a decision it settled, that is a halt and
a finding, never a quiet divergence.

**Line numbers below were resolved against `main` `44e5a2d`.** Phase 1 moves many of them; re-resolve by
symbol name rather than trusting a number from an earlier phase.

**⛔ Metered cost is ZERO on phases 1, 2 and 3.** No pod, no `generate`, no `infra/up.sh`. A pod in any
of them is a halt.

---

## 1 — The split: five names to `foundation/run.py`, the arm still working

**The arm still works at the end of this phase.** Nothing is deleted except `briefing_text` and `ROOT`;
the rest is a move and a rename. `design.md` D12–D15.

- [x] 1.1 **Move four names from `isekai/boundary/claude_cli.py` into `isekai/foundation/run.py`**, with
  their docstrings carried verbatim:

  | name | at | note |
  |---|---|---|
  | `CliFailure` | `claude_cli.py:91-101` | **renamed `StageFailure`** (D13). Its `Kind` import is already local — `run.py:124` defines `Kind`. |
  | `refusal_for` | `:148-166` | **signature widened** (D14), see 1.2 |
  | `instructions_record` | `:259-272` | reads `ROOT` — repoint at `DATA_ROOT.parent` (D12) |
  | `constant_record` | `:275-291` | no change to the body |

  `run.py` already imports `hashlib` (`:32`), `Path` (`:38`) and `Refusal` (`:41`), so **no new import is
  needed**. Append all four at the **end of the module**, after `check_budget` (`:511`) — not between
  `record_failure` (`:485-510`) and `check_budget`, which would split the failure-recording group that
  reads as one unit.

  **Do not create `foundation/refusal.py` entries for these.** That module's first line is *"The one
  refusal exception, in a module that imports nothing"*, and `run.py:41` already imports it — a cycle.

- [x] 1.2 **Widen `refusal_for`** from `(stage, run_id, failed: CliFailure, record, where, verb)` to
  `(stage, run_id, kind: Kind, detail: str, record, where, verb)`. It reads exactly two attributes today,
  both at `claude_cli.py:163`. Update all three call sites:

  | site | today | becomes |
  |---|---|---|
  | `isekai/pipeline/caption.py:269-271` | `refusal_for("reader", run.id, failed, …)` | `…, failed.kind, failed.detail, …` |
  | `isekai/pipeline/tagging.py:268-275` | fabricates `CliFailure("permanent", str(failed))` at `:271` | `"permanent", str(failed)` — **delete the fabrication**; the same two values are already literal at `:265-266` |
  | `isekai/pipeline/tagging.py:332-334` | `refusal_for("tagger", run.id, failed, …)` | `…, failed.kind, failed.detail, …` |

  After this, `caption_wd14` (`tagging.py:211-291`) holds **no** `StageFailure` reference at all.

- [x] 1.3 **Inline and delete `briefing_text`** (`claude_cli.py:143-145`). Its one caller anywhere,
  including tests, is `caption.py:259` — replace with `briefing_path.read_text()`. Verified: a repo-wide
  grep finds only the definition, the import at `caption.py:46`, that call, and one prose mention in
  `openspec/changes/archive/0019-open-models/design.md:172`.

- [x] 1.4 **Delete `ROOT`** (`claude_cli.py:51`). It has no production importer — its only reads are
  `:268` and `:270`, inside `instructions_record`, which now uses `DATA_ROOT.parent` (`run.py:52`).
  Delete `pytest.param(claude_cli.ROOT, (), id="claude_cli.ROOT")` at **`tests/test_package_paths.py:56`**
  and drop `claude_cli` from that file's import at `:28`.

  ⚠️ **`tests/test_package_paths.py:56` evaluates at module scope** — leaving it gives an `AttributeError`
  at collection, not a test failure. Nothing asserts the param count; the "six constants" claim is prose
  at `:3` and `:95`, corrected in phase 3.

- [x] 1.5 **Tidy `claude_cli.py`'s imports.** Once `instructions_record`, `constant_record` and `ROOT`
  leave, `import hashlib` (`:39`) and `from pathlib import Path` (`:45`) are unused → `ruff check` F401.
  Remove them in this commit.

- [x] 1.6 **Re-point and rename in six test files.** Every one of these is a module-scope import, so a
  miss is a collection error:

  | file:line | what |
  |---|---|
  | `tests/test_caption.py:17-23` | split the import: `BASE_FLAGS, classify, models_that_ran` stay on `claude_cli`; `StageFailure` and `instructions_record` come from `isekai.foundation.run` |
  | `tests/test_caption.py:198, :233` | `instructions_record(BRIEFING_PATH)` |
  | `tests/test_caption.py:313, :325, :349, :385` | `FakeReader(failure=CliFailure(...))` → `StageFailure` |
  | `tests/test_caption.py:377, :404` | `pytest.raises(CliFailure)` → `StageFailure` |
  | `tests/test_run_directory.py:18` | `from isekai.boundary.claude_cli import instructions_record` → `isekai.foundation.run` |
  | `tests/test_tagging.py:23` | `from isekai.boundary.claude_cli import CliFailure, constant_record` → `isekai.foundation.run`, renamed |
  | `tests/test_tagging.py:447` | `raise CliFailure("permanent", …)` inside `class Failing` → `StageFailure` |
  | `tests/test_package_paths.py:28, :56` | see 1.4 |

  `isekai/pipeline/caption.py:121` — `FakeReader.failure: CliFailure | None` — and `:128`'s
  `raise self.failure` are **production** sites (D13); rename both.

  `tests/test_ollama.py:203` mentions `CliFailure` in a **docstring only**. Leave it; phase 3.

- [x] 1.7 **Verify:** `uv run pytest tests/test_caption.py tests/test_tagging.py tests/test_run_directory.py tests/test_package_paths.py tests/test_isolation.py -v`

- [x] 1.8 **Verify the arm still resolves** — this phase's whole claim:
  `uv run python -c "from isekai.foundation.flow import load_flow; from isekai.interface.wiring import reader_for; r = reader_for(load_flow('summon-v1')); print(type(r).__name__, r.implementation)"`
  **Expected: `ClaudeReader claude-cli`.**

- [x] 1.9 **Verify:** `make gate`

---

## 2 — The flow set, the loader and the arm, together

**Why this is one phase and not three:** `isekai/interface/wiring.py:176` is the only line that selects
an arm and it reads `flow.hosted`, which this phase deletes. Splitting it in either direction ends a
phase on a red gate — `design.md` D26 has the full argument. **This is the largest phase in the change.**

### 2a — the loader

- [x] 2.1 **`isekai/foundation/flow.py`:**
  - `SIBLINGS` (`:59`) → `(GRAPH_NAME, SCHEMA_NAME, CAPTION_BRIEFING_NAME)`. Delete
    `SHEET_BRIEFING_NAME` (`:58`) and `Flow.sheet_briefing_path` (`:282-284`) (D9).
  - `MANIFEST_VERSION` (`:47`) → `3`. Replace the `:78-85` comment block — its stated reason expires
    here (D2).
  - Delete `class Hosted` (`:221-234`), `Flow.hosted` (`:249`), `REQUIRED_HOSTED` (`:94`) and its
    `:88-93` comment, the missing-key check (`:371-379`) and the construction (`:425-433`).
  - Add `model: str` to `Flow` as the **last field**, where `hosted` was (`:249`) — every field is then
    required and none carries a default. Field order is otherwise free: `Flow` is constructed in exactly
    one place, `flow.py:413`, with keyword arguments only. Add `"model"` to `REQUIRED` (`:63-72`) as its
    **last** entry, and make `KNOWN` (`:86`) just `REQUIRED` — delete the `+ ("hosted",)`.
  - Parse it with a **non-empty-string check**, refused by name (D4). Today `flow.py:427-429` applies a
    bare `str()`, so `{"reader": null}` loads as the string `"None"`.
  - Update `load_flow`'s docstring at `:326-333`: the typo path it describes is now closed by the
    top-level allowlist at `:350-357`, which needs no change (D3).

- [x] 2.2 **Verify the refusals by hand before touching a flow:**
  `uv run pytest tests/test_flow.py -v -k "manifest or refused or version"`

### 2b — the flow set (D5)

**A flow is never edited. Delete the directory, create the new one.**

**⚠️ The byte shape of a manifest is load-bearing**, because `manifest_digest` hashes file bytes and
`PINNED` freezes the result. Every existing `flow.json` is `json.dumps(..., indent=2)` plus **one
trailing newline**, keys in the order written, no trailing spaces. Produce the new manifests by
**editing a copy of the source file's text**, not by round-tripping through a JSON library with
different defaults — and put `"model"` **exactly where the key it replaces sat**: last in the document
for `summon-anime-wai` (where `hosted` was), and appended after `models` for `conjure-anime-wai`, which
had no `hosted` block. Re-run 2.6's digest command after any later edit to either directory.

- [x] 2.3 **Delete** `flows/summon-v1/`, `flows/conjure-v1/`, `flows/summon-open-v1/` — `git rm -r`.

- [x] 2.4 **Create `flows/summon-anime-wai/`, four files:**
  - `flow.json` — `summon-open-v1`'s, with `"flow": "summon-anime-wai"`, `"manifest_version": 3`, the
    whole `hosted` block (its last four lines, `:96-100`) replaced by a top-level
    `"model": "joycaption-beta-one-q4k"`. **Every dial, node binding and all 12 model digests
    unchanged.**
  - `graph.json` — `summon-open-v1`'s, **byte-identical**, including `"filename_prefix": "summon-v1"` at
    `:174`. That string is inert and is carried deliberately (D11).
  - `schema.json` — `summon-open-v1`'s, **byte-identical**. 16 fields.
  - `caption.briefing.md` — `summon-open-v1`'s, **byte-identical**.
  - **No `sheet.briefing.md`.**

- [x] 2.5 **Create `flows/conjure-anime-wai/`, four files:**
  - `flow.json` — `conjure-v1`'s, with `"flow": "conjure-anime-wai"`, `"manifest_version": 3`, and a
    top-level `"model": "joycaption-beta-one-q4k"` appended after `models`. `conjure-v1` has no `hosted`
    block to remove. **`inputs` stays `["sheet"]`** — it gates only `generate.py:405`'s `upload_image`
    (D29).
  - `graph.json` — `conjure-v1`'s, **byte-identical**. 14 nodes.
  - `schema.json` — `conjure-v1`'s, **byte-identical. 21 fields, `eyelashes` KEPT** (D7). Dropping it
    raises `KeyError` in `scripts/derive_field_map.py`'s `claims()` and forces a table regeneration this
    change does not do.
  - `caption.briefing.md` — a **byte-identical copy of `summon-anime-wai`'s** (D8). Not conjure-v1's.
  - **No `sheet.briefing.md`.**

- [x] 2.6 **Rewrite `PINNED`** (`tests/test_flow.py:48-70`) to the two new flows. **Compute the digests,
  never invent them:**
  `uv run python -c "from isekai.foundation.flow import manifest_digest, tracked_flows; [print(f'{n}: {manifest_digest(n)}') for n in tracked_flows()]"`
  Replace the three entries and their comments with two, and record in the comment that this is a flow-set
  replacement rather than a re-pin — the exception at `:54-60` is not being used.

- [x] 2.7 **Re-point the session fixtures. These are module-scope loads and each one is a collection
  error for every module that imports it:**

  | file:line | today | becomes |
  |---|---|---|
  | **`tests/stages.py:35`** | `FLOW = load_flow("summon-v1")` | `load_flow("summon-anime-wai")` — **imported by 12 test modules** |
  | `tests/stages.py:37` | `SHEET_BRIEFING = FLOW.sheet_briefing_path` | **delete** |
  | `tests/conftest.py:51` | `_shipped_workflow` → `load_flow("summon-v1").graph_path` | `summon-anime-wai` |
  | `tests/conftest.py:98` | `_shipped_schema` → `load_flow("summon-v1").schema` | **`summon-anime-wai`, not conjure** — `test_sheet_schema.py:59` expects 16 fields and conjure declares 21 |
  | `tests/test_sheet_schema.py:26` | `SCHEMA_PATH = load_flow("summon-v1").schema_path` | `summon-anime-wai` |

  And one real load the earlier sweeps missed, in a file otherwise untouched by this change:
  **`tests/test_image.py:26`** — `flow = load_flow("summon-v1")` inside
  `test_the_scale_node_is_found_by_role_not_by_class`. Re-point at `summon-anime-wai`, which carries the
  same graph byte for byte, so the two `ImageScale` nodes its comment at `:23` depends on are still
  there. **Do not point it at `conjure-anime-wai`** — that graph has 14 nodes and no identity leg.

  Then the plain `FLOW = "summon-v1"` string constants: `tests/test_run_view.py:23`,
  `tests/test_ui.py:32`, `tests/test_resume.py:36`, `tests/test_review.py:37`,
  `tests/test_run_directory.py:58`, `tests/test_ui_api.py:57`, `tests/test_generate.py:60`,
  `tests/test_sheet_stage.py:35`. And `tests/test_tagging.py:61` — `FLOW = "summon-open-v1"`.

### 2c — the arm (D16, D17, D18)

- [x] 2.8 **`isekai/pipeline/caption.py`** — delete `class ClaudeReader` (`:132-164`), the nine
  `claude_cli` imports (`:41-51`, keeping only what `run.py` now provides), `"ClaudeReader"` from
  `__all__` (`:291`), and the module docstring's Claude sentences (`:21-22`).

- [x] 2.9 **`isekai/interface/wiring.py`** — delete `DEFAULT_IMPLEMENTATION` (`:97`), `_claude_reader`
  (`:100-103`), `_no_tagger` (`:122-128`), `_named_by` (`:105-114`), `_resolve` (`:169-184`), the
  `Hosted` import (`:28`), and both `"claude-cli"` entries (`:152`, `:164`). `READERS` and
  `HOSTED_TAGGERS` collapse: `reader_for` and `hosted_tagger_for` read `flow.model` directly.
  **Rewrite the `:142-150` comment** — its premise is gone (D17).

- [x] 2.10 **`git rm isekai/boundary/claude_cli.py`** and **`git rm tests/test_isolation.py`** (D18).

- [x] 2.11 **Tests to delete outright** — each named with its reason, none of them a silent drop:

  | file:line | test | why |
  |---|---|---|
  | `tests/test_flow.py:676-684` | `test_the_manifest_format_version_is_unchanged_by_the_optional_key` | its premise is inverted |
  | `tests/test_flow.py:588-592` | `test_a_flow_declaring_no_hosted_block_reports_none` | unrepresentable |
  | `tests/test_flow.py:595-605` | `test_the_incumbent_flows_declare_no_hosted_block_and_load` | unrepresentable |
  | `tests/test_flow.py:655-673` | `test_a_hosted_block_missing_one_of_its_three_keys_is_refused` | `REQUIRED_HOSTED` gone |
  | `tests/test_flow.py:714-733` | `test_the_sorter_key_is_carried_dead_and_has_not_moved_the_digest` | D24 |
  | `tests/test_flow.py:734-742` | `…_graph_and_schema_are_the_incumbents_byte_for_byte` | comparison target deleted |
  | `tests/test_flow.py:745-758` | `test_the_open_caption_briefing_licenses_absence_verbatim` | both briefings are now one file; `caption:inputs:only-the-photograph-is-passed` keeps five other bindings |
  | `tests/test_flow.py:761-766` | `test_the_open_sheet_briefing_names_every_one_of_the_sixteen_fields` | the file is deleted |
  | `tests/test_sheet_stage.py:369-383` | `test_every_field_name_the_briefing_mentions_exists_in_the_schema` | reads `SHEET_BRIEFING` |
  | `tests/test_pipeline_cli.py:415-420` | `test_a_flow_declaring_no_block_resolves_to_the_default_implementation` | no default |
  | `tests/test_tagging.py:385-391` | the `hosted is None` triple in `…_resolves_for_every_tracked_flow` | D25 |
  | `tests/test_tagging.py:497-500` | `_hosted(flow) -> Hosted` helper | `Hosted` gone |
  | `tests/test_caption.py:240` | `test_the_argument_vector_carries_every_load_bearing_flag` | `spec_exempt`, orphans nothing |
  | `tests/test_caption.py:265` | `test_the_adapter_reads_prose_out_of_the_envelope` | key kept by `:538` and `:65` |
  | `tests/test_caption.py:286` | `test_the_models_that_ran_come_from_the_envelope_not_from_the_flag` | key kept by `:76`, `:88` |
  | `tests/test_caption.py:305` | `test_a_rate_limit_a_server_error_or_a_timeout_is_transient` | key kept by `:312`, `:324` |
  | `tests/test_caption.py:339` | `test_a_declined_request_is_permanent` | key kept by `:346` |
  | `tests/test_caption.py:394` | `test_output_that_is_not_an_envelope_at_all_is_a_failure` | key kept by `:384` and the rewritten `:367` |
  | `tests/test_caption.py:414`, `:428` | the two absent-reader tests | D20 |

- [x] 2.12 **Tests to rewrite, not delete:**

  | file:line | test | onto what |
  |---|---|---|
  | `tests/test_flow.py:552-568` | `test_a_flow_declaring_hosted_models_is_loaded_with_them` | the top-level `model` |
  | `tests/test_flow.py:571-585` | `test_no_value_in_a_hosted_block_is_derived_at_load_time` | the top-level `model` |
  | `tests/test_flow.py:632-651` | `test_a_misspelled_hosted_block_is_refused_rather_than_ignored` | re-parametrize onto `model` typos — `["modl", "Model", "models", "model_name"]` |
  | `tests/test_flow.py:698-711` | `test_the_open_flow_declares_the_implementation_it_is_meant_to_run` | assert `flow.model == "joycaption-beta-one-q4k"` |
  | `tests/test_flow.py:155-176` | `test_the_schema_briefings_and_graph_each_flow_needs_are_in_its_directory` | drop the `sheet_briefing_path` entry at `:169` |
  | `tests/test_generate.py:145` | copies `SHEET_BRIEFING_NAME` from the source flow | drop it and the `:23` import — otherwise `FileNotFoundError` |
  | `tests/test_pipeline_cli.py:92-117` | `_flow_declaring` | writes `manifest["hosted"]` and loads `summon-v1`; rewrite onto `model` + `summon-anime-wai` |
  | `tests/test_pipeline_cli.py:116-138` | `_two_arms` | **rewrite, do not delete.** Rename to `_two_models` and build both scratch flows the same way — each gets a top-level `model`, one `"a-reader"` and one `"b-reader"`, and neither omits the key. Its one consumer, `:475-501`, is rewritten with it (next row) |
  | `tests/test_pipeline_cli.py:151-154` | `_arm_aware_reader` | reads `flow.hosted` and `DEFAULT_IMPLEMENTATION` |
  | `tests/test_pipeline_cli.py:394` | `assert "claude-cli" in message and "ollama" in message` | `"ollama"` only |
  | `tests/test_pipeline_cli.py:398-412` | `test_each_registrys_keys_are_the_strings_the_artifacts_record` | one entry |
  | `tests/test_pipeline_cli.py:474-501` | `test_one_command_over_two_flows_writes_two_artifacts_each_naming_its_own` | **rewrite, keep the test.** Re-bind from `cli:resolution:one-command-two-implementations` to **`cli:resolution:one-command-two-models`**; build the flows with `_two_models`; drop `_arm_aware_reader` and read the **model** out of each producer instead of the implementation, so the assertion becomes `{"flow-a": "a-reader", "flow-b": "b-reader"}`. The docstring's argument survives verbatim — hoisting the resolution still hands one flow's model to the other's artifact |
  | `tests/test_tagging.py:423-429` | `test_two_flows_on_two_arms_each_get_their_own_hosted_tagger` | one arm |
  | `tests/test_tagging.py:483-495` | builds a `Hosted` via `dataclasses.replace` | the `model` field |
  | `tests/test_caption.py:367` | `test_a_response_the_stage_cannot_read_as_prose_is_permanent` | `OllamaReader` + `FakeTransport({"response": ""})` — `:603` shows the shape |
  | `tests/test_resume.py:255, :292` | `ClaudeReader(binary="not-a-real-binary")` in the refusal collector | an `OllamaReader` unreachable-host case |

- [x] 2.13 **Add the assertion the rule has never had** (D10): `len(SIBLINGS) == 3`, and a flow directory
  holding exactly `MANIFEST_NAME` plus `SIBLINGS`. Rename
  `test_a_flow_is_five_flat_files_and_the_manifest_names_none_of_them` and re-bind it.

- [x] 2.14 **The bindings, by key.** The spec delta is already written under `specs/`; these are the keys
  the suite must name after this phase. **Do not invent a key — every one below is in the delta.**

  | key | bound by |
  |---|---|
  | `image-generation:manifest:a-flow-is-flat-and-its-files-are-named` | the renamed test from 2.13 |
  | `image-generation:manifest:tracked-flows-are-gate-checked` | existing test; its "both briefings" assertion becomes the caption briefing alone |
  | `image-generation:model:flow-declares-the-model-it-runs` | the rewrite of `test_a_flow_declaring_hosted_models_is_loaded_with_them` |
  | `image-generation:model:an-absent-model-is-refused` | new |
  | `image-generation:model:an-empty-model-is-refused` | new — the `{"model": null}` case D4 closes |
  | `image-generation:manifest:a-misspelled-model-key-is-refused` | the re-parametrized `…_misspelled_…` test |
  | `image-generation:manifest:unknown-key-is-refused` | unchanged, keeps its binding |
  | `caption:selection:the-flow-names-the-model` | the rewrite of `test_a_flow_declaring_ollama_resolves_to_the_models_its_manifest_names` |
  | `caption:selection:an-unreachable-model-is-refused` | the rewrite of `test_an_unknown_reader_implementation_refuses_naming_what_this_build_carries` |
  | `cli:resolution:one-command-two-models` | the rewrite of `test_one_command_over_two_flows_writes_two_artifacts_each_naming_its_own` |
  | `tagging:independence:the-local-tagger-needs-no-manifest-key` | unchanged key, widened WHEN |
  | `tagging:independence:the-hosted-tagger-runs-the-flows-model` | the rewrite of `test_the_hosted_tagger_resolves_only_where_a_flow_declares_an_arm` |

  **Keys that leave, and whose tests are deleted rather than re-bound:**
  `caption:selection:the-flow-names-the-implementation` ·
  `caption:selection:unknown-implementation-is-refused` ·
  `caption:selection:no-path-reaches-another-implementation` ·
  `caption:refusal:absent-reader-names-the-fix` ·
  `cli:resolution:one-command-two-implementations` ·
  `image-generation:hosted:flow-declares-its-hosted-models` ·
  `image-generation:hosted:absent-block-means-the-default` ·
  `image-generation:hosted:incumbent-flows-are-unchanged` ·
  `image-generation:hosted:an-unread-key-is-carried` ·
  `image-generation:manifest:flow-is-five-flat-files` ·
  `image-generation:manifest:misspelled-hosted-block-is-refused` ·
  `tagging:independence:the-hosted-tagger-is-absent-without-a-hosted-block`

  **Two scenarios keep their keys but lose a clause** (D21) — the tests that assert the dropped `AND`
  must drop it too: `caption:seam:producer-names-the-implementation` loses *"a caption produced by a
  different implementation is distinguishable"*; `caption:failure:decline-is-permanent` loses *"no other
  implementation is substituted"*.

- [x] 2.15 **Verify:** `uv run pytest tests/test_flow.py tests/test_pipeline_cli.py tests/test_tagging.py tests/test_caption.py -v`

- [x] 2.16 **Verify no arm remains reachable:**
  `uv run python -c "import isekai.interface.wiring as w; print(sorted(w.READERS)); print(sorted(w.HOSTED_TAGGERS))"`
  **Expected: `['ollama']` twice.**

- [x] 2.17 **Verify both flows load and name their model:**
  `uv run python -c "from isekai.foundation.flow import load_flow, tracked_flows; [print(n, load_flow(n).model, len(load_flow(n).schema.names)) for n in tracked_flows()]"`
  **Expected: `conjure-anime-wai joycaption-beta-one-q4k 21` and `summon-anime-wai joycaption-beta-one-q4k 16`.**

- [x] 2.18 **Verify the table is untouched** (D7, D30) — this is the phase's negative claim:
  `git diff --stat main -- scripts/field_map.json scripts/derive_field_map.py isekai/shared/field_map.py tests/test_field_map.py`
  **Expected: no output.** Then `uv run pytest tests/test_field_map.py -v` — all green, none skipped for
  a reason this change introduced.

- [x] 2.19 **Verify:** `make gate`

---

## 3 — The documents and the spec delta

**No gate command reads markdown**, so nothing here can turn the gate red on its own — which is exactly
why it needs its own phase and its own review rather than being folded into phase 2. **This phase carries
a real requirement removal, not only prose.**

- [ ] 3.1 **`openspec/specs/` deltas** — written under `openspec/changes/0022-one-arm/specs/`, five
  capabilities. See that directory; `openspec validate 0022-one-arm --strict` must pass.

- [ ] 3.2 **`CLAUDE.md`:**
  - `:205-215` — the flow layout paragraph: four files not five, named not counted (D10); the three
    tracked flows become two; `sheet.briefing.md` leaves the list.
  - `:269-283` — the `hosted` paragraph and the `hosted.sorter` paragraph: replaced by the top-level
    `model` key. **`:275` and `:281` are two of the nine live `qwen` lines.**
  - `:328-334` — *"three system dependencies"*: `claude` is no longer one. **`:332` is a third qwen
    line** (`ollama pull qwen3:8b`).
  - **Add the flow naming rule** (D6): `<verb>-<style>-<base>`, with `-v2` only for a second generation
    of the same triple. This is the first such rule in the file.
  - `:148-153` — the capability count sentence says *"eleven capabilities today"*; it is twelve since
    v0.21's fold. Correct it, and keep the *"count the directory rather than trusting this sentence"*
    clause that it already carries.

- [ ] 3.3 **`README.md`:**
  - `:16-22` — the banner still says `summon-v1` and `conjure-v1` *"read and sort through the `claude`
    CLI"*. Rewrite for one arm.
  - `:97`, `:99` — v0.21's converge left these: the quickstart's first numbered step still says the sheet
    is sorted from the prose, contradicted seven lines below. Fix here.
  - `:101-102`, `:120-121`, `:134`, `:153`, `:358` — flow names.
  - `:220-233` — the provisioning block: delete `ollama pull qwen3:8b` (`:224`) and the paragraph
    explaining why the key is kept (`:227-229`). **Two of the nine qwen lines.**
  - `:287-292` — the flow tree: four files, and `sheet.briefing.md`'s line goes.

- [ ] 3.4 **`scripts/joycaption.Modelfile`** — `:34-38`. Delete the `ollama pull qwen3:8b` line (`:35`)
  and rewrite `:37`, which still calls it *"the sorter, stage ②"* in the present tense. That sentence is
  false today, not merely after this change: v0.21's phase 6 corrected `README.md` and `CLAUDE.md` and
  missed this file (D28).

- [ ] 3.5 **The package READMEs:** `isekai/boundary/README.md` (`:10`, `:22`, `:40-43` — the
  `claude_cli.py` row and the "imports nine names" sentence), `isekai/foundation/README.md` (`:12`,
  `:18-20` — the importer rows for `refusal.py`, `run.py` and `flow.py` now gain the rehomed names),
  `isekai/README.md`.

- [ ] 3.6 **Docstrings and comments naming a deleted thing** — none is red, all are false:
  `isekai/boundary/ollama.py:6, :9, :11, :12, :86, :102, :156, :163` · `isekai/pipeline/tagging.py:168`
  (`ClaudeReader.argv()`) · `isekai/boundary/wd14.py:223` · `isekai/interface/ui/bundle.py:10, :19`
  (prose only — its own `BINARY = "npm"` is unrelated) · `isekai/pipeline/generate.py:289` ·
  `isekai/shared/field_map.py:19` · `isekai/foundation/flow.py:21` · `tests/transports.py:16` ·
  `tests/test_ollama.py:203` · `tests/test_ui.py:326` · `tests/test_package_paths.py:3, :95` (the "six
  constants" claim, now five) · `tests/test_field_map.py:29, :249` (a hand-built `DECLARED` dict naming
  `summon-v1` — not red, but stale) · `tests/test_run_directory.py:315, :323, :344, :368` (hand-built
  envelopes with `"implementation": "claude-cli"`).

- [ ] 3.7 **Verify the scrub, and read every survivor rather than counting them.** Run both, from the
  repository root:

  ```sh
  grep -rniI claude --exclude-dir=.git --exclude-dir=archive --exclude-dir=node_modules \
    --exclude-dir=.venv --exclude-dir=.minions --exclude-dir=0022-one-arm . \
    | grep -Ev '^(\./)?(CHANGELOG\.md|ui/design/|CLAUDE\.md:1:)'
  grep -rniI qwen --exclude-dir=.git --exclude-dir=archive --exclude-dir=node_modules \
    --exclude-dir=.venv --exclude-dir=.minions --exclude-dir=0022-one-arm . \
    | grep -Ev '^(\./)?CHANGELOG\.md'
  ```

  Three things the filters are doing, each for a reason rather than to make the count look good.
  **`(\./)?`** — BSD `grep` on this machine prints `CHANGELOG.md`, GNU prints `./CHANGELOG.md`, and a
  pattern anchored to one of them silently passes the other through.
  **`--exclude-dir=.minions`** — gitignored orchestrator output, not part of the repository.
  **`--exclude-dir=0022-one-arm`** — this change's own directory, which quotes both words heavily and is
  *a live document until `mf-release` archives it*. That is the same position `0021` was in while it
  named the sorter, and it resolves itself the same way. Do not scrub it.
  **The test is *does this sentence claim something untrue of the running system*, not *does the word
  appear*** (D28). Every remaining hit must be a historical record — `openspec/changes/archive/`,
  `CHANGELOG.md`'s released sections, `ui/design/`, `CLAUDE.md`'s own filename, or a
  `Co-Authored-By` trailer. **Paste the full output and justify each survivor by name.**

- [ ] 3.8 **Verify:** `npx @fission-ai/openspec@1.11.0 validate 0022-one-arm --strict`

- [ ] 3.9 **Verify:** `make gate`

---

## 4 — ⚠️ **HUMAN · METERED** — the acceptance, both flows, the same photographs

**HALT and hand back.** This is the only phase that spends money, and the operator has approved it.
v0.21's comparable run was 21m36s on an RTX PRO 4500 Blackwell at ≈$0.30 for eight renders.

**The claim, and it is v0.19's isolation proof inverted:** there is no second arm to prove separation
from, so what is being shown is that **the one arm is complete**.

- [ ] 4.1 **Both flows, end to end, on the same photographs.** `caption` → `sheet` → `ui` → `generate`,
  for `summon-anime-wai` and `conjure-anime-wai`, over one set of photographs. Two reviews, one per flow
  — the surface serves one flow at a time (`cli:flow-selection:a-serving-verb-takes-one-flow`).
- [ ] 4.2 **The renders are what the operator wants.** A judgement, stated directly. **A no is a
  finding**, recorded as such rather than retried into a yes.
- [ ] 4.3 **Record, beside it:** that `conjure-anime-wai` carries all 21 fields including `eyelashes`,
  and how many of the five face-only fields the operator filled by hand. That number is what a later
  version re-reads if the schema is ever revisited (D7).
- [ ] 4.4 **Tear the pod down and confirm it.** `infra/down.sh`, then verify no pod remains. Record the
  wall time and the cost.
- [ ] 4.5 **Write the result into `design.md` as a new decision**, and say which of the claims failed if
  any did. *(v0.21's phase 9 recorded its result in `CHANGELOG.md` and the commit body instead, at the
  operator's call; converge accepted that. If the same call is made here, record it in the same two
  places and say so — the point is that the result is written somewhere durable, not which file.)*
