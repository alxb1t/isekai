## MODIFIED Requirements

### Requirement: A hosted model that is not running or not installed is refused before any attempt is spent

The system SHALL refuse, naming the command that would fix it, when the host serving a declared model
cannot be reached or reports that the model does not exist, when the model is built from files other than
the ones the reader's manifest pins for it, and when no entry in that manifest pins the model at all. It
SHALL record no attempt against the stage's retry budget for any of these conditions, and SHALL make that check at the first call rather than when
the implementation is constructed.

A retry budget counts models tried and failed. A server that is not running and a model that was never
created are neither: both are the operator's single-command fix, and spending a budgeted attempt on them
leaves a run whose error records have to be deleted by hand before it can be resumed. This is the posture
the build already takes toward a missing binary, applied to a port and to a model name instead of a path
entry. Checking at first call rather than at construction is what lets a machine that will never use an
implementation avoid touching it at all.

**A model built from other files is the same kind of fix.** The alias is a name the local runtime resolves,
and the files behind it are what shape the prose; the runtime's own record of those files, read once per
model per invocation, is compared with the manifest's digests. A mismatch is not a failed attempt: it is a
model to rebuild from the pinned files, one command away.

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

## ADDED Requirements

### Requirement: A caption records the files its model was built from and the options it was sampled at

The system SHALL record in each caption's producer the digests of the model and projector files the model
was verified to be built from, SHALL declare the caption pinned only when that verification ran, and SHALL
record the sampling options the reader was called with, as they were sent.

A model named by an alias records nothing a later reader can check: the same name can be rebuilt from other
files and every artifact would still agree. Once the files are verified before the call, the record can say
which ones answered, and the pin claim becomes true rather than absent.

The sampling options shape the prose as much as the model does, and they are constants in code rather than
manifest keys. Recording them verbatim is what lets two captions produced under different options be told
apart from the record alone.

#### Scenario: a verified model's caption declares its pin and names both files
- **Key:** `caption:provenance:a-verified-model-is-pinned`
- **Layers:** unit
- **WHEN** a caption is written by a reader whose model was verified against the manifest
- **THEN** its producer declares the caption pinned
- **AND** it names the digest of the model file and of the projector file

#### Scenario: the caption records the options it was sampled at
- **Key:** `caption:provenance:the-options-are-recorded`
- **Layers:** unit
- **WHEN** a caption is written
- **THEN** its producer records the sampling options the reader sent, key for key
