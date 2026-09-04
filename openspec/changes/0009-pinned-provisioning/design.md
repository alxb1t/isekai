# Design — 0009 pinned provisioning

**Verdict: `feasible-with-caveats`.** The mechanism is not novel: it is already running in the
operator's sibling project, `synthetic_portraits`, and is ported rather than invented. Three caveats
are named below with the phase that resolves each: the 62 GB volume's contents are unknown until the
inventory phase and nothing may be destroyed before it; the annotator redirect relies on an
undocumented environment variable whose own startup log reports the *pre-override* path, so it must
be confirmed on the filesystem; and the pre-flight digest check rests on an observed response
header, not a contract, so it must degrade to post-download verification rather than to trust.

## Context

`scripts/download_models.sh` pins nothing and verifies nothing, and it does not describe the stack —
see `proposal.md - Why`. Two constraints shape every decision here.

The first is that **the suite is offline and deterministic**. Nothing in `tests/` may reach a GPU or
the network. Provisioning is inherently a network act, so the parts of it that can be specified and
tested are the *manifest* (a tracked data file), the *verification* (a pure function over bytes) and
the *binding between the manifest and the graph*. The transfer itself is proven on a pod, once, by
a phase — not by a scenario.

The second is that **the network volume is not this project's alone**. It carries a second project's
models under a different mount convention, it is 98% full, it holds Qwen weights that v0.8 removed
from the script but not from disk, and the two repositories' `.env` files name different volume ids
while the account holds exactly one volume. Any destructive step has to assume a neighbour.

## Goals / Non-Goals

**Goals:**

- Make the set of bytes this repository renders with a *decidable* question, answerable from tracked
  files rather than from whatever a mirror served on the day a pod booted.
- Make the manifest's completeness a property the offline suite enforces, so the gap this change
  fixes cannot silently reopen when v0.10 edits the graph.
- Leave a volume whose entire contents were placed by the script, with the previous volume intact
  until that is demonstrated.

**Non-Goals:**

- **No change to what is rendered.** `ckpt_name` stays Animagine XL 4.0; the graph, the CLI, the
  transport and the prompts are untouched. That is the whole point of the ordering (D1).
- **No sandboxing of model code.** Two artifacts are pickle and one is TorchScript; all three
  execute code on load. A digest proves *identity*, never *safety* — see Risks.
- **No CPU-pod tooling** (D12), and no attempt to make the live transfer a test (D13).

## Decisions

### D1 — This version does not swap the base

The base swap moves to v0.10. `0008-one-path`'s proposal says v0.9 swaps the checkpoint; this
reverses that, deliberately.

A base swap performed against an unverifiable volume conflates two failures that must stay
separable: *the manifest is wrong* and *the new base does not work*. Provisioning a fresh volume and
rendering the **unchanged, known-good** Animagine path off it leaves exactly one variable, so a
green render means the manifest is proven and nothing else is being claimed. v0.10 then changes one
thing against storage it can trust.

*Alternative considered:* one version doing both, with the volume work sequenced last. Rejected —
the smoke test would be the first render ever made from a manifest-provisioned volume *and* the
first render ever made on the new base, so a failure would be unattributable, which is the exact
defect this repository's arc is trying to leave behind.

### D2 — The downloader is ported, not designed

`synthetic_portraits/download_models.sh` already implements this contract in production: pinned
`resolve/<commit-sha>/` URLs, a SHA-256 per file, `.partial` → verify → `mv`, and re-verification of
files already present. Porting it costs a reading; designing a second one costs a design and earns a
second set of bugs. Two constants come across directly, because they name the same repository and
the same file this project already pulls unpinned: `InstantX/InstantID` at
`57b32dfee076092ad2930c71fd6d439c2c3b1820`, and that revision's digest for `ip-adapter.bin`.

One behaviour is changed on the way in. The sibling's `verify_sha256` deletes the offending file
before exiting. On a volume shared with another project that is a foot-gun: a digest disagreement
between two repositories would have each deleting files the other had just written. Here, a *present*
file that fails verification aborts the run and is **left on disk** (D4).

