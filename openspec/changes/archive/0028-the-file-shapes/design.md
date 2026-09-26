# Design — 0028 the file shapes

How every run file's shape is declared once and every writer and reader is typed against it, with no byte
on disk and no behaviour changed. **Verdict: `feasible`.** Every file, symbol and line below was re-checked
at `main` `a3d0ca3`.

## Context

- **The run's JSON files, by kind, as they are written today:**

  | kind | schema name | written at | read at |
  |---|---|---|---|
  | frame | `run` | `isekai/foundation/run.py:329-341` (`open_run`) | `run.py:238-242` (`Run.frame`), `:247`, `:289`; `isekai/interface/run_view.py:158-166` |
  | error record | `error` | `run.py:492-515` (`record_failure`) | filenames only |
  | caption | `caption` | `isekai/pipeline/caption.py:249-261` | `isekai/interface/ui/app.py:261` |
  | wd14 | `wd14` | `isekai/pipeline/tagging.py:284-297` | `isekai/pipeline/sheet.py:118-120`, `:135-137`; `app.py:376` |
  | tags | `tags` | `tagging.py:350-363` | `app.py:411` |
  | sheet | `sheet` | `sheet.py:125-147` | `isekai/pipeline/review.py:144`, `:357` |
  | review draft | `review` | `review.py:146-159`; rewritten by `save_draft` at `:220-222` | `review.py:209`, `:303`; `app.py:250` |
  | review approved | `review` | `review.py:321-343` | `review.py:144`; `isekai/pipeline/generate.py:173`; `app.py:250`; `scripts/derive_field_map.py:465` |
  | prompt | `prompt` | `generate.py:191-203` | `generate.py:410` |
  | render sidecar | `render` | `generate.py:454-469` | filenames only |

  The photograph copy and the render image are bytes, with no shape to declare. `run_view._producer_of`
  (`run_view.py:62-82`) reads every kind's producer with a bare `json.loads`.
- **`SCHEMA_VERSION = 1`** (`run.py:67`) stamps every kind, through `open_run`, `envelope()` (`:414-428`) and
  `record_failure`. `read_artifact` (`:431-447`) refuses any other version and never checks the name.
- **Every file under the operator's `.data/` declares version 1 and re-serialises byte-identically** through
  `json.dumps(indent=2) + "\n"`, the one JSON form `write_json` (`run.py:218-220`) writes. Sheets hold earlier
  shapes under that same version: before v0.16 `schema_document` carried a `version`, and before v0.21 the
  producer carried `briefing` where it now carries `artifacts`, with no `field_map`. Readers touch only
  `vocabulary` and `fields`, which every sheet shape has.
- **Names already taken:** `Kind` (`run.py:131`) is the failure kind; `WD14`, `TAGS`, `REVIEW` and `PROMPTS`
  (`run.py:113-120`) are stage directories, and `tagging.py` uses `WD14` and `TAGS` as schema names today.
- **WD14 stores Danbooru's spelling** — `Scored(tag=label.name)` at `isekai/boundary/wd14.py:347` — and the
  router normalises it (`isekai/shared/field_map.py:279`). `tests/stages.py:99`'s default tags and the WD14
  literals in `tests/test_sheet_stage.py` are spelled with spaces; only `tests/test_sheet_stage.py:94`
  passes underscores.
- **Line numbers are `a3d0ca3`'s.** A builder re-resolves each by the text it names.

## Goals / Non-Goals

**Goals**

- Every run file's shape, and its producer's, is declared once, in `isekai/foundation/artifacts.py`.
- Every production writer and reader is typed against those shapes, so `ty` rejects a misspelled key.
- Each kind has its own version.
- A space-spelled tag standing in for WD14's output is a type error.

**Non-Goals**

