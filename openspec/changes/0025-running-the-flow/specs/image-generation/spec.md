## MODIFIED Requirements

### Requirement: A flow is pinned by equality; changing any file in it is an explicit act

The system SHALL hold each tracked flow against a committed digest computed over every file in its
directory, so that altering a dial, a prompt fragment, the graph, the schema or either briefing fails the
suite naming the flow. Re-pinning SHALL be possible only as a deliberate edit to the committed digest, in
a change that states what moved and why.

**The freeze's job is that nothing changes silently, not that nothing changes.** The previous wording said
changing a file *"creates a new flow"*, and the repository then did otherwise: `v0.22.3` removed two tags
from both tracked flows' negative prompts and re-pinned, because the reason for the edit was that the
renders were better — a claim about output that the freeze exists to surface rather than to forbid.
Stating a rule the project does not follow is worse than stating the narrower one it does.

**A new identifier is still what a *divergence* costs.** Two flows exist to be compared over one cohort,
and that comparison is only possible if an identifier means one configuration. So the test is not whether
a file changed but whether the old configuration is still wanted: where both must exist — a variant, an
alternative base, a second generation — the answer is a new flow, and re-pinning would destroy the
comparison. Where the old configuration is simply abandoned, re-pinning records that in one place.

**Re-pinning is not free and must not become routine.** Runs rendered before the edit were produced by
bytes that no longer exist, and nothing on disk records which side of the edit any given run falls on —
`manifest_digest` has one consumer and it is the suite. A change that re-pins therefore owes a statement
of what moved, in prose a later reader can find; a change that re-pins without one has spent the rule and
left nothing in its place.

#### Scenario: editing any file in a tracked flow fails the suite
- **Key:** `image-generation:immutability:flow-manifest-is-pinned-by-equality`
- **Layers:** unit
- **WHEN** any file in a tracked flow directory differs from its committed digest
- **THEN** the suite fails naming the flow

#### Scenario: a re-pin states what moved
- **Key:** `image-generation:immutability:a-re-pin-is-recorded`
- **Layers:** unit
- **WHEN** a tracked flow's committed digest is changed
- **THEN** every tracked flow still matches its committed digest
- **AND** the change that moved it records which flow moved and what changed in it
