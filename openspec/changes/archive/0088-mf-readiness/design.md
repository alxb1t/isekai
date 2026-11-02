# Design — 0088 mf readiness

The worktree, the changelog, the documents, the threat model and the ruleset, each as the unattended line needs it.
**Verdict: feasible.**

## Context

MinionsFactory's line now cuts each version in its own worktree and takes it to `main` unattended. A fresh worktree
holds tracked files only, a run reads root `AGENTS.md`, and `mf-release` writes `## [<tag>] - <today>`. Review reads the
documents `AGENTS.md` names, and a missing one reads `inconclusive`.

## Goals / Non-Goals

**Goals:** `make setup && make gate` passes in a fresh worktree. A release passes `tests/test_changelog.py`. Review finds
real standards, an architecture map and a threat model. `main` refuses a force-push and a deletion.

**Non-Goals:** a run under the sandbox; any change to `isekai/`, a flow, a spec or the image.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `make setup` runs `uv sync --locked`, `npm ci --prefix ui`, `make browsers` and the vocabulary fetch. The gate stays free of fetches | a fresh worktree then runs the vocabulary's tests rather than skipping them | `ISEKAI_VOCABULARY=absent` in the gate: the operator's gate keeps those checks on purpose |
| <a id="d2"></a>**D2** | `AGENTS.md` carries `**Worktrees:**` `` `../` ``, `**Workspace setup:**` `` `make setup` `` and `**Ship network:**` none, the last with no backticks on its line | each backticked word on that line is read as a domain, and a word that is none halts a run; the cut's `.venv` already holds gpunit | `github.com` listed now: a host is added only when a run needs it |
| <a id="d3"></a>**D3** | `_wait` in `tests/e2e/conftest.py` opens through `urllib.request.build_opener(urllib.request.ProxyHandler({}))`, as `tests/test_ui.py` does | a proxy in the environment would otherwise stall the browser tests' start for its whole bound | leaving it until a sandbox fails |
| <a id="d4"></a>**D4** | `tests/test_changelog.py` holds headings up to `0.60.0` as they are; from `0.60.1` a heading's change id and a bullet's `###` section are optional | the release writes neither, and a rule resting on a worker's memory halts an unattended run | stating the stricter rule in prose |
| <a id="d5"></a>**D5** | The rules move, never copied. `CODING_STANDARDS.md` takes *Engineering conventions* and *How a spec reads*. `CONTRIBUTING.md` takes *The quality gate* and *How a change is cut here*, rewritten: `bump:` opens `proposal.md`, the tag comes from `next_tag.py`, the branch is the change id, a phase's entry goes under `## [Unreleased]`, `pyproject.toml` and `uv.lock` are the version files, `mf-cut-change` scaffolds a change, and `openspec/specs/*/` lists the capabilities. `AGENTS.md` names them as mandatory context | a second copy drifts | copies beside `AGENTS.md`; `openspec/config.yaml` |
| <a id="d6"></a>**D6** | `ARCHITECTURE.md` is one screen: what the system is, its layers a line each, its boundaries, links into `docs/`. No diagram is copied | `docs/` stays the one source, and review gets a way in | a full architecture document |
| <a id="d7"></a>**D7** | `THREAT_MODEL.md` has the sections `## Worth protecting`, `## Trust boundaries`, `## Entry points` and `## Out of scope`, from `docs/principles.md`'s privacy principles, the secret and spend guardrails of `AGENTS.md`, and D6, D18, D22–D24, D26, D28, D34–D36, D41, D43 | security reads it first | |
| <a id="d8"></a>**D8** | A ruleset on `~DEFAULT_BRANCH` of `non_fast_forward` and `deletion`, by a person, last. No pull request is required | a release pushes to `main` | a pull-request rule |

## The run's lines

`AGENTS.md` gains this section. The `**Ship network:**` line holds no backticks, per [D2](#d2).

```markdown
## The run's lines

- **Worktrees:** `../` — each version's worktree sits beside the primary, named by its change id.
- **Workspace setup:** `make setup` — restores what a fresh worktree lacks.
- **Ship network:** none — the given package hosts are enough, because the setup fills the worktree first.
```

## The mandatory lines

`AGENTS.md`'s opening gains these lines, and states `make gate` as the gate.

```markdown
**Before work, read [the coding standards](CODING_STANDARDS.md) and [how a change lands](CONTRIBUTING.md): mandatory
shared context.** **Before designing, building or reviewing, also read [the decisions in force](docs/decisions.md) and
[the architecture](ARCHITECTURE.md).**
```

## Tests

| layer | adds | removes |
|---|---|---|
| unit | `test_a_release_after_the_line_needs_no_change_or_section`, in `tests/test_changelog.py` | none |
| end-to-end | none, so no new runs | none |

The suite stands at 1454 tests, by `uv run pytest` at the base. This change deletes and merges no test.

## Dependencies

None.

## Risks / Trade-offs

- **`make setup` fetches at each cut** → it runs in the cut's session, never in the gate, and a failure halts the cut.
- **Chromium under the sandbox is unmeasured** → the operator's proof before the first `mf-ship`; a failure is a design
  question for MinionsFactory.
- **`tests/test_changelog.py` loosens** → from `0.60.1` only; every earlier heading stays held, and the bullet length and
  section names stay held for all.

## Verdict

**feasible.** Every file named exists at the base, and no format, verb or product moves, so the change is a patch.
