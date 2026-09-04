## REMOVED Requirements

### Requirement: Name resolution

**Reason**: There is one path. With `--model` removed there is no name to resolve, no set of valid
choices to list back to the user, and no unknown name to refuse — the pipeline resolves to a single
committed graph.

**Migration**: None available to a caller: `--model` is removed outright and every value it accepted
except `animagine-i2i-cn` refers to a deleted path. Runs that named `animagine-i2i-cn` drop the flag;
runs that named `qwen`, `animagine` or `animagine-i2i` have no equivalent and must accept the
surviving path's behaviour.

### Requirement: Injection adapter pairing

**Reason**: Pairing exists to select one adapter from several. One graph carries one injection
adapter, so the pairing is the identity function and the registry that performed it is deleted.

**Migration**: None needed — the surviving path uses the adapter it always used, now reached
directly rather than through a lookup.

### Requirement: Mutation seam pairing

**Reason**: Mutation was a per-model capability because two of the four paths could not vary their
dials. The surviving path always carries the seam, so the attachment is unconditional and the
`variations` refusal it protected is removed with it.

**Migration**: None needed. Every run now varies its dials; no invocation can reach a path that
cannot.
