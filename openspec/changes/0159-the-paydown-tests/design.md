# The paydown tests — design

The cards of `debt:` close with tests, red runs kept as mutants and one scenario split; no line of the product changes. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`.minions/debt.md` is over its paydown line, and the cards of `debt:` are the ones that touch tests, the mutants' file or a record alone. The page's cards are the next version. Every card here names a line it guards, and each guard exists in the tree today.

```
 card            guarded line                                   test that holds it
 0137·R1         app.py guard: Host checked on every method     test_a_request_carrying_someone_elses_host_is_refused
 0137·S1         staging.py put_file: length before body        test_an_upload_past_its_declared_length_is_refused_...
 0148·R2         rendering.py _held: the running-session reason test_one_quote_covers_every_ticked_collection
 0154·R1         names.py media_type: a third format refused    test_a_source_named_as_a_page_is_served_...
 0154·R1         artifacts.py require: a draft with no sheet    test_review_reads_a_drafted_draft_against_...
 0158·R1         staging.py delete_staging: the cancel          test_staging_serves_a_read_file_full_size_...
```

## Goals / Non-Goals

- Goals: each card of `debt:` closes by what it asks, with a red run kept for the cards that ask one.
- Goals: a patch holds the conditions of [CONTRIBUTING](../../../CONTRIBUTING.md#how-a-change-lands): no format version moves, nothing deprecates a verb or a flag, nothing changes the product, and a scenario added sits under a requirement that exists.
- Non-goals: any line of `isekai/` or `ui/src/`, any archived file, any case in the scanner's twin, any page card.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the foreign-Host test sends a read with the foreign `Host` beside its write | the scenario says no artifact is read, and a guard on writes alone passes the write | a second test: [*Extend before adding*](../../../CODING_STANDARDS.md#project-rules) |
| [D2](#d2) | the upload test makes `starlette.requests.Request.body` raise, and keeps its other patches | the reader's `put` runs after the body is buffered, so a body read before the length check passes it (Q166) | patching a name of `isekai`, which the patch ratchet counts |
| [D3](#d3) | the CSS guard drops comments in one left-to-right pass before it counts; its twin gains a case for each comment form | a block-commented import still counts today (0149·S1) | a TypeScript parser, a dependency for one file |
| [D4](#d4) | the refused third format is a scenario of its own, and its test gains the key | the scenario holds three ANDs where the standard allows two (Q167) | a new requirement, which a patch may not add |
| [D5](#d5) | one edit each in `tests/mutants.json`, after `P6` and before `VT-14`, keeps the red run of a guarded line | a red run kept nowhere is the cards' own complaint (Q165) | the runs in a commit body alone |
| [D6](#d6) | `0135·S1` closes on a check of the scanner's own line; `0143·R1`, `0144·R1` and `0156·R1` close with no edit | the fix is in since `0157`, and an archived change is frozen (Q163, Q164) | a case in the twin, which changes an existing test's expected value |
| [C12](#c12) | decided by the cutter: the third-format edit is anchored in `names.py`, not in the `image.py` lines the brief cites | `media_type` raises the refusal the `/photo` route answers; `image.py` never sees that request | the brief's anchor, which no test reaches |

### D1

In `test_a_request_carrying_someone_elses_host_is_refused`, after the write's assertions, the test sends `client.get(_at(made), headers={"host": f"evil.example:{PORT}"})` and asserts `403` and `{"refusal": "not addressed here"}`. Its name, its key and its lines stay. Edit `PD-1` of [D5](#d5) holds it: the guard on writes alone answers the read `200`.

### D2

The test imports `Request` from `starlette.requests` and patches `Request.body` with a plain function that raises `AssertionError("the request's body was read")`, before it builds its client. The route calls `request.body()` only after its length check, so the refusal comes first and the patch never runs. A body read before the check raises, and the test is red. `tests/test_ratchets.py` counts a patch only when it resolves into the repository's own packages, so the patch of Starlette adds no row, and [D61](../../../docs/decisions.md#d61--what-a-test-replaces-in-the-server-is-a-parameter-of-create_app) is not touched.

### D3

`tests/test_css_files.py` gains one pattern, and `css_faults` counts the imports of the text with every match removed:

```python
COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)
```

One pass takes the earliest comment, so a `//` line holding `/*` hides no import after it. The twin `test_the_check_catches_an_unimported_css_file` gains a tree for each comment form after its `missing` block: an import inside a block comment is `b.css imported 0 times`, and an import after a line comment holding `/*` is no fault. Only the block case is red against today's guard, and it is run red before the guard changes. No existing assertion changes.

### D4

The delta carries the requirement as it stands, each of its scenarios and the new `ui:renders:a-photograph-in-a-third-format-is-refused`, which takes the fourth AND of `ui:renders:a-photograph-is-served-as-its-bytes`. `test_a_source_named_as_a_page_is_served_as_the_image_it_is` gains the new key beside its own; it holds both scenarios and asserts the same. `tests/specs.py` reads an active delta as the living spec, so the binding holds before the release.

### D5

The objects of [the edits](#the-edits) sit in order after `P6` and before `VT-14`, so the page version's edits, which go at the file's end, merge with no conflict. Each `find` occurs once in its file, and each `tests` entry is one test's node id, so a replay runs that test and not its module. A survivor is killed by an assertion in the named test, never named equivalent.

The third-format edit is anchored as [C12](#c12) says.

### The edits

```json
  {
    "finding": "PD-1",
    "path": "isekai/interface/ui/app.py",
    "find": "        if request.headers.get(\"Host\", \"\") not in allowed:\n",
    "replace": "        if request.method != \"GET\" and request.headers.get(\"Host\", \"\") not in allowed:\n",
    "tests": ["tests/test_ui_api.py::test_a_request_carrying_someone_elses_host_is_refused"],
    "why": "the foreign Host is refused on writes alone, so a read of any artifact is answered; the test sent a write only"
  },
  {
    "finding": "PD-2",
    "path": "isekai/interface/ui/routes/staging.py",
    "find": "        declared = request.headers.get(\"content-length\")\n",
    "replace": "        await request.body()\n        declared = request.headers.get(\"content-length\")\n",
    "tests": ["tests/test_ui_api.py::test_an_upload_past_its_declared_length_is_refused_before_its_body_is_read"],
    "why": "an upload's body is buffered before its declared length is checked, so the memory bound is gone; the reader's patch ran after the buffering"
  },
  {
    "finding": "PD-3",
    "path": "isekai/interface/ui/routes/rendering.py",
    "find": "        if self.surface.jobs.running(\"render\"):\n            return \"A render session is running.\"\n",
    "replace": "",
    "tests": ["tests/test_ui_api.py::test_one_quote_covers_every_ticked_collection"],
    "why": "a running session no longer holds the quote and the offer back, so a second render can be offered over the first"
  },
  {
    "finding": "PD-4",
    "path": "isekai/foundation/names.py",
    "find": "    raise Refusal(\n        \"this build reads JPEG and PNG photographs, and these bytes are neither; \"\n        \"convert the photograph to JPEG or PNG and offer it again\"\n    )\n",
    "replace": "    return _SIGNATURES[0][1], _SIGNATURES[0][2]\n",
    "tests": ["tests/test_ui_api.py::test_a_source_named_as_a_page_is_served_as_the_image_it_is"],
    "why": "bytes of a third format are named a supported image, so a run's photograph is served instead of refused"
  },
  {
    "finding": "PD-5",
    "path": "isekai/foundation/artifacts.py",
    "find": "    if not isinstance(body.get(key), shape):\n        noun = _NOUNS.get(shape, \"value\")\n        raise Refusal(f\"{path.name}: records no `{key}` {noun}; {remedy}\")\n",
    "replace": "    return\n",
    "tests": ["tests/test_ui_api.py::test_review_reads_a_drafted_draft_against_its_sheet_and_its_image"],
    "why": "a draft with no sheet number is read as if it had one, and the refusal naming its file is gone"
  },
  {
    "finding": "PD-6",
    "path": "isekai/interface/ui/routes/staging.py",
    "find": "        self.surface.imports.cancel(staged)\n",
    "replace": "        pass\n",
    "tests": ["tests/test_ui_api.py::test_staging_serves_a_read_file_full_size_until_it_is_removed"],
    "why": "a cancelled import answers 200 and deletes nothing, so a person's photographs stay in the staging folder"
  },
```

### D6

`0135·S1`: `_patches` in `tests/test_ratchets.py` binds each node in source order, `for _, _, index in sorted(positioned)`, before it reads that node's patch, and `test_five` of `test_a_reused_local_alias_hides_no_patched_module` holds the rebinding. The task checks that line and edits nothing; the twin gains no case, because a shared-name case would change its expected value.

`0143·R1`, `0144·R1` and `0156·R1` each ask for a word in an archived change. An archived design is frozen ([CODING_STANDARDS](../../../CODING_STANDARDS.md#baseline)); each closes by a checked task that reads the archived line and edits nothing. The release deletes the cards named under `debt:`.

### C12

Decided by the cutter. The third-format edit is anchored in `isekai/foundation/names.py`, not in the `isekai/shared/image.py` lines the brief cites. `/photo` serves a run's photograph through `_photograph`, which calls `media_type`, and the `raise Refusal` of `media_type` is the line that answers `409`. The `image.py` lines are the upload's strip and the importer's report, and no `/photo` test reaches them.

## Tests

The change adds no test function and removes none; each added case rides under a test that holds it, per [*Extend before adding*](../../../CODING_STANDARDS.md#project-rules). No test is deleted or merged, so there is no table of removed tests, and no end-to-end test is added.

| file | what the change does to it | command |
|---|---|---|
| `tests/test_ui_api.py` | a read in one test, a patch in another, a key on a third; no new function | `git grep -c "^def test_a_source_named_as_a_page" -- tests/test_ui_api.py` prints `tests/test_ui_api.py:1` |
| `tests/test_css_files.py` | cases in its twin, one pattern in its guard; no new function | `git grep -c "^def test_" -- tests/test_css_files.py` prints `tests/test_css_files.py:2` |
| `tests/mutants.json` | one edit for each guarded line of [the edits](#the-edits) | `git grep -c -F '"finding": "PD-' -- tests/mutants.json` prints `tests/mutants.json:6` |
| `tests/test_ratchets.py` | read, not edited | `git diff --name-only main...HEAD -- tests/test_ratchets.py` prints nothing |

Every new case is a unit test at the lowest layer that can fail: the foreign Host and the upload through `TestClient`, the guard through a throwaway tree under `tmp_path`.

## Dependencies

None.

## Risks / Trade-offs

- A mutant whose test is one node id may survive when the named test does not reach the edit. The replay says so, and an assertion in that test kills it ([D5](#d5)).
- `//` inside a string literal of `ui/src/main.ts` would read as a comment. The file holds import lines only, so the guard stays a regex ([D3](#d3)).
- The replay of every mutant takes minutes and stays out of the gate, as before.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the tests, the scenario, the red runs, the closings.
