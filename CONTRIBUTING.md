# Contributing

How a change reaches `main`, and what proves it. The method is OpenSpec SDD: work is defined as a change before it
is built, the living spec is test-backed, and a release folds one into the other.

```
mf-cut-change ──▶ mf-build ──▶ mf-converge ──▶ mf-release
the artifacts     the phases   review          fold · archive · tag
```

## How a change lands

Work is defined before it is built, as a change under `openspec/changes/<id>/`. A change is the unit of
work **and** the unit of release.

A change is `proposal.md`, `specs/`, `design.md` and `tasks.md`, always all of them, plus the tracked
`.openspec.yaml` where one is needed. It may carry a file of its own beside them — `0023-backlog-paydown`
shipped `no-spec-delta.md` — but never fewer.

1. **Settle the decisions first.** A change is cut from decisions argued against a person, not from a first
   draft. The verdict — `feasible` / `feasible-with-caveats` / `needs-precursor` /
   `infeasible-as-specified` — is recorded in the change's `design.md`.
2. **`mf-cut-change` scaffolds the change** and its branch, which is the change id. The id is
   `<digits>-<lowercase-slug>`, and the digits are **the next free number**, zero-padded to four — higher
   than every id under `openspec/changes/` and its `archive/`, on the default branch and every unmerged
   version branch, for a minor and a patch alike. An id is never renamed once commits carry it as a trailer.
3. **Author** each artifact against `openspec instructions <proposal|specs|design|tasks> --change
   <NNNN-slug>`, one at a time, fetching each immediately before writing it. `proposal.md` additionally
   opens with `bump:` frontmatter, `minor` or `patch` — **the CLI neither emits nor checks that key; it is
   on the author.**
4. **A change that changes no requirement** declares the absence rather than inventing one: `skip_specs:
   true` in the change's tracked `.openspec.yaml`, **plus** `specs/.gitkeep`. Both, not either —
   `0023-backlog-paydown` carries the pair. Never write a requirement solely to satisfy the validator.
5. **Finish on a green check** — `openspec validate <NNNN-slug> --strict`.

**Progress lives in `tasks.md`**, in its `## Progress` checklist, and **the current phase is the first
unchecked box**. A phase is advanced by a commit **and** a ticked box, in that phase's own commit — either
alone is not an advance.

**The living spec** is `openspec/specs/<capability>/spec.md`, each capability a contract with one
owner; `openspec/specs/*/` lists them. A capability enters and leaves the living spec only when a change
is **archived**, which is `mf-release`'s act and never the builder's — so what is on disk is never what a
pending change implies. Every `#### Scenario:` carries a `- **Key:**` and a `- **Layers:**` bullet, and the
key is `<capability>:<requirement-slug>:<scenario-slug>`, so a key locates its own file. On release the delta
is folded in and the change moves to `openspec/changes/archive/`; archived changes are never deleted. A spec
reads as [the standards](CODING_STANDARDS.md#project-rules) say.

**The tag comes from `bump:`.** `mf-release` runs `next_tag.py` on it: `minor` after `v0.40.0` → `v0.41.0`. The
annotated tag, `CHANGELOG.md`'s `## [X.Y.Z]` and the version in `pyproject.toml` and `uv.lock`, the version
files, all carry that number, and the release writes `version:` below `bump:`. One branch per version.

`CHANGELOG.md` follows Keep a Changelog + SemVer and its preamble's rules: each phase appends one bullet under
`## [Unreleased]` — 1–3 short lines, what changed and why, ending with its design id — and the release
renames that heading `## [X.Y.Z] - <date>`. No code, doc or README cites it: it is a release record, not a
source.

**A minor delivers one feature; a patch delivers none**, and meets every one of these — work that
cannot is not a patch:

- no format version moves — `MANIFEST_VERSION`, any run file kind's version, which
  `isekai/foundation/artifacts.py` declares;
- every behaviour fix is required by an existing requirement: a scenario may be added under one, a
  requirement may not;
- nothing deprecates a verb or a flag;
- nothing changes the product — a sheet's fields, the prompt, the image — for the same inputs and
  configuration.

Every commit is a Conventional Commit, **one phase = one commit**, staged **by name** and never with
`git add -A`. Each carries a `Change: <change-id>` git trailer, in the trailer block at the end of the
message and **contiguous** with any `Co-Authored-By:` line — a blank line between them silently breaks the
block.

## The evidence a change carries

**The gate is `make gate`**, run from the repository root; `make -n gate` prints what it runs. The
`Makefile` is its one declaration, and the notes on each command are the `Makefile`'s. CI
(`.github/workflows/ci.yml`) runs `make gate` too. The browser tests are `make e2e`, out of the gate while an
unattended run's sandbox cannot run them; CI runs them after the gate, on every push.

**A change is measured as well as gated.** `metrics/catalogue.toml` names the measures, each a script under
`scripts/metrics/` or a value the station passes. The build drafts a change's values and the release commits them to
`metrics/changes/<change-id>.json` ([D47](docs/decisions.md#d47--a-change-is-measured-from-isekais-own-catalogue)).
A measure that cannot be read is recorded unavailable; nothing halts.

**A move is pre-flighted.** A change that moves or rewrites lines of `isekai/` or `evaluation/` runs
`uv run python -m tools.mutate <path:lines> --tests <files>` over those lines, before the move and over the same lines after
it, on the tests that cover them. A survivor is killed by a test, or the change says why it is equivalent. It is not in the gate:
a run takes minutes. The run works in a copy that is a git repository of the tracked files and
links `models/` alone, so a test that writes under `models/` writes through to the checkout: isolate it.

Every command green, or the phase is not done. **Never weaken the gate to pass** — see `AGENTS.md`'s guardrails.

Beyond the gate, **image-as-code phases also run `docker build --check`**.
That is a convention for those phases, not part of the gate; adding it to the gate means adding it to the
`Makefile`.

**The suite runs offline and deterministically.** The ComfyUI transport is faked behind a `ComfyTransport`
Protocol (`FakeComfyClient`), the suite reads the shipped graph itself rather than a fixture copy of it,
and seed drawing takes an injected `random.Random`. No test hits a GPU or the network. A scenario only a
browser shows declares `Layers: e2e` and runs under `tests/e2e/`, by `make e2e` — Playwright on Chromium, which
`make browsers` fetches, against the real server on the suite's doubles through `ISEKAI_WIRING`; every
other declares `Layers: unit`. Diffusion quality and identity fidelity are verified **live on a pod, by
eye**, never mocked and never asserted.

The tooling is **operator tooling, recorded and not pinned**: `@fission-ai/openspec@1.11.0`, resolved on
`PATH`. It is deliberately **not** in the gate — nothing in CI runs it, so a moving version can never
turn CI red. `tests/test_spec_bindings.py` holds every binding: each living key has a test, each marker a
key, and each behaviour a test holds carries its key — a test carries its `spec` markers or one `spec_exempt`.
Both markers are registered in `pyproject.toml`, because pytest only warns on an unregistered marker.
