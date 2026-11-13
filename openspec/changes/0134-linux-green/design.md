# Linux green — design

Each platform difference that keeps `main` red on Linux, fixed at its cause: one product line with a twin that holds on any machine, and tests that stop pinning what only one machine writes. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

CI runs ubuntu-24.04 with the system's Python; the Mac runs a managed Python, an Accelerate numpy and a zlib-ng Pillow. The gate fails on Linux for differences no single pin closes: the lock holds the same numpy and Pillow versions, whose wheels bring different native backends.

| machine | Python | numpy solver | Pillow's deflate |
|---|---|---|---|
| Mac | managed 3.12.14 | Accelerate | zlib-ng |
| CI | system 3.12.3 | OpenBLAS | the system's zlib |

| red on Linux | cause | the fix | phase |
|---|---|---|---|
| `tests/test_chain.py::test_chain_lookup_samples_between_pixels_bilinearly` | the solve maps a pixel to y = -3e-15; `_sample` has no tolerance, so the pixel reads transparent white | [D1](#d1): a tolerance at the edge | 1 |
| `tests/test_artifact_bytes.py::test_each_kind_is_written_byte_for_byte[edit]` | the golden holds the digests of two PNGs, which deflate differently | [D2](#d2), [D3](#d3): check each digest against its file, compare a placeholder | 2 |
| `tests/test_record.py::test_each_record_file_is_what_the_writer_derives[run]` | the run's record holds the same digests | [D2](#d2), [D3](#d3) | 2 |
| `tests/test_record.py::test_each_record_file_is_what_the_writer_derives[verbs]` and `test_the_walk_reads_each_flag_of_a_parser` | from Python 3.12.7 a positional with `nargs="*"` is not required | [D4](#d4): pin the Python | 3 |
| `tests/test_record.py::test_the_record_directory_holds_the_files_the_writer_names` | it lists the records above as differing | none of its own | 2, 3 |

The product is right in each row but the first: a digest checks a file on the machine that wrote it, and the files travel as bytes.

## Goals / Non-Goals

- **Goals:** the gate is green on Linux and on the Mac; each fix holds by construction, with a twin that fails without it on any machine.
- **Non-Goals:** reading CI before a merge; a deterministic PNG encoder; a change to the pod image's Python; any other fact of the series.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `_sample` takes a point within `EDGE`, 1e-9 px, of the image's edge as on it | the solver's rounding differs by 1e-15 px between machines, and a pixel row must not flip with it | a test moved off the edge: the product still flips; a wider tolerance: it moves visible pixels |
| [D2](#d2) | each PNG digest is checked against its file's bytes, then compared as a placeholder | a digest checks a file only on the machine that wrote it | pin the encoder: `compress_level=0` makes every file far larger; commit a fixed PNG: the product re-encodes the composite; drop the digest: the record then checks nothing |
| [D3](#d3) | the golden names each placeholder for its file; the record names none | the edit record names its files; the run's record holds many PNGs of equal bytes | one form for both: a name in the record is the first of several equal files, which reads as a claim |
| [D4](#d4) | `.python-version` is `3.12.14` | CI's uv then takes the Mac's Python, and no later patch moves the record | `requires-python = ">=3.12.7"`: it moves `pyproject.toml` and `uv.lock` and still allows any later patch; recording `required` for options alone: it hides a real interpreter difference |
| [D5](#d5) | the verbs' record names an action by its kind | a rename of argparse's private class must not move a record | recording `type(action).__name__`: it is argparse's private name |

### D1

`isekai/shared/chain.py` gains `EDGE = 1e-9`. The `inside` test of `_sample` reads `x >= -EDGE`, `y >= -EDGE`, `x <= width - 1 + EDGE` and `y <= height - 1 + EDGE`.
`x0` and `y0` are already clipped, and `fx` and `fy` stay within 1e-9 of 0 and 1, so no other line changes. No requirement changes: *a lookup outside the tattoo SHALL be transparent white* stands, and the delta adds the scenario [a point a hair past the edge is on it](specs/tattoo/spec.md).

```
 target pixel (0,0)  --stage-->  (1.5, y)      y on Mac  = 0.0
                                               y on CI   = -3.2e-15

 before   y >= 0           CI: outside -> transparent white (1.0)
 after    y >= -1e-9       both: inside -> the ink's top row (0.5)
```

### D2

For the `edit` kind, the byte-for-byte test reads the record, checks `source_sha256` against the sha256 of the file the record's `source` names and `composite_sha256` against the sha256 of the record's `.composite.png`, then replaces each digest by its placeholder before it compares with `tests/golden/edit.json`.
For the run's record, `normalised` in `tests/record.py` replaces each string equal to the sha256 of a PNG under the root by a placeholder, and `tests/record/run.json` is written again. A digest equal to no PNG stays as it is, so a wrong digest still fails.

### D3

The golden's placeholders are `<sha256 of 42.png>` and `<sha256 of 42.edit-1.composite.png>`. The run's record writes `<sha256 of a PNG>` for each digest.

### D4

`.python-version` holds `3.12.14` and nothing else. `pyproject.toml` and `uv.lock` keep `requires-python = ">=3.12"`, so the lock does not move. The image's own `image/.python-version` is frozen and not touched.

### D5

`tests/record.py` holds a table from argparse's own action classes to their kinds: `store`, `store_true`, `append`, `help` and `boolean_optional`. A class defined outside `argparse` is recorded by its own `__name__`. An argparse class the table lacks raises a `ValueError` naming it, so a new kind is a decision and not a silent value.

```
 _StoreAction          -> "store"
 _StoreTrueAction      -> "store_true"
 _AppendAction         -> "append"
 _HelpAction           -> "help"
 BooleanOptionalAction -> "boolean_optional"
 isekai's _Targets     -> "_Targets"   (its own class)
```

## Tests

Tests only grow by the twins below, and no end-to-end run is added: every test is a unit test, at the lowest layer that can fail for its behaviour ([T1](../../../CODING_STANDARDS.md)).
At the cut, `uv run pytest --collect-only -q tests/test_chain.py tests/test_artifact_bytes.py tests/test_record.py` ends `63 tests collected`; after the build it ends `67 tests collected`. The browser runs added are none: tests × engines is 0.

| test | file | layer | why it is a new test | its twin proves |
|---|---|---|---|---|
| `test_chain_lookup_takes_a_point_a_hair_past_the_edge_as_on_it` | `tests/test_chain.py` | unit | binds the new scenario; the existing bilinear test reaches the edge only by a solver's rounding | a point 1e-12 px past each edge is on it and one 1e-6 px past is not, on any machine |
| `test_an_edit_record_holds_whatever_level_its_png_was_deflated_at` | `tests/test_artifact_bytes.py` | unit | twin of `test_each_kind_is_written_byte_for_byte`: the source PNG deflated at level 1 and at level 9 | the held record equals the golden at both levels, while the written records differ |
| `test_a_png_digest_in_a_json_file_is_a_placeholder` | `tests/test_record.py` | unit | twin of `test_each_record_file_is_what_the_writer_derives`: a digest of a PNG deflated at level 0 and at level 9 | both levels normalise alike, and a digest of no PNG stays |
| `test_the_interpreter_is_pinned_to_a_patch` | `tests/test_record.py` | unit | the pin is held by a test: a bare `3.12` is red | `.python-version` names a full `3.12.N` from 7 on |

These existing tests change and are not new: `test_each_kind_is_written_byte_for_byte` holds the edit record by its placeholders, and `test_the_walk_reads_each_flag_of_a_parser` expects kinds and walks a store-true flag and a class of its own.
`tests/record.py`, the record's writer, gains the placeholder and the action kinds. `tests/golden/edit.json`, `tests/record/run.json` and `tests/record/verbs.json` are written again, by hand and by `uv run python -m tests.record`; they are files of the tests above and no test of their own. No test is deleted or merged, so there is no table of retired tests.

The moved lines of `isekai/shared/chain.py` are pre-flighted by [CONTRIBUTING](../../../CONTRIBUTING.md): `uv run python -m tools.mutate isekai/shared/chain.py:118 --tests tests/test_chain.py` leaves survivors before the edit, all on the far edges: `width + 1`, `height + 1` and `height - (1 + 1)`. The new test puts a point past each far edge, which kills them; after the edit the lines of `inside` begin at the first match of `grep -n -F "inside = " isekai/shared/chain.py` and end where its expression does.

## Dependencies

None.

## Risks / Trade-offs

- **CI is the proof.** The sandbox has no Linux, so CI's run on the merge's push proves each fix; each has a twin that holds here by construction. A red run is fixed by a patch at once.
- **A pin costs a download.** CI's uv fetches the managed Python 3.12.14 on its first run, and the setup step's cache keeps it after.
- **A placeholder checks less than a digest.** A record that holds a PNG's digest of the wrong PNG passes; the golden, which names its files, does not.
- **A tolerance admits a hair.** A point 1e-9 px past an edge reads as the edge pixel, for every platform alike.

## Verdict

Ready to build: each fix has its cause proven, its twin and its phase; the product line is one constant and one comparison, and no requirement changes but a scenario added under one.
