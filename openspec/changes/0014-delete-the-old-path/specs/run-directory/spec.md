## ADDED Requirements

### Requirement: A run root is under the ignored root or outside the repository

The system SHALL refuse a run root that lies inside the repository working tree and is not under the
repository's single ignored data root. A run root outside the repository entirely SHALL be accepted.

A run holds a copy of the photograph by construction — that is what makes a run reconstructable from
disk — so a run directory is a directory of personal photographs. Inside the working tree and outside
the ignored root, those photographs are trackable by version control and are one `git add` from being
published; outside the repository they are not, whatever path they sit at. The rule therefore bounds
the working tree rather than bounding the filesystem, which is also what keeps the flag useful: a
version's acceptance run, or a run on another disk, remains expressible.

Stating it as a requirement is the point. The claim has been made in a source comment since the flag
was introduced and has been false for that whole time, because no scenario held it.

#### Scenario: a run root inside the working tree and outside the ignored root is refused
- **Key:** `run-directory:containment:in-tree-run-root-is-refused`
- **Layers:** unit
- **WHEN** a run root resolves to a path inside the repository working tree that is not under the
  ignored data root
- **THEN** the invocation is refused before any run is created
- **AND** the message names the path given and what would be accepted

#### Scenario: a run root outside the repository is accepted
- **Key:** `run-directory:containment:external-run-root-is-accepted`
- **Layers:** unit
- **WHEN** a run root resolves to a path outside the repository working tree
- **THEN** it is accepted and runs are created under it
- **AND** no containment check applies to it, because version control cannot reach it

#### Scenario: the default run root is under the ignored root
- **Key:** `run-directory:containment:default-is-the-ignored-root`
- **Layers:** unit
- **WHEN** no run root is given
- **THEN** runs are created under the repository's ignored data root
