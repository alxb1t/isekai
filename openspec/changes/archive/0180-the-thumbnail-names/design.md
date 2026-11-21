# The thumbnail names — design

A thumbnail's path, its drop and the digest that names it move into `isekai/foundation/library.py`, and `isekai/interface/ui/library.py` re-binds what its readers use. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`thumbnail` and `drop_thumbnails` of `isekai/interface/ui/library.py` each build the path `<library>/.cache/<run digest>/<image's folder in the run>/<stem>.<image digest>.jpg`, one from `image.relative_to(run.path)` and the other from the absolute forms of both. The image digest is `_digest`, a memo keyed by `_key`, what a file's stat says. `_carries` and `_size` read `_key` too.

```
now                                          after
ui/library.py                                foundation/library.py
  thumbnail ──path──┐                          stat_key  file_digest  thumbnail_of
  drop_thumbnails ──┴─ spelled twice           drop_thumbnails ─▶ thumbnail_of
  _key  _digest  _DIGESTS                    ui/library.py
                                               thumbnail ─▶ thumbnail_of, makes the JPEG
                                               _key _digest drop_thumbnails: re-bound
```

A thumbnail is named by its image's digest, so it goes while the image is still a file. A delete's one owner in the foundation, which [the next version](proposal.md#not-in-this-change) adds, must drop it first, and a foundation module cannot import the interface. The foundation already holds `CACHE`, `RUNS`, `is_collection` and `Run`, so the names read nothing above it.

`wc -l isekai/interface/ui/library.py` prints 806 at the base, and its row in the long files' ratchet says 881. The moved names take it under the ceiling in phase 1, as [D6](#d6) counts.

## Goals / Non-Goals

- Goals: a thumbnail's path is spelled once; the digest and its stat key are foundation names; the `discard` verb stops importing the UI package for the drop; no path a thumbnail takes and no line the verb prints changes.
- Non-Goals: see [proposal](proposal.md#not-in-this-change). In short, the delete's owner, the sources' thumbnails and `render_running`'s wrapper are not here.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `thumbnail_of(library, run, image)` in `foundation/library.py` returns a thumbnail's path, made or not; `thumbnail` and `drop_thumbnails` both call it | the path was spelled twice, and a delete's owner needs it below the interface | a second spelling in the foundation's drop; a method on `Run` |
| [D2](#d2) | `stat_key` and `file_digest` with the `_DIGESTS` memo move to `foundation/library.py`; `ui/library.py` re-binds them as `_key` and `_digest`; `_CARRIES` and `_SIZES` stay | the path reads the digest, `_carries` and `_size` read the key, and tests read `library._digest` | moving `_carries` and `_size`: they are no thumbnail's name; a second stat key in the foundation |
| [D3](#d3) | `drop_thumbnails` moves with its text but for the path, which it takes from `thumbnail_of`; `ui/library.py` re-binds it as `drop_thumbnails as drop_thumbnails` | the route and a test call `library.drop_thumbnails`, and no importer changes | repointing the route and the test: both edit existing code or a test |
| [D4](#d4) | `ui/__init__.py` loses its wrapper of `drop_thumbnails`; `verbs/drafts.py` imports it from `isekai.foundation.library` and still imports `render_running` from the UI inside the handler | the wrapper only forwarded; `render_running` stays out of scope | moving `render_running` too: it is a different version's subject |
| [D5](#d5) | the lines that move are measured by `tools.mutate` before they move; the cases for the new names are written first, green on the old home, and switched to the foundation's names in the move | a move is pre-flighted, and a case at the new home proves the move kept the answers | a pre-flight over the whole of `ui/library.py`: its other lines move in no phase |
| [D6](#d6) | the file's row in `LONG_FILES` and the table's count go in phase 1, where `ui/library.py` first falls to 800 lines or fewer | a row whose offender no longer offends is red ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)), so phase 1 ends green only without it | a phase of its own after the drop: phase 1 would end red |
| [D7](#d7) | [D68](../../../docs/decisions.md#d68--the-collections-names-and-the-sessions-read-side-are-foundationlibrarypy-re-bound-at-their-old-homes) is amended and no decision is added | the change widens D68's list of names and adds no rule | a new decision: the rule that the library's names live in `foundation/library.py` is D68's |

### D1

`thumbnail_of` takes both paths absolute, as `drop_thumbnails` did, so the verb's relative paths and the route's absolute ones give one answer:

```python
def thumbnail_of(library: Path, run: Run, image: Path) -> Path:
    """Return where `image`'s thumbnail sits in `library`'s cache, made or not.

    Under `.cache/<run digest>/` at the image's path in the run, named by the image's
    own digest too: two collections can hold one source rendered at one seed, and only
    the bytes tell them apart. The image must exist, since its bytes name the file.
    e.g. `…/outputs/001/42.png` -> `.cache/0d4b…/…/001/42.<image digest>.jpg`
    """
    within = image.absolute().relative_to(run.path.absolute())
    named = f"{within.stem}.{file_digest(image)}.jpg"
    return library / CACHE / run.digest / within.parent / named
