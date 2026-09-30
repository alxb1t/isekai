# Design — 0052 the paydown

Where each accepted risk is written, what `show` prints that it hid, how the guard reads ssh, and the words that
change. **Verdict: feasible** — prose, one pattern, and one module's listing.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`4fd5d99`):

- **The decisions each risk belongs to:** D6 *Ollama at a fixed local address* (`docs/decisions.md:94-106`); D27
  *The models live on a network volume* (`:309-321`); D35 *The pod's operator is a trust boundary* (`:343-350`); D36
  *A render session is `infra/render.sh`* (`:352-363`). Each ends in `- **Why:**` and `- **Made by:**`.
- **The principles:** *A component is a contract* has no *Known breaks* (`docs/principles.md:50-51`); *Only a front
  end composes* has one (`:65-69`). `tests/test_principles.py` fails on a *Known breaks* line naming a test that does
  not exist.
- **The seams:** `MODEL_RECORDS` (`isekai/boundary/ollama.py:91`) and `POD_IMAGE` (`isekai/interface/wiring.py:45`)
  are module globals the suite patches. `_once` keeps a refusal but re-raises a transient `TransportFailure`
  (`isekai/interface/cli.py:395-421`, the branch at `:411`).
- **`refusal_for`** (`isekai/foundation/run.py:606-650`) builds `--new-version` into the remedy; its docstring does
  not say `tag` runs both taggers.
- **The boundary README's `ollama.py` row** (`isekai/boundary/README.md:33`) omits `tests/test_tagging.py`, which
  imports `ollama`.
- **`show`** is `isekai/interface/run_view.py`. `_listing` keeps only names matching `ARTIFACT` (`:117`); `rendered`
  keeps only digit-named output groups (`:163`); `STAGES` is fixed (`:46`); `_producer_of` formats `kind!r` with no
  `None` branch (`:75-77`); `report` prints `(none)` for a stage with no artifact (`:196-198`) and ends on the legend
  (`:210`).
- **Failure records** are `NNN.error.<attempt>.<kind>.json`, matched by `_ERROR` (`isekai/foundation/run.py:139-141`)
  and written beside the version they stand in for: in a stage directory, or in the render group
  `outputs/NNN/` (`isekai/pipeline/generate.py:464`). A render group also holds `<seed><suffix>` and its sidecar
  `<seed>.render.json` (`:515`).
- **The clone guard** is `ADD_GIT` (`tools/derive_image_project.py:77-79`); `URL` (`:80`) already matches `ssh://`
  and `user@host:path`. Its twin is `test_the_count_catches_a_clone_with_a_flag_and_another_host`
  (`tests/test_infra.py:423-443`). The `Dockerfile` has no `ADD`.
- **The review surface:** `Batch.wd14_path`'s docstring says a failed tagger leaves "every list after it" absent
  (`isekai/interface/ui/batch.py:101-102`); the rail's run button reads `run · N of M approved`
  (`ui/src/components/BatchRail.vue:80`) while its legend lists re-opened apart (`:72-73`); the `beforeunload`
  comment promises "a close mid-debounce loses nothing" (`ui/src/ReviewApp.vue:367-368`).

## Goals / Non-Goals

**Goals:** every card in the proposal's `backlog:` is paid by a fix or a record; `show` hides nothing below a flow.