- Any byte on disk, any refusal's text, or what any read accepts.
- Checking a file's kind name, or adding the version check `Run.frame` and `show` skip.
- Validating a shape at run time.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | a new `isekai/foundation/artifacts.py` is the contract; `write_json` moves into it | `run.py` imports it, so the reverse would be a cycle | growing `run.py` |
| [D2](#d2) | a `TypedDict` per kind and per producer | a dict at run time, so no byte can move | a dataclass per kind, which parses and validates |
| [D3](#d3) | an `Artifact[T]` descriptor per kind carries its name and version | the types flow from one object | a function pair per kind |
| [D4](#d4) | one `write(path, KIND, artifact)`; one `read(path, KIND)` | one writer and one reader serve every kind | a producer-and-body writer, which cannot write the frame or the error record |
| [D5](#d5) | every production writer and reader converts, kind by kind | the tripwire's allowlist empties as they do | converting readers first |
| [D6](#d6) | `DanbooruTag` types the tags in a WD14 file; `route` accepts only it | the `v0.21` defect becomes a type error | a runtime spelling check |
| [D7](#d7) | `SCHEMA_VERSION`, `envelope` and `read_artifact` are deleted once nothing calls them | nothing old is removed before the new is proven | deleting them first |
| [D8](#d8) | a golden file per kind, captured from today's code | every later phase proves no byte moved | trusting the type checker for bytes |
| [D9](#d9) | a tripwire: only `artifacts.py` calls `write_json` | a module writing JSON by hand re-spells a shape | the UI's tripwire alone |
| [D10](#d10) | tests write valid files through `write`; broken ones through `write_json` | a negative test must be able to write what no shape allows | typing the negative tests |
| [D11](#d11) | `record_failure` takes a typed `Failure` | the error record's shape is declared like every other | a free `Mapping` of detail |
| [D12](#d12) | the docs name the contract | the principle's *not yet* for the shapes closes | leaving the principle open |
| [D13](#d13) | phases: guards, contract, then kind by kind, then retirement, then docs | the guards hold every later phase | the retirement in the contract phase |
| [D14](#d14) | a patch, with no spec delta | no requirement or behaviour changes | a minor |

### D1

**`isekai/foundation/artifacts.py` is the run directory's contract.**

- It holds every kind's `TypedDict` ([D2](#d2)), its `Artifact` descriptor ([D3](#d3)), `read` and `write`
  ([D4](#d4)), `DanbooruTag` ([D6](#d6)), `Failure` ([D11](#d11)), and `write_json`, moved from
  `run.py:218-220` unchanged.
- `run.py` keeps the layout, the numbering, the frame's creation, the failure mechanics, and
  `instructions_record` and `constant_record`, which now return the record shapes `artifacts.py` declares.
- **The import runs one way:** `run.py` imports `artifacts.py`, which imports only the standard library,
  `foundation/atomic_write.py` and `foundation/refusal.py`. It stays stdlib-only, because `run.py` is on
  `python -m isekai`'s import graph (`tests/test_pipeline_cli.py`'s `-S` guard).
- `write_json`'s importers follow it, with no re-export: `isekai/pipeline/caption.py:52`,
  `generate.py:63`, `review.py:56`, `sheet.py:56`, `tagging.py:55`, `tests/stages.py:28`,
  `tests/test_run_directory.py:44`.

### D2

**A `TypedDict` per kind, and per producer.** The shapes are today's, key for key and in today's order.

| shape | keys | producer shape and its keys |
|---|---|---|
| `Frame` | `schema`, `id`, `photo` (`PhotoRecord`: `name`, `sha256`, `bytes`, `media_type`) | none |
| `ErrorRecord` | `schema`, `version`, `attempt`, `kind`, `stage`, `detail`, `seed` *(NotRequired)* | none |
| `Caption` | `schema`, `producer`, `prose` | `CaptionProducer`: `implementation`, `models`, `pinned`, `briefing` (`InstructionsRecord`: `path`, `sha256`) |
| `Wd14` | `schema`, `producer`, `tags` (`ScoredTag`: `tag` as `DanbooruTag`, `confidence`) | `Wd14Producer`: `implementation`, `models`, `pinned`, `artifacts` (`dict[str, DigestRecord]`) |
| `Tags` | `schema`, `producer`, `tags` (`list[str]`) | `TagsProducer`: `implementation`, `models`, `pinned`, `prompt` (`DigestRecord`: `sha256`) |
| `Sheet` | `schema`, `producer`, `schema_document`, `vocabulary`, `field_map`, `fields` | `SheetProducer`: `implementation`, `models`, `pinned`, `artifacts`, `from` |
| `ReviewDraft` | `schema`, `producer`, `flow`, `sheet`, `vocabulary`, `fields` | `ChainProducer`: `implementation`, `from`, `source` |
| `ReviewApproved` | as `ReviewDraft` | `ApprovedProducer`: `implementation`, `from`, `source`, `edited`, `approved_from` |
| `Prompt` | `schema`, `producer`, `flow`, `positive`, `negative`, `edited` | `ChainProducer` |
| `Render` | `schema`, `producer`, `flow`, `seed`, `sheet_version`, `graph_sha256`, `flow_graph_sha256`, `edited` | `ChainProducer` |

- `schema` is `SchemaBlock`: `name`, then `version`. `vocabulary` is `VocabularyRecord` (`name`, `revision`,
  `sha256`); `field_map` is `FieldMapRecord` (`name`, `revision` as `int`, `sha256`); `fields` is
  `dict[str, list[str]]`.
- **A producer with a `from` key uses `TypedDict`'s functional form**, since `from` is a Python keyword.
- **`Sheet` is today's shape.** A comment beside it states that runs written before v0.21 hold earlier sheet
  shapes under the same version, and that readers use only `vocabulary` and `fields`.
- **`ErrorRecord.kind` is a `str`.** `Kind` stays in `run.py`, where the failure mechanics use it; the
  filename, not the file, is where a kind is read.

### D3

**One `Artifact[T]` descriptor per kind**: a frozen, generic class with `name` and `version`, and a `schema`
property returning the `SchemaBlock`.

```python
CAPTION_FILE: Artifact[Caption] = Artifact("caption", 1)
```

- **The descriptors end in `_FILE`** — `RUN_FILE`, `ERROR_FILE`, `CAPTION_FILE`, `WD14_FILE`, `TAGS_FILE`,
  `SHEET_FILE`, `DRAFT_FILE`, `APPROVED_FILE`, `PROMPT_FILE`, `RENDER_FILE` — because `WD14`, `TAGS` and
  `REVIEW` already name stage directories.
- **The draft and the approved sheet share the name `review` and one version**, declared once:
  `APPROVED_FILE`'s version is `DRAFT_FILE.version`.
- The version is each kind's own. All are `1`, as every file on disk declares.

### D4

**One writer and one reader.**

- `write(path, kind: Artifact[T], artifact: T) -> None` writes the whole file through `write_json`. A writer
  passes a dict literal that opens with `"schema": KIND.schema`; `ty` checks it against the shape, and the
  literal's order is the file's key order.
- `read(path, kind: Artifact[T]) -> T` parses the file and refuses a version other than `kind.version`, with
  `read_artifact`'s text word for word — `kind.version` where `SCHEMA_VERSION` stood. It does not check the
  name.
- **`Run.frame` returns a `Frame` without the version check**, as today. **`run_view._producer_of` keeps its
  bare `json.loads`**: it reads every kind's producer and reports an unreadable file rather than refusing.

### D5

**Every production writer and reader converts**, in [D13](#d13)'s phases:

| phase | writers | readers |
|---|---|---|
| run files | `open_run`, `record_failure` | `Run.frame` |
| readings | `caption.py:249-261`, `tagging.py:284-297`, `tagging.py:350-363` | — |
| sheets | `sheet.py:125-147`, `review.py:146-159`, `:220-222`, `:321-343` | `sheet.py:118`, `review.py:144` ([D5a](#d5a)), `:209`, `:303`, `:357` |
| renders | `generate.py:191-203`, `:454-469` | `generate.py:173`, `:410` |
| readers | — | `app.py:250`, `:261`, `:376`, `:411`; `scripts/derive_field_map.py:465` |

#### D5a

**`review()`'s origin is read with one typed read per branch** (`review.py:136-156`): `read(origin,
APPROVED_FILE)` when an approval exists, `read(origin, SHEET_FILE)` otherwise. The draft's `sheet` number
comes from the approved file's `sheet`, or from `source_sheet`, so `carried.get("sheet", source_sheet)` goes
and the result is the same.

`save_draft` (`review.py:220-222`) rewrites the draft it read, with its `fields` replaced; `approve` spreads
the draft's producer into `ApprovedProducer`. Both keep today's key order.

### D6

**`DanbooruTag = NewType("DanbooruTag", str)`**, in `artifacts.py`.

- `ScoredTag.tag` and `Scored.tag` (`isekai/boundary/wd14.py:123-127`) are `DanbooruTag`; `wd14.py:347`
  wraps `label.name`.
- `route` (`isekai/shared/field_map.py`) takes `Iterable[DanbooruTag]`; `sheet.py:120` passes the typed
  WD14 file's tags. `normalise` still takes any `str`: it is the one conversion to the prompt's spelling.
- `tests/test_wd14.py:91` and `:99` build `Scored(tag=DanbooruTag("1girl"), …)`.
- No runtime code: a `NewType` is the `str` it wraps.

### D7

**The old names go once nothing calls them**, in the readers phase:

- `SCHEMA_VERSION`, `envelope` and `read_artifact` are deleted from `run.py`.
- Tests that read a file with `read_artifact` call `read(path, KIND)`: `tests/test_caption.py`,
  `tests/test_generate.py`, `tests/test_resume.py`, `tests/test_review.py`, `tests/test_run_directory.py`,
  `tests/test_sheet_stage.py`, `tests/test_tagging.py`, `tests/test_ui_api.py`. The version-refusal tests
  (`tests/test_run_directory.py:384-415`, `tests/test_resume.py:320-324`) keep their assertions and
  bindings, with `CAPTION_FILE.version` where `SCHEMA_VERSION` stood.
- Tests that build a file with `envelope` write it through `write` when it is valid, and through
  `write_json` when it is broken on purpose ([D10](#d10)).
- **`CLAUDE.md:123`**: *"the artifact envelope's `SCHEMA_VERSION`"* → *"any run file kind's version, which
  `isekai/foundation/artifacts.py` declares"*. **`CLAUDE.md:136`**: *"the gate array"* → *"the gate"*
  (`v0.22.5 review/R2`).

### D8

**A golden file per kind**, in `tests/golden/`, compared byte for byte by `tests/test_artifact_bytes.py`.

- Each golden is written by the production function that writes that kind, from fixed inputs: `open_run`,
  `record_failure`, the caption stage with `FakeReader`, `caption_wd14` with `tests.stages.fake_tagger`, the
  hosted tagger with `FakeTagger`, the sheet stage, `review`, `approve`, `prompt_artifact`, and `render`
  with `FakeComfyClient`.
- **They are captured in the guards phase, from today's code**, and never regenerated by this change. A
  golden that changes in a later phase is a defect in that phase.
- One test, `test_each_kind_is_written_byte_for_byte`, parametrised over the kinds.
  `spec_exempt("structural: the bytes each writer produces are pinned before the contract changes it")`.

### D9

**The tripwire: in `isekai/`, only `foundation/artifacts.py` calls `write_json`.**

- `test_only_the_contract_writes_a_run_file`, an AST scan in `tests/test_artifact_bytes.py` like
  `tests/test_layers.py`'s, counting calls of `write_json` and `envelope`.
- **It lands with an exact allowlist of today's callers** — `isekai/foundation/run.py`,
  `isekai/pipeline/caption.py`, `isekai/pipeline/tagging.py`, `isekai/pipeline/sheet.py`,
  `isekai/pipeline/review.py`, `isekai/pipeline/generate.py`. A listed module that no longer calls either
  fails the test, so each phase deletes the entries it converts. The docs phase deletes the empty allowlist.
- A twin builds a module that calls `write_json` and asserts the check reports it.
- `tests/test_ui.py:281`'s forbidden strings lose `"envelope("` and gain `"write("`, since `write` is now how
  a file is built.

### D10

**Tests write valid files through the contract.**

- `tests/stages.py`'s `write_wd14` (`:102-135`) builds its file with `write(path, WD14_FILE, …)`, and its
  default tags (`:99`) are production's spelling: `long_hair`, `brown_hair`, `smile`, `shirt`. The WD14
  literals in `tests/test_sheet_stage.py` switch to underscores. **Outcomes do not change**: the router
  normalises. This pays the backlog row `stages-spelling`.
- **Negative tests keep writing broken files** — `{}`, a schema named `c`, versions `2` and `99`, a missing
  `fields` — with `write_json` or `write_text`.

### D11

**`record_failure(directory, version, kind, failure: Failure)`**, where `Failure` is `stage`, `detail` and
an optional `seed`.

- The record is `schema`, `version`, `attempt`, `kind`, then the failure's keys in the order the caller
  built them — `generate.py:442`'s `stage`, `seed`, `detail` stays in that order.
- Tests that record a failure with no detail pass a `stage` and a `detail`: `tests/test_run_directory.py`
  (`:476`, `:487`, `:488`, `:502`, `:518`, `:535`, `:551`, `:577`), `tests/test_generate.py:764`,
  `tests/test_sheet_stage.py:156`, `tests/test_tagging.py:241`, `tests/test_resume.py:308`. Only file names
  are read from an error record, so no assertion changes.

### D12

**The docs name the contract.**

- `docs/principles.md`, *The run directory is the only channel*: the *not yet, for the shapes* sub-bullet
  becomes the golden test and the tripwire, by name.
- `docs/modules.md` and `isekai/foundation/README.md` add `artifacts.py`.
- `docs/data-flow.md` says where a file's shape is declared.
- Docstrings that name what is retired: `isekai/interface/cli.py:9-12` (*"Only schema version 1 exists"*)
  and `isekai/interface/ui/app.py:435-443` (*"`schema.version` is the constant `1`"*, *"which
  `read_artifact` refuses"*).

### D13

**Phases**, each green alone:

```
1 guards      golden bytes for every kind, from today's code · the tripwire and its allowlist
2 contract    foundation/artifacts.py: shapes, descriptors, read, write, DanbooruTag,
              Failure · write_json moves in
3 run files   frame, error record                                  allowlist − run.py
4 readings    caption, wd14, tags · Scored.tag                     − caption.py, tagging.py
5 sheets      sheet, review draft, review approved · route         − sheet.py, review.py
6 renders     prompt, render sidecar                               − generate.py
7 readers     app.py, derive_field_map.py · SCHEMA_VERSION, envelope, read_artifact
              deleted · tests converted · stages.py, underscores · CLAUDE.md
8 docs        principles, modules, data-flow, foundation README, docstrings · allowlist deleted
```

**One refinement of the grilling's order, from A4 (*keep the old thing declared until the new one is
proven*):** `SCHEMA_VERSION` and `CLAUDE.md`'s wording leave in the readers phase, once the last caller
has converted, not in the contract phase.

### D14

**This is a patch, and it carries no spec delta.**

| condition | met because |
|---|---|
| no format version moves | every kind's version is `1`, as `SCHEMA_VERSION` was; the golden files prove the bytes |
| a behaviour fix is required by an existing requirement | no behaviour is fixed |
| nothing deprecates a verb or a flag | no verb or flag changes |
| nothing changes the product | the sheet, the prompt and the image are untouched |

No requirement changes: *An unknown schema version is refused, naming the fix* still holds, per kind and
with the same text; *The server never constructs an artifact body or an artifact filename* still holds.

## Dependencies

None.

## Risks / Trade-offs

- **`ty` may not accept a `TypedDict` literal spread with `**`** — `save_draft`'s `{**body, "fields": …}`,
  `approve`'s producer, `record_failure`'s failure. → Build the literal key by key in today's order; the
  goldens catch any reordering.
- **A `TypedDict` is a claim, not a check.** A file that does not match its shape reads as before, typed
  wrongly. → Deliberate ([D2](#d2)); runtime validation is behaviour, and waits for a change that asks for it.
- **Older sheets are typed as today's.** → Readers use only keys every sheet shape has.
- **The goldens depend on fixture inputs** — the flow's briefing file, `FAKE_PINS`, the fixture photograph.
  → They are committed and pinned; a golden that moves when a fixture moves is regenerated in that change,
  not this one.

## Verdict

**`feasible`.** Structural: every kind keeps its bytes, proven by a golden per kind before anything moves,
and every read accepts what it accepted.
