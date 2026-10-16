# Design — 0060 the working window

How isekai moves to gpunit `v0.7.0` and a window volume, closes the pod cards the old record held back, and proves
the window across pods. **Verdict: feasible** — gpunit's `session` takes the same arguments; the rest is a spec key, a test, the
skill's order and one rebuild.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `d503f84` (`v0.35.1`):

- **The pin:** `pyproject.toml:49` names `gpunit@v0.2.0`; `uv.lock:79-81` locks it. The one call is
  `gpunit.session(cwd / "gpunit.toml", environ=environ, cwd=cwd, say=say)` (`isekai/boundary/gpu.py:44`); its
  exceptions are handled in `isekai/interface/render.py` (`:271`, `:300-319`). `v0.7.0` exports the same
  `session`, `Lost`, `Refused`, `TeardownFailed` and `Interrupted`, with the same signature.
- **The boot script:** `Dockerfile:85-86` `ADD`s `boot.sh` from `v0.2.0` by checksum. gpunit refuses a `boot.sh`
  older than its `v0.6.0`, so the pinned image `v0.35.1-rc3` cannot boot under `v0.7.0`.
- **The volume:** `gpunit.toml:19` is `volume = "db7sc8cild"`, which answers 404; the account lists no network
  volume. `tests/test_infra.py:895-911` holds that `gpunit.toml` names one.
- **The pins tests:** `tests/test_infra.py:707-746` holds the `boot.sh` tag equal to `pyproject.toml`'s;
  `:281-284` holds `config/image.json`'s `files` equal to the tree; `:842-846` holds the image equal to its digest.
- **The pod:** `pod_start.py` reads `GPUNIT_VOLUME_PATH`, refuses a volume under `VOLUME_SIZE_FLOOR = 40 * 1024**3`
  (`:28`, `:101`) and uses `<volume>/isekai`; `provision.py`'s `decide` skips a present, verified file (`:379-407`).
  `config/models.json`, measured below, is what the first pod of a window downloads.
- **The cards** (`.minions/backlog.md`): `0059·R8` at `pod_start.py:132`; `0059·R9` at `can_swap` (`:163-173`);
  `0059·S3` at `shm_type` (`:145-160`, the match at `:158`); `0059·R16` at `_get` (`provision.py:513-533`) and its
  comment (`:71-72`).
- **The skill:** `run-flows` step 4 asks the go and runs `isekai render` (`SKILL.md:117-144`); step 5 is
  `compare-renders` (`:146-154`). `CLAUDE.md:247-268` is the GPU protocol.
- **The guards:** `tests/test_spec_prose.py` refuses a version in the effective spec and in a code comment;
  `tests/test_principles.py` refuses a *Held by* naming a test that does not exist.

| measured at the cut | value | command |
|---|---|---|
| entries in `config/models.json` | 12 | `python3 -c "import json; print(len(json.load(open('config/models.json'))['entries']))"` |
| their size, GB | 14.43 | `python3 -c "import json; print(sum(e['bytes'] for e in json.load(open('config/models.json'))['entries']) / 1e9)"` |

## Goals / Non-Goals

**Goals:** a render that works again, inside a window nobody pays for between batches; `0059·R8`, `R9`, `R16` and
`S3` closed with a test each; one metered window that shows the second pod skipping every model.

