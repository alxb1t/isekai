## MODIFIED Requirements

### Requirement: No `isekai` pod goes unseen

The pod-creation script SHALL refuse while a pod is recorded, or while the provider lists any pod this project
made. The teardown script SHALL leave no pod this project made: the recorded one, then every other listed. A create
whose outcome is unknown SHALL name the teardown script. The listing SHALL name only pods from this project's image,
and SHALL fail, never end in silence or loop, when a page repeats its cursor or a pod this project named carries no
image. A render session SHALL sweep without a record only after its own create was lost.

A pod no file records bills with nothing watching it. A second creation overwrote the record and orphaned the first
pod, and a lost create left one only the provider's console could find. A listing that misses a pod, or never ends,
leaves it billing; one that over-matches deletes a pod that is not this project's.

#### Scenario: a recorded pod refuses a creation
- **Key:** `pod-image:reconcile:a-recorded-pod-refuses`
- **Layers:** unit
- **WHEN** a pod is recorded and the pod-creation script runs
- **THEN** it refuses before any request to the provider, naming the record and the teardown script

#### Scenario: a listed pod refuses a creation
- **Key:** `pod-image:reconcile:a-listed-pod-refuses`
- **Layers:** unit
- **WHEN** the provider lists a pod this project made, on any page
- **THEN** the pod-creation script refuses before creating anything, naming the pod and the teardown script

#### Scenario: the teardown leaves no pod
- **Key:** `pod-image:reconcile:the-teardown-leaves-none`
- **Layers:** unit
- **WHEN** the teardown script runs, with a recorded pod or without one
- **THEN** it removes the recorded pod and every other listed pod this project made
- **AND** it exits non-zero when any removal, or the listing, fails

#### Scenario: a lost create names the teardown
- **Key:** `pod-image:reconcile:a-lost-create-names-the-teardown`
- **Layers:** unit
- **WHEN** a create's outcome is unknown
- **THEN** the pod-creation script says a pod may exist and names the teardown script

#### Scenario: a render session refuses a recorded pod
- **Key:** `pod-image:reconcile:a-session-refuses-a-recorded-pod`
- **Layers:** unit
- **WHEN** a pod is recorded and the render-session script runs
- **THEN** it refuses before its trap is set, so its teardown cannot remove that pod

#### Scenario: a repeated cursor fails the listing
- **Key:** `pod-image:reconcile:a-repeated-cursor-fails`
- **Layers:** unit
- **WHEN** the provider answers a page with the cursor it was asked for, and more to come
- **THEN** the listing fails rather than asking again

#### Scenario: only this project's image is listed
- **Key:** `pod-image:reconcile:only-this-image-is-listed`
- **Layers:** unit
- **WHEN** a pod named for this project runs an image whose name only begins with this project's
- **THEN** the listing leaves it out

#### Scenario: a pod with no image fails the listing
- **Key:** `pod-image:reconcile:a-pod-with-no-image-fails`
- **Layers:** unit
- **WHEN** a pod named for this project carries no image
- **THEN** the listing fails rather than leaving it out

#### Scenario: a refused session leaves a listed pod
- **Key:** `pod-image:reconcile:a-refused-session-leaves-a-listed-pod`
- **Layers:** unit
- **WHEN** a render session holds no record and its pod-creation script refuses, beside a listed pod
- **THEN** the session's teardown does not run the teardown script
- **AND** after a create whose outcome is unknown, it does
