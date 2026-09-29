## MODIFIED Requirements

### Requirement: A hosted model that is not running or not installed is refused before any attempt is spent

The system SHALL refuse, naming the command that would fix it, when the host serving a declared model
cannot be reached or reports that the model does not exist, when the model is built from files other than
the ones the reader's manifest pins for it, and when no entry in that manifest pins the model at all. It
SHALL record no attempt against the stage's retry budget for any of these conditions, and SHALL make that check
at the first call rather than when the implementation is constructed.

A retry budget counts models tried and failed. A server not running, a model never created and a model built from
other files are none of these: each is the operator's one-command fix, and a spent attempt would leave error records
to delete by hand before the run resumes. The alias is a name the runtime resolves and the files behind it shape the
prose, so the runtime's record of them is compared with the manifest's digests
([D6](../../../docs/decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model)). Checking at the first
call lets a machine that never captions leave the reader untouched.

#### Scenario: an unreachable host is refused and costs no attempt
- **Key:** `caption:reachability:unreachable-host-refuses-without-an-attempt`
- **Layers:** unit
- **WHEN** the host serving the declared reader is not answering
- **THEN** the command refuses naming what to start
- **AND** no attempt is recorded against the stage's budget

#### Scenario: a model the host does not have is refused naming how to create it
- **Key:** `caption:reachability:absent-model-names-how-to-create-it`
- **Layers:** unit
- **WHEN** the host reports that the declared model does not exist
- **THEN** the command refuses naming the command that would create or fetch it
- **AND** no attempt is recorded against the stage's budget

#### Scenario: the reachability check is not made until a flow asks
- **Key:** `caption:reachability:the-check-fires-at-first-call`
- **Layers:** unit
- **WHEN** a wiring is composed and no captioning is performed
- **THEN** no host is contacted, no binary is looked up and no model record is read

#### Scenario: a model built from other files is refused naming how to rebuild it
- **Key:** `caption:reachability:an-unpinned-build-is-refused`
- **Layers:** unit
- **WHEN** the runtime's record of the declared model names a model or projector file whose digest is not
  the one the reader's manifest pins
- **THEN** the command refuses naming both digests and the commands that provision the pinned files and
  rebuild the model
- **AND** no attempt is recorded against the stage's budget

#### Scenario: a model no manifest entry pins is refused
- **Key:** `caption:reachability:an-unpinned-model-is-refused`
- **Layers:** unit
- **WHEN** a flow names a model the reader's manifest has no entry for
- **THEN** the command refuses naming the model and the manifest
- **AND** no host is contacted

#### Scenario: a model with no readable record names the files first
- **Key:** `caption:reachability:no-record-names-the-files-first`
- **Layers:** unit
- **WHEN** the runtime holds no readable record of the declared model
- **THEN** the command refuses naming the command that fetches the pinned files, then the one that builds the model
