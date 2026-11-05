# Design — 0097 the gpunit upgrade

How gpunit moves to `v0.12.0` without a rebuild, and how its refusals reach the drawer and the terminal. **Verdict:
feasible.**

## Context

Read at `22291a5f`. The pin is `pyproject.toml:50`; `uv.lock` locks it at `:79-81` and `:242`. The `Dockerfile` adds
`v0.7.0`'s `boot/boot.sh` (`:85-86`), and `tests/test_infra.py:717-782` holds that tag equal to the pin's. gpunit
deleted `boot/boot.sh` in `v0.8.0`, so moving the pin alone turns that test red. Any `Dockerfile` edit is a rebuild,
because `config/image.json`'s `files` digest covers it.

gpunit `v0.12.0` keeps isekai's API: `load_spec`, `session(spec, *, environ, cwd, say)`, `Refused`, `Lost`,
`TeardownFailed`, `Interrupted`. `Refused` is `gpunit.log.Refusal`, whose `code` is 1, 4 (`NO_CAPACITY`) or 5
(`NO_FIT`). Each gpunit line opens with the UTC time; a refusal is `<UTC> refused: <reason>`, a form gpunit documents for
callers to parse. gpunit reads a `boot.sh` from `v0.6.0` on.

`run_gpunit` (`isekai/boundary/gpu.py:130-150`) runs the verb to its end, then hands its output to `say`. The drawer's
messages are `isekai/interface/ui/jobs.py:497-500` and `:562-566`. `isekai render` turns `Refused` into exit 1
(`isekai/interface/render.py:1079-1091`).

## Goals / Non-Goals

**Goals:** the pin at `v0.12.0` with no rebuild; gpunit's lines in the log as they come; a refusal for stock or fit
named by its kind, with gpunit's reason, in the drawer and the terminal.