```

`thumbnail` keeps its docstring and reads `cached = thumbnail_of(library, run, image)` where it built `within`, `named` and `cached`; the rest of its body stands. Its callers pass a path the route built under `run.path`, so both forms were absolute or both relative, and the answer is the one it gave.

### D2

`stat_key` and `file_digest` are `_key` and `_digest` with their text unchanged, the memo is `_DIGESTS` as it was, and the comment above it names the file's digest alone:

```python
# A file's digest by what its stat says: reading every photograph on every listing
# would read the whole library each time.
_DIGESTS: dict[tuple[str, int, int, int], str] = {}
```

`ui/library.py` binds `from isekai.foundation.library import file_digest as _digest` and `from isekai.foundation.library import stat_key as _key`, in the sorted place of its `X as X` lines, and drops `digest_of` from its import from `isekai.foundation.run`. The comment above its `_CARRIES` and `_SIZES` stays two lines, so the ranges below hold:

```python
# What a source carries and its size, by what its file's stat says: reading every
# photograph on every listing would read the whole library each time.
```

`source_thumbnail` and the sources' listing call `_digest` as before.

### D3

`drop_thumbnails` is appended after `thumbnail_of` with its docstring unchanged and its path from the builder:

```python
    folder = run.path.absolute()
    if not (folder.parent.name == RUNS and is_collection(folder.parent.parent)):
        return []
    own = thumbnail_of(folder.parents[2], run, image)
    if not own.is_file():
        return []
    own.unlink()
    return [own]