### D3 — Plain URLs and `wget`, not the `hf` CLI

The `hf` CLI resolves a repo and a path; the thing being pinned is a *revision and a digest*, which
`resolve/<sha>/<path>` expresses directly in the URL. Dropping the CLI also removes a dependency
from the image, makes every source a single string that the manifest can carry and the suite can
inspect, and makes the ordered fallback list of D10 a loop over strings rather than a
special case per source type.

*Cost:* `hf`'s resumable, parallel transfer is lost, and the largest artifact is 6.9 GB. Accepted:
the operator reports RunPod-side download of the full stack completing in under ten minutes, and the
`.partial` discipline means an interrupted transfer is retried from zero rather than trusted.

### D4 — Verification runs on the skip path, and a present file that fails is not deleted

Skip-if-present is what makes provisioning idempotent across pod boots, and it is also what would
make a pinned manifest a lie: on a warm volume every file that already exists by name would have its
digest entry never once evaluated. So the present-file branch verifies before it skips.

The failure behaviour differs by origin, because the blast radius differs. A `.partial` that fails
is this run's own artifact and is removed, so the destination filename is never occupied by
unverified bytes. A file *already at the destination* may belong to a neighbour; the run aborts and
leaves it, and a human decides.

### D5 — The manifest is tracked data; verification is Python the gate can reach

The manifest becomes a tracked data file rather than shell variables, so a test can read it without
executing anything. The digest comparison moves into a small stdlib module (`hashlib`) that the
shell invokes, so `pytest` exercises the real code path — including the corrupt-file case — while
the bytes still move through `wget`.

This is the narrow version of "move it into Python": the *decision* is tested, the *transfer* is
not. Rewriting the transfer in `urllib` to make it testable would mean hand-rolling resumption and
redirect handling for a 6.9 GB download, to test a thing that is already covered by the digest.

*Note on the stdlib constraint:* `CLAUDE.md` requires the **runtime** — `convert.py`'s import graph
— to need no wheel. The verification module satisfies that with `hashlib`, and provisioning runs on
the pod regardless, so no dependency is added anywhere.

Which decisions live in the module, and how they become unit-testable, is D14.

### D14 — The module owns the policy; the shell owns only the transfer

Four of this capability's scenarios describe outcomes that sound like shell behaviour: a failed
download never lands, a present file that fails is not deleted, a present file is verified rather
than skipped, a pre-flight mismatch aborts before transfer. Written as shell, each would need a
subprocess test of a script — and every one of them declares `Layers: unit`.

So the split is drawn one level higher than "the shell downloads, Python hashes". For each manifest
entry the module decides, and returns, one of: **skip** (present and verified), **abort** (present
and mismatched — and it does not delete), **fetch from source N** (absent, or absent after a
pre-flight rejection). The shell's whole job is to call the module, run `wget` for whatever URL it
is handed, and call the module again to verify and land the result.

The fetcher is an **injected seam**, and it earns that under this repository's own rule — *a
parameter is a seam only if something else is actually passed through it*: a fake fetcher is what
lets the suite exercise interrupted downloads, mismatched bytes and pre-flight rejection offline and
deterministically, exactly as `FakeComfyClient` does for the transport. All four scenarios then bind
to genuine unit tests, and the suite still touches no network.

*Alternative considered:* subprocess-testing `download_models.sh` against `file://` sources.
Rejected — it would be offline and would work, but it tests the script's *plumbing* rather than its
*decisions*, and it puts shell into a gate that has never contained any.

### D15 — Where the manifest and the module live, and what the image must carry

The manifest is data beside the script it drives: `scripts/models.json`. The module is code in the
package so `pytest` can import it like any other: `isekai/provision.py`. Neither is imported by
`convert.py`, so the runtime's stdlib-only constraint is untouched.

The consequence is easy to miss and would break provisioning on the pod: the `Dockerfile` currently
copies `start.sh` and `scripts/download_models.sh` and nothing else. It must also copy the manifest
and the module, or the script arrives on the pod without the two things it now depends on. That is a
phase-3 task with its own verification, not an implementation detail.

