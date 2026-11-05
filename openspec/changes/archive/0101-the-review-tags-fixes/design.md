# Design — 0101 the review tags fixes

How the deriver excludes every tattoo tag and `photorealistic`, and how the tag search, approval and sheet
preparation keep an excluded tag out of a sheet. **Verdict: feasible.**

## Context

The table is generated: `tools/derive_field_map.py` writes `config/field_map.json`, and
`tests/test_field_map.py::test_the_committed_table_re_derives_without_reading_the_gitignored_runs` wants the re-run
byte-identical. At `7fdbad24`:

```
tools/derive_field_map.py
  :62        REVISION = 3
  :141-154   the comment over EXCLUDED
  :155       EXCLUDED = ("photorealistic",)
  :487-527   build(vocabulary, fields): groups → browsable → {"primary", "also"}; never reads EXCLUDED
  :605       main(): load_vocabulary() (:620), build() (:622), write (:624-634), "excluded" (:630)

isekai/shared/field_map.py   FieldMap.excluded: frozenset[str] (:93); _parse refuses excluded ∩ browsable (:179-187)
isekai/shared/vocabulary.py  Vocabulary.search(self, term) (:112-115); knows no field map
isekai/shared/fields.py      validate(fields, schema, vocabulary, *, remedy=None) (:22); reads no field map
isekai/pipeline/review.py    approve (:897), _copy_approval (:1000); validate at :941 and :1046
isekai/pipeline/sheet.py     validate at :189, :270, :305; each caller holds `field_map`
isekai/interface/ui/app.py   GET /api/tags (:651-672); the approve handler's call (:827-829); shared.field_map() (:1173)
isekai/interface/cli.py      the cached field_map() (:780-789); approve_flow's approve call (:928-934)
```

The table routes these tattoo tags: `stomach tattoo` and `full-body tattoo` → `body_shape`; `shoulder tattoo` →
`clothes` (browsed under `body_shape`); `arm tattoo`, `leg tattoo`, `back tattoo`, `hand tattoo` → `pose`.

The pinned vocabulary, `models/wd14/selected_tags.csv` (`config/vocabulary.json:7-14`), holds these tattoo tags, as the
loader spells them: `tattoo`, `arm tattoo`, `shoulder tattoo`, `facial tattoo`, `pubic tattoo`, `chest tattoo`,
`leg tattoo`, `stomach tattoo`, `number tattoo`, `breast tattoo`, `neck tattoo`, `heart tattoo`, `back tattoo`,
`barcode tattoo`, `full-body tattoo`, `hand tattoo`, `flower tattoo`, `star tattoo`, `glowing tattoo`,
`forehead tattoo`, `teardrop tattoo`, `tribal tattoo`, `butterfly tattoo`.

No `FILED` key holds `tattoo` or
`photorealistic`, so `test_every_approved_tag_is_reachable_in_the_field_it_was_approved_in` is unmoved.

```
tagger ─▶ route() ─▶ sheet ─▶ draft ─▶ approve ─▶ prompt
            ▲                   ▲         ▲
   D1 D2: no group      D3: /api/tags   D4 D5: validate(excluded=)
   holds an excluded    skips one       D6: and at sheet preparation
```

## Goals / Non-Goals

**Goals:** an excluded tag never routes, is never offered, and never approves; the excluded set is read from the
loaded field map at each boundary.

