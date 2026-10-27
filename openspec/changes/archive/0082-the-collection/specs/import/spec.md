## MODIFIED Requirements

### Requirement: Import is staged, and a commit is one move

The system SHALL read chosen files into a staging folder under the library's `.staging/`, SHALL create the collection
and move every staged file into its `sources/` in one commit, SHALL delete the staging folder on cancel, and SHALL
delete, when the surface starts, each staging folder an import left in the library, keeping any written to within
the last hour and any folder import did not make. A file with the same bytes as a source already in the collection SHALL
be skipped; a different file whose name is taken SHALL be written as `<stem>-2`. A collection name SHALL be refused when
empty, holding `/`, starting with a dot, or taken. A collection whose folder sits inside the repository's working tree
and outside its ignored data root SHALL be refused before anything is staged.

Nothing half-read reaches a collection, and a collection never looks complete while files are still arriving. A staging
folder still being written belongs to an import open elsewhere, and a folder import did not make is not its to delete.
Bytes, not names, decide sameness. A collection holds copies of photographs, so it stays where git cannot reach it
([D18](../../../docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)).

#### Scenario: a commit moves every staged file into the batch
- **Key:** `import:stage:a-commit-moves-every-file`
- **Layers:** unit
- **WHEN** a staging folder with read files is committed as a new collection
- **THEN** the collection holds them in `sources/`
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
- **WHEN** the surface starts with a staging folder an import left under `.staging/`
- **THEN** that folder is deleted
- **AND** a folder import did not make, or one an import is still writing, is kept

#### Scenario: the same bytes are skipped and a taken name is renamed
- **Key:** `import:stage:same-bytes-skip-and-a-taken-name-is-renamed`
- **Layers:** unit
- **WHEN** a collection gains one file with a source's bytes and another with a source's name
- **THEN** the first writes nothing
- **AND** the second is written as `<stem>-2`

#### Scenario: an unusable batch name is refused
- **Key:** `import:stage:an-unusable-name-is-refused`
- **Layers:** unit
- **WHEN** a commit names a collection that is taken, empty, holds `/` or starts with a dot
- **THEN** it is refused
- **AND** the staging folder is kept

#### Scenario: a batch git can reach is refused
- **Key:** `import:stage:a-batch-git-can-reach-is-refused`
- **Layers:** unit
- **WHEN** `isekai import` names a collection inside the working tree and outside `.data/`
- **THEN** it is refused, naming where a collection may go
- **AND** nothing is written

## REMOVED Requirements

### Requirement: A source is cleaned before it enters a batch

**Reason**: a library folder is a collection; the requirement is renamed in that word.

**Migration**: the requirement holds, unchanged but for the word, under its new title, *A source is cleaned before it enters a collection*.

## ADDED Requirements

### Requirement: A source is cleaned before it enters a collection

The system SHALL write into a collection's `sources/` only a JPEG or PNG carrying its pixels, its orientation and
nothing else. A JPEG or PNG in sRGB or with no colour profile SHALL be stripped without re-encoding; one with another
profile SHALL be converted to sRGB and re-encoded. Any other format that decodes to one image SHALL be converted to
JPEG, or to PNG when it holds real transparency, with its orientation applied. A converted file SHALL keep its original
stem, and a 16-bit greyscale image its tones, scaled to 8 bits.

A library holds personal photographs, so a source keeps no location, camera or time, and neither does any run copied
from it. A dropped profile without conversion shifts every colour, on screen and in the render, and a 16-bit value
clipped to 8 bits turns a scan white.

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

#### Scenario: a Display P3 JPEG or PNG is converted to sRGB
- **Key:** `import:clean:another-profile-is-converted-to-srgb`
- **Layers:** unit
- **WHEN** a JPEG or a PNG with a Display P3 profile is imported
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
- **AND** it carries no profile, whether or not the WebP had one

#### Scenario: a 16-bit greyscale image keeps its tones
- **Key:** `import:clean:a-16-bit-image-keeps-its-tones`
- **Layers:** unit
- **WHEN** a 16-bit greyscale TIFF is imported, in either byte order
- **THEN** the source is a JPEG whose pixels are the original's scaled to 8 bits
