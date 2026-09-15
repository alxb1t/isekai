## REMOVED Requirements

### Requirement: Jitter is relative to the current base
**Reason**: **L4** — a variation draws a new seed and changes no dial. A flow's dials are settled
against its publisher's own recommendations and confirmed by measurement (F25, F26, F35, F39);
jittering them does not produce a variant of the flow, it produces an untested flow, which L3 forbids
from being selectable.
**Migration**: None. Dial jitter is a closed avenue.

### Requirement: Run output layout
**Reason**: Superseded by the run directory, which `run-directory` owns: a photo-id, append-only
numbering, approval in the filename, and outputs named by seed under their sheet version.
**Migration**: `run-directory:*` and `image-generation:seeds:outputs-carry-the-sheet-version`.

### Requirement: Dial overrides on the one graph
**Reason**: Deleted with `isekai/overrides.py` and the one graph.
**Migration**: None.

### Requirement: Seeded dial jitter from an injected source
**Reason**: L4, as above. **One scenario survives this requirement** and it is the only binding in the
living spec on the seed's width.
**Migration**: `image-generation:seeds:seeds-are-drawn-at-full-64-bit-width` carries
`workflow-mutation:jitter:seed-is-64-bit` forward. `seed-comes-from-the-rng` is already covered by
`image-generation:seeds:count-draws-distinct-seeds`, which draws from an injected source.

### Requirement: ControlNet strength jitter around per-node baselines
**Reason**: L4.
**Migration**: None.

### Requirement: Reproducibility contract for a varied run
**Reason**: Superseded, and at a finer grain: an output is named by the seed that produced it, under
the sheet version it was rendered from, so one image is identified by one integer rather than by a
run-level manifest of seeds.
**Migration**: `image-generation:seeds:*` and `image-generation:idempotence:*`.

### Requirement: Variation runs vary unless the run asks for the graph's own dials
**Reason**: L4 — there is nothing left to vary but the seed, which is what a variation always was.
**Migration**: None.

### Requirement: The committed dials are pinned
**Reason**: Superseded by a stronger rule. A flow is immutable: the suite holds each tracked manifest
against a committed digest, so changing a dial creates a new flow identifier rather than editing this
one.
**Migration**: `image-generation:immutability:flow-manifest-is-pinned-by-equality`.
