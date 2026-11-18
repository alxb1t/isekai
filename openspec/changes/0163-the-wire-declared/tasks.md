# The wire declared — tasks

The phases: a walker proven on its own declarations, the declarations of the hub, staging and vocabulary tables, those of images and reviewing, then the documents.

## Progress

- [x] 1 — The walker · hard
- [x] 2 — Hub, staging and vocabulary · moderate
- [x] 3 — Images and reviewing · moderate
- [x] 4 — The documents · moderate

## 1 — The walker

- [x] 1.1 Create `tests/test_ui_shapes.py`: a module docstring, `faults(declared, sampled, at)` written to the table of [D4](design.md#d4), and `test_the_walker_accepts_what_a_declaration_allows`, which walks a `TypedDict` of the file's own holding every form of the table against a sampled shape that fits it, with `spec_exempt("structural: the walker takes each form a declaration is written in")`.
  Verify: `uv run pytest tests/test_ui_shapes.py -k accepts` exits 0.
- [x] 1.2 In the same file add `test_the_walker_refuses_an_undeclared_key`, `test_the_walker_refuses_a_missing_required_key` and `test_the_walker_refuses_a_wrong_leaf`, each over the file's own declaration, each asserting `faults(...)` is the one line naming the path, each with a `spec_exempt` reason that opens `structural: twin of` and names the accepting case.
  Verify: `uv run pytest tests/test_ui_shapes.py -k refuses` exits 0.

## 2 — Hub, staging and vocabulary

- [x] 2.1 Create `isekai/interface/ui/shapes.py`: a module docstring that says it declares the server's answers and imports no web framework, `from isekai.pipeline.review import Status`, the path constants `COLLECTION`, `STAGED` and `STAGED_FILE`, and each class of the [declarations](design.md#declarations) from `FlowCount` to `FieldCandidates`, a one-line docstring each.
  Verify: `uv run python -c "from isekai.interface.ui.shapes import HubCell"` exits 0.
- [x] 2.2 In `shapes.py` add `ANSWERS: dict[str, Any]` with the rows of the hub, staging and vocabulary tables of the [keys table](design.md#declarations), each key `f"<METHOD> {PATH}"`, the way the record keys its entries.
  Verify: `uv run python -c "from isekai.interface.ui.shapes import ANSWERS; print(len(ANSWERS))"` prints `10`.
- [x] 2.3 In `tests/test_ui_shapes.py` add `TABLES`, a tuple of the `ROUTES` tuples of `isekai.interface.ui.routes.hub`, `.staging` and `.vocabulary`, imported at the top of the file, and `test_every_answer_fits_the_record` and `test_every_recorded_shape_of_the_tables_has_a_row` as [D5](design.md#d5) says, each with a `spec_exempt("structural: …")` naming its rule.
  Verify: `uv run pytest tests/test_ui_shapes.py -k record` exits 0.
- [x] 2.4 Derive the *Imported by* tables, which `shapes.py`'s import of `pipeline/review.py` makes stale: `uv run python -m tools.derive_imported_by` adds `interface/ui/shapes.py` to the `review.py` row of `isekai/pipeline/README.md` ([D7](design.md#d7)).
  Verify: `uv run pytest tests/test_docs.py` exits 0.

## 3 — Images and reviewing

- [x] 3.1 In `shapes.py` add the path constants `RENDER`, `REVIEW` and `COMPARE`, and each class of the [declarations](design.md#declarations) from `Renders` to `Drafts`, a one-line docstring each.
  Verify: `uv run python -c "from isekai.interface.ui.shapes import InputDetail"` exits 0.
- [x] 3.2 In `shapes.py` add the rows of the images and reviewing tables of the [keys table](design.md#declarations) to `ANSWERS`.
  Verify: `uv run python -c "from isekai.interface.ui.shapes import ANSWERS; print(len(ANSWERS))"` prints `21`.
- [x] 3.3 In `tests/test_ui_shapes.py` add the `ROUTES` tuples of `isekai.interface.ui.routes.images` and `.reviewing` to `TABLES` as further items, imported as `from isekai.interface.ui.routes.reviewing import ROUTES as REVIEWING` and its twin for images.
  Verify: `uv run python -c "from tests.test_ui_shapes import TABLES; print(len(TABLES))"` prints `5`.

## 4 — The documents

- [x] 4.1 In `isekai/interface/README.md` add a row to the *Files* table after the `ui/surface.py` row: ``| `ui/shapes.py` | each JSON answer of the hub, staging, images, vocabulary and review routes as a `TypedDict`, and `ANSWERS`, keyed as `tests/record/routes.json` is; a test holds each against its record and no route reads it. **Imports no web framework** |``.
  Verify: `git grep -c -F 'ui/shapes.py' -- isekai/interface/README.md` prints `isekai/interface/README.md:1`.
- [x] 4.2 In `docs/decisions.md` add D63 after D62 and before `## Infrastructure`, headed `### D63 · The wire is declared in shapes.py and held by tests`, written as D62 is: the rule in bold, then the bullets **Why**, **Accepts** and **Made by**, each as [D8](design.md#d8) gives it.
  Verify: `git grep -c -F '### D63 · The wire is declared in shapes.py and held by tests' -- docs/decisions.md` prints `docs/decisions.md:1`.
