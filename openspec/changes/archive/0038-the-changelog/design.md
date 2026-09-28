# Design — 0038 the changelog

The rules the rewritten changelog follows, what it drops, what it keeps, and what holds it. **Verdict: feasible** —
prose, `CLAUDE.md` rules and a structural test file; no behaviour moves.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`9dc8240`):

- **The file:** `CHANGELOG.md` has a preamble (`:1-24`), `## [Unreleased]`, and every version from `0.26.0` down to
  `0.1.0`, `## [0.5.0]` among them with no body but "Skipped". A link-reference block ends the file and stops at
  `0.7.0`.
- **Its sections:** Added, Changed, Fixed, Removed and Security, plus Notes, Verified, Documentation, Not verified,
  Known defects and titled one-offs in `0.8.0`–`0.22.3`.
- **Its only reader in code:** `tests/test_flow.py`'s `test_a_re_pin_leaves_a_record_a_later_reader_can_find` finds
  each `PINNED` digest in the file: `conjure-anime-wai`'s in `0.23.0`, `summon-anime-wai`'s in `0.25.1`.
  `tests/test_docs.py` lists `CHANGELOG.md` among the root files `docs/pins.md` may name.
- **Its citations:** `CLAUDE.md:114-118`, `:152`, `:204`; `docs/pins.md:78`; `evaluation/baseline/README.md:50`,
  `:159`, `:258`; the comment at `evaluation/baseline/build_subjects.py:30`.
- **Its writers:** mf-build appends each phase's entry under `## [Unreleased]`, "1–3 short lines: what the phase
  changed and why". mf-release renames `[Unreleased]` to a dated version heading, without a change id.

## Goals / Non-Goals

**Goals:** a changelog a person reads in minutes and an agent loads cheaply; one pointer per version to its change;
rules stated once and checked by a test.

