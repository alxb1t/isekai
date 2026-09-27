# Design — 0036 the prose

How each piece of prose is rewritten, and why no behaviour moves. **Verdict: feasible** — every edit is prose, a
comment, a message or an inert placeholder, and each is checked by a command.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`7aa23d3`):

- **Intimate tags in prose** sit in archived `0018`, `0020`, `0021` and `0025`, in `CHANGELOG.md`, and in the
  `inflect()` docstring; the living specs, `docs/`, the READMEs, `CLAUDE.md`, the skills, the flows and the tests hold none.
- **The code that maps tags to the sheet keeps them:** `FILED`'s keys and the `SEEDS` stems in
  `tools/derive_field_map.py`, and `config/field_map.json`.
- **Nothing hashes the archive or `CHANGELOG.md`**; the only automated reader of `CHANGELOG.md` is
  `tests/test_flow.py`'s digest-substring check. The archive's freeze and the changelog's append-only rule are
  policy (`CLAUDE.md`), and this change is a stated exception to both ([D1](#d1)).
- **`flow_digest` is recorded and never read** (`isekai/pipeline/sheet.py:103`), so a re-pin breaks no run.

## Goals / Non-Goals

**Goals:** no intimate tag, rating term or per-tag count from the operator's sheets in tracked prose; D33; an honest
pins guide; teardown and port messages that name the right fix; no real photograph's filename in a flow.

**Non-Goals:** any behaviour change; `FILED`'s shape or its `.data/` refresh; the living specs; git history; the
changelog's format.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | rewrite by describing, never by substituting | every sentence stays true | invented neutral examples — they would claim what no sheet held |
| [D2](#d2) | comments and docstrings only in `tools/derive_field_map.py` | the operator: no code that affects behaviour changes | an authored count-free `FILED` — a code change |
| [D3](#d3) | the term list is `.minions/prose-terms.txt`, gitignored | a tracked list puts the tags back in the repo | a tracked test holding the list |
| [D4](#d4) | D33: isekai restricts no content | self-hosted, private by default, open models | a rating tag; a README line |
| [D5](#d5) | *Not pinned* rows for the reader's template and the image's build tools, and a *where it stops* line, in `docs/pins.md` | the guide overstates what is held | the pins' code fixes — each waits for its trigger |
| [D6](#d6) | the lost-create, no-record, other-status and port messages rewritten; the teardown test narrowed | `CLAUDE.md` names `infra/down.sh` as the act | an MCP `delete-pod` as the route |
| [D7](#d7) | a neutral placeholder, re-pinned in place | `build_graph` overwrites it, so no output moves | a new flow id — nothing a render sees differs |
| [D8](#d8) | no spec delta: `skip_specs` | no requirement changes | a rationale edit — it needs a MODIFIED delta |

### D1

**Rewrite by describing.** Each line that quotes a tag from the operator's sheets, a rating term, or an intimate
example is rewritten to say what kind of thing it was, and keeps its point. Before → after, in shape:

```
before: WD14 read <tag>, <tag> and <tag> off the photograph …
after:  WD14 read three clothing tags off the photograph …
```

- **The lines:** archived `0018` `design.md:573`, `tasks.md:281`; `0020` `design.md:86`; `0021` `design.md:172-174,
  210-212, 346, 361-362, 508-509, 616, 631, 637`, `proposal.md:44, 65, 110`, `specs/sheet/spec.md:111-112`,
  `tasks.md:148, 153-157, 165, 217, 224, 257, 496-497`; `0025` `design.md:20, 23, 25`, `proposal.md:11, 35`,
  `tasks.md:46, 49, 56`; `CHANGELOG.md:336, 341, 436, 438, 447, 1177-1178, 1197, 1289, 1305, 1350-1351, 1381, 1390,
  2281, 4021`.
- **Per-tag counts from the operator's sheets and photographs** (`0021` `design.md:210-212`, `:361-362`,
  `tasks.md:496-497`, `CHANGELOG.md:1177-1178`, `:1350-1351`) become a statement without the counts.
- **Kept:** `navel`, `leotard`, `pantyhose` and `thighhighs` — ordinary clothing and body words — and aggregates such
  as "102 of the 200".
- **The version's own `CHANGELOG.md` entry** states the exception — archived changes and earlier entries edited, so
  that no intimate tag stays in the prose — and names no tag.

### D2

**Comments and docstrings only.** In `tools/derive_field_map.py`:

- **`:70-75`** — the per-tag counts become "the operator's own sheets show the split separates cleanly".
- **`:207-211`** — "the counts are load-bearing" is false: the keys decide, and `PRECEDENCE` alone picks the same
  winner for each tag filed under more than one criterion. The comment says so.
- **`:369-375`** — the `inflect()` docstring's quoted tags become their shapes: an `-ing` form, a phrase with an
  `-ed` word.

`FILED`, `SEEDS`, `PRECEDENCE`, `--refresh`, `filings()` and every test that reads `.data/` stay. A digest of
`FILED`, `SEEDS` and `PRECEDENCE` is `b8f6544393739af5` at the cut and after it.

### D3

**The check lives outside the tree.** `.minions/prose-terms.txt` holds the intimate tags `FILED` holds and the
generic terms, each in its space and underscore spellings; it is gitignored with the rest of `.minions/`. The prose grep
and the comment grep use it: over every tracked `*.md`, and over the comments and docstrings of `tools/` and `isekai/`, which a
`tokenize` and `ast` pass prints. `FILED`'s keys and the `SEEDS` stems are string literals, so the second pass never
sees them. No tracked test holds the list; review holds the rule.

### D4

**D33 goes under `## The product` in `docs/decisions.md`, after D30, verbatim:**

```
### D33 · The operator decides what is rendered

**isekai places no restriction on content: no filter, no rating tag, no safety terms in the negative.** The operator
writes the positive prompt by approving the sheet, and answers for what renders — as JoyCaption reads without
restriction.

- **Why:** self-hosted, private by default, open models on the operator's own machine and pod
  ([D0](#d0--self-hosted-open-source-open-models)).
- **Made by:** `0036`.
```

It closes `0025·S1`.

### D5

**`docs/pins.md` says what it holds.**

- **`:42`**, *pinned by* for the image's Python environment: `a lock with every hash; Python by patch` →
  `a lock with every installed package's hash; Python by patch; the sdist builds' tools by version`.
- **`:88`**, the Ollama runtime's *what stands in*: `the alias's layers are checked` → `the alias's model and projector
  layers are checked`.
- ***Not pinned* rows after `:90`**, in the table's columns:

  | input | why not | what stands in |
  |---|---|---|
  | the reader alias's template, system prompt and parameters | the check compares the model and projector layers alone, and changing the rest needs write access to the operator's Ollama store | `config/joycaption.Modelfile`, from which the alias is built |
  | the build tools of the image's sdist-only packages | `image/pyproject.toml`'s build constraints fetch them by version into an isolated build, with no hash checked | the image digest freezes what they built; PyPI never re-serves a released file under new bytes |

  The first closes `0033·S2`; the second is the doc half of `0033·S3`.
- **`:26`**, *attribution*'s *where it stops*: add `; a render on another server, after a teardown that did not answer
  204, borrows .runpod_pod_image's pin` — closes `0033·R2`, and with [D6](#d6) `0033·S1`, whose `down.sh` half
  `0034`'s design D3 settled against.

Every backticked path in a new row exists: `tests/test_docs.py`'s `test_every_path_the_pins_guide_names_exists`
holds it.

### D6

**The messages route through `infra/down.sh`.** Before → after:

- **`infra/up.sh` `lost()`, `:30-32`:** `Check the RunPod MCP's list-pods, delete any 'isekai' pod there with
  delete-pod, then re-run bash infra/up.sh.` → `Check the RunPod MCP's list-pods; for an 'isekai' pod there, write its
  id to .runpod_pod_id and run bash infra/down.sh, then re-run bash infra/up.sh.` Closes `0034·R5`.
- **`infra/down.sh:16`:** `…check the RunPod MCP's list-pods.` → `…find the pod with the RunPod MCP's list-pods,
  write its id to .runpod_pod_id and run bash infra/down.sh again.`
- **`infra/down.sh`'s other-status branch, `:36-43`:** add, before its `exit 1`, `echo "Once the RunPod MCP confirms
  it gone: rm .runpod_pod_id .runpod_pod_image" >&2`.
- **`infra/render.sh`'s port refusal, `:46-47`:** `stop what holds the port, likely an earlier tunnel: kill
  \$(lsof -t -iTCP:8188 -sTCP:LISTEN)` → `An earlier session's tunnel stops with pkill -f -- '-L 8188:localhost:8188';
  lsof -iTCP:8188 -sTCP:LISTEN shows anything else`. Closes `0035·S6`.

**The teardown test narrows.** `tests/test_infra.py`'s `test_the_timeout_teardown_resolves_from_the_root_the_script_moved_to`
takes the first non-comment line naming `down.sh`; once `lost()` names it, that is an `echo`. The test skips `echo`
lines too, so it keeps checking the teardown call at `:158`.

**Constraints the new text keeps:** `up.sh` still names `list-pods`; `render.sh`'s refusal holds no `curl `, no
`infra/up.sh` and no `--server`, which `tests/test_infra.py` reads as the calls themselves.

### D7

**A neutral placeholder.** `flows/summon-anime-wai/graph.json:13`'s `LoadImage` `image` — a real photograph's
timestamped filename — becomes `photo.jpeg`. `build_graph` replaces it with the uploaded name
(`isekai/pipeline/generate.py:342`) before any submission, so the submitted graph and its `graph_sha256` do not move.

- **The re-pin, in place,** as `0.23.0` did: `PINNED` in `tests/test_flow.py` takes the flow's new digest, and the
  phase's `CHANGELOG.md` entry names it in full (`test_a_re_pin_leaves_a_record_a_later_reader_can_find`).
- **The goldens** `tests/golden/{sheet,sheet-empty,prompt,render}.json` carry the summon flow's digest; `render.json`
  also carries the raw graph's `flow_graph_sha256`. Each takes the new value.
- **A new test,** `test_the_graph_placeholder_never_reaches_a_submitted_graph` in `tests/test_generate.py`,
  `spec_exempt`: `build_graph` over the tracked flow and over a copy whose placeholder is another name, with the same
  photograph, prompt and seed, gives the same bytes.

### D8

**No spec delta.** No requirement changes: the living specs hold no hit, and R2's limit goes to `docs/pins.md`
([D5](#d5)). `.openspec.yaml` sets `skip_specs: true`, and `specs/.gitkeep` stands in.

**Patch conditions hold:** no format version moves; no behaviour fix; nothing deprecated; the product — a sheet's
fields, the prompt, the image — is unchanged. New records name the summon flow's new digest, which no reader reads.

## Dependencies

None.

## Risks / Trade-offs

- **A description loses a detail a reader wanted** → the history holds the original, and the argument each line made
  stays.
- **The term list misses a term** → the list is built from `FILED`'s own intimate tags plus the generic terms; review
  reads the diff.
- **Editing the archive and the changelog breaks their stated rules** → the operator's exception, stated in the
  version's entry ([D1](#d1)).
- **The re-pin moves the digest new records carry** → nothing reads it; a comparison across the re-pin finds the
  `CHANGELOG.md` entry.

## Verdict

**feasible** — prose, comments, messages and an inert placeholder, each with a check that fails before the build.
