## MODIFIED Requirements

### Requirement: The comparison canvas is the render's own

The system SHALL compare a photograph to a render on the render's canvas, deriving that canvas by
asking the render path for the working resolution of the photograph rather than re-deriving the rule,
and SHALL apply the loader's orientation correction to the photograph's pixels before any region is
parsed from them.

The flow scales the photograph once and every consumer reads that scaled image, so the scaled
photograph and the render are the same canvas exactly rather than approximately. A second
implementation of the resolution rule would be a second thing to keep in step, and a photograph parsed
upright while the render was produced from transposed pixels would place every region in the wrong
place.

#### Scenario: the working resolution comes from the injector
- **Key:** `evaluation:canvas:resolution-comes-from-the-injector`
- **Layers:** unit
- **WHEN** a photograph is prepared for comparison
- **THEN** its target dimensions are the ones the render path computes for that photograph
- **AND** the evaluator states no resolution rule of its own

#### Scenario: an orientation tag is honoured before regions are parsed
- **Key:** `evaluation:canvas:orientation-is-applied-before-parsing`
- **Layers:** unit
- **WHEN** the photograph declares a transposing orientation
- **THEN** the pixels are transposed before any region is derived from them
- **AND** the regions therefore land where the render's own pixels are

#### Scenario: a render whose dimensions disagree with the canvas is refused
- **Key:** `evaluation:canvas:mismatched-render-is-refused`
- **Layers:** unit
- **WHEN** a render's dimensions are not the ones derived from the photograph
- **THEN** the comparison is refused naming both sizes
- **AND** no axis is scored against a canvas the two images do not share