**Non-Goals:** MinionsFactory's skills; the re-pin record's home; the archived changes; any behaviour.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | one bullet per change: 1–3 short lines, what and why, ending with its design id | mf-build's own rule, with `P9`'s stable id | paragraphs; a bullet per phase or per commit |
| [D2](#d2) | each heading from `0.7.0` names its change | one pointer per version to the archive and to `git log` | an id per bullet only |
| [D3](#d3) | figures, pod ids, old digests, non-standard sections, `0.5.0` and the link references go | the archived changes and git hold them | a pointer to the old text |
| [D4](#d4) | the current `conjure` and `summon` digests stay, in the bullets of the versions that pinned them | `tests/test_flow.py` and its scenario read them | moving the re-pin record — not a patch's |
| [D5](#d5) | the preamble holds the rules only | the file's rules are read where it is read | provenance notes |
| [D6](#d6) | `CLAUDE.md` states the entry, heading and no-citation rules; the pod-id guardrail is rewritten | one statement beside the version line | a rule in the preamble alone |
| [D7](#d7) | the `evaluation/baseline/` citations are removed, the fact stated in place | a component's README holds what it needs | pointing them at the archive |
| [D8](#d8) | `tests/test_changelog.py` holds the format and the no-citation rule | a rule nothing checks erodes | a length limit in prose only |
| [D9](#d9) | no spec delta; the patch conditions hold | no requirement changes | — |

### D1

**A bullet is one change an operator notices.** It sits under one of Added, Changed, Deprecated, Removed, Fixed or
Security, and says in 1–3 short lines what changed and why. It ends with its design id: `(0035 D2)`, or
`(0035 D2, D4)`; a change with no decision behind it ends with the change alone, `(0035)`. Versions `0.1.0`–`0.6.0`
have no change and carry no id. Before → after, in shape:

```
before:  - **`compare`, a new verb** (`0035` design D2): `python -m isekai compare <batch>` writes …
           (four more lines of what it links, how it sorts, and what it prints)
after:   - `compare` verb: writes `compare.html`, each photograph beside its renders (0035 D2).
```

No bullet holds a figure, a cost, a test count, a file:line reference or a pod id. The rewrite takes each version
from its current entry and its archived `proposal.md`, and keeps only what is true of that version.

### D2

**Each heading names its change** from `0.7.0` on: `## [0.25.0] - 2026-09-27 · 0035-the-flow-skills`. The ids, by
version:

| versions | changes |
|---|---|
| `0.7.0` | `0001-mf-standard` |
| `0.8.0`–`0.13.0` | `0008-one-path` … `0013-walking-skeleton` |
| `0.14.0`–`0.22.0` | `0014-delete-the-old-path` … `0022-one-arm` |
| `0.22.1`–`0.22.9` | `0023-backlog-paydown` … `0031-the-backlog` |
| `0.23.0`, `0.24.0`, `0.24.1`, `0.25.0`, `0.25.1`, `0.26.0` | `0032-the-tag-verb`, `0033-pin-and-record`, `0034-runpod-rest-v2`, `0035-the-flow-skills`, `0036-the-prose`, `0037-the-boundaries` |

Each id is the directory under `openspec/changes/archive/` whose `proposal.md` names that version. `0.4.0` and
`0.6.0` keep their headings and dates; `0.1.0`–`0.6.0` carry no id.

### D3

**What goes:** every figure, time, cost and test count; the pod ids; every flow digest but those [D4](#d4) keeps;
Notes, Verified, Not verified, Known defects and the titled one-off sections (Documentation becomes Changed); the
`## [0.5.0]` heading; the link-reference block. Git holds the old text; no bullet points at it.

### D4

**The current digests stay.** `0.23.0`'s bullet for the re-pinned `conjure-anime-wai` names
`f2bd3202079b1288068aed7ccf57e2b6b0e3b9a1db037973b4be99f83bf22a1f`, and `0.25.1`'s for `summon-anime-wai` names
`96c605821e68a8ac2f1c7a60807cfcfb4c3658ae4112cc84d21a00bf39f3e698`, in full, as `tests/test_flow.py` requires.

### D5

**The preamble holds the rules only.** Everything above `## [Unreleased]` becomes:

```
# Changelog

Notable changes, per [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0/).

A version's heading names its change: `## [0.25.0] - 2026-09-27 · 0035-the-flow-skills`. A bullet is one change
an operator notices, in 1–3 short lines — what changed and why — ending with its design id, `(0035 D2)`. It holds
no figure, file:line reference or pod id; a re-pinned flow's bullet names its new digest.
```

### D6

**`CLAUDE.md` states the rules.** Before → after:

- **`:117-118`:** `` `CHANGELOG.md` follows Keep a Changelog + SemVer, with an entry appended **per phase** under
  `## [Unreleased]` and cut at release. `` → `` `CHANGELOG.md` follows Keep a Changelog + SemVer and its preamble's
  rules: each phase appends one bullet under `## [Unreleased]` — 1–3 short lines, what changed and why, ending with
  its design id — and the release cuts the heading as `## [X.Y.Z] - <date> · <change-id>`. No code, doc or README
  cites it: it is a release record, not a source. ``
- **`:204-205`:** `` the three pod ids already in `CHANGELOG.md` stay, because that file is append-only history and
  this rule is what stops a fourth being added. `` → `` no pod id is in `CHANGELOG.md`, and this rule keeps it so. ``

The rewrite is the exception to append-only; this version's own bullet says so.

### D7

**The citations go.** `evaluation/baseline/README.md:50` and `:159` and the comment at
`evaluation/baseline/build_subjects.py:30` state the landscape gap in place, without naming the changelog;
`README.md:258` drops its `see CHANGELOG.md` parenthesis. The comment edit changes no behaviour.

### D8

**`tests/test_changelog.py` holds the rules**, each test `spec_exempt` as structural, each with a twin that feeds it a
breaking input:

- **`test_the_changelog_keeps_its_format`:** `## [Unreleased]` is the first `## ` heading; every other matches
  `## [X.Y.Z] - YYYY-MM-DD`, with ` · NNNN-slug` from `0.7.0` on; every `### ` heading is one of Keep a Changelog's names;
  no bullet is nested; no bullet, its continuation lines joined, runs past 300 characters.
- **`test_nothing_cites_the_changelog`:** no text file `git ls-files` lists names `CHANGELOG.md`, except
  `CHANGELOG.md`, `CLAUDE.md`, `docs/pins.md`, `tests/test_flow.py`, `tests/test_docs.py`, `tests/test_changelog.py`
  and anything under `openspec/changes/`.

### D9

**No spec delta.** No requirement changes; the tests are structural. `.openspec.yaml` sets `skip_specs: true`, and
`specs/.gitkeep` stands in. **The patch conditions hold:** no format version moves, no behaviour fix, nothing
deprecated, the product unchanged.

## Dependencies

None.

## Risks / Trade-offs

- **A rewrite drops a fact someone wanted** → git keeps every earlier text, and each version names its change.
- **mf-release writes a heading without the change id** → the format test fails the release gate before the tag;
  the release agent adds the id.
- **A long re-pin bullet** → a 64-character digest and its flow fit inside 300 characters.

## Verdict

**feasible** — prose and rules, each held by a check that fails before the build.
