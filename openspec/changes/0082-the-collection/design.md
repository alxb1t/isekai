# Design — 0082 the collection

Which *batch* becomes *collection*, and which stays. **Verdict: feasible** — a rename with no behaviour of its own,
done in three phases that each end green: the CLI and the stages, the app, the docs.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `f65d803` (`v0.54.0`):

- **The CLI:** `import --batch` (`isekai/interface/cli.py:317–320`); `compare`'s positional `batch` (`:328–330`);
  `compare_view` names `BATCH_RUNS` and `BATCH_PHOTOS` (`isekai/interface/compare_view.py:37`, `:40`), used by
  `isekai/interface/render.py` too.
- **The app:** `library.is_batch` and `library.batch` (`isekai/interface/ui/library.py:221`, `:263`); every API path
  under `/api/b/{batch}` (`isekai/interface/ui/app.py`, `grep -c '"/api/b/'` 23); the event stream's `batch`
  (`isekai/interface/ui/events.py:74–102`); the routes under `/b/:batch/…` (`ui/src/router.ts:18–20`, six in all);
  `useBatchStore` (`ui/src/stores/batch.ts:18`), imported in eight files.
- **The docs:** D40 *A batch is a library folder holding `sources/`* (`docs/decisions.md:297`), linked from
  `docs/data-flow.md:83`; `import --batch` in `README.md:215`, `:323`.
- **Both senses in code:** the folder in `isekai/interface/` and `importing.py`; the processed set in
  `isekai/pipeline/generate.py:3–5`, `isekai/pipeline/review.py:30–31`, `isekai/foundation/run.py:166`, `:708`,
  `isekai/foundation/flow.py:127`, `:281`, `isekai/shared/image.py:46`, `:337`, `isekai/interface/wiring.py:156`; a
  tensor's axis in `isekai/boundary/wd14.py:285`, `:402`.

| measured at the cut | value | command |
|---|---|---|
| `batch` lines in `isekai/` | 309 | `grep -rniwE 'batch\|batches' isekai \| wc -l` |
| `batch` lines in `ui/src/` | 334 | `grep -rniwE 'batch\|batches' ui/src \| wc -l` |
| `batch` lines in `tests/` | 236 | `grep -rniwE 'batch\|batches' tests \| wc -l` |
| vitest tests | 43 | `cat ui/src/*.test.ts ui/src/*/*.test.ts \| grep -cE "^(spec\|test\|it)\("` |
| e2e tests | 32 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** one word per thing. **Non-Goals:** a behaviour change; a file moved on disk; a scenario key renamed.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | **two senses:** a library folder — the thing holding `sources/` and `runs/` — is a **collection**, everywhere it is named; what one verb invocation or render session processes stays a **batch**: the stages, `wiring.py`, `principles.md`, `image-generation`, `run-directory`, the `review` spec, and the phrases *flows batch*, *serve a batch*, *caps a batch*, *mid-batch*, *A batch ends in a question*; `wd14.py`'s batch axis is a tensor's | the multi-batch render needs *batch* free for its set | renaming every *batch* |
| [D2](#d2) | **the CLI and the stages:** `import --collection COLLECTION`, no alias; `compare`'s positional `collection`; `COLLECTION_RUNS`, `COLLECTION_PHOTOS`; every folder-sense word, identifier and refusal in `cli.py`, `render.py`, `compare_view.py`, `importing.py`, `artifacts.py`, `evaluation/`, `tools/derive_field_map.py` | the CLI names what the operator holds | a `--batch` alias |
| [D3](#d3) | **the app:** routes `/c/:collection/…`; API `/api/c/{collection}/…`; payload keys and query parameters `batch` → `collection`; `library.is_collection`, `library.collection`; `ui/src/stores/collection.ts` with `useCollectionStore`; every word on screen — *New collection*, *Add sources*, the Library's rows; no redirect from `/b/` | one word on screen and in the address | redirects |
| [D4](#d4) | **the docs:** D40 → *A collection is a library folder holding `sources/`*, its links re-anchored; `README.md`, `AGENTS.md`, `docs/data-flow.md`, `docs/modules.md`, `ui/design/spec.md` and each code folder's `README.md` in the folder sense; *batch* stays where D1 keeps it | the docs name what the code does | |
| [D5](#d5) | **the spec:** a requirement whose title names the folder is REMOVED and ADDED under the new title; one whose body alone does is MODIFIED; scenario keys, and the scenario headings of a block that keeps its title, are unchanged | the validator reads a renamed heading as a dropped scenario; a key is an id | renaming keys |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | none | every folder-sense name, path and flag — `/api/b/` → `/api/c/`, `--batch` → `--collection`, `BATCH` constants | `tests/test_importing.py`, `tests/test_pipeline_cli.py`, `tests/test_compare.py`, `tests/test_render.py`, `tests/test_ui_api.py`, `tests/test_ui_library.py`, `tests/test_ui_jobs.py` |
| unit · vitest | none | the store's name and every folder-sense identifier | `ui/src/**/*.test.ts` |
| e2e | none | the routes and the words on screen | `tests/e2e/` |

**End-to-end runs added:** none. **Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a processed-set *batch* renamed by a blind replace → D1 lists each kept sense; each phase's check counts
  only the folder-sense files.
- **[Trade-off]** scenario headings in kept-title blocks still say *batch* → their keys do too; the spec audit tidies
  both.

## Verdict

**Feasible.** A rename, phase by phase, each green.
