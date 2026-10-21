## Purpose

How a file the operator chooses becomes a source in a batch: read, cleaned of everything but its pixels and
orientation, verified, and committed into the batch's `sources/` in one move.

## ADDED Requirements

### Requirement: A source is cleaned before it enters a batch

The system SHALL write into a batch's `sources/` only a JPEG or PNG carrying its pixels, its orientation and nothing
else. A JPEG or PNG in sRGB or with no colour profile SHALL be stripped without re-encoding; one with another profile
SHALL be converted to sRGB and re-encoded. Any other format that decodes to one image SHALL be converted to JPEG, or
to PNG when it holds real transparency, with its orientation applied. A converted file SHALL keep its original stem.

A library holds personal photographs, so a source keeps no location, camera or time, and neither does any run copied
from it. A dropped profile without conversion shifts every colour, on screen and in the render.

```
JPEG/PNG, sRGB or none ──▶ strip, lossless ─────────┐
JPEG/PNG, other profile ─▶ to sRGB, re-encode ──────┼─▶ pixels + orientation ─▶ sources/
HEIC WebP AVIF TIFF BMP GIF ─▶ decode ─▶ JPEG / PNG ┘
```

#### Scenario: a JPEG's EXIF is stripped and its pixels kept
- **Key:** `import:clean:a-jpegs-exif-is-stripped`
- **Layers:** unit
- **WHEN** a JPEG in sRGB carrying location and camera EXIF is imported
- **THEN** the source carries no EXIF but its orientation
- **AND** its decoded pixels equal the original's

#### Scenario: a Display P3 JPEG is converted to sRGB
- **Key:** `import:clean:another-profile-is-converted-to-srgb`
- **Layers:** unit
- **WHEN** a JPEG with a Display P3 profile is imported
- **THEN** the source carries no profile
- **AND** its pixels are the original's converted to sRGB

#### Scenario: a HEIC becomes a JPEG
- **Key:** `import:clean:a-heic-becomes-a-jpeg`
- **Layers:** unit
- **WHEN** a HEIC photograph is imported
- **THEN** the source is a JPEG with the same stem
- **AND** its orientation is applied to its pixels

#### Scenario: a transparent image becomes a PNG
- **Key:** `import:clean:a-transparent-image-becomes-a-png`
- **Layers:** unit
- **WHEN** a WebP with transparent pixels is imported
- **THEN** the source is a PNG with the same stem

### Requirement: A file that cannot be a source is refused by name

The system SHALL refuse, naming the file, the reason and a fix: a RAW photograph; a file that does not decode; a file
holding more than one image; a file over the size limit the configuration sets; and a photograph render's header
check would refuse. A refusal SHALL leave the other chosen files to import.

A photograph render would refuse fails here, before anything is rented. One bad file costs only itself.

#### Scenario: a RAW photograph is refused with its fix
- **Key:** `import:refuse:a-raw-photograph-is-refused`
- **Layers:** unit
- **WHEN** a NEF file is imported
- **THEN** it is refused, naming the file and the fix of exporting it as JPEG
- **AND** the other files chosen with it import

#### Scenario: an animated GIF is refused
- **Key:** `import:refuse:a-multi-image-file-is-refused`
- **Layers:** unit
- **WHEN** a GIF holding more than one frame is imported
- **THEN** it is refused as holding more than one image

#### Scenario: a file over the limit is refused before it is read
- **Key:** `import:refuse:a-file-over-the-limit-is-refused`
- **Layers:** unit
- **WHEN** a file larger than the configured limit is offered
- **THEN** it is refused naming the limit
- **AND** nothing of it is written

#### Scenario: a photograph render would refuse is refused at import
- **Key:** `import:refuse:what-render-would-refuse-is-refused`
- **Layers:** unit
- **WHEN** a photograph's aspect ratio passes render's limit
- **THEN** it is refused with render's reason

### Requirement: Every source is verified before it is committed, and one that cannot be cleaned is left out unless chosen

The system SHALL verify each file after it is cleaned — a JPEG or PNG by its bytes, it decodes, it carries no block
beyond its pixels and orientation, nothing follows the image's end, and render's header check passes. A file that
fails SHALL be re-encoded from its decoded pixels and verified again; one that still fails SHALL be named with what
it carries and left out, unless the operator chooses to import it as it is. A commit SHALL verify every file again.

The check is the import's own, not trust in the reader. Leaving an uncleaned file out by default keeps a choice to
let it in with the operator, one file at a time.

#### Scenario: a file that fails is re-encoded and passes
- **Key:** `import:verify:a-failing-file-is-re-encoded`
- **Layers:** unit
- **WHEN** a cleaned file still carries an XMP block
- **THEN** it is re-encoded from its pixels
- **AND** the re-encoded file passes

#### Scenario: a file that cannot be cleaned is left out
- **Key:** `import:verify:an-uncleanable-file-is-left-out`
- **Layers:** unit
- **WHEN** a file still fails after re-encoding
- **THEN** it is named with what it carries
- **AND** a commit leaves it out

#### Scenario: an uncleanable file chosen as it is imports
- **Key:** `import:verify:an-uncleanable-file-chosen-imports`
- **Layers:** unit
- **WHEN** the operator chooses to import an uncleanable file as it is
- **THEN** the commit writes it into `sources/`

### Requirement: Import is staged, and a commit is one move

The system SHALL read chosen files into a staging folder under the library's `.staging/`, SHALL create the batch
and move every staged file into its `sources/` in one commit, SHALL delete the staging folder on cancel, and SHALL
delete any staging folder left in the library when the surface starts. A file with the same bytes as a source
already in the batch SHALL be skipped; a different file whose name is taken SHALL be written as `<stem>-2`. A batch
name SHALL be refused when empty, holding `/`, starting with a dot, or taken.

Nothing half-read reaches a batch, and a batch never looks complete while files are still arriving. Bytes, not
names, decide sameness.

#### Scenario: a commit moves every staged file into the batch
- **Key:** `import:stage:a-commit-moves-every-file`
- **Layers:** unit
- **WHEN** a staging folder with read files is committed as a new batch
- **THEN** the batch holds them in `sources/`
- **AND** the staging folder is gone

#### Scenario: a cancel deletes the staging folder
- **Key:** `import:stage:a-cancel-deletes-staging`
- **Layers:** unit
- **WHEN** an import is cancelled
- **THEN** its staging folder is deleted
- **AND** the library is unchanged

#### Scenario: staging left behind is swept at start
- **Key:** `import:stage:leftover-staging-is-swept`
- **Layers:** unit
- **WHEN** the surface starts with a folder under `.staging/`
- **THEN** that folder is deleted

#### Scenario: the same bytes are skipped and a taken name is renamed
- **Key:** `import:stage:same-bytes-skip-and-a-taken-name-is-renamed`
- **Layers:** unit
- **WHEN** a batch gains one file with a source's bytes and another with a source's name
- **THEN** the first writes nothing
- **AND** the second is written as `<stem>-2`

#### Scenario: an unusable batch name is refused
- **Key:** `import:stage:an-unusable-name-is-refused`
- **Layers:** unit
- **WHEN** a commit names a batch that is taken, empty, holds `/` or starts with a dot
- **THEN** it is refused
- **AND** the staging folder is kept
