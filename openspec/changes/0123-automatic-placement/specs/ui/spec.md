## ADDED Requirements

### Requirement: Stage 2 proposes its pairs when it opens with none

The photograph-to-render stage, for a tattoo placed in two stages and for a cut, SHALL ask the server for proposed pairs
once, when it opens on a tattoo and render with no pair held, sending the tattoo's points on the photograph: the
photograph side of the stage-1 pairs, or a cut's outline. It SHALL show that it is asking, and SHALL show a refusal with
its fix, with the pair editor still taking clicks. An answer with no pair SHALL say so. A stage that holds a pair, the
direct stage, and a stage already asked on this tattoo and render SHALL ask nothing.

Proposing is a convenience on top of clicking, so it never blocks the editor and never asks twice for the same work.

#### Scenario: a stage with no pairs asks once
- **Key:** `ui:proposal:a-stage-with-no-pairs-asks-once`
- **Layers:** unit
- **WHEN** stage 2 opens on a two-stage tattoo with no pair held, and is opened again after the answer
- **THEN** the first opening asks and the second does not

#### Scenario: a stage with pairs asks nothing
- **Key:** `ui:proposal:a-stage-with-pairs-asks-nothing`
- **Layers:** unit
- **WHEN** stage 2 opens with one pair held
- **THEN** no proposal is asked

#### Scenario: the direct stage asks nothing
- **Key:** `ui:proposal:the-direct-stage-asks-nothing`
- **Layers:** unit
- **WHEN** the stage between a tattoo and a render opens with no pair held
- **THEN** no proposal is asked

#### Scenario: the points sent are the tattoo's on the photograph
- **Key:** `ui:proposal:the-points-sent-are-the-tattoos-on-the-photograph`
- **Layers:** unit
- **WHEN** a proposal is asked for an upload with stage-1 pairs, and then for a cut with an outline
- **THEN** the first sends the stage-1 pairs' photograph points and the second sends the outline's points

#### Scenario: the page shows that it is asking
- **Key:** `ui:proposal:the-page-shows-that-it-is-asking`
- **Layers:** unit
- **WHEN** a proposal is asked and not yet answered
- **THEN** the view is asking, and after the answer it is not

#### Scenario: a refusal shows its words and the clicks still work
- **Key:** `ui:proposal:a-refusal-shows-its-words-and-the-clicks-still-work`
- **Layers:** unit
- **WHEN** the proposal is refused with the fetch command in its words, and a point is then clicked
- **THEN** the view shows the words, and the click places the point

#### Scenario: an empty answer says so
- **Key:** `ui:proposal:an-empty-answer-says-so`
- **Layers:** unit
- **WHEN** the proposal is answered with no pair
- **THEN** the view says nothing was proposed, and no pair is added

### Requirement: A proposed pair is accepted by a button or a drag

A proposed pair SHALL be a pair marked proposed, numbered after the pairs held, drawn with a dashed marker. *Accept*
SHALL accept the selected proposed pair and *Accept all* every proposed pair, a proposed pair accepted being an
ordinary pair. Dragging either point of a proposed pair SHALL accept it. Undo SHALL restore the state before an accept
and never remove the arrival, and delete SHALL remove a proposed pair as it removes any pair. A proposed pair SHALL be
sent to the server as any pair is, with no mark. The component SHALL declare no key.

The operator corrects what the proposal got wrong, and a drag is the correction, so it is also the acceptance.

#### Scenario: proposed pairs arrive numbered after the held ones
- **Key:** `ui:proposal:proposed-pairs-arrive-numbered-after-the-held-ones`
- **Layers:** unit
- **WHEN** a proposal of four pairs arrives while two ordinary pairs are held
- **THEN** pairs 3 to 6 are the proposed ones, in the answer's order

#### Scenario: accept takes the selected pair
- **Key:** `ui:proposal:accept-takes-the-selected-pair`
- **Layers:** unit
- **WHEN** one of four proposed pairs is selected and accepted
- **THEN** that pair is an ordinary pair and three stay proposed

#### Scenario: accept all takes every pair
- **Key:** `ui:proposal:accept-all-takes-every-pair`
- **Layers:** unit
- **WHEN** four proposed pairs and one ordinary pair are accepted all
- **THEN** every pair is ordinary and none is proposed

#### Scenario: a drag accepts the pair it moves
- **Key:** `ui:proposal:a-drag-accepts-the-pair-it-moves`
- **Layers:** unit
- **WHEN** a point of a proposed pair is dragged
- **THEN** the point is at the pointer and the pair is ordinary, and the other proposed pairs stay proposed

#### Scenario: undo restores a proposed pair
- **Key:** `ui:proposal:undo-restores-a-proposed-pair`
- **Layers:** unit
- **WHEN** a proposed pair is accepted and then undone
- **THEN** it is proposed again, at its place

#### Scenario: undo never removes the arrival
- **Key:** `ui:proposal:undo-never-removes-the-arrival`
- **Layers:** unit
- **WHEN** a point is clicked while a proposal is asked, the proposal arrives, and undo is asked twice
- **THEN** the click is undone, and the proposed pairs stand through both

#### Scenario: a proposed pair is sent as an ordinary pair
- **Key:** `ui:proposal:a-proposed-pair-is-sent-as-an-ordinary-pair`
- **Layers:** unit
- **WHEN** the pairs are made ready for a preview while one pair is proposed
- **THEN** each pair is its two points, and none carries a mark

#### Scenario: a deleted proposed pair is gone
- **Key:** `ui:proposal:a-deleted-proposed-pair-is-gone`
- **Layers:** unit
- **WHEN** the second of four proposed pairs is deleted
- **THEN** three pairs stand, numbered 1 to 3, all still proposed

### Requirement: Forward waits while a pair is proposed

Stage 2 SHALL go forward only when no pair is proposed, as well as with the floor and with no lone point of the pairs
editor. While a pair is proposed it SHALL say so as its reason, before the floor and the lone point.

A proposed pair is a guess, and a bake of a guess the operator never read is the failure the screen exists to prevent.

#### Scenario: forward waits while a pair is proposed and says so
- **Key:** `ui:proposal:forward-waits-while-a-pair-is-proposed-and-says-so`
- **Layers:** unit
- **WHEN** four pairs stand, all proposed, against a floor of eight
- **THEN** forward waits, saying *4 proposed · accept or delete them*, and not the floor

#### Scenario: forward goes when every pair is accepted
- **Key:** `ui:proposal:forward-goes-when-every-pair-is-accepted`
- **Layers:** unit
- **WHEN** nine proposed pairs stand against a floor of eight, and are accepted all
- **THEN** forward goes
