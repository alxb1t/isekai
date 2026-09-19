## MODIFIED Requirements

### Requirement: A run root is under the ignored root or outside the repository

The system SHALL refuse a run root that lies inside the repository working tree and is not under the
repository's single ignored data root. A run root outside the repository entirely SHALL be accepted.
The system SHALL decide whether a run root lies inside either of those directories **by the identity of
the directories themselves**, and SHALL NOT decide it by comparing the text of resolved paths.

A run holds a copy of the photograph by construction — that is what makes a run reconstructable from
disk — so a run directory is a directory of personal photographs. Inside the working tree and outside
the ignored root, those photographs are trackable by version control and are one `git add` from being
published; outside the repository they are not, whatever path they sit at. The rule therefore bounds
the working tree rather than bounding the filesystem, which is also what keeps the flag useful: a
version's acceptance run, or a run on another disk, remains expressible.

Deciding by text was the whole of the rule's first implementation and it did not hold. Path resolution
follows symbolic links and removes relative segments, but it does not fold case, and the filesystem this
system is developed on opens a differently-cased spelling of a directory as that directory. So a run
root inside the working tree, named with one letter of its own path in the wrong case, compared as a
different path and was accepted — the exact outcome the rule exists to refuse, reached without any
adversary and by an ordinary typing mistake. Identity is decidable where text is not: two names for one
directory are one directory, and the filesystem will say so.

#### Scenario: a run root inside the working tree and outside the ignored root is refused
- **Key:** `run-directory:containment:in-tree-run-root-is-refused`
- **Layers:** unit
- **WHEN** a run root resolves to a path inside the repository working tree that is not under the
  ignored data root
- **THEN** the invocation is refused before any run is created
- **AND** the message names the path given and what would be accepted

#### Scenario: a differently-spelled name for a directory inside the tree is still inside it
- **Key:** `run-directory:containment:containment-is-decided-by-identity`
- **Layers:** unit
- **WHEN** a run root names a directory inside the working tree by a spelling the filesystem treats as
  the same directory but a textual comparison does not
- **THEN** the invocation is refused exactly as the plainly-spelled path would be

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
