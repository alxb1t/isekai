# Tasks — 0032 the tag verb

The manifest key first, because `tag` and `sheet` both read it; then the verbs, the sheet, the review surface,
the record; the acceptance last, on the operator's machine.

## Progress

- [x] 1 — The manifest: `tagger`, version 4, both flows re-pinned
- [x] 2 — The verbs: `tag` and `caption`, each tagger isolated
- [ ] 3 — The sheet: an empty fill for a flow that declares no tagger
- [ ] 4 — The review surface: a missing caption names its command
- [ ] 5 — The record: D1, D31, ① as two verbs
- [ ] 6 — 🛑 **HUMAN · HALT** — the acceptance, on one synthetic portrait

Line numbers are `50a6b17`'s; find each site by the text it names.

## 1 — The manifest: `tagger`, version 4, both flows re-pinned

- [x] 1.1 **HALT CHECK** — the manifest is at version 3 and no flow declares `tagger`.
  Verify: `grep -c '^MANIFEST_VERSION = 3$' isekai/foundation/flow.py` prints `1`, and `cat flows/summon-anime-wai/flow.json flows/conjure-anime-wai/flow.json | grep -c '"tagger"'` prints `0`.
- [x] 1.2 In `isekai/foundation/flow.py`, add `"tagger"` to `REQUIRED` and `Flow`, its boolean check after `model`'s, and `MANIFEST_VERSION = 4`, per [D1](design.md#d1). In `tests/test_flow.py`, test `flow-declares-whether-it-is-tagged`, `an-absent-declaration-is-refused` and `a-non-boolean-declaration-is-refused`, and make `:865` assert version 4 and `"tagger"` in `REQUIRED`.
  Verify: `grep -c '^MANIFEST_VERSION = 4$' isekai/foundation/flow.py` prints `1`, and `grep -c 'image-generation:tagger:' tests/test_flow.py` prints a number above `2`.