**Non-Goals:** a change to a flow, the sheet, the prompt or a model; `0058·R5`–`R7`; a volume deleted by hand; a
skill added; a requirement on the skill's text.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | gpunit `v0.7.0` in `pyproject.toml`, relocked; `boot.sh` `ADD`ed from `v0.7.0` with its checksum (Q1) | pod work is broken until it lands; `v0.7` needs a `v0.6.0`+ `boot.sh` | staying on `v0.2.0` with a new kept volume |
| [D2](#d2) | `gpunit.toml`: `volume_gb = 50`, `volume_ceiling = "4h"`, no `volume`; the test holds the pair and the floor (Q1, Q2) | 50 GB clears the 40 GiB floor; a 4 h window is ~$0.02 | `volume_datacenter`; a kept volume |
| [D3](#d3) | README, D27 and the pins guide describe the window (Q1) | a decision in force is edited where it lives | leaving D27 on a named volume |
| [D4](#d4) | close `0059·R8`, `R9`, `R16`, `S3`, each a line and a test (Q5) | the rebuild is their trigger | another deferral |
| [D5](#d5) | the order lives in `run-flows`: go → `volume up` → `render`; step 5 asks *another batch?*; `CLAUDE.md`'s protocol names the volume (Q3, Q4) | the skill is how the operator renders; the window spans batches | a `volume down` after each render |
| [D6](#d6) | **HUMAN** — rebuild as `v0.36-rc1`, re-pin `config/image.json` and `gpunit.toml` (Q1) | only CI builds the image | a metered phase before the rebuild |
| [D7](#d7) | **HUMAN · METERED** — one window: `volume up`, a first and a second render on new pods, `volume down` (Q6) | the window is proven only across pods | one render |

### D1

`pyproject.toml:49` → `"gpunit @ git+https://github.com/alxb1t/gpunit@v0.7.0"`, then `uv lock`. `Dockerfile:85-86`
→

```
ADD --checksum=sha256:517ade6bf20d9869baeb1f1ff1ab45d9ab63c2fa477127ff11dac89611bec842 \
    https://raw.githubusercontent.com/alxb1t/gpunit/v0.7.0/boot/boot.sh /opt/gpunit/boot.sh
```

The checksum is `curl -fsSL <url> | shasum -a 256` at the cut, equal to `git show v0.7.0:boot/boot.sh` in the gpunit
clone. The `Dockerfile` is a recorded file, so `config/image.json`'s `files` is re-derived with
`uv run python -m tools.image_record`. No `isekai` code changes: `gpu.py` and `render.py` call what `v0.7.0` keeps.

### D2

```
gpunit.toml   before: volume = "db7sc8cild"
              after:  volume_gb = 50
                      volume_ceiling = "4h"
```

A comment above the pair says what it is: the models volume of a working window, made by `gpunit volume up` and
ended by `gpunit volume down` or its ceiling. Stock chooses the data centre.

In `tests/test_infra.py`, `window_volume_faults(spec)` replaces `unnamed_volume` and returns each fault by name:

| fault | when |
|---|---|
| `"names a kept volume"` | `volume` is set |
| `"no volume_gb"` | `volume_gb` is not an int |
| `"no volume_ceiling"` | `volume_ceiling` is not a non-empty string |
| `"under the capacity floor"` | `volume_gb * 1000**3 < VOLUME_SIZE_FLOOR`, imported from `pod_start` |

- `test_the_session_spec_declares_a_window_volume` binds
  `model-provisioning:reachability:provisioning-requires-the-network-volume`: no kept volume, no missing
  `volume_gb`, no missing `volume_ceiling`.
- `test_the_window_volume_clears_the_capacity_floor` binds
  `model-provisioning:reachability:the-window-volume-clears-the-floor`: not under the capacity floor. RunPod sizes are
  decimal, as `test_the_capacity_floor_clears_the_container_disk_as_well` reads them.
- The twin, `spec_exempt`, holds each fault on a spec built to have it.

### D3

- **`README.md`:** the *How it works* weights bullet and the diagram's footer say the volume lives for a window;
  *Lifecycle* says `gpunit volume up` comes first; the ④–⑦ block and the batch block run
  `uv run --env-file .env gpunit volume up` before `render` and `uv run --env-file .env gpunit volume down` when
  done; *Setup*'s prerequisite 2 is the window volume `volume up` makes; *Cost* says about $0.02 for a 4 h window of
  50 GB, in place of `~$3.50/mo`; the provisioning diagram's last line names the window's volume.
- **`docs/decisions.md` D27:** the volume lives for a working window — `volume up` makes it in a data centre chosen
  from stock, each pod of the window runs there, `volume down` or the 4 h ceiling deletes it. *Why* gains: the
  weights download once a window, and no storage bills between windows. *Made by* gains `0060`; the title, and so
  its anchor, stays.
- **`docs/pins.md`:** the gpunit recipe adds that a session refuses an image whose `boot.sh` is too old for its
  gpunit, so the rebuild comes before any render.

### D4

- **`0059·R8`:** `provision()`'s docstring ends "through `fetch`." — the `(D2)` goes; D2 in force is the sheet.
- **`0059·R9`:** `can_swap` returns `bool | None`, `None` when `/proc/swaps` cannot be read. `prepare_memory`
  prints `swap: could not read whether the container can swap` for `None`, and holds for none of them.
  `test_an_unread_swap_table_is_reported_and_never_held_for` binds `pod-image:memory:an-unread-swap-is-reported`.
- **`0059·S3`:** the type is read by device.
  - `Pod.mounts` → `Pod.mountinfo`, default `/proc/self/mountinfo`.
  - `shm_type` reads `os.stat(pod.memory).st_dev` as `f"{os.major(dev)}:{os.minor(dev)}"`. It returns the field
    after the `-` separator of the last line whose third field equals it. An unreadable file, a failed `stat` or no
    matching line return `None`, which holds as today.
  - The fixture writes a `mountinfo` whose memory line carries the temporary tree's own device.
  - `test_a_later_mount_shadows_an_earlier_one` → `test_the_type_is_read_from_the_memory_directorys_device`, binding
    `pod-image:memory:the-type-is-read-by-device`: a line naming the `shm` path `tmpfs` on another device, beside an
    `ext4` line on the memory's device, holds.
  - The tests `docs/principles.md` names keep their names; its *Held by* gains the new test.
- **`0059·R16`:** a client error is not tried again.
  - `_get` catches `urllib.error.HTTPError` before `OSError`. A code from 400 to 499 removes the partial, prints
    `WARNING: <url> answered HTTP <code>; not tried again`, and returns `False` with no wait.
  - The comment above `ATTEMPTS` says a client error is not tried again.
  - `tests/fakes.py`'s `FakeFetcher` gains `refuses: dict[str, int]`: a URL in it raises `HTTPError` with that code.
  - `test_a_source_that_answers_404_is_asked_once` binds
    `model-provisioning:source-fallback:a-refusing-source-is-not-tried-again`.

`pod_start.py` and `provision.py` are recorded files: `config/image.json`'s `files` is re-derived after them.

### D5

**`run-flows` step 4.** The go quotes both prices: *one pod session, at most 45 minutes and about $0.30; the models
volume, 50 GB for up to 4 hours, about $0.02*. On the go, before the render block:

```bash
BATCH=.data/<batch>
uv run --env-file .env gpunit volume up --yes >> "$BATCH/log.txt" 2>&1; echo "exit $?"
grep -o 'until [0-9TZ:-]*' "$BATCH/log.txt" | tail -1
```

- `volume up` creates the volume, or extends a live one to 4 hours from now.
- Non-zero: report the `refused:` lines and render nothing.
- Exit `3`: the create's answer was lost and a volume may bill. Tell the operator at once, and run
  `uv run --env-file .env gpunit volume down` only on their word.
- The render block is unchanged; its tail filter also drops `volume <id>`.

**`run-flows` step 5.** After `compare`, name the window's end — the last `until` line — and ask *another batch?*
On yes, stop: the next step 4 extends the window. On no:

```bash
BATCH=.data/<batch>
uv run --env-file .env gpunit volume down >> "$BATCH/log.txt" 2>&1; echo "exit $?"
```

- Confirm through the RunPod MCP's `list-network-volumes` that no `gpunit-isekai` volume is left; report what it
  returned. A window nobody closes ends at its ceiling.
- **The skill never runs `volume down` on its own.**
- *Never* adds the volume id beside the pod id.
- README's *The batch, run by an agent* says the skill opens the window and asks before closing it.

**`CLAUDE.md`'s GPU protocol**, one line each:

| item | gains |
|---|---|
| 1 who creates | `uv run --env-file .env gpunit volume up --yes` makes or extends the window's volume, announced with the render |
| 2 who tears down | `uv run --env-file .env gpunit volume down`, on the operator's word, or the 4 h `volume_ceiling` |
| 3 who confirms | after `volume down`, `list-network-volumes` shows no `gpunit-isekai` volume |
| the ceiling | the window: 4 hours and ~$0.02 |
| the renders bullet | the models volume persists for its window |

### D6

A **HUMAN** phase. Push `v0.36_the_working_window`; run
`gh workflow run build-image.yml --ref v0.36_the_working_window -f tag=v0.36-rc1`; check the summary's build record
equals `config/image.json`'s `files`; write the tag and digest into `config/image.json` and the digest into
`gpunit.toml`'s `image`. It comes before [D7](#d7): `v0.7.0` refuses the pinned image's `boot.sh`.

### D7

A **HUMAN · METERED** phase, on a batch with approved runs:

```
gpunit volume up --yes ──▶ isekai render (the first pod: every model saved (verified))
                       ──▶ isekai render (the second pod: every model skip (present, verified))
                       ──▶ gpunit volume down ──▶ MCP: no pod, no volume
```

While each session is open, read the pod's start lines through the RunPod MCP's `stream-pod-logs`, and write its
`saved (verified)` and `skip (present, verified)` lines, no pod id, to `.minions/0060_window_first.txt` and
`.minions/0060_window_second.txt`. After `volume down`, record `no gpunit-isekai pod` and `no gpunit-isekai volume`
from `list-pods` and `list-network-volumes` in `.minions/0060_window_proof.txt`. About $0.60: both sessions under the
45-minute ceiling, and the window.

## The phases

```
1 the pin      pyproject + uv.lock at v0.7.0; the Dockerfile's ADD; the record      D1
2 the window   gpunit.toml; the volume test; README, D27, the pins guide            D2, D3
3 the pod      0059·R8, R9, S3, R16, with their tests; the record                  D4
4 the skill    run-flows steps 4–5; CLAUDE.md's GPU protocol                       D5
5 HUMAN        the image rebuilt as v0.36-rc1 and re-pinned                         D6
6 METERED      a window: volume up, a first and a second render, volume down          D7
```

## Dependencies

- `gpunit @ git+https://github.com/alxb1t/gpunit@v0.7.0` — replaces `@v0.2.0`; locked by `uv lock`. Stdlib only,
  `requires-python = ">=3.11"`: it adds no package.

## Risks / Trade-offs

- **Stock moves inside a window** → every pod goes to the volume's data centre; a session refused for stock is
  answered by `volume down` and `volume up`, which re-downloads 14.43 GB.
- **A window nobody closes bills to its ceiling** → 4 h is ~$0.02; gpunit deletes an overdue volume on its next
  command. A volume no command reaches bills $0.07/GB a month until one does.
- **A 408 or 429 is a client error too** → it moves on at once; the next source, or the pod's hold, is the remedy.
- **The floor and the window's size** → D27 says a network volume reports its cluster's capacity, so the pod's floor
  may never read `volume_gb`; the test holds `volume_gb` above the floor anyway, as Q2 chose.
- **`CLAUDE.md` is edited by the build** → the grilling settled the lines (Q3); the human reads them at phase 4.
- **The pinned image cannot boot until phase 5** → phases 1–4 run offline; no session is opened before the rebuild.

## Verdict

Feasible: the library call is unchanged, the window is configuration and a test, each card is a line and a test, and
the rebuild and a metered window prove it on pods.