### D6 — The graph and the manifest are bound by a test, including what the graph never names

Half the binding is direct: every model filename appearing in `workflows/pipeline.json`'s node
inputs must have a manifest entry. The other half is the gap this change was found through —
`LineArtPreprocessor` names no file at all, and downloads two. So the binding also carries a tracked
mapping from **node class → files that node fetches for itself**, and a graph containing such a node
whose class is absent from the mapping fails rather than passing silently.

The reverse direction is deliberately not asserted: the manifest legitimately carries artifacts no
graph field names, such as the antelopev2 pack that `InstantIDFaceAnalysis` resolves by directory.

### D7 — The annotator checkpoints move onto the volume, and the move is confirmed on disk

`comfyui_controlnet_aux` writes to `<node dir>/ckpts` by default, which is container disk: 386 MB
re-downloaded on every pod's first render, inside a metered window, unpinned. `AUX_ANNOTATOR_CKPTS_PATH`
redirects it, and because the pack reads it as `os.getenv(NAME, default)` the environment wins over
its own `config.yaml`.

The trap: the pack logs `Using ckpts path: …` from the *config-derived* value, not the override. The
log will report the old path while writing to the new one. Confirmation is therefore a filesystem
check, never a log line — and once redirected onto the models tree, the four files become ordinary
manifest entries fetched ahead of time rather than lazily.

### D8 — One symlink for the whole models directory, not per-folder symlinks

`extra_model_paths.yaml` is not sufficient: the sibling project established live that the InstantID
node and the Impact Subpack resolve from `${COMFYUI_HOME}/models/<x>` directly and ignore the yaml —
and that without the redirect the InstantID node **auto-downloads a broken, nested antelopev2 pack**.
Its fix was a symlink per affected folder.

This change goes one level up: mount the volume at `/runpod-volume` and symlink
`/opt/ComfyUI/models` → `/runpod-volume/isekai`. Because `folder_paths.models_dir` is then itself
inside the namespace, *every* node is namespaced, including ones neither project has installed yet.
It also makes a scratch namespace and a rollback the same operation — a symlink flip.

### D9 — Artifacts shared with the sibling project are duplicated, not shared

Both projects use InstantID and antelopev2. A shared `common/` tree would save ~4.6 GB and cost
independence: this project's manifest would describe bytes another repository's pin controls, so the
D6 binding would pass while the files on disk answered to someone else. At $0.07/GB/month the
duplication is about **32¢/month**. Independence is worth more than that.

Note the concrete hazard this avoids: the two projects currently pull antelopev2 from *different*
mirrors — `DIAMONIK7777/antelopev2` here, `MonsterMMORPG/InstantID_Models` there — into
same-shaped paths. They do not collide today only because their mount conventions nest one level
apart, which is luck rather than design.

### D10 — Ordered fallback sources, and a pre-flight before large transfers

A digest makes the *source* interchangeable: any host serving matching bytes is acceptable, and one
that does not is rejected whoever it is. So each entry carries an ordered list of sources and tries
the next on failure. This adds availability without adding trust, which is the same argument that
justifies pulling a third-party mirror at all.

Hugging Face returns the file's SHA-256 in an `x-linked-etag` response header, so a mismatch can be
detected with a ranged request before a multi-gigabyte transfer starts. This is an **optimisation,
not a check**: where the header is absent the entry proceeds to download and post-verify. It must
never be treated as a substitute for hashing the bytes that actually landed.

### D11 — The volume is replaced, not wiped; the destroy is last and gated on a render

RunPod network volumes have no snapshot, no versioning and no restore, and `DELETE` is immediate.
The ordering is therefore: **inventory → create the new volume → provision it by script only →
render the unchanged path → destroy the old volume.** The old volume is untouched, and remains a
complete rollback, until a render off the new one has succeeded.

