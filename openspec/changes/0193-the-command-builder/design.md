# The command builder — design

A command a person is told to run is built by `command(verb, *words)`, each site keeping its own words and quotes, and a test fails on a string that spells the entry outside the builder's module. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The entry, `python -m isekai`, starts every command a refusal or a message prints. It is spelt by builders, by sites and behind a prefix today:

```
builders   stage_command · migrate_command          isekai/foundation/run.py
           _draft_command                           isekai/pipeline/review.py
           _named_a_flow · prog=                    isekai/interface/cli.py
sites      f"python -m isekai render {root} …"      pipeline, boundary, interface: a string in a refusal or a message
prefixed   "uv run python -m isekai assign …"       interface/render.py
           "uv run --env-file .env python -m isekai ui"   interface/ui/routes/rendering.py
```

`_again`, `_command` and `_remedy` call `stage_command`, and `refusal_for` builds its fix from it. Each site quotes as it chose: `shlex.quote` for a path, none for the paths of `ui/surface.py`, a placeholder such as `<runs>` for a hint. A shared builder that quoted would change the bytes of the unquoted ones.

`stage_command` reads `RUNS_ROOT` of `run.py`, which a test patches, so it stays in `run.py` ([D62](../../../docs/decisions.md#d62--the-run-directory-is-runpy-its-siblings-imported-through-it)). The entry and the joining read nothing, so they can live in a sibling.

```
before:  site ─ f"python -m isekai verb …"                  (spelt at each site)
after:   site ─ command(verb, *words) ─ ENTRY ─ one string     (spelt once)
```

## Goals / Non-Goals

- Goal: one string, `ENTRY`, spells the entry in `isekai/`, so *the isekai command* edits one line.
- Goal: every printed byte is equal: each site passes the words it printed, in the order it printed them, quoted as it quoted them.
- Goal: a test fails on a string that spells the entry outside the builder's module, and a twin shows it can.
- Non-goal: a quoting builder, a refusal's fix as a field, and the `isekai ui` texts.
- Non-goal: the argv lists of `again` and of the children, which a person never pastes as a string.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `ENTRY = "python -m isekai"` and `command(verb, *words)` are in a new `isekai/foundation/command.py`; `command` joins the entry, the verb and the words by one space and quotes none; `run.py` re-exports both | the entry reads nothing a test patches, a module that spells it alone is one path for the guard to exempt, and a word a site quoted stays quoted | `command` in `run.py`: the guard would exempt a file of hundreds of lines; a quoting builder: `ui/surface.py` prints a path unquoted and its bytes would change |
| [D2](#d2) | `stage_command`, `migrate_command`, `_draft_command` and `_named_a_flow` build their words and call `command`; `prog` is `ENTRY` | they are the functions that spelt the entry and the shapes of the other sites; each already holds its words | a `Command` class holding the flags: more surface than one join, and a site would pass a flag as a field |
| [D3](#d3) | Each site that spelt the entry calls `command` with the words it printed; `render.py` and `ui/routes/rendering.py` write their `uv run` prefix before the call | a prefix is the site's, as its quoting is; the entry stays the builder's | a prefix argument: only `render.py` and `ui/routes/rendering.py` print one, and *the isekai command* drops them |
| [D4](#d4) | `again` in `render.py`, the children's argv in `ui/jobs.py`, the bare `isekai ui` texts of `ui/library.py` and `ui/bundle.py`, and the `isekai.boundary` provisioning commands stay | each prints another prefix or is no string a person pastes; *the isekai command* makes the bare texts true | forcing them through: a list is not text, and a bare text is not an entry that works today |
| [D5](#d5) | The guard is `entry_spellings(root)` in `tests/test_run_directory.py`, an `ast` scan of each `.py` file under `isekai/` for a string constant, a docstring excepted, that holds `ENTRY` not followed by a word character or a dot, outside `isekai/foundation/command.py`; a test runs it on the repository and a twin on a small tree | `ast` reads an f-string's pieces and sees a docstring as one, so prose that names the entry passes; the dot lets `python -m isekai.boundary.provision` pass | a `git grep` in a test: it reads docstrings and comments, and the pattern could not tell a module from the entry |
| [D6](#d6) | Cases for `command` are written first, and a mutation run over `stage_command` and `migrate_command` passes before a line moves and over `command`, `stage_command` and `migrate_command` again after | byte-equal is the version's promise, and today the cases that read `stage_command` and `migrate_command` read a refusal that holds their text, not the text | none: a conversion with no case would hold only where a test already reads the text |
| [D7](#d7) | D75 is added to [docs/decisions.md](../../../docs/decisions.md), and D62's statement lists `command.py` among the siblings `run.py` re-exports | a decision is added where it sets a rule, and the documents a version makes false are amended in its diff | amending only D62: the rule that nothing spells the entry has no home |

### D1

```python
"""The command a person is told to run, spelt once.

Imports nothing, and is on `python -m isekai`'s import graph (D20).
"""

# The words every printed command starts with; a prefix such as `uv run` is its site's.
ENTRY = "python -m isekai"


def command(verb: str, *words: str) -> str:
    """Return `verb` and `words` after the entry, joined by one space, none quoted.

    A word is its site's own text: quoted by it, or a placeholder.
    e.g. ("render", "b/runs", "f=1") -> "python -m isekai render b/runs f=1"
         ("migrate",) -> "python -m isekai migrate"
    """
    return " ".join((ENTRY, verb, *words))
```

`run.py` imports both from `isekai.foundation.command` and lists them in `__all__`; a module outside the foundation reads `command` from `isekai.foundation.run`. A word that is the empty string makes a double space, as it did where a site joined an empty list.

### D2

```python
def stage_command(run: Run, verb: str, *flows: str, options: Sequence[str] = ()) -> str:
    root = run.path.parent
    flagged = [word for flow in flows for word in ("--flow", flow)]
    runs = (
        []
        if root.resolve() == RUNS_ROOT.resolve()
        else ["--runs", shlex.quote(str(root))]
    )
    return command(verb, *flagged, *runs, *options, run.id)


def migrate_command(run: Run) -> str:
    root = run.path.parent
    if root.resolve() == RUNS_ROOT.resolve():
        return command("migrate")
    return command("migrate", "--runs", shlex.quote(str(root)))
```

The docstrings stay. In `pipeline/review.py`, `_draft_command` returns `command("draft", "--flow", flow, shlex.quote(str(image)))`. In `interface/cli.py` `_named_a_flow` builds its flags as tuples:

```python
    root = () if args.runs == RUNS_ROOT else ("--runs", shlex.quote(str(args.runs)))
    again = ("--new-version",) if args.new_version else ()
    photos = " ".join(shlex.quote(target) for target in targets) or "<photo>"
    ...
        f"which every flow reads; run `{command(verb, *root, *again, photos)}`"
```

and `build_parser` passes `prog=ENTRY`. The words are those the old f-strings joined with one space each, so every string is byte-equal.

### D3

| site | before | after |
|---|---|---|
| `_stale` of `pipeline/edit.py` | ``f"…; run `python -m isekai discard {image}` to remove "`` | ``…; run `{command('discard', image)}` to remove `` |
| `_held_way` of `pipeline/review.py`, the render remedy | `f"python -m isekai render {shlex.quote(str(run.path.parent))} {source}=1"` | `command("render", shlex.quote(str(run.path.parent)), f"{source}=1")` |
| `source_seeds` of `pipeline/generate.py`, the refusal of a source with no render | ``f"`python -m isekai render {_runs_root(run)} {source}=1" f"{_dependents(flows, source)}`"`` | `command("render", _runs_root(run), f"{source}=1{_dependents(flows, source)}")`, bound before the `raise` |
| `_reported` of `boundary/comfy/client.py`, the unreachable endpoint's hint | ``"`python -m isekai render <runs> " "<flow>=<count>`"`` | `command("render", "<runs>", "<flow>=<count>")`, in an f-string |
| `_runs` of `interface/compare_view.py` | ``f"`python -m isekai tag --runs {q(root)} " f"{q(photos)}/*`"`` | `command("tag", "--runs", q(root), f"{q(photos)}/*")`, `q` being `shlex.quote(str(…))`, bound before the `raise` |
| `Surface.rendered` and `Surface.bake_image` of `interface/ui/surface.py` | ``f"`python -m isekai render {found / library.RUNS}`"`` | `command("render", str(found / library.RUNS))`, the path unquoted as before |
| `sheet_cell` of `interface/verbs/prepare.py` | ``f"`python -m isekai assign --flow {flow} --runs {runs} " f"{run_id}`"`` | `command("assign", "--flow", flow, "--runs", runs, run_id)` |
| `parse_cells` of `interface/verbs/common.py` | ``f"`python -m isekai assign --flow {flow} --runs {runs} <photo>`"`` | `command("assign", "--flow", flow, "--runs", runs, "<photo>")` |
| `run_edit` of `interface/verbs/edits.py`, the refusal of a request with no edit and the success line | ``"`python -m isekai edit <edit> <render> --composite <png>`"``, ``f"`python -m isekai render {shlex.quote(str(runs))}`"`` | `command("edit", "<edit>", "<render>", "--composite", "<png>")`, `command("render", shlex.quote(str(runs)))` |
| `_asked` of `interface/render.py`, with `uv run` | ``f"uv run python -m isekai assign {' '.join(flows)} --runs " f"{shlex.quote(str(runs))} {photos}/*"`` | `"uv run " + command("assign", " ".join(flows), "--runs", shlex.quote(str(runs)), f"{photos}/*")`, bound before the `raise` |
| `RenderRoutes._held` of `interface/ui/routes/rendering.py`, with `uv run --env-file .env` | ``"`uv run --env-file .env python -m isekai ui` again."`` | ``f"`uv run --env-file .env {command('ui')}` again."`` |

`" ".join(flows)` stays one word: an empty list makes `assign  --runs` with a double space, today as after. `again` in `render.py` and `refusal_for` of `run.py` bind a local named `command`, which the new import would shadow; each local is renamed (`argv`, `pasted`) where the import lands.

### D4

`again` returns `shlex.join(["uv", "run", "python", "-m", "isekai", "render", …])`, `prepare_command` and `render_command` of `ui/jobs.py` start `[sys.executable, "-m", "isekai", …]`, and the guard reads strings: no string of any of them holds `python -m isekai`. The bare `isekai ui` texts, `ui/library.py` twice and `ui/bundle.py` once, do not hold it either. `ollama.py`, `unpack.py` and `vocabulary.py` name `python -m isekai.boundary.…`, which the dot in the guard's pattern lets pass. Docstrings and comments that name the entry stay as they are.

### D5

```python
SPELT = re.compile(re.escape(ENTRY) + r"(?![\w.])")
BUILDER = Path("isekai/foundation/command.py")


def entry_spellings(root: Path) -> list[str]:
    """Return `path:line` of each string under `root/isekai` that spells the entry.

    The builder's module and docstrings are not read; a comment is no string.
    """
    found: list[str] = []
    for path in sorted((root / "isekai").rglob("*.py")):
        if path.relative_to(root) == BUILDER:
            continue
        tree = ast.parse(path.read_text())
        docs = {id(n.body[0].value) for n in ast.walk(tree) if _holds_doc(n)}
        found += [
            f"{path.relative_to(root)}:{node.lineno}"
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docs
            and SPELT.search(node.value)
        ]
    return found
```

`_holds_doc(node)` is true for a module, class or function whose first statement is an expression of a string. The guard is `assert entry_spellings(REPOSITORY) == []`, and the twin writes a small tree under `tmp_path` and asserts the result is exactly the lines it planted: an f-string that spells the entry, a plain string behind `uv run`, and a string in a nested function; and none for a docstring, a comment, `python -m isekai.boundary.provision`, and the entry in `isekai/foundation/command.py`.

### D6

The mutation tool mutates a line of a function's body, so the runs are over `stage_command` and `migrate_command` of `run.py` before phase 2 and over `command` of `command.py`, `stage_command` and `migrate_command` after it, one run a range:

```
uv run python -m tools.mutate isekai/foundation/run.py:<first>-<last> --tests tests/test_run_directory.py tests/test_review.py tests/test_resume.py tests/test_pipeline_cli.py
```

A survivor is killed by a case in `tests/test_run_directory.py`, named `test_stage_command_…` for `stage_command` and `test_migrate_command_…` for `migrate_command`. A survivor no case can kill is named equivalent, with its reason, in the commit body. The replay of the standing mutants in the last phase stops on a find that an edit moved, and the version re-points it.

### D7

D75 in `docs/decisions.md`, after D73:

```
### D75 · A command is built by command, in isekai/foundation/command.py

**`isekai/foundation/command.py` holds `ENTRY`, the words every printed command starts with, and `command(verb, *words)`, which joins the entry, the verb and the words by one space and quotes none. `run.py` re-exports `ENTRY` and `command`. A command a refusal or a message prints is built by `command`, its site keeping its own quoting and any prefix such as `uv run`, and a test holds that no string of `isekai/` outside the module spells the entry.**

- **Why:** a command a person pastes was spelt by hand at sites beside its builders, so a change to the entry would edit each and nothing failed on a missed one. One constant is one edit.
- **Accepts:** the argv of `again` and of the children, the bare `isekai ui` texts and the `isekai.boundary` provisioning commands stay as they are, and a docstring or a comment that names the entry is not read. A refusal's reason and its fix are still one string. Reopen when the entry changes, or when a refusal's fix rides the wire.
- **Made by:** `0193`.
```

D62's statement gains `command.py` in its list of siblings and its *Made by* gains `0193`.

## Tests

The version adds cases and a guard, deletes and merges none, and changes no assertion. Counts, each from its command:

| layer | added | command |
|---|---|---|
| unit | the cases of `command`, the parser's `prog`, the guard and its twin, and a case for each survivor the mutation run finds | `git grep -c -e 'def test_command_' -e 'def test_stage_command_' -e 'def test_migrate_command_' -e 'def test_the_parser_prints_the_entry' -e 'def test_no_string_spells_the_entry' -e 'def test_the_guard_finds_a_string' -- tests/test_run_directory.py` prints nothing before, and after one line whose count is at least six |
| end-to-end | none | no browser test is touched |

| test | reason |
|---|---|
| `test_command_joins_the_entry_the_verb_and_the_words`, `test_command_with_no_words_ends_at_the_verb` and `test_command_quotes_no_word` | the builder's contract, bound to `cli:refusals:refusal-names-the-remedy`; `T1`, unit |
| `test_the_parser_prints_the_entry` | `prog` is `ENTRY`; `T1`, unit, `structural:` exempt |
| `test_no_string_spells_the_entry_outside_the_builder` and its twin `test_the_guard_finds_a_string_that_spells_the_entry` | the guard and the proof it can fail, per `T6` at the lowest layer; `structural:` exempt |

No test is deleted or merged, so the `I16` table is empty. Every new test is in `tests/test_run_directory.py`, and the tests that read a printed command, `tests/test_review.py`, `tests/test_resume.py` and `tests/test_pipeline_cli.py` among them, hold the bytes and do not change. The standing mutants of `tests/mutants.json` are replayed, and a find an edit moved is re-pointed.

## Dependencies

None.

## Risks / Trade-offs

| risk | answer |
|---|---|
| a word a site joined with a space is joined with another | `command` joins by a space, and the old f-strings put a space between each word; `" ".join(flows)` is passed whole where an empty list printed a double space; the record and the suites that read a command hold the rest |
| `boundary/comfy/client.py` newly imports `run.py` | `boundary/comfy/contract.py` imports it already, `run.py` is standard library, and the layer guard and the `-S` guard hold the graph |
| a local named `command` shadows the import | `refusal_for` and `again` rename theirs; `_remedy` of `ui/routes/reviewing.py` binds one and imports no `command`, so it stays |
| the guard reads a string that is prose | a docstring is skipped, and a message that names the entry in prose is itself a site, so it goes through `command` |
| the ratchets read the edited files | no function passes a ceiling it was under, and a listed row stays, since no edit removes its offender |
| a standing mutant finds a line an edit moves | the last phase replays them and re-points a find that is gone |

## Verdict

Ready to build, each phase green alone: the builder with its cases, the builders, the sites, the guard, and the documents.
