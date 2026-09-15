## REMOVED Requirements

### Requirement: Dial flags default to unset
**Reason**: These flags belong to `convert.py`'s surface, which this version deletes. Under L8 a flow
declares its own dials in its manifest and under L3 a flow is immutable, so there is no dial for a
command line to set.
**Migration**: None. A configuration change is a new flow identifier, not a flag.

### Requirement: Dial range validation at parse time
**Reason**: Same. Twelve scenarios validating the range of flags that no longer exist.
**Migration**: The *principle* — refuse at parse time rather than on a rented machine — survives in
`cli:generate-signature:count-and-seed-are-exclusive`, which was written at v0.13 and is not inherited
from here. The vault records these twelve as "survives"; they do not.

### Requirement: Dial flags reach the run
**Reason**: Same.
**Migration**: None.

### Requirement: The output destination is a directory
**Reason**: `convert.py`'s `--output` is deleted with it. Outputs are written under the run directory,
which `run-directory` owns.
**Migration**: The run root is `--runs`, and this version gives it the containment requirement it has
never had. The vault records this requirement as "survives, relocated"; nothing in the living spec
covered `--runs` before this change, so there was no relocation to survive into.

### Requirement: Seed and variation-count flags
**Reason**: Superseded by `cli:generate-signature:*` and `image-generation:seeds:*`, which take many
photographs and either a count or explicit seeds.
**Migration**: `python -m isekai generate <id>… --count N` or `--seed S`.

### Requirement: A flag holds the graph's dials still
**Reason**: Dial jitter is deleted under L4 — jittering a flow's dials does not produce a variant of
the flow, it produces an untested flow, which L3 forbids from being selectable. A flag holding still
something that no longer moves has nothing to hold.
**Migration**: None. `cli:fixed-dials:mode-is-recorded` is superseded by the `producer` record on every
artifact (L25), read through `cli:show:producers-are-reported`.
