# The session requests — tasks

Move the group that reads a render's requests and builds its argv from `isekai/interface/render.py` to `isekai/interface/requests.py`, narrow the wide signatures of `_asked` and `Record.__init__`, and correct the documents. No moved line changes.

## Progress

- [x] 1 — The move · moderate
- [x] 2 — The keywords · moderate
- [x] 3 — The documents · moderate

## 1 — The move

- [x] 1.1 **HALT CHECK** The versions before this one left `Line` and `Edits` in `isekai/interface/plan.py`, which the group reads. A failure means the base is not the one this change was cut on.
  Verify: `grep -n -e "^class Line" -e "^class Edits" isekai/interface/plan.py` prints two lines.
- [x] 1.2 Create `isekai/interface/requests.py` per [D1](design.md#d1): the docstring, the imports, then `REQUEST`, `Generate` with its comment, `Request`, `parse_request`, `in_session_sources`, `again`, `without_flags`, `_taken`, `run_ids`, `_asked`, `_requested` and `_edit_argv`, copied from `isekai/interface/render.py` unchanged with their docstrings.
  Verify: `uv run python -c "from isekai.interface.requests import REQUEST, Generate, Request, parse_request, in_session_sources, again, without_flags, _taken, run_ids, _asked, _requested, _edit_argv"` exits 0.
- [x] 1.3 In `isekai/interface/render.py` delete those definitions and the comment over `Generate`; `REMEDY`, `REFUSALS`, `LOST_EXIT`, `PORT` and their comments stay.
  Verify: `git grep -n -e "^REQUEST" -e "^Generate" -e "^class Request" -e "^def parse_request" -e "^def in_session_sources" -e "^def again" -e "^def without_flags" -e "^def _taken" -e "^def run_ids" -e "^def _asked" -e "^def _requested" -e "^def _edit_argv" -- isekai/interface/render.py` prints nothing.
- [x] 1.4 In `render.py` import from `isekai.interface.requests`, per [D2](design.md#d2). Plainly: `Generate`, `_asked`, `_edit_argv`, `_taken`, `again`, `in_session_sources`, `parse_request`, `run_ids`. As `without_flags as without_flags`, its own statement as `record_running` is, under a comment that `ui/jobs.py` and a test import it here.
  Verify: `uv run python -c "from isekai.interface.render import Generate, parse_request, in_session_sources, again, without_flags, _taken, run_ids, _asked, _edit_argv; assert again.__module__ == 'isekai.interface.requests'"` exits 0.
- [x] 1.5 Run `uv run ruff check --fix isekai/interface/render.py isekai/interface/requests.py` and `uv run ruff format isekai/interface/render.py isekai/interface/requests.py`: they drop each import `render.py` no longer reads and sort both files' imports.
  Verify: `uv run ruff check isekai/interface/render.py isekai/interface/requests.py` exits 0.
- [x] 1.6 `requests.py` names nothing of `isekai.interface.render`, which would close a cycle.
  Verify: `grep -n -F "isekai.interface.render" isekai/interface/requests.py` prints nothing.
- [x] 1.7 In `tests/mutants.json` set the `path` of `CL-4a` and `CL-4b` to `isekai/interface/requests.py` ([D6](design.md#d6)); their `find` texts are unchanged.
  Verify: `git grep -c -F "isekai/interface/requests.py" -- tests/mutants.json` prints `tests/mutants.json:2`.
- [x] 1.8 In `tests/test_ratchets.py` delete the `LONG_FILES` row `isekai/interface/render.py` and set `FILE_ROWS` to the rows left. Re-key `_asked`'s `WIDE_FUNCTIONS` row from the path of `isekai/interface/render.py` to the path of `isekai/interface/requests.py`, its number as it stands ([D5](design.md#d5)).
  Verify: `git grep -n -e "^    .isekai/interface/render.py.: [0-9]" -- tests/test_ratchets.py` prints nothing.
- [x] 1.9 **HALT CHECK** `render.py` is under the long-file ceiling, so the row of 1.8 had to go. A failure means the moves before this one took less than the plan names.
  Verify: `uv run pytest tests/test_ratchets.py` exits 0.
- [x] 1.10 In `isekai/interface/README.md` add a `requests.py` row directly after the `render.py` row in `## Imported by`, `—` in its other cells, then run `uv run python -m tools.derive_imported_by`, which fills it and the other layers' tables.
  Verify: `git grep -c -e "^| .requests.py. |" -- isekai/interface/README.md` prints `isekai/interface/README.md:1`.
- [x] 1.11 Confirm the suite still reads each name through `render`, and the derived tables and the layers hold.
  Verify: `uv run pytest tests/test_render.py tests/test_edit_session.py tests/test_ui_jobs.py tests/test_ui_api.py tests/test_pipeline_cli.py tests/test_spec_bindings.py tests/test_docs.py tests/test_layers.py` exits 0.
- [x] 1.12 Replay the standing mutants, which `CL-4a` and `CL-4b` join at their new path.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.

## 2 — The keywords

- [x] 2.1 In `isekai/interface/requests.py` write `*,` between `verb: Sequence[str],` and `generate: Generate,` in `_asked`, and in `isekai/interface/render.py` make `_session`'s call of `_asked` pass `generate=generate` ([D3](design.md#d3)).
  Verify: `uv run python -c "import inspect; from isekai.interface.requests import _asked; assert inspect.signature(_asked).parameters['generate'].kind == inspect.Parameter.KEYWORD_ONLY"` exits 0.
- [x] 2.2 In `render.py` write `*,` between `asked: Mapping[str, int],` and `planned` in `Record.__init__`, and make `_session`'s `Record(...)` call pass `planned=` and `others=` by keyword, `order=` as it does.
  Verify: `uv run python -c "import inspect; from isekai.interface.render import Record; p = inspect.signature(Record.__init__).parameters; assert p['planned'].kind == p['others'].kind == p['order'].kind == inspect.Parameter.KEYWORD_ONLY"` exits 0.
- [x] 2.3 In `tests/test_ratchets.py` delete the `WIDE_FUNCTIONS` rows `isekai/interface/render.py::Record.__init__` and `isekai/interface/requests.py::_asked`, and set `WIDE_ROWS` to the rows left.
  Verify: `git grep -n -e "::_asked" -e "Record.__init__" -- tests/test_ratchets.py` prints nothing.
- [x] 2.4 Confirm no call of either function breaks, and the ratchets hold.
  Verify: `uv run pytest tests/test_render.py tests/test_edit_session.py tests/test_ui_jobs.py tests/test_ui_api.py tests/test_artifact_bytes.py tests/test_ratchets.py` exits 0.

## 3 — The documents

- [x] 3.1 In `docs/principles.md` add the *Known breaks* bullet of [D4](design.md#d4) at the end of *Free work first*, after its *Held by* bullet, wrapped as the file wraps.
  Verify: `git grep -c -F "are the free pass" -- docs/principles.md` prints `docs/principles.md:1`.
- [x] 3.2 In `isekai/interface/README.md` add a `requests.py` row directly after the `render.py` row in `## Files`: it parses `<flow>=<count|source>` requests, refuses a source placed before or chained to another, builds the retry command and the `--without` pairs, lists a collection's runs and builds the `generate` and `edit` argv, importing `plan.py`, `wiring.py`, `compare_view.py` and the foundation and never `render.py`. In the `render.py` row put `(parsed, with their argv, by requests.py)` after `takes the requests`.
  Verify: `git grep -c -e "^| .requests.py. |" -- isekai/interface/README.md` prints `isekai/interface/README.md:2`.
- [x] 3.3 In `isekai/README.md` add `requests.py` directly after `render.py` in the `interface/` row.
  Verify: `git grep -c -F "requests.py" -- isekai/README.md` prints `isekai/README.md:1`.
- [x] 3.4 Run the tests that hold the documents.
  Verify: `uv run pytest tests/test_docs.py tests/test_principles.py tests/test_layers.py` exits 0.
- [x] 3.5 Replay the standing mutants once more over the finished tree.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
