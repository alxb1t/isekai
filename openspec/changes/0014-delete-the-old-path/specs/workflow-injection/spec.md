## REMOVED Requirements

### Requirement: The positive prompt is graph configuration
**Reason**: The prompt is assembled per flow from an approved sheet (L10), before any session opens.
A prompt committed to a graph is the architecture this version deletes.
**Migration**: `image-generation:assembly:*` — assembly is pure, local, and happens before the session.

### Requirement: Node location on the one graph
**Reason**: There is no "one graph". A flow's manifest names every node it edits by role
(`flow.node("sampler")`), so nothing locates a node by class at runtime. Under L8 the manifest declares
and never computes, which is what lets a broken flow be caught by the suite rather than by a boot.
**Migration**: `image-generation:manifest:*`. Note that class lookup could not have survived in any
case: `find_node`'s exactly-one contract refuses on `summon-v1`, which has two `KSampler` nodes.

### Requirement: Photo wiring into the one graph
**Reason**: Same — the flow manifest names the loader node.
**Migration**: `image-generation:manifest:*`.

### Requirement: Latent initialisation from the photo
**Reason**: **F24.** Taking the photograph out of the latent is what removed the blur. The surviving
flow initialises from `EmptyLatentImage` at denoise 1.0. img2img is a closed avenue.
**Migration**: None. This requirement is the thing this version exists to delete.

### Requirement: The photo is scaled to a working resolution
**Reason**: The rule survives; this capability does not. Nine of its ten scenarios move to
`image-generation`, which is the capability that owns *"the render target is derived from the
photograph's own header"* and is the live caller of the rule.
**Migration**: `image-generation:working-resolution:*`, same scenario names, new keys. The tenth —
`dimensions-are-written-by-injection` — does not move: it asserts that *injection* writes the
dimensions, and injection is deleted.

### Requirement: The base's CLIP layer is committed to the graph
**Reason**: The CLIP layer is now a flow's declared dial (`clip_skip: -2` in `summon-v1`'s manifest),
not a value committed to a graph file, because the measured configuration and the graph file
deliberately disagree (design.md D12 of change 0013).
**Migration**: `image-generation:manifest:flow-declares-its-inputs` — the manifest declares the dials, and `summon-v1` declares `clip_skip: -2`.