**Non-Goals:** a refusal on save; touching `SourcePanel.vue`, `openspec/specs/ui/spec.md` or any other part of
`isekai/interface/ui/app.py`; re-writing existing sheets.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **The classes.** Below `EXCLUDED`, add `EXCLUDED_CONTAINING: tuple[str, ...] = ("tattoo",)` and `def exclusions(vocabulary: Vocabulary) -> set[str]`, docstring `` """Return `EXCLUDED` and every tag containing an `EXCLUDED_CONTAINING` word.""" ``, body `return set(EXCLUDED).union(*(vocabulary.search(word) for word in EXCLUDED_CONTAINING))`, as `ruff format` wraps it. The comment at `:148-154` becomes [the comment](#the-comment); `:141-147` stay | a word expanded against the pinned vocabulary excludes a tattoo tag a new vocabulary adds, with no edit; `search` is the pipeline's own substring rule | a hand list of the tattoo tags, which drifts from the vocabulary |
| <a id="d2"></a>**D2** | **Subtracted, then re-derived.** `build(vocabulary, fields, excluded: set[str])`; after the loop at `:512-514`, the loop `for field in names:` with `browsable[field] -= excluded` on its own line beneath, under the comment `# No group holds an excluded tag, or the loader refuses the table.` `main()` sets `excluded = exclusions(vocabulary)`, calls `build(vocabulary, fields, excluded)`, and writes `"excluded": vocabulary.rank(excluded),` in place of `:630`'s `"excluded": list(vocabulary.rank(EXCLUDED)),` (`rank` already returns a list). `REVISION = 4`, and the comment's line at `:61` → `# 1 is the first table, 2 the seeded table, 3 the operator's pass, 4 the exclusions.` Then `uv run python -m tools.derive_field_map` rewrites `config/field_map.json` | `_parse` refuses a tag both excluded and browsable, so adding to the list alone breaks the load; subtracting from `browsable` cleans `primary` and `also` together | a hand-edit of the table, which the re-derive test reverts |
| <a id="d3"></a>**D3** | **The search skips.** `Vocabulary.search(self, term: str, *, skip: frozenset[str] = frozenset()) -> list[str]`, docstring `` """Return every tag containing `term`, but those in `skip`, ranked.""" ``, body `needle = normalise(term)` as it is, then `return self.rank(tag for tag in self.counts if needle in tag and tag not in skip)`, as `ruff format` wraps it. In `read_tags` (`app.py:661`): `found = vocabulary.search(fragment, skip=shared.field_map().excluded) if fragment else []`, as `ruff format` wraps it, so `total` leaves them out too | `Vocabulary` knows nothing of the field map, which loads from it; the endpoint holds both | the filter inside `Vocabulary`; a filter in `TagInput.vue` |
| <a id="d4"></a>**D4** | **`validate()` refuses.** `validate(fields, schema, vocabulary, *, excluded: frozenset[str] = frozenset(), remedy: str \| None = None)`. After the spelling check, a last one: each `(name, tag)` with `tag in excluded`, joined as the others are, raises `` Refusal(f"{listed}: on the field map's excluded list, which no criterion can hold; " + (remedy or "delete it from the draft")) ``; approval passes no `remedy`, so it says "delete it from the draft", and sheet preparation's `remedy` at `sheet.py:270` and `:305` stays its own. The docstring becomes [the docstring](#the-docstring) | `sheet --new-version` replaces neither a waiting draft (`review.py:174-175`) nor a draft copied from an approval (`:184-194`), so deleting is the fix that always works (brief Q10); the default keeps every caller that passes nothing as it was | a silent drop at approve, which hides the tag the operator sees |
| <a id="d5"></a>**D5** | **Approval takes it.** `approve(run, flow, schema, vocabulary, source=None, *, excluded: frozenset[str] = frozenset())` passes `excluded=excluded` to `_copy_approval(run, flow, schema, vocabulary, source, *, excluded: frozenset[str])` and to `validate` at `:941`; `_copy_approval` passes it to `validate` at `:1046`. The UI's call at `app.py:827-829` adds `excluded=shared.field_map().excluded`; the CLI's at `cli.py:928-934` adds `excluded=field_map().excluded,` after `source=args.source,`. The fake `approve_` in `tests/test_ui_api.py:1013-1024`, which `_update_during_approval` patches over `app_module.approve`, gains `*, excluded: frozenset[str] = frozenset()` and calls `approving(run, flow, schema, vocabulary, excluded=excluded)`. `save_draft` is unchanged | `approve` holds no field map, and the pipeline must not read `config/field_map.json` itself; saving is not approving (`openspec/specs/review/spec.md:45`) | a refusal on save, which parks a half-edited autosave |
| <a id="d6"></a>**D6** | **Sheet preparation takes it.** `sheet.py`'s `validate` calls at `:189`, `:270` and `:305` each add `excluded=field_map.excluded` | each holds the field map it routes by; the check is what a producer that does not route meets | no check at preparation, which leaves the sheet requirement to routing alone |
| <a id="d7"></a>**D7** | **Docs D2 amended in place** to [the decision](#the-decision); its Made-by becomes `` `0021`, `0101` `` | the excluded classes are a decision in force; D29 is cited, not edited | a new decision entry |

### The comment

`tools/derive_field_map.py:148-154`, before → after:

```
# **One entry, at the operator's call, and it is a start rather than a survey.**
# `photorealistic` describes how the picture was rendered and not the person in
# it, so no identity criterion can hold it -- and the router drops it either way.
# What the entry buys is the record: the absence is a decision somebody took
# rather than a gap nobody had looked at. `realistic` 19,111 is the same kind of
# tag and appears on all eight photographs of the collection `APPROVED` names; it is
# deliberately not here yet, because the operator named one.
```

```
# **Two classes, at the operator's call, and a start rather than a survey.**
# `photorealistic` describes how the picture was rendered and not the person in
# it, and a tattoo is outside what `summon` preserves, so no identity criterion
# can hold either. `EXCLUDED_CONTAINING` is a word, expanded against the pinned
# vocabulary, so every tag containing it is excluded; `build()` subtracts the
# whole set from every group, which the loader's disjointness check needs.
# `realistic` 19,111 is the same kind of tag as `photorealistic` and appears on
# all eight photographs of the collection `APPROVED` names; it is deliberately
# not here yet, because the operator named one.
```

### The docstring

`isekai/shared/fields.py`'s `validate()`, after:

```
    """Refuse a sheet that is not exactly the schema's fields of canonical tags.

    Each way a sheet can be wrong names what to do about it: a field the schema
    declares is missing, a key the schema does not declare is present, a tag is
    not in the vocabulary's prediction set, a tag is not in its spelling, or a
    tag is on the field map's `excluded` list. An empty field is none of those.
    `remedy` replaces each edit-the-sheet advice for a caller whose sheet does
    not exist yet, so editing it is no fix.
    """
```

### The decision

`docs/decisions.md:60-67`, after:

```
### D2 · A table fills the sheet

**The sheet is filled from WD14's tags by one authored table, `config/field_map.json`, read from tag to
field. No model decides a sheet.** No tag on its excluded list — `photorealistic` and every tag containing
`tattoo` — reaches a field: no group holds one, the tag search skips one, and approval and sheet preparation
refuse one.

- **Why:** WD14's tags are all in the vocabulary, because its label file *is* the vocabulary, and a table
  cannot invent a tag. The router placed 73% of the tags offered, and 90% of those survived review.
- **Why those excluded:** neither describes the person: `photorealistic` is how a picture was rendered, and a
  tattoo is outside what `summon` preserves ([D29](#d29--what-summon-preserves)). A sheet routed by an earlier
  table may still hold one, so approval refuses it rather than routing alone.
- **Made by:** `0021`, `0101`.
```

## Tests

Every new test is a pytest unit test, the lowest layer that can fail for each behaviour (`T1`); a `TestClient` test
is the lowest that can fail for the endpoint's wiring. No end-to-end test is added or changed.

| layer | adds | removes |
|---|---|---|
| unit | phase 1: `tests/test_field_map.py::test_the_committed_table_excludes_every_tattoo_tag_and_photorealistic` (`field-map:excluded:tattoos-and-photorealistic-are-excluded`), over `load(provisioned)`: `excluded == {"photorealistic", *provisioned.search("tattoo")}`, `"tattoo"` and `"butterfly tattoo"` in it, and no `field_map.group(field)` meets it | none |
| unit | phase 2: `tests/test_vocabulary.py::test_search_skips_the_tags_it_is_told_to` and `tests/test_ui_api.py::test_the_tag_search_offers_no_excluded_tag` (`field-map:excluded:the-tag-search-skips-an-excluded-tag`); `tests/test_review.py::test_an_excluded_tag_refuses_approval_naming_the_remedy`, `tests/test_review.py::test_an_excluded_tag_refuses_a_copied_approval`, `tests/test_pipeline_cli.py::test_approve_refuses_a_tag_the_wired_field_map_excludes` and `tests/test_ui_api.py::test_approve_refuses_an_excluded_tag_the_draft_saved` (`field-map:excluded:approval-refuses-an-excluded-tag`); `tests/test_sheet_schema.py::test_a_sheet_carrying_an_excluded_tag_is_refused` and `tests/test_sheet_stage.py::test_sheet_preparation_refuses_an_excluded_tag` (`sheet:purity:an-excluded-tag-is-refused`) | none |

- **Markers:** each test carries `@pytest.mark.spec("<key>")` with the key in parentheses after it above; none is
  `spec_exempt`.
- **The fixture tag:** each phase-2 test excludes `glasses`, which `tests/stages.py`'s `FIELD_MAP` routes to
  `accessories`, through `frozenset({"glasses"})` or `replace(FIELD_MAP, excluded=frozenset({"glasses"}))`, as
  `tests/test_ui_api.py:1356` does.
- **The search tests:** `test_search_skips_the_tags_it_is_told_to` asserts
  `vocabulary.search("hair", skip=frozenset({"long hair"}))[:3] == ["short hair", "brown hair", "very long hair"]`.
  `test_the_tag_search_offers_no_excluded_tag` sets `accessories` to an empty `Group`, as `:1357-1359` do, gets
  `/api/tags` with `q="s"` and `limit=100`, and asserts the matches' tags are
  `[t for t in vocabulary.search("s") if t != "glasses"]` and `total` is their length.
- **The fake approve:** `_update_during_approval`'s `approve_` (`tests/test_ui_api.py:1013-1024`) takes and
  passes `excluded`, per [D5](#d5), or `test_an_update_overlapping_an_approval_is_refused` turns red.
- **The draft's tag:** no default draft holds `glasses` (`tests/stages.py`'s `TAGS`), so each approval test puts
  it there: `_edit(draft, accessories=["glasses"])` in `tests/test_review.py`; `save_draft` in
  `tests/test_pipeline_cli.py`; the PUT `/draft` body in `tests/test_ui_api.py`; and for the copy, the source flow
  approved with `glasses` before `approve(..., source=FLOW, excluded=frozenset({"glasses"}))`.
- **The approval remedy:** `test_an_excluded_tag_refuses_approval_naming_the_remedy` asserts the refusal holds
  `glasses`, `accessories` and `delete it from the draft`.
- **The sheet-stage test** calls `tests/stages.py`'s `sheet(run, schema, vocabulary, field_map=replace(FIELD_MAP,
  excluded=frozenset({"glasses"})), tags=[DanbooruTag("glasses")])`, the own-tag-list path; it asserts the `Refusal`
  names `glasses` and `accessories`, and `versions(run.directory(FLOW, "sheets")) == []`. The failure record it
  leaves is not a sheet version.
- **The UI approve test** saves the draft first, and asserts the save answers 200 and the approve 409, naming
  `glasses`.
- **The stale comment** at `tests/test_ui_api.py:1354`, in
  `test_the_excluded_list_reaches_no_group_and_is_not_in_the_response`: "The committed table's excluded list is empty" → "The
  fixture table's excluded list is empty".

At the base, `uv run pytest --collect-only -q --ignore=tests/e2e` collects 1481 tests and
`uv run pytest tests/e2e --collect-only -q` collects 19. This change adds nine unit tests and no end-to-end run. It
deletes and merges no test.

## Dependencies

None.

## Risks / Trade-offs

- **An existing sheet holding an excluded tag now refuses approval** → the refusal names the tag and the remedy;
  this is the intent for sheets routed by an earlier table.
- **A future vocabulary tag containing `tattoo` that is not a tattoo** → excluded too; every such tag in the pinned
  vocabulary is a tattoo, and the re-derive shows any new one in the table's diff.
- **The CLI's approve now reads the field map** → it is cached per invocation beside the vocabulary, and every test
  wiring supplies one.

## Verdict

**feasible.** Every file and line named exists at `7fdbad24`. No dependency, no flow digest and no format version
moves.
