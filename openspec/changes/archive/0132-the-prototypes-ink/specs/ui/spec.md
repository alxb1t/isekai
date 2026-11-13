## MODIFIED Requirements

### Requirement: The outline step shows the ink and keeps its white point and tone

The outline step SHALL show the tattoo in the panel and let its outline be drawn, saving it as it changes.
Once the outline is closed it SHALL offer the ink view beside the photograph or image,
drawn from the server's answer on the crop's offset.
It SHALL show the automatic white point as an 8-bit grey and let the operator set one by hand,
stored as the scale on the automatic point, and return to automatic.
It SHALL offer *neutral* and *depth* from 1.0 to 2.0, and *Reset* to the kind's defaults once either differs.
On a cut it SHALL show the photograph with the ink at full strength inside the outline
and the photograph dimmed around it, and the size of the ink on the photograph,
and offer *Upload a tattoo instead*, which keeps a new tattoo under its own name and leaves the cut kept.
While the outline is open the controls SHALL be disabled, and one line above them SHALL say how to close it:
*add N more points to close · K of F* while the outline holds K points, fewer than the floor F of `outline_min`, and
*close the outline on its first point · K points* from the floor on; once it is closed the line SHALL go.
The step SHALL carry no line that explains its gestures.

The ink view is the judge: nothing on the screen grades the cut.

#### Scenario: the white grey converts to a scale and back
- **Key:** `ui:outline-step:the-white-grey-converts-to-a-scale-and-back`
- **Layers:** unit
- **WHEN** an 8-bit grey is set by hand against an automatic grey
- **THEN** the stored scale is their ratio, and the grey shown is the automatic grey times the scale, rounded

#### Scenario: a scale of one is automatic
- **Key:** `ui:outline-step:a-scale-of-one-is-automatic`
- **Layers:** unit
- **WHEN** the white scale is 1.0
- **THEN** the state reads *auto*, and any other scale reads *set by hand*

#### Scenario: reset appears when the tone differs from the default
- **Key:** `ui:outline-step:reset-appears-when-the-tone-differs`
- **Layers:** unit
- **WHEN** a cut's depth is changed from 1.6
- **THEN** *Reset* is offered, and choosing it restores neutral on and depth 1.6

#### Scenario: the controls wait for a closed outline
- **Key:** `ui:outline-step:the-controls-wait-for-a-closed-outline`
- **Layers:** unit
- **WHEN** the outline is open
- **THEN** the ink view, the white point and the tone are disabled

#### Scenario: one line says how to close
- **Key:** `ui:outline-step:one-line-says-how-to-close`
- **Layers:** unit
- **WHEN** an outline of three vertices and of five vertices is open under a floor of 3, and then closed
- **THEN** the line reads *close the outline on its first point · 3 points* and then *· 5 points*, and a closed outline
  has none

#### Scenario: the line names the floor while the outline is short of it
- **Key:** `ui:outline-step:the-line-names-the-floor-while-the-outline-is-short`
- **Layers:** unit
- **WHEN** an outline of no vertex, one vertex and two vertices is open under a floor of 3
- **THEN** the line reads *add 3 more points to close · 0 of 3*, then *add 2 more points to close · 1 of 3*, then
  *add 1 more point to close · 2 of 3*

#### Scenario: the size of the cut's ink is the outline's box
- **Key:** `ui:outline-step:the-size-of-the-cuts-ink-is-the-outlines-box`
- **Layers:** unit
- **WHEN** a cut's closed outline spans a box of the photograph
- **THEN** the source line gives that box's width and height in photograph pixels

#### Scenario: uploading instead keeps the cut
- **Key:** `ui:outline-step:uploading-instead-keeps-the-cut`
- **Layers:** unit
- **WHEN** a tattoo is uploaded instead of a cut named `bow`
- **THEN** its name starts as `bow_closeup`, and `bow` is still kept

### Requirement: The outline step goes forward to the stage its tattoo takes

The outline step SHALL go forward, once its outline is closed, to the stage the tattoo takes on this photograph: stage
1 for an uploaded tattoo, the direct stage for a tattoo that is not on this photo, and stage 2 for a cut. The stepper
SHALL list the steps of that mode, each keeping its number, so a number names one screen in every mode. While the
outline is open, forward SHALL wait and say so with the points placed, and with the floor of `outline_min` while the
points are fewer than it.

```
two stages   ① tattoo · ② outline · ③ tattoo ↔ photograph · ④ photograph ↔ render · ⑤ review
direct       ① tattoo · ② outline · ③ tattoo ↔ render · ⑤ review
cut          ① tattoo · ② outline · ④ photograph ↔ render · ⑤ review
```

A number that meant stage 2 in one mode and stage 1 in another would mislead an operator who moves between modes on
one photograph.

#### Scenario: the stepper lists the steps of the mode
- **Key:** `ui:stages:the-stepper-lists-the-steps-of-the-mode`
- **Layers:** unit
- **WHEN** the steps of an uploaded tattoo, a direct tattoo and a cut are listed
- **THEN** each list holds the steps drawn above, with the numbers kept

#### Scenario: forward goes to the stage of the mode
- **Key:** `ui:stages:forward-goes-to-the-stage-of-the-mode`
- **Layers:** unit
- **WHEN** the outline is closed on an uploaded tattoo, a direct tattoo and a cut
- **THEN** forward is stage 1, the direct stage and stage 2

#### Scenario: forward waits for a closed outline
- **Key:** `ui:stages:forward-waits-for-a-closed-outline`
- **Layers:** unit
- **WHEN** the outline is open with 27 points under a floor of 3
- **THEN** forward waits, saying *outline open · 27 points*

#### Scenario: forward names the floor while the outline is short of it
- **Key:** `ui:stages:forward-names-the-floor-while-the-outline-is-short`
- **Layers:** unit
- **WHEN** the outline is open with one point under a floor of 3
- **THEN** forward waits, saying *outline open · 1 of 3 points*
