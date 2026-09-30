# Design — 0051 the terse comments

What a comment may say, how each citation is rewritten, what the guard reads, and how meaning is checked in place of
converge. **Verdict: feasible** — prose and a structural test; no code moves.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`9f8a479`):

- **The history**, counted by the guard's own pattern in [D4](#d4) over `tokenize` comments and triple-quoted strings
  of `git ls-files isekai tools infra start.sh Dockerfile tests` (not `tests/golden`):

  | form | hits |
  |---|---|
  | `design.md Dn` | 204 |
  | a change id with its slug, `design`, `proposal`, `tasks` or a `Dn` | 114 |
  | an isekai version | 76 |
  | files with any | 76 of 102 |

  By tree: `isekai` 185, `tests` 115, `tools` 47, `infra` 22, `start.sh` 15, `Dockerfile` 10.
- **The decisions in force** are `docs/decisions.md`'s D0–D36; each names the changes that made it.
- **The spec guard:** `_HISTORY` in `tests/test_spec_prose.py:18-22` reads the effective spec for a version, a change
  id with its slug or `design`, and a backticked commit hash.
- **The READMEs:** the importer rows at `isekai/foundation/README.md:25`, `isekai/shared/README.md:31` and
  `isekai/boundary/README.md:31` miss importers `git grep` finds.
- **Baked files** — `start.sh`, the `Dockerfile`, `tools/download_models.sh`, `tools/stop_pod.sh`,
  `isekai/boundary/provision.py` — are rewritten here and carried by the next image rebuild.

## Goals / Non-Goals

**Goals:** no history in a comment or docstring of the named trees; the reason in force named by its D-id; a guard.

**Non-Goals:** shortening a comment beyond its history; `ui/`; `evaluation/`; any code.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | a citation becomes the plain D-id of `docs/decisions.md` that holds its reason, and goes where none does | the why stays reachable through the decision in force | a link in code, which nothing renders |
| [D2](#d2) | history leaves comments, docstrings, `spec_exempt` reasons and one refusal; a reason the comment only had through the archive is stated in one clause; data stays; nothing else is reworded | a sweep, not a rewrite | a full terse rewrite |
| [D3](#d3) | the rule goes into *Engineering conventions* | every change after this follows it | a separate style file |
| [D4](#d4) | `tests/test_spec_prose.py` gains the comment guard, sharing one widened pattern with the spec guard | one pattern for history, wherever it is written | a second pattern |
| [D5](#d5) | the three README rows name every importer `git grep` finds | the rows claim to be complete | dropping the rows |
| [D6](#d6) | a prose-only proof and a meaning check replace converge | the change moves no code | converge's review and security |

### D1

**Citations.** Before → after:

```
# A runs root must sit under .data/ (0018 design D3).        →   # A runs root must sit under .data/ (D18).
"""… the tagger seam's shape (design.md D4, v0.16)."""        →   """… the tagger seam's shape."""
```

A D-id holds a citation's reason when its rule is the comment's reason; the builder reads the decision to decide.
A test's docstring citing the design that added it keeps only what the test proves.

### D2

**What goes.** A version (`v0.16`), a change id (`0033`, `0033-the-slug`), a design, proposal or tasks citation, and
narration — "used to", "no longer", "since", "this replaced", "the first build" — go. A reason the comment carried only
by pointing at the archive is written into it in one clause. Every other word stays. **Prose outside comments** gets
the same sweep: a `spec_exempt` reason, and the refusal in `isekai/boundary/wd14.py:211-216` ("as of v0.22.3").
**Data stays** — the `.data/v0.20` path, pod image tags in fixtures, a third party's `v0.2.2.4`, a guard's twin inputs.

### D3

**The rule**, under *Tests are bound to the spec.* in `CLAUDE.md`:

> **A comment says what and why, in the present tense.** It names a decision in force as a plain `D27`, never a link,
> and carries no version, change id or design citation; the archive keeps the history.

### D4

**The guard.** `_HISTORY` widens and is shared:

```
\bv0\.\d{1,2}(?:\.\d{1,2})?(?![.\d])                          an isekai version, not v0.2.2.4
\b00\d\d(?:-[a-z]|`?\s+(?:design|proposal|tasks|D\d))         a change id cited
design\.md`?,?\s*D\d+                                         a design citation
`[0-9a-f]{7,12}`                                              a commit hash
```

`test_no_comment_names_a_version_change_or_design` reads every comment through `tokenize`, every docstring through
`ast.get_docstring` and every `spec_exempt` reason in the `.py` files of the named trees, and every `#` line of their shell scripts and the
`Dockerfile`, naming each hit as `file:line`. A twin feeds a source holding each form in a comment and a docstring,
and one holding a third party's `v0.2.2.4`. The module's docstring names both guards.

### D5

**The README rows.** `isekai/foundation/README.md`'s `run.py` row gains `interface/compare_view.py`,
`interface/ui/app.py` and `tests/test_compare.py`; `isekai/shared/README.md`'s `vocabulary.py` row gains
`tests/test_artifact_bytes.py` and `tests/test_compare.py`; `isekai/boundary/README.md`'s `comfy/` row gains
`tests/stages.py` — each re-checked with `git grep` at the build.

### D6

**The meaning check**, after the build, in place of `mf-converge`:

```
1 mechanical   each .py: ast.dump of the module with docstrings removed, main vs branch → equal
               each shell file and the Dockerfile: non-comment lines, main vs branch → equal
               allowed: the spec_exempt reasons and the wd14.py refusal, each listed
2 meaning      parallel read-only subagents, a tree each: every rewritten comment,
               old against new → SAME | CHANGED, with the line
3 fix          one commit restoring each CHANGED meaning; recorded here, under this heading
```

**The check, run after the build.** The mechanical proof held: every changed `.py` file's AST, docstrings and
`spec_exempt` reasons aside, and every shell file's non-comment lines, match `main`, but the `wd14.py` refusal's
"as of v0.22.3" and `tests/test_spec_prose.py`'s guard. Six parallel readers, a tree each, judged each rewritten hunk:

| tree | hunks | SAME | CHANGED |
|---|---|---|---|
| foundation, shared | 41 | 39 | 2 |
| boundary, pipeline | 65 | 64 | 1 |
| interface, `CLAUDE.md` | 48 | 48 | 0 |
| tools, infra, `start.sh`, `Dockerfile` | 71 | 67 | 4 |
| tests, the larger files | 75 | 74 | 1 |
| tests, the rest | 78 | 76 | 2 |

**One fix commit restores nine:** `flow.py`'s single key is not a declaration, and only the model `model` names is
local; `sheet.py`'s comparison with that seam's own property; `test_ui_api.py`'s reason a missing tag list never
blocks review; `download_models.sh`'s reason for the split; `manifest.py`'s "a refactor", not "a change";
`derive_field_map.py`'s "only copy", twice, which git contradicts; `stages.py`'s call sites passing nothing;
`test_labels.py`'s reason no rollup exists. **One is kept:** `run.py` names `config/` for `joycaption.Modelfile`, a
true present-tense fact the old text left implied.

## Dependencies

None.

## Risks / Trade-offs

- **A citation's D-id is wrong** → the meaning check reads each against the old text.
- **A comment loses its only reason** → [D2](#d2) writes the reason in; the meaning check catches a loss.
- **The baked files drift further from the pinned image** → comments only; the next image rebuild carries them.

## Verdict

**feasible** — a prose sweep over the named trees, a rule, a guard and three rows.
