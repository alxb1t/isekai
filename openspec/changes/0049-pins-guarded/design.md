# Design — 0049 pins guarded

How each pin's guard is tightened, how a bad runtime report is refused once, where the models root is anchored, and
what the drift job runs. **Verdict: feasible** — tests, a constant, a message and a workflow; no file the image
copies.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`df5e436`):

- **The clone count:** `pinned_commits` (`tools/derive_image_project.py:71-80`) finds `git clone https://github.com/…`
  and `git checkout <40-hex>`, and exits when the two counts differ. The deriver uses its `owner/name → sha` map
  (`:162`). `test_every_git_clone_in_the_image_is_pinned_to_a_commit` (`tests/test_infra.py:414-419`) asserts `== 3`.
- **The build tools:** `SDIST_BUILDS` (`tests/test_infra.py:739-744`) keys the source-only packages by name;
  `uncovered_sdists` (`:747-768`) compares tool names. The lock's source-only packages are insightface `0.7.3`, fvcore
  `0.1.5.post20221221`, iopath `0.1.10` and antlr4-python3-runtime `4.9.3`. `docs/pins.md`'s *Not pinned* table
  (`:81-91`) names no build tool.
- **The goldens:** `_caption` and `_tags` (`tests/test_artifact_bytes.py:59-75`) use `FakeReader` and `FakeTagger`,
  whose readings leave `artifacts` and `options` empty, so neither key is written.
- **The runtime report:** `read_runtime` (`isekai/pipeline/generate.py:419-436`) turns a `KeyError` or `TypeError`
  into a plain `Refusal` worded "carries no <exception>". The transport turns the same errors into a permanent
  `TransportFailure`, "the endpoint answered in a shape this build does not read (…)"
  (`isekai/boundary/comfy/client.py:145-150`). `cache(partial(read_runtime, client))`
  (`isekai/interface/cli.py:608`) keeps no exception, so each render asks again. The tagger's seam keeps a refusal
  as well as a success (`cli.py:457-468`).
- **The models root:** `DEFAULT_MODELS_DIR = Path("models")` (`isekai/shared/vocabulary.py:32`); a copy at
  `evaluation/__main__.py:49`. `REPOSITORY` (`isekai/foundation/run.py:72`) is anchored. `ANCHORS`
  (`tests/test_package_paths.py:41-66`) lacks the models root and `FIELD_MAP_PATH`.
- **"16.5 GiB":** `infra/up.sh:180`; comments at `tests/test_infra.py:403`, `:441`. The manifest's size is
  computed, never stated, at `infra/up.sh:59`.
- **Drift:** `make derive` (`Makefile:24-31`) ends in `git diff --stat`, which exits 0. No workflow has a `schedule:`.
  `uv_versions_apart` (`tests/test_infra.py:603-617`) reads uv's version from `ci.yml` alone. The principles' *Known
  breaks* (`docs/principles.md:165-167`) says the fetching derivers are never re-run.

## Goals / Non-Goals

**Goals:** each guard fails on the case it claims; a bad report is refused once in the transport's words; the models
root resolves from anywhere; drift turns something red.

