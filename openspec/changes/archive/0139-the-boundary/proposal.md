---
bump: patch
version: 0.86.13
after: [0138-the-review-and-the-import]
---

# The boundary

The tag stage, the tagger, the provisioner, the pose module and Ollama's transport are held by tests that never reach their lines, and a digest mismatch and an undecodable photograph end in a traceback where a requirement says refuse. This change reaches each, fixes those lines, and pins them with mutants.

Reading map: [design](design.md) holds the decisions, the exact product lines and the tests, [tasks](tasks.md) its phases, [mutants](mutants.json) the entries phase 5 replays.

## Why

The audit ran each test against mutants of the product. The findings below survived or never ran, and the refactor's versions for the stages and the boundary move the code they guard.

| finding | what it leaves unheld |
|---|---|
| `BD-1` | the label index's digest is never planted wrong, and a mismatch ends `tag` and `prepare` in a traceback |
| `P6` | a photograph too large to decode crashes the tag stage with no failure record |
| `BD-10` | the tagger's preparation, its session and its opener run in no test |
| `BD-2` | the provisioner's published-digest pre-flight reads a header no test supplies |
| `BD-6` | Ollama's `post` and `probe` catch an answered status in no test |
| `BD-3` | the pose crop is held by its shape alone |

## What Changes

- Tests plant each half of the pin wrong, run the preparation by value, open the tagger over a stub runtime and over one tiny model through the real runtime, supply the published-digest header offline, answer Ollama with a status, and hold the pose crop by value. No test is deleted or merged.
- `isekai/interface/wiring.py`: `tagger_for` turns a digest mismatch into a refusal naming the file and the fetch.
- `isekai/boundary/wd14.py`: `prepare` turns a photograph it cannot decode into a refusal naming it, and the stale comment on what the gate installs is corrected.
- `tests/mutants.json` gains this change's mutants, replayed by `make mutants`.

Each requirement the delta touches:

- `tagging` · *The model and its label index are verified together or not used*: gains a scenario for a vector that disagrees with the index, and one for a graph opened only after both digests verify.
- `tagging` · *The tagger is an injectable seam with an offline stand-in*: gains a scenario for the preparation rule.
- `tagging` · *Each tagger's failure is its own, and the local tagger runs first*: gains a scenario for a photograph that will not decode.
- `model-provisioning` · *A source is checked before a large transfer begins*: gains a scenario for the digest read from the source's answer.
- `placement-proposal` · *A person's pose is read from one box and one crop*: gains a scenario for the crop's pixels, normalised.
- `caption` · *A hosted model that is not running or not installed is refused before any attempt is spent*: gains a scenario for a host that answers with a status.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `tagging`: scenarios under the pin, seam and order requirements.
- `model-provisioning`: one scenario under an existing requirement.
- `placement-proposal`: one scenario under an existing requirement.
- `caption`: one scenario under an existing requirement.

## Impact

- Product: `isekai/interface/wiring.py`, `isekai/boundary/wd14.py`.
- Tests: `tests/test_wd14.py`, `tests/test_tagging.py`, `tests/test_pipeline_cli.py`, `tests/test_wd14_runtime.py` (new), `tests/test_provision.py`, `tests/test_ollama.py`, `tests/test_pose.py`.
- Specs: the tagging, model-provisioning, placement-proposal and caption capabilities, by the delta of this change.
- Waits for `0138-the-review-and-the-import`: both append to `tests/mutants.json`.
- A patch by [CONTRIBUTING](../../../CONTRIBUTING.md): no format version moves, no verb or flag changes, each fix is required by a requirement that stands, and a sheet's fields, the prompt and the image are the same for the same inputs. The fixes change what a failing input ends in, a refusal where it ended in a traceback.

## Not in this change

- The provisioner's other findings `BD-7` and `BD-8`, the unpacker's `BD-9`, the derivation's `BD-4` and `BD-5`, and the audit's other low findings of the boundary: the sweep after the refactor's last version (Q59).
- `isekai/boundary/provision.py`, which the pod image freezes: its mutants are replayed in a copy and no line of it is edited.
- A new patch of `isekai.pipeline.tagging` or `isekai.boundary.pose`, which would add a row to the patch ratchet: no test of this change patches either.
- The mis-bound scenarios: the spec audit.
- Any package: the tiny model is built from the standard library, and the runtime is a locked dependency already.