- [x] 1.3 Declare `"manifest_version": 4` and `"tagger": true` in both `flows/*/flow.json`; set each `graph.json`'s `filename_prefix` to its flow's id; add `"tagger": True` to the manifest `tests/test_generate.py:134-152` builds, per [D1](design.md#d1).
  Verify: `cat flows/summon-anime-wai/flow.json flows/conjure-anime-wai/flow.json | grep -c '"tagger": true'` prints `2`, and `cat flows/summon-anime-wai/graph.json flows/conjure-anime-wai/graph.json | grep -c -e '"summon-v1"' -e '"conjure-v1"'` prints `0`.
- [x] 1.4 Re-capture `tests/golden/render.json`: its `graph_sha256` and `flow_graph_sha256` move with `filename_prefix`, and no other byte does, per [D1](design.md#d1).
  Verify: `grep -c '23a67480b487' tests/golden/render.json` prints `0`.
- [x] 1.5 Re-pin both flows in `tests/test_flow.py`'s `PINNED`, per [D1](design.md#d1).
  Verify: `grep -c -e '5de6632e33a8' -e '3ad0f323d0f4' tests/test_flow.py` prints `0`.
- [x] 1.6 Reword `flow.py`'s module docstring (`:16-17`), the `model` refusal (`:420`) and the comment on `model` (`:94-99`), per [D1](design.md#d1).
  Verify: `grep -c -e 'first two stages' -e 'it creates a new identifier' -e 'prompts stage (1) sends' isekai/foundation/flow.py` prints `0`.

## 2 — The verbs: `tag` and `caption`, each tagger isolated

- [x] 2.1 **HALT CHECK** — `caption` still runs both taggers, and the remedies name `caption`.
  Verify: `grep -c 'caption_wd14(run, name' isekai/interface/cli.py` prints `1`, and `grep -c '^VERB = "caption"$' isekai/pipeline/tagging.py` prints `1`.
- [x] 2.2 Rename `caption_wd14` to `tag_wd14` and `caption_tags` to `tag_hosted`, and set `VERB = "tag"` with its comment and the module docstring, in `isekai/pipeline/tagging.py`, `isekai/interface/cli.py`, `tests/stages.py`, `tests/test_tagging.py`, `tests/test_ui_api.py`, `tests/test_run_view.py` and `tests/test_artifact_bytes.py`, per [D2](design.md#d2).
  Verify: `grep -rn -e caption_wd14 -e caption_tags isekai tests` prints nothing.
- [x] 2.3 In `isekai/interface/cli.py`, add `tag` to `VERBS` and to the `--flow` and `--new-version` loops; `caption` runs `caption()` alone; `tag` runs `tag_wd14`, then `tag_hosted`, each `Refusal` collected into the list `_per_item` is handed and `dispatch` reports, per [D2](design.md#d2).
  Verify: `grep -c '("tag", ' isekai/interface/cli.py` prints `1`, and `grep -c 'tag_wd14(run, name' isekai/interface/cli.py` prints `1`.
- [x] 2.4 In `tests/test_tagging.py`, run the ordering test through `tag`, and add `tagging:order:a-local-failure-leaves-the-hosted-list-written` (a failing photograph and an unopenable tagger) and `tagging:order:captioning-writes-no-tag-list`.
  Verify: `grep -c 'tagging:order:' tests/test_tagging.py` prints a number above `2`.
- [x] 2.5 Give `tag` its place in `tests/test_pipeline_cli.py`'s `EXPECTED_VERBS` and `STAGE_VERBS` and in `tests/test_resume.py`'s `VERBS`, after `caption`; `_calls`' docstring says `caption` reaches the reader alone.
  Verify: `grep -c '"tag"' tests/test_pipeline_cli.py` prints a number above `1`, and `grep -c '^VERBS = ("caption", "tag", ' tests/test_resume.py` prints `1`.
- [x] 2.6 Refuse a flow that declares no tagger in `dispatch`, per [D2](design.md#d2), with `tagging:declaration:a-flow-without-a-tagger-is-refused` in `tests/test_tagging.py` on a fixture flow copied with `"tagger": false`.
  Verify: `grep -c 'tagging:declaration:a-flow-without-a-tagger-is-refused' tests/test_tagging.py` prints `1`.
- [x] 2.7 Name `tag` in `isekai/pipeline/sheet.py`'s refusals (`:115-128`) and reword `isekai/boundary/ollama.py:199`, per [D2](design.md#d2); update `tests/test_sheet_stage.py:155`, `:351`, `tests/test_tagging.py:225` and `tests/test_resume.py`'s `AVAILABLE` (`:348`).
  Verify: `cat isekai/pipeline/sheet.py isekai/pipeline/tagging.py | grep -c 'isekai caption'` prints `0`, and `grep -c 'stages 1 and 2' isekai/boundary/ollama.py` prints `0`.
- [x] 2.8 Test `cli:explicit-versions:the-caption-flag-writes-prose-only` and `cli:explicit-versions:the-tag-flag-writes-both-lists` in `tests/test_resume.py`.
  Verify: `grep -c -e 'the-caption-flag-writes-prose-only' -e 'the-tag-flag-writes-both-lists' tests/test_resume.py` prints `2`.
- [x] 2.9 In `tests/test_tagging.py`, bind the local-tagger test to `tagging:independence:the-local-tagger-needs-no-model-key`, the hosted-model test to `tagging:independence:the-hosted-tagger-runs-the-flows-model`, and a `tag` run on a tracked flow to `cli:resolution:a-pinned-seam-resolves-for-every-flow-that-declares-it`; reword `wiring.tagger_for`'s docstring, per [D2](design.md#d2).
  Verify: `grep -c -e 'a-seam-without-a-manifest-key' -e 'the-local-tagger-needs-no-manifest-key' tests/test_tagging.py` prints `0`.

## 3 — The sheet: an empty fill for a flow that declares no tagger

- [ ] 3.1 **HALT CHECK** — `sheet()` takes no `tagged`, and every producer's `from` is required.
  Verify: `grep -c 'tagged: bool' isekai/pipeline/sheet.py` prints `0`, and `grep -c '"from": int,' isekai/foundation/artifacts.py` prints `2`.
- [ ] 3.2 Add the required keyword `tagged` and the empty fill to `sheet()` in `isekai/pipeline/sheet.py`, per [D3](design.md#d3); make `SheetProducer`'s `from` `NotRequired[int]` in `isekai/foundation/artifacts.py`; pass `flow.tagger` from `isekai/interface/cli.py`, and `tagged` from `tests/stages.py`'s helper.
  Verify: `grep -c 'tagged=flow.tagger' isekai/interface/cli.py` prints `1`, and `grep -c '"from": NotRequired\[int\]' isekai/foundation/artifacts.py` prints `1`.
- [ ] 3.3 In `tests/test_sheet_stage.py`, test `sheet:output:a-flow-without-a-tagger-gets-empty-fields`: every field empty, no `from`, `models` empty, and a `wd14/` list beside it left unread.
  Verify: `grep -c 'sheet:output:a-flow-without-a-tagger-gets-empty-fields' tests/test_sheet_stage.py` prints `1`.
- [ ] 3.4 Add a `sheet-empty` kind to `KINDS` in `tests/test_artifact_bytes.py` and capture `tests/golden/sheet-empty.json` from the writer, per [D3](design.md#d3).
  Verify: `test -f tests/golden/sheet-empty.json && grep -c '"sheet-empty"' tests/test_artifact_bytes.py` prints `1`.

## 4 — The review surface: a missing caption names its command

- [ ] 4.1 **HALT CHECK** — the payload carries no command for a missing caption.
  Verify: `grep -c 'caption_command' isekai/interface/ui/app.py` prints `0`.
- [ ] 4.2 Add `caption_command` to `read_input`'s payload in `isekai/interface/ui/app.py`, per [D4](design.md#d4), with `ui:source:a-missing-caption-names-its-command` in `tests/test_ui_api.py`: `null` beside a caption; otherwise a command naming the run that `build_parser` parses.
  Verify: `grep -c 'ui:source:a-missing-caption-names-its-command' tests/test_ui_api.py` prints `1`.
- [ ] 4.3 Carry `caption_command` from `ui/src/types.ts` through `ui/src/ReviewApp.vue` and `ui/src/components/SourcePanel.vue` to `ui/src/components/CaptionPanel.vue`, which shows *no caption* and the command when the prose is `null`; reword the *"no hosted block"* comments, per [D4](design.md#d4).
  Verify: `grep -c 'caption_command' ui/src/types.ts` prints `1`, and `cat ui/src/types.ts ui/src/components/SourcePanel.vue | grep -c 'hosted block'` prints `0`.
- [ ] 4.4 Bound and assert both waits in `_update_during_approval` (`tests/test_ui_api.py:586`, `:593`), per [D4](design.md#d4).
  Verify: `grep -c -e 'approved.wait()' -e 'timeout=None if unlocked' tests/test_ui_api.py` prints `0`.

## 5 — The record: D1, D31, ① as two verbs

- [ ] 5.1 In `docs/decisions.md`, rewrite D1 as *Stage ① is two independent verbs* and add D31 under *Flows*, per [D5](design.md#d5).
  Verify: `grep -c '^### D1 · Stage ① is two independent verbs' docs/decisions.md` prints `1`, and `grep -c '^### D31 · ' docs/decisions.md` prints `1`.
- [ ] 5.2 Draw ① as `tag` and `caption` side by side, and walk through `tag`, `caption`, `sheet`, `ui`, in `docs/data-flow.md`, `docs/README.md`, `README.md` and `CLAUDE.md:7-8`, per [D5](design.md#d5).
  Verify: `grep -c 'isekai tags' docs/data-flow.md` prints `0`, and `grep -c 'python -m isekai tag --flow' README.md` prints a number above `0`.
- [ ] 5.3 Name `tagger` in the manifest's key lists — `docs/principles.md:147-148` (*"… prompts, models"* → *"… prompts, models, whether it is tagged"*) and `README.md:331` — and correct `docs/modules.md:62-63`, `isekai/README.md:11` and `isekai/pipeline/README.md:10-23`, per [D5](design.md#d5).
  Verify: `grep -c 'whether it is tagged' docs/principles.md` prints `1`, and ``grep -c 'on every `caption`' docs/modules.md`` prints `0`.
- [ ] 5.4 Rewrite `isekai/interface/cli.py`'s module docstring (`:9-24`), the `cli` spec's preamble (`openspec/specs/cli/spec.md:5-7`) and the `sheet` spec's (`openspec/specs/sheet/spec.md:5-7`), naming the verbs rather than counting them, per [D5](design.md#d5).
  Verify: `grep -c 'Seven verbs' isekai/interface/cli.py` prints `0`, and `grep -c 'seven verbs' openspec/specs/cli/spec.md` prints `0`.

## 6 — 🛑 **HUMAN · HALT** — the acceptance, on one synthetic portrait

Free and local: Ollama and WD14 on this machine, no pod. **A synthetic portrait, never a real person's
photograph.**

- [ ] 6.1 ⛔ **HALT.** Ask the operator for a synthetic portrait and the `--runs` root, and wait for an explicit go; record it as the first line of `openspec/changes/0032-the-tag-verb/acceptance.md`, `Go: <date>`.
  Verify: `grep -c '^Go: ' openspec/changes/0032-the-tag-verb/acceptance.md` prints `1`.
- [ ] 6.2 For both flows, run `tag`, `caption`, `sheet`, then `ui` on the run; record each command and what it printed in `openspec/changes/0032-the-tag-verb/acceptance.md`, with no absolute path.
  Verify: `grep -c -e 'isekai tag --flow' -e 'isekai caption --flow' openspec/changes/0032-the-tag-verb/acceptance.md` prints a number above `1`.
- [ ] 6.3 With Ollama stopped, `tag --new-version` writes WD14 and refuses only the JoyCaption list; on a fresh run, `sheet` before `tag` refuses naming `tag`. Record both.
  Verify: `grep -c -e 'Ollama stopped' -e 'refused' openspec/changes/0032-the-tag-verb/acceptance.md` prints a number above `1`.