**Non-Goals:** any file the image copies; a guard that the tree matches the image; refusing a session with no record.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `pinned_commits` counts every `git clone`, whatever its flags or host, against the checkouts; the test compares the clone count with the map | a principle's guard must not narrow to today's clones | the hard-coded `== 3` |
| [D2](#d2) | `SDIST_BUILDS` is keyed by name and version; pins.md's *Not pinned* gains the requirements a backend adds while it builds | a bump then fails until its tools are recorded again | the deriver writing the map, which needs the network |
| [D3](#d3) | the caption and tags goldens come from readings carrying `artifacts` and `options` | the bytes of a pinned producer are held | a second golden per kind |
| [D4](#d4) | a malformed report raises the transport's permanent failure in its words; the CLI keeps a refused report for the session | the transport SHALL and "read once per session" | refusing the session once with no record, a new requirement |
| [D5](#d5) | the models root is `REPOSITORY / "models"`, pinned in `ANCHORS` with `FIELD_MAP_PATH`; `evaluation/` imports it; the refusal keeps "from the repository root" | every other root is anchored; the remedy's command is relative to the root | a `--models` flag |
| [D6](#d6) | "16.5 GiB" leaves `up.sh`'s message and the tests' comments, with no figure in its place | a figure goes stale | the corrected figure |
| [D7](#d7) | `make drift` runs the fetching derivers and fails on a diff; `make derive` adds the field map; `drift.yml` runs `make drift` weekly | a drift report that never updates anything | re-deriving the field map in CI, which lacks the vocabulary |

### D1

**Clones.** `pinned_commits` finds each `git clone` command — any flags, any URL — and each `git checkout <40-hex>`,
and exits naming the gap when their counts differ. Its map still keys a GitHub clone by `owner/name`. The test asserts
that the map holds one entry per `git clone` in the `Dockerfile`. A twin feeds a clone with a flag and one from
another host, each without a checkout, and expects the exit.

### D2

**Build tools.** Before → after:

```
SDIST_BUILDS = {"insightface": ("setuptools", "numpy", "cython"), …}
→
SDIST_BUILDS = {("insightface", "0.7.3"): ("setuptools", "numpy", "cython"), …}
```

`uncovered_sdists` reads each source-only package's name and version, and reports one the map lacks as
`<name> <version>`. The twin gains a bumped insightface. pins.md's *Not pinned* gains a row: *the requirements a build
backend adds while it builds* | uv fetches what the backend asks for at build time, outside the constraints | the map
of each source-only package's declared tools, checked against the lock.

### D3

**Goldens.** In `tests/test_artifact_bytes.py`, `_caption` and `_tags` use readers whose readings carry
`READER_ARTIFACTS` and the reader's and tagger's options. `tests/golden/caption.json` and `tests/golden/tags.json` are
rewritten to the bytes those produce.

### D4

**The runtime report.** `read_runtime` raises `TransportFailure("permanent", …)` in the words `_reported` uses for a
shape this build does not read, so a `{"system": null}` report reads as any other unread answer. In `cli.py`, the
report's reader keeps a refusal as well as a success, as the tagger's seam does, so the endpoint is asked once per
session. `render` still records the refusal per photograph and flow, before any seed is submitted.

### D5

**The models root.** `DEFAULT_MODELS_DIR = REPOSITORY / "models"`, imported from `isekai/foundation/run.py`.
`evaluation/__main__.py` imports it in place of its copy. `ANCHORS` gains `vocabulary.DEFAULT_MODELS_DIR` with
`("models",)` and `field_map.FIELD_MAP_PATH` with `("config", "field_map.json")`. The vocabulary refusal names the
absolute root and keeps "run … from the repository root", since its command is a relative path.

### D6

**The figure.** `infra/up.sh:180`: "Without the network volume, provisioning downloads 16.5 GiB onto storage" →
"Without the network volume, provisioning downloads every model onto storage". The comments at
`tests/test_infra.py:403` and `:441` say "the models" in place of the figure.

### D7

**Drift.** The `Makefile`:

```
drift:   derive_manifest · derive_eval_manifest · derive_vocabulary · derive_reader ·
         derive_image_project · git diff --exit-code --stat -- config/ evaluation/eval_models.json image/
derive:  derive_field_map, then drift's recipe
```

`.github/workflows/drift.yml`: `schedule` weekly and `workflow_dispatch`; `permissions: contents: read`; no secrets;
the same pinned `actions/checkout` and `astral-sh/setup-uv` as `ci.yml`, uv at the root project's version; one step,
`make drift`. `uv_versions_apart` reads every workflow's uv version. The *Known breaks* line says the fetching
derivers run weekly in `drift.yml`, outside the gate. pins.md's *Re-pinning* names `make drift`.

## Dependencies

None.

## Risks / Trade-offs

- **A source goes down for a day** → the weekly run is red once; the next run tells a move from an outage.
- **`uv lock` resolves differently on a new uv** → uv is pinned to the root project's version in the workflow.
- **A kept refusal outlives a fixed endpoint within one session** → the session is one invocation; the next asks
  again.

## Verdict

**feasible** — each guard a few lines, each held by a test; the drift job is a workflow and a `make` target.
