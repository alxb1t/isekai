## MODIFIED Requirements

### Requirement: A render session runs every pending edit

The system SHALL, when `isekai render` names collections and no request, run every pending edit of each in the
same pod, after its renders, in each run's flow less each `--without` flow. It SHALL derive and check each pending
edit before anything is rented, refusing one whose source no longer has the recorded digest. A session SHALL be
allowed to hold edits alone. A request SHALL run no edit. The pod SHALL receive only the crop, its mask and its
control; the sampled crop SHALL be scaled, stitched through the mask and multiplied by the ink's lines here, and
`<seed>.edit-<k>.png` SHALL be written last, beside its source, after the record is completed with the graph's
digest, the runtime and the duration. A failed sampling SHALL leave its request pending.

One verb creates a pod ([D36](../../../docs/decisions.md#d36--a-render-session-is-isekai-render)), so an edit is
run by it.

#### Scenario: a pending edit runs beside the renders
- **Key:** `edit:session:a-pending-edit-runs-beside-the-renders`
- **Layers:** unit
- **WHEN** a session names a collection with an approval short of one image and a pending edit
- **THEN** the render is made first, then the edit's image appears beside its source
- **AND** the edit's record holds the graph's digest, the runtime and the duration

#### Scenario: a changed source refuses before the pod
- **Key:** `edit:session:a-changed-source-refuses-before-the-pod`
- **Layers:** unit
- **WHEN** a pending edit's source no longer has the recorded digest
- **THEN** the session is refused, naming the edit
- **AND** nothing is rented

#### Scenario: a session may hold edits alone
- **Key:** `edit:session:a-session-may-hold-edits-alone`
- **Layers:** unit
- **WHEN** nothing is short of its count and an edit is pending
- **THEN** the session runs the edit

#### Scenario: a flow taken out takes its edits out
- **Key:** `edit:session:a-flow-taken-out-takes-its-edits-out`
- **Layers:** unit
- **WHEN** `--without` names a run's flow that holds a pending edit
- **THEN** that edit stays pending

#### Scenario: a request runs no edit
- **Key:** `edit:session:a-request-runs-no-edit`
- **Layers:** unit
- **WHEN** the verb names a request
- **THEN** no pending edit runs

#### Scenario: a failed sampling leaves the request pending
- **Key:** `edit:session:a-failed-sampling-leaves-the-request-pending`
- **Layers:** unit
- **WHEN** the endpoint rejects the edit's graph
- **THEN** no edit image is written and the request is still pending
- **AND** the refusal names the discard that removes it

#### Scenario: a failed sampling costs the next edit nothing
- **Key:** `edit:session:a-failed-sampling-costs-the-next-edit-nothing`
- **Layers:** unit
- **WHEN** the endpoint rejects one pending edit's graph and another pending edit follows it
- **THEN** the next edit is sampled and its image is written
- **AND** the rejected request is still pending and the session exits with a failure

#### Scenario: a chain of pending edits runs in order
- **Key:** `edit:session:a-chain-of-pending-edits-runs-in-order`
- **Layers:** unit
- **WHEN** a pending edit's source is the image another pending edit will write
- **THEN** the pending edits are checked before anything is rented, without that image
- **AND** the first is sampled, and then the second from the first's image

#### Scenario: the pod receives only crops
- **Key:** `edit:session:the-pod-receives-only-crops`
- **Layers:** unit
- **WHEN** an edit is sampled
- **THEN** the endpoint receives the crop, its mask and its control, each at the sampling size, and no other image