```

The old body built `within` from `image.absolute().parent.relative_to(folder)`; the builder takes `image.absolute().relative_to(folder).parent`, the same folder for an image under the run. `foundation/library.py` imports `ID_DIGEST_CHARS`, `Run` and `digest_of` from `isekai.foundation.run` in one line, and its docstring gains the thumbnail's path and its digest:

```python
"""The library's folder names and a collection's, and its session records' read side.

`RUNS` is a collection's runs root and `SOURCES` its photographs' folder; `names.py`'s
`SOURCES` is a flow's. A folder in the library is a collection when it holds
`sources/` (D40), and a dot-folder is never listed. A thumbnail's path in the cache
and the digest that names it are here too (D68).
"""
```

The module's names land in this order after `_session`: `_DIGESTS`, `stat_key`, `file_digest`, `thumbnail_of`, `drop_thumbnails`. That fixes the line numbers the closing runs name.

### D4

`ui/__init__.py` deletes `drop_thumbnails` and keeps `render_running`, `Run` and `Path`, which it still reads. `verbs/drafts.py` adds `from isekai.foundation.library import drop_thumbnails` between its imports of `flow` and `refusal`, and its handler imports `render_running` alone from `isekai.interface.ui`. The verb's docstring stands: the UI is still imported inside the handler for `render_running`. `foundation/library.py` is standard library and foundation only, so it stays on `python -m isekai`'s import graph.

### D5

The pre-flight is `tools.mutate` over each range, one run a range, on the tests that reach it, leaving out the draft-lock race test, which races by design and times a mutant out. The cut ran each at `3dc8274b`:

| range at the base | what it holds | result |
|---|---|---|
| `ui/library.py:444-458` | `thumbnail` | 3 killed, 0 survived |
| `ui/library.py:461-479` | `drop_thumbnails` | 9 killed, 0 survived |
| `ui/library.py:683-694` | `_key` and `_digest` | 3 killed, 0 survived |

The command is `uv run python -m tools.mutate isekai/interface/ui/library.py:<lo>-<hi> --tests tests/test_ui_library.py tests/test_pipeline_cli.py tests/test_ui_api.py "-k not test_without_the_lock_an_update_writes_after_the_approval"`. No mutant survives at the base, so no case is written to kill one. A build whose base differs, `0179` having landed, runs the same command over each function's lines from its `def` to its last line, and kills a survivor by a case in `tests/test_ui_library.py` before the lines move.

The closing runs name the ranges as D1 to D3 leave them, after phase 2:

| function | range after the change |
|---|---|
| `stat_key` and `file_digest` | `isekai/foundation/library.py:153-164` |
| `thumbnail_of` | `isekai/foundation/library.py:167-177` |
| `drop_thumbnails` | `isekai/foundation/library.py:180-196` |
| `thumbnail` | `isekai/interface/ui/library.py:447-459` |

They sit in phase 2's last tasks, because that phase is the last to edit either file. A rescue re-fits them if the text differs from D1 to D4, or if `0179` left `ui/library.py` another length; a range with no mutant is refused with exit 2.

The cases are unit tests in `tests/test_ui_library.py`, written against `library.thumbnail` and `library._digest` and green before a line moves, then switched to `thumbnail_of` and `file_digest` in the same phase:

| case | holds |
|---|---|
| `test_a_thumbnail_is_named_for_its_runs_digest_its_place_and_its_images_digest` | two collections' runs of one source hold different bytes at `outputs/001/42.png`; each thumbnail's path is `<lib>/.cache/<run digest>/summon-anime-wai/outputs/001/42.<image digest>.jpg`, the two differ, and `thumbnail` returns it |
| `test_a_files_digest_is_the_first_twelve_characters_of_its_sha256` | the bytes `abc` give `ba7816bf8f01` |
| `test_a_files_digest_is_read_once_for_one_stat` | a rewrite of equal length with the old mtime keeps the old digest, and a new mtime gives the new one |

### D6

The cut counts the lines of `ui/library.py` by hand, from the base that `0179` leaves. A task of phase 1 measures it with `wc -l` before the row goes, and a measure above the ceiling is a **HALT CHECK**: the plan is wrong. `FILE_ROWS` becomes 4.

| step | lines |
|---|---|
| base at `3dc8274b`, `wc -l` | 806 |
| `0179` adds `current_draft` to the import from `isekai.foundation.run` | +1 |
| phase 1: three imports in, `digest_of` and `_DIGESTS` out | +3 −1 −1 |
| phase 1: `_key` and `_digest` with their blank lines, and `thumbnail`'s path | −14 −2 |
| file after phase 1 | 792 |
| phase 2: `drop_thumbnails` with its blank lines out, one import in | −21 +1 |
| file after phase 2 | 772 |

### D7

- D68's bold paragraph gains `stat_key`, `file_digest`, `thumbnail_of` and `drop_thumbnails`; its heading stays so no link moves.
- Its *Accepts* line loses the clause that `ui/library.py` stays a listed long file and gains that `thumbnail` and the sources' thumbnails stay in it and `render_running` stays wrapped by `ui/__init__.py`. Its *Made by* gains `0180`.
- The foundation README's `library.py` row names the new names, and the interface README's rows for `ui/__init__.py` and `ui/library.py` say what they still hold.
- `tools.derive_imported_by` writes the derived rows.

## Tests

The change adds unit tests in `tests/test_ui_library.py` and no end-to-end run, and removes no test, so no table maps a deleted test. The pre-flight runs read `tests/test_ui_library.py`, `tests/test_pipeline_cli.py` and `tests/test_ui_api.py` and change none of them. `tests/test_ratchets.py` loses a row of its table and its row count, which are the table's data, not an assertion.

| count | command | prints |
|---|---|---|
| unit tests added | `git grep -c -E "^def test_a_(thumbnail_is_named\|files_digest)" -- tests/test_ui_library.py` | `tests/test_ui_library.py:3` |

The thumbnail's case binds the existing scenario `ui:renders:a-thumbnail-is-its-own-images`; the two digest cases carry `structural:` exemptions, because no scenario states how a file is digested ([T1](../../../CODING_STANDARDS.md#baseline): a new test binds a scenario or is structural). They sit at the lowest layer, over files in `tmp_path`, with no server and no page.

## Dependencies

None.

## Risks / Trade-offs

- **A closing range shifts if the text differs from D1 to D4, or if `0179` changes `ui/library.py`'s length.** `0179` is cut, not built, at this cut. A different wrapping of a docstring moves the ranges, and a rescue re-fits them.
- **The measure of [D6](#d6) rests on `0179`'s added line.** It leaves the file a few lines under the ceiling; a miscount past that fails the HALT CHECK of phase 1 rather than a phase later.
- **`ui/library.py` binds private names from another module.** `_digest` and `_key` stay as aliases because `tests/test_pipeline_cli.py`, `tests/test_ui_library.py`, `_carries` and `_size` read them; a later version may repoint them.
- **`thumbnail_of` takes absolute forms of both paths.** An image given relative while the run is absolute now resolves against the working directory, where it raised before; no caller does that.

## Verdict

Ready to build, in the phases of [tasks](tasks.md).