**Non-Goals:** `stock_wait`; `boot.py` and any `Dockerfile` edit; a pod proof; exit 1's message, which stays as it is.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `pyproject.toml:50` `gpunit@v0.7.0` → `gpunit@v0.12.0`, then `uv lock`, which re-locks `uv.lock`'s gpunit entries. D22 holds: an exact tag | one pin; `v0.12.0` is the grilled tag | `v0.12.1`, tagged after the grilling: its fixes are `serve`'s rows and the wait for stock, neither of which isekai uses |
| <a id="d2"></a>**D2** | **The untie**, in `tests/test_infra.py`: the boot-script check reads the `Dockerfile` alone, and wants any gpunit tag with a checksum. Both boot-script tests keep their names and markers; [the shape](#the-untie) | the test stops asserting a tie the version removes; editing the `Dockerfile` would be a rebuild | moving the boot script's tag, which is a rebuild |
| <a id="d3"></a>**D3** | **The docs.** `docs/pins.md`'s row (`:41`) and recipe (`:69-72`) say the boot script's tag is pinned on its own, and give gpunit's rule for an old `boot.sh`. `Volume`'s docstring (`gpu.py:157`) names exits 4 and 5. The `Dockerfile` comment (`:82-84`) stays; [the text](#the-docs) | the guide says what holds; editing the comment is a rebuild | |
| <a id="d4"></a>**D4** | **The lines (`0074·R6`).** `run_gpunit` opens the verb with `subprocess.Popen`, the same argv, `cwd`, `env`, `stdout=PIPE`, `stderr=STDOUT`, `text=True` and `start_new_session=True`, as a context manager. It hands each line to `say` without its newline as the line comes, and returns the child's `returncode` once the block ends | a verb in progress shows in the log, and a server that dies mid-verb keeps the lines said before it died | a file the child keeps, prefixed afterwards: it still reaches the log late |
| <a id="d5"></a>**D5** | **The refused line.** `gpu.py` gains `refused_line`, which reads gpunit's `<UTC> refused: <reason>` line, and `GpunitExit`, the exit code with the last such line. `run_gpunit`, `Gpunit` and `Volume`'s verbs return a `GpunitExit`; [the shape](#the-refused-line) | the boundary reads gpunit's documented line once; isekai's own `refused:` lines carry no UTC time, so they never match | reading the session record's message: a volume verb writes none |
| <a id="d6"></a>**D6** | **The kinds.** `render.py` gains, beside `LOST_EXIT`, `REFUSALS = {4: "no card in stock", 5: "no card fits max_hourly / vram_gb"}` | one table the terminal and the drawer both read | a table per surface |
| <a id="d7"></a>**D7** | **The drawer.** `jobs.py` gains `refusal`, the message for a 4 or a 5: the kind, gpunit's `refused:` line, and the log named for the cards it skipped. The volume-up failure and the render child's failed exit both take it, the child's line caught by `_tee`; [the shape](#the-drawer) | the job leads with the kind, quotes gpunit's line, and names the log for the `skipped:` lines, for the window and the render alike | reading the render child's JSON lines: they carry no reason |
| <a id="d8"></a>**D8** | **The terminal.** `isekai render`'s `except Refused` returns `refused.code`, and for a code `REFUSALS` holds prints `f"{lead}, per gpunit's line above; its skipped lines name each card it passed"` to `wired.err`, after `record.end` and before the `REMEDY` note. The record keeps `str(refused)` as its message, and `run_session`'s docstring (`render.py:476-477`) reads `· 3 the create's answer` / `was lost · 4 no card in stock · 5 no card fits · 128+n a signal ended it.` on its second line | gpunit has already written its `refused:` line through `say`, so the kind follows it, and one refusal still prints one `refused:` line, as `tests/test_render.py:808-848` holds | repeating gpunit's line after the kind: two `refused:` lines for one refusal |
| <a id="d9"></a>**D9** | **D36 amended** in `docs/decisions.md`. Before its `**Made by:**` bullet it gains `` - **Refusals:** `isekai render` exits with gpunit's code, 1, 4 or 5, and the drawer names a 4 or a 5 by its kind and quotes gpunit's `refused:` line, a form gpunit documents for callers to parse. `` Its *Made by* gains `` `0097` `` after `` `0083` ``. No new decision | the session's outcomes are D36's | a new decision |

## Shapes

The exact text of [D2](#d2), [D3](#d3), [D5](#d5) and [D7](#d7), for the build to place.

### The untie

- `gpunit_tag` goes. Its readers are `tests/test_infra.py:742` and `:758` alone.
- `BOOT_SOURCE` becomes the pattern `r"https://raw\.githubusercontent\.com/alxb1t/gpunit/v\d+\.\d+\.\d+/boot/boot\.sh"`.
- `boot_script_faults(dockerfile)` takes no `pyproject`. Its first fault → `the boot script is not added from a gpunit
  tag with a checksum`, and its docstring says "at a pinned gpunit tag" for "at its pin".
- `test_each_boot_runs_gpunits_boot_script_at_its_pin` reads no `pyproject.toml`.
- Its twin builds `pinned` at tag `v9.0.0`, which passes. Its `elsewhere` case swaps `/v9.0.0/` for `/main/`, a branch,
  not a tag; it and `unchecked` give the first fault, and the `CMD` alone gives both.

### The docs

- `docs/pins.md:41` → `` | gpunit's boot script | sha256, at a gpunit tag pinned on its own | `Dockerfile` | at build; `tests/test_infra.py` holds it to a gpunit tag, with a checksum | ``.
- `docs/pins.md:69-72` → `` - **gpunit.** Move its tag in `pyproject.toml` and run `uv lock`. The boot script keeps its own tag in the `Dockerfile`, pinned on its own, and moves only with an image rebuild: gpunit reads a `boot.sh` from `v0.6.0` on, and refuses an older one, whose host-key line carries no session nonce. ``, wrapped at 120.
- `isekai/boundary/gpu.py:157`, `Volume`'s docstring, becomes these lines, each under ruff's 88:

  ```
      Each returns gpunit's exit: 0 done, 1 refused or failed, 3 a lost create,
      4 no card in stock, 5 no card fits.
  ```

### The refused line

- `REFUSED = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z (refused: .+)$")`, with a comment naming it gpunit's
  documented line.
- `refused_line(line: str) -> str | None` returns group 1, else `None`. e.g. `2026-11-03T09:14:02Z refused: no card in
  'gpus' was placed` → `refused: no card in 'gpus' was placed`.
- `@dataclass(frozen=True) class GpunitExit` holds `code: int` and `refused: str | None = None`.
- `run_gpunit` returns `GpunitExit(child.returncode, <the last line refused_line matched>)`.
- `Gpunit = Callable[[Sequence[str], Say], GpunitExit]`. `Volume`'s `up`, `down` and `status` return `GpunitExit`, and
  its docstring's exit lines become:

  ```
      Each returns gpunit's exit and its last refused line: 0 done, 1 refused or
      failed, 3 a lost create, 4 no card in stock, 5 no card fits.
  ```
- `isekai/boundary/README.md`'s `gpu.py` row, after `` `Volume`, the window volume and `.gpunit/` through gpunit's
  verbs; `` gains `` `run_gpunit`, a gpunit verb whose lines reach `say` as they come, and its `GpunitExit`, the exit
  with the last `refused:` line `refused_line` reads; ``.
- Each gpunit double returns `GpunitExit(<the code it returns today>)`; `_order`'s `run` returns
  `GpunitExit(LOST_EXIT if … else 0)`. `_no_gpunit` and `unstartable`, which only raise, are annotated `-> GpunitExit`.

### The drawer

- `refusal(code: int, refused: str | None, collection: str) -> str | None` is `None` for a code `REFUSALS` lacks.
  Else it is `f"{lead}; gpunit {refused}; read {collection}/{LOG} for the cards it skipped"`, the `; gpunit {refused}`
  part left out when `refused` is `None`.
- e.g. `refusal(4, "refused: no card in 'gpus' was placed", "b")` → `no card in stock; gpunit refused: no card in 'gpus'
  was placed; read b/log.txt for the cards it skipped`.
- `_named(kind, folders, verb: Callable[[Say], GpunitExit]) -> GpunitExit`. In `_run_render`,
  `ended = _named(job.kind, folders, self._volume.up)`, and each read of the volume up's exit — the `!= 0` test, the
  `LOST_EXIT` tests and `(exit {code})` — reads `ended.code`. Its failure message is `refusal(ended.code, ended.refused,
  job.collection)` where that is not `None`, else today's. The volume-down call reads `.code`.
- `_Slot` gains `refused: str | None = None`. `_spawn` resets it and hands the slot to `_tee`, which sets it to each
  line `refused_line` matches.
- `_render_child`, on a failed exit while not stopping, takes `refusal(code, slot.refused, job.collection)` where it is
  not `None`, else today's message.

## Tests

The tests the change adds and edits, by layer. It adds no end-to-end test (`T1`): each outcome is a job's message or an
exit, which a unit test reads.

| layer | adds | edits |
|---|---|---|
| unit | `tests/test_gpu.py`, new: `test_run_gpunit_says_a_line_before_the_verb_exits`, `spec_exempt("structural: gpunit's lines reach say as they come")`, and `test_run_gpunit_returns_the_last_refused_line`, bound to `ui:render-job:a-refusal-names-its-kind-and-reason`. `tests/test_ui_jobs.py`: `test_a_refused_window_names_its_kind_and_reason` and `test_a_refused_render_names_its_kind_and_reason`, bound to the same key. `tests/test_render.py`: `test_a_refused_session_exits_with_gpunits_code`, bound to `cli:render-session:a-refused-session-exits-with-gpunits-code` | the two boot-script tests in `tests/test_infra.py` ([D2](#d2)); `test_a_gpunit_verb_runs_in_its_own_session` in `tests/test_ui_jobs.py`, which records `Popen` instead of `run` ([D4](#d4)); each gpunit double, which returns a `GpunitExit` ([D5](#d5)) |
| end-to-end | none | `tests/e2e/wiring.py`'s `_gpunit` double alone |

`test_run_gpunit_says_a_line_before_the_verb_exits` replaces `gpu.subprocess.Popen` with one that starts the real
`Popen` on `[sys.executable, "-c", <script>, <marker>]` with `run_gpunit`'s keywords, typed `**kwargs: Any`. The script
prints `first` with `flush=True`, waits up to 10 s for the marker file, then prints `after` if it exists, else `late`;
`say` writes the marker on `first`. It
asserts `say` heard `first` then `after`. `test_run_gpunit_returns_the_last_refused_line` uses the same replacement on
a script that prints two gpunit `refused:` lines and one other line, then exits 4.

The three `spec_exempt` tests of `tests/test_render.py:758-848` stay as they are. This change deletes and merges no test.

## Dependencies

None.

## Risks / Trade-offs

- **No pod has run a `v0.12.0` laptop on `v0.7.0`'s `boot.sh`** → gpunit documents that it reads it; the person renders
  by hand after release, and the split-image version's pod proof covers the boot.
- **`uv lock` fetches the new tag from `github.com`** → it runs once, in phase 1; `make setup` filled the rest.
- **The terminal names the kind after gpunit's reason, not before it** → gpunit's line is written as it happens; the
  kind is the one line isekai adds.
- **A breaking exit for a caller of `isekai render` that reads 1 as "no card"** → the app's job is the one caller, and
  it reads 4 and 5 by [D7](#d7).

## Verdict

**feasible.** Every file and symbol named exists at `22291a5f`, and each gpunit name at `v0.12.0`.