*Alternatives considered:* wiping in place (rejected — the irreversible act would precede its own
validation, on a platform with no undo) and pruning in place while keeping everything (rejected —
pruning proves nothing about the manifest, and D4's skip-path verification would then be evaluating
entries against files the script did not place, so a wrong revision or a wrong path-in-repo would
remain undetected until the day the volume was gone).

### D12 — No CPU-pod tooling; provisioning is a metered phase

RunPod CPU pods do mount network volumes, at roughly a seventh of GPU cost, and the provisioning
step touches no GPU. It was still rejected: `infra/up.sh` posts to RunPod's **deprecated** REST v1,
where a CPU pod is a different field shape, and v2 differs again — so a `--cpu` mode is either new
code on a deprecated API or a v1→v2 migration inside a change about supply chain. For a step that
runs a handful of times per version, against a download the operator measures in single-digit
minutes, that is not worth the surface.

The consequence is stated rather than absorbed: provisioning becomes a **metered** phase and
`tasks.md` marks it ⚠️ GPU, because `CLAUDE.md` grants spend authority to phases, not to agents.

### D13 — Live provisioning is a phase, not a scenario

Every scenario in `specs/model-provisioning/spec.md` declares `Layers: unit` and is provable
offline, which keeps this repository's property that no test reaches a GPU or the network. The one
thing that can only be shown on a pod — that a volume filled *solely by the script* renders — is a
metered task with an explicit acceptance criterion, verified once and recorded, in the same way
diffusion quality has always been handled here.

## Risks / Trade-offs

- **The 62 GB volume may hold something irreplaceable** (a trained artifact, outputs, anything in
  neither project's script) → the inventory phase runs first and the destroy is gated on it; both
  projects' scripts are pinned and checksummed, so anything they *do* declare is re-downloadable.
- **`AUX_ANNOTATOR_CKPTS_PATH` may not take effect**, and the pack's own log will not reveal it →
  confirmed by listing the directory on the pod during the metered phase, never from the log.
- **`x-linked-etag` is observed behaviour, not a documented contract** → treated as an optimisation
  (D10); its absence degrades to post-download verification, never to trust.
- **A digest proves identity, not safety.** `ip-adapter.bin` and the pose estimator execute code on
  load, and pinning only guarantees they are the *same* code every time → out of scope here; stated
  so it is not mistaken for solved.
- **Three of eleven sources are third-party mirrors** (antelopev2, and both DWPose repos), so the
  digests were recorded from those mirrors rather than from a publisher → the pin freezes exactly
  what was reviewed; a bump re-derives and is re-reviewed.
- **The sibling project's `.env` names a different volume id than this one** while the account holds
  a single volume → one is already stale; the inventory resolves which, and the replacement updates
  both.
- **Losing `hf`'s resumable transfer** (D3) → an interrupted 6.9 GB fetch restarts; the operator
  reports the full stack downloading in under ten minutes on RunPod, and `.partial` guarantees a
  restart rather than a corrupt success.

## Migration Plan

1. Land the script, manifest, module, tests, `Dockerfile` and `infra` changes on the branch, gate
   green. Nothing metered, nothing destroyed.
2. **⚠️ Inventory** the existing volume; publish the file list; confirm nothing irreplaceable.
3. Create the new volume in the same data center, sized from both projects' manifests.
4. **⚠️ Provision it with the script alone** — no file placed by hand — then render the unchanged
   Animagine path and confirm five images and exit 0.
5. Destroy the old volume; update both repositories' `.env`.

**Rollback.** Until step 5 the old volume is intact and complete: reverting is `RUNPOD_VOLUME_ID`
plus the previous `volumeMountPath`. After step 5 the new volume is itself script-reproducible, so
recovery is a re-provision rather than a restore — which is the property step 4 exists to establish.

## Open Questions

- **The new volume's size.** It depends on the sibling project's next base, which is that project's
  decision. Computed from both manifests at step 3; it changes no requirement here.
- **Whether the sibling project adopts the same namespace convention in this window** or keeps its
  current `<volroot>/models/` nesting. Either works — the namespaces do not overlap. Coordination
  only.
