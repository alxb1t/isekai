# The wire derived — tasks

The phases: the tool and its grammar, the file it writes, the documents. No file under `isekai/` changes.

## Progress

- [x] 1 — The grammar · hard
- [ ] 2 — The file · moderate
- [ ] 3 — The documents · moderate

## 1 — The grammar

The cases come first, over trees of their own; then the tool that makes them pass ([D1](design.md#d1)–[D5](design.md#d5)).

- [x] 1.1 Create `tests/test_derive_wire.py` with a helper `_tree(root, files)` that writes each text of `files`, a map from a path relative to `root` to its text, and returns `root`, and the case for the leaves and `None`. Each case carries `@pytest.mark.spec_exempt("structural: …")` and calls `derive(root)` of `tools.derive_wire`.
  Verify: `grep -c -E "^def test_" tests/test_derive_wire.py` prints `1`.
- [x] 1.2 Add the cases for a list, a map by `str`, a map by an alias, `NotRequired` and an inline `Literal` with `None`, each asserting the text of [D2](design.md#d2)'s row.
  Verify: `grep -c -E "^def test_" tests/test_derive_wire.py` prints `6`.
- [x] 1.3 Add the cases for an alias imported through its module, an alias imported by its own name, an alias that nests another, a base in the module, a base in another module whose field names a third class of that module, and an empty class, each asserting the names of [D3](design.md#d3).
  Verify: `grep -c -E "^def test_" tests/test_derive_wire.py` prints `12`.
- [x] 1.4 Add the case for the `Events` map, written in `EVENTS`' order, and the refusal case, parametrised over a union of arms that are not `None`, a tuple and a name that is no class or alias; each refusal matches `<Class>.<field>: … is no form of the wire`.
  Verify: `grep -c -E "^def test_" tests/test_derive_wire.py` prints `14`.
- [x] 1.5 Create `tools/derive_wire.py`: standard library and `ast` alone, `derive(root: Path) -> str` and `main() -> int`, written to [D1](design.md#d1)–[D4](design.md#d4); `main` writes `ui/src/wire.ts` and returns 0, and `python -m tools.derive_wire` runs it.
  Verify: `uv run pytest tests/test_derive_wire.py` passes.
- [x] 1.6 Hold the tool to the standard library: it imports no module of `isekai`.
  Verify: `grep -n -E "^(from|import) isekai" tools/derive_wire.py` prints nothing.

## 2 — The file

The file is what the tool writes from today's `shapes.py`, then the cases that hold it ([D5](design.md#d5)).

- [ ] 2.1 Add to `tests/test_derive_wire.py` the case that `derive(REPO_ROOT)` equals `ui/src/wire.ts`, and the case that the keys of its `Events` block equal `EVENTS`' keys, imported from `isekai.interface.ui.shapes` (the file `isekai/interface/ui/shapes.py`, which this change leaves as it is). Each carries `@pytest.mark.spec_exempt("structural: …")`; the red run, before the file exists, is the proof.
  Verify: `grep -c -E "^def test_" tests/test_derive_wire.py` prints `16`.
- [ ] 2.2 Run `uv run python -m tools.derive_wire` from the repository root, which writes `ui/src/wire.ts`. Edit nothing by hand.
  Verify: `uv run pytest tests/test_derive_wire.py` passes.
- [ ] 2.3 **HALT CHECK** `ui/src/wire.ts` stands within the page's 600-line ratchet. If it does not, stop: the plan splits the file by table, and no row is added.
  Verify: `uv run pytest tests/test_ratchets.py` passes.
- [ ] 2.4 Typecheck the file: the page's tsconfig includes every `.ts` file under `src`, so `vue-tsc` reads it.
  Verify: `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 2.5 Leave the page unread of it: no import in `ui/src` ends in `/wire'`.
  Verify: `git grep -n "/wire'" -- ui/src` prints nothing.

## 3 — The documents

The tool joins `make derive`, and the rule is written where the rules live ([D6](design.md#d6)).

- [ ] 3.1 In `Makefile`, add the tool to the `derive` target after the importer tables, and say so in its comment; the `gate` recipe and `make -n gate` do not change. The new recipe line starts with a tab, as every recipe line does:
  ```diff
  - # vocabulary, the READMEs' importer tables, then the fetched ones.
  + # vocabulary, the READMEs' importer tables, the page's wire, then the fetched ones.
  + uv run python -m tools.derive_wire
  ```
  Verify: `git grep -n "tools.derive_wire" -- Makefile` prints one line.
- [ ] 3.2 In `docs/principles.md`, add `tests/test_derive_wire.py::test_the_committed_wire_is_the_one_the_tool_writes` to the *Held by* bullet of *Configuration is declared, never computed, and declared once*, after the importer tables' test.
  Verify: `git grep -n "test_the_committed_wire_is_the_one_the_tool_writes" -- docs/principles.md` prints one line.
- [ ] 3.3 In `README.md`, change the comment of the `derive_*.py` line of the `tools/` tree from `re-derive the manifests, the field map and image/` to `re-derive the manifests, the field map, image/ and the page's wire`.
  Verify: `git grep -n "the page's wire" -- README.md` prints one line.
- [ ] 3.4 In `docs/decisions.md`, add D67 after D66, titled *The page's wire is derived from shapes.py, and a test re-derives it*: the rule of [D1](design.md#d1)–[D4](design.md#d4), a *Why* (a hand-written copy drifts; a derived one is held by a test; the tool names no `isekai` module), an *Accepts* (a form outside the grammar is refused, a pair stays a list, the page reads the file from `the-page-wire`) and *Made by:* `0168`.
  Verify: `git grep -n "^### D67" -- docs/decisions.md` prints one line.