**Non-Goals:** any behaviour a stage writes; the run's top level (`photo.*`, `run.json`, the flow directories); the
UI's behaviour beyond one label.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | an accepted risk is an `- **Accepts:**` bullet in its topic's decision, or a *Known breaks* line under its principle | a reader of a topic finds its risk there | one "accepted risks" decision; a decision per risk |
| [D2](#d2) | the records gain a sentence each: `refusal_for`'s docstring, *Only a front end composes*'s *Known breaks*, the README row | the code is right; the record is incomplete | a per-tagger flag; moving `_once`'s rule into a stage |
| [D3](#d3) | `show` lists every failure record, one `!` line an attempt, under its stage or render group | append-only and rare; the attempt count is information | only the last attempt of each version |
| [D4](#d4) | `show` names every file or directory below a flow it does not read, on a `not read` line | "`show` hides nothing" with no exception | directories only |
| [D5](#d5) | a file with no kind reads `declares no kind, which this build does not read` | `read`'s own wording (`isekai/foundation/artifacts.py:387`) | — |
| [D6](#d6) | `ADD_GIT` also matches `ssh://` and a whitespace- or quote-led `user@host:` source | the ssh and scp forms BuildKit clones, which the guard misses | reusing `URL` whole, which also matches `https://` |
| [D7](#d7) | the review surface's `wd14_path` docstring, run button and `beforeunload` comment are reworded; the rail's count is unchanged | the count matches the manifest's rows; only its label is wrong | recounting re-opened inputs |

### D1

**The accepted risks.** Each bullet goes after the decision's `Why` and before its `Made by`, which gains `0052`:

```
D6    - **Accepts:** whatever holds port 11434 receives the photograph; nothing probes that it is Ollama.
        Reopen when a listener that is not Ollama is seen there, or the address stops being loopback-only.
D27   - **Accepts:** a pin freezes bytes, not intent: most weights come only from third-party mirrors,
        trusted as the publisher's. Reopen when a publisher ships a first-party copy, or a mirror is compromised.
D35   - **Accepts:** code ComfyUI runs can read the stop key from other processes' environments, since the
        image names no `USER`. Reopen when a node or model is not fully trusted, or the key's scope is account-wide.
D36   - **Accepts:** ComfyUI's history and node cache hold the batch's photograph until the teardown.
        Reopen when a pod serves more than one batch.
      - **Accepts:** a `down.sh` run while a create is in flight spends that create's pending marker, so an interrupt
        before it records leaves a pod only the pod's own stop ends. Reopen when two sessions share a checkout.
```

*A component is a contract* gains, after its `Held by`:

```
- **Known breaks:** `boundary/ollama.py`'s `MODEL_RECORDS` and `interface/wiring.py`'s `POD_IMAGE` are module
  globals the suite patches, not parameters, so two roots in one process means patching global state.
```

A risk with no line: a fully rendered old run refusing at assembly is behaviour, loud, and uploads nothing.

### D2

**The records.**

- `refusal_for`'s docstring gains, after its last paragraph: "`tag` runs both taggers, so its `--new-version` also
  writes a new version of the list that did not fail."
- *Only a front end composes*'s *Known breaks* gains: "`interface/cli.py`'s `_once` decides that a transient
  transport failure is not kept for the session — the render stage's rule."
- The README's `ollama.py` row gains `tests/test_tagging.py` at the end of its *outside* column.

### D3

**Failure records.** `_ERROR` becomes the public `ERROR` in `isekai/foundation/run.py`, and `run_view` imports it.
A record is read from its name alone, never opened. `Listing` gains `failures`, each a version, attempt and kind,
sorted by version then attempt, filled in the same `os.listdir` pass as the artifacts. A new `render_failures(run)`
returns each render group's records the same way; `rendered()` keeps its return.

```
  summon-anime-wai/wd14
   * 001  wd14-eva02 · …
   ! 002  failed · attempt 1 · transient
   ! 002  failed · attempt 2 · permanent
  summon-anime-wai/outputs/001
     20260908
   ! 001  failed · attempt 1 · permanent
  * marks the active version for each stage · ! marks a failure record
```

A stage whose only content is failure records prints its header and its `!` lines, never `(none)`.

### D4

**What `show` reads.** Below each flow, a name is read when it matches its place; anything else is named:

```
<flow>/                 a STAGES name · outputs
<flow>/<stage>/         ARTIFACT · ERROR
<flow>/outputs/         a directory named by digits
<flow>/outputs/NNN/     <seed><suffix> · <seed>.render.json · ERROR
```

A new `unread(run, flows_dir)` returns each unread name as a path below the run, with `/` after a directory, sorted;
it does not descend into an unread directory. `report` builds it with the other lists, before any line, and prints
one `  not read  <path>` line each after the render groups and before the legend.

### D5

**No kind.** `_producer_of` returns `declares no kind, which this build does not read` when `schema.name` is absent,
and `declares kind '<name>', which this build does not read` otherwise.

### D6

**The guard.** Before → after:

```
ADD_GIT  (?:\bgit://|\bgit@|\.git\b)
      →  (?:\bgit://|\bgit@|\.git\b|\bssh://|[\s"'][\w.-]+@[\w.-]+:)
```

The twin gains `ADD ssh://deploy@example.com/nodes /opt/nodes` (`an-ssh-add`),
`ADD deploy@example.com:nodes /opt/nodes` (`an-scp-add`) and its exec form
`ADD ["deploy@example.com:nodes", "/opt/nodes"]` (`an-scp-exec-add`). An `https://user@host:port` source is still
not a git `ADD`: no whitespace or quote precedes its user.

### D7

**The words.** Before → after:

```
batch.py      a failed tagger leaves its own list absent and every list after it
          →   a failed tagger leaves its own list absent and never the other's

BatchRail     run · {{ approved }} of {{ inputs.length }} approved
          →   run · {{ approved }} of {{ inputs.length }} in the manifest

ReviewApp     // The draft is written before the tab goes, so a close mid-debounce loses
              // nothing. Nothing lives only in the browser.
          →   // The draft is flushed as the tab goes, best-effort: the browser may cancel
              // the request, so a close mid-debounce can lose the last edit.
```

## Dependencies

None.

## Risks / Trade-offs

- **An older run's sidecars** are `<seed>.json`, which this build does not write → `show` names each as not read.
  That is true of this build, and the renders still list.
- **A failure-heavy stage** prints a line per attempt → the budgets bound the attempts a version can record.
- **The scp form's pattern** could match a non-git `ADD` whose source starts `user@host:` → no such `ADD` exists, and
  the guard's refusal names the line to check.

## Verdict

**feasible** — records, one pattern, and one module's listing; nothing a stage writes changes.

**A patch:** `show`'s new lines are required by the existing requirement *Inspection prints the run directory with
its provenance*, because a run directory printed without its failure records is not the run directory; the delta's
SHALL only states that outright.
