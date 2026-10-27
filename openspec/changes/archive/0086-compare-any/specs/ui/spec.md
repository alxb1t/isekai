## REMOVED Requirements

### Requirement: A version says what it was, and Compare shows a seed's two versions

**Reason**: Compare reaches any image of the source — any flow's, or the photograph — and *Side by side* is the
photograph's compare.

**Migration**: `c` opens the pick of the source's images; its scenarios hold under *A version says what it was, and
Compare sets an image beside any image of its source*.

## ADDED Requirements

### Requirement: A version says what it was, and Compare sets an image beside any image of its source

The system SHALL head each image's large view with its approval version, the version it came from, read from its
producer, naming it a revision when its fields differ from that version's and a re-roll when only its count or seeds do,
and the approval's time, count and seeds. `c` on a large view SHALL open a pick of its source's images: the photograph's
row on top, then a row per flow holding images of the source, each row its images oldest to newest, each named by its
version and seed, the image compare started from marked; the focus SHALL start on the newest older version of its seed,
else the image before it, else the photograph; `h j k l` and the arrows SHALL move it, keeping the column, held at a
shorter row's end, `↵` SHALL compare the image picked and `Esc` close the pick. Compare SHALL set the image picked on
the left and the image compare started from on the right, at equal size, each headed by its flow, version and seed:
between two renders it SHALL show the fields both flows declare, marked where they differ, and say when the two seeds
differ or the two share a sheet; with the photograph, the pair alone. The large view SHALL offer no *Side by side*.

```
large view · summon v2 · seed 9423   c ─▶  photo                  [▣]
                                           summon-anime-wai       [v1][v2·][v3]
                                           summon-flat-anime-wai  [v1]
                                       ↵ ─▶ Compare: the image picked │ summon v2 · seed 9423
```

The origin is already on disk, so nothing new records it. A pick reads as a choice when every choice is in view; one
source's images are every comparison the operator makes for one person. The eye returns to where it came from, on the
right.

#### Scenario: a version is named a revision or a re-roll
- **Key:** `ui:compare:a-version-is-named-by-what-changed`
- **Layers:** unit
- **WHEN** one version changes a field of the version it came from and another changes only its seeds
- **THEN** the first's large view is headed a revision and the second's a re-roll

#### Scenario: Compare pairs a seed with its newest older version
- **Key:** `ui:compare:a-seed-pairs-with-its-newest-older-version`
- **Layers:** unit
- **WHEN** a seed is rendered under versions one, two and three
- **THEN** version three's pick opens focused on version two

#### Scenario: Compare shows the pair and the changed fields
- **Key:** `ui:compare:compare-shows-the-pair-and-the-change`
- **Layers:** e2e
- **WHEN** `c` is pressed on a revised image, then `↵`
- **THEN** the older version is on the left and the revised image on the right, with the changed fields
- **AND** a pick of another flow's image compares it, saying the seeds differ

#### Scenario: the photograph's pick sets it beside the image
- **Key:** `ui:compare:side-by-side-sets-the-image-beside-its-photograph`
- **Layers:** e2e
- **WHEN** `c` is pressed on an image's large view, then `k` to the photograph's row and `↵`
- **THEN** the photograph is on the left and the image on the right, at equal height, with no fields

#### Scenario: Compare takes any two images of a source
- **Key:** `ui:compare:any-two-images-of-a-cell`
- **Layers:** unit
- **WHEN** Compare is asked for a summon image of v4 against a flat summon image of v1 with another seed
- **THEN** it serves both, the shared fields that differ and that the seeds differ
- **AND** the image picked is on the left, the image compare started from on the right

#### Scenario: the pick moves by row and column
- **Key:** `ui:compare:the-pick-moves-by-row-and-column`
- **Layers:** unit
- **WHEN** `j` is pressed on the photograph's row, then `l` twice, then `j` onto a shorter row
- **THEN** the focus moves to the first flow's first image, then its third, then the shorter row's last
