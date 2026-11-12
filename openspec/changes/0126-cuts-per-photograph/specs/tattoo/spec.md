## ADDED Requirements

### Requirement: A tattoo is kept in the library, whole until it is removed

The system SHALL keep an uploaded tattoo under the library's `.tattoos/<name>/` and a cut under
`.tattoos/.cuts/<digest>/<name>/`, `<digest>` the photograph's twelve characters, one folder a tattoo,
outside every collection.
An uploaded tattoo SHALL be taken from the import's staging, where it was cleaned to pixels and orientation,
and kept upright, with its metadata gone, at most the declared long side,
its size and the size it came with recorded.
A name SHALL be refused when it is empty, starts with a dot, holds a separator or a NUL,
or is taken: an upload's by an upload or by a cut of any photograph, a cut's by an upload or by a cut of the same photograph.
A file still carrying metadata SHALL be refused.
The system SHALL list for a photograph's digest the uploads and that photograph's cuts, and no other cut,
and SHALL take that digest with every name it reads a tattoo by, so one name resolves to one tattoo.
The system SHALL remove a tattoo on the operator's word: its folder and what the folder holds, and nothing else.
The system SHALL offer no way to rename a kept tattoo.
A cut kept at `.tattoos/<name>/` SHALL move to `.tattoos/.cuts/<cut_from>/<name>/` the first time the library is read.

A tattoo is one input to many renders, in any collection, so it lives beside the collections
and is never listed as one
([D40](../../../docs/decisions.md#d40--a-collection-is-a-library-folder-holding-sources)).
A cut serves its photograph's renders alone, so it is kept by that photograph and named there.
The photograph of a tattoo never leaves the machine. A baked edit keeps its own copy of what it was placed with,
so a removal changes no edit.

#### Scenario: an upload is kept upright and bounded
- **Key:** `tattoo:library:an-upload-is-kept-upright-and-bounded`
- **Layers:** unit
- **WHEN** a staged JPEG with an orientation tag is kept as `bow`
- **THEN** `.tattoos/bow/` holds its pixels turned upright, with no metadata
- **AND** its record holds the kept size

#### Scenario: an oversized upload is downscaled and says so
- **Key:** `tattoo:library:an-oversized-upload-is-downscaled`
- **Layers:** unit
- **WHEN** a staged image longer than the declared long side is kept
- **THEN** the kept image's long side is the declared one and its aspect is held
- **AND** the record holds the size it came with

#### Scenario: a taken name is refused
- **Key:** `tattoo:library:a-taken-name-is-refused`
- **Layers:** unit
- **WHEN** a tattoo is kept under a name a kept upload has
- **THEN** it is refused, naming the name and asking for another
- **AND** the kept tattoo is as it was

#### Scenario: a name that is no folder name is refused
- **Key:** `tattoo:library:a-bad-name-is-refused`
- **Layers:** unit
- **WHEN** a tattoo is kept as an empty name, `.hidden`, `a/b` or a name holding a NUL
- **THEN** each is refused and nothing is written

#### Scenario: a file that still carries metadata is refused
- **Key:** `tattoo:library:an-unclean-file-is-refused`
- **Layers:** unit
- **WHEN** a staged file that the import's walk reports as not cleaned is kept
- **THEN** it is refused, naming what it carries
- **AND** nothing is written

#### Scenario: a name is one tattoo on a render
- **Key:** `tattoo:library:a-name-is-one-tattoo-on-a-render`
- **Layers:** unit
- **WHEN** an upload is kept under a name a cut of any photograph holds, and a cut is kept under a name an upload
  or a cut of the same photograph holds
- **THEN** each is refused, naming the name and asking for another
- **AND** a cut of another photograph under a name a cut holds is kept

#### Scenario: the list names each tattoo of a photograph
- **Key:** `tattoo:library:the-list-names-each-tattoo`
- **Layers:** unit
- **WHEN** the library holds an upload, a cut of one photograph and a cut of another, and the list is read for the first photograph's digest
- **THEN** it holds the upload and the first photograph's cut, each with its name, kind, size and whether it is outlined, in the order kept
- **AND** the other photograph's cut is not in it

#### Scenario: a name resolves by the render's digest
- **Key:** `tattoo:library:a-name-resolves-by-the-renders-digest`
- **Layers:** unit
- **WHEN** two photographs each hold a cut of one name, and the name is read with each digest
- **THEN** each read gives its own photograph's cut
- **AND** a name read with a digest that holds none of that name is refused, naming the photograph a cut of it is from when one is

#### Scenario: a removed tattoo is gone
- **Key:** `tattoo:library:a-removed-tattoo-is-gone`
- **Layers:** unit
- **WHEN** an upload and a cut are removed
- **THEN** their folders are gone, and the other tattoos and the library's other folders are as they were
- **AND** the removed names can be kept again

#### Scenario: a removal reaches only the named tattoo
- **Key:** `tattoo:library:a-removal-reaches-only-the-named-tattoo`
- **Layers:** unit
- **WHEN** a removal is asked of an unknown name, of `.cuts`, of `..`, of a name holding a separator, and of a name with a digest that is no photograph's
- **THEN** each is refused and nothing is removed

#### Scenario: a cut kept the old way moves
- **Key:** `tattoo:library:a-cut-kept-the-old-way-moves`
- **Layers:** unit
- **WHEN** a cut sits at `.tattoos/<name>/` and the library is read
- **THEN** it sits at `.tattoos/.cuts/<cut_from>/<name>/` with its record and outline as they were
- **AND** an upload at `.tattoos/<name>/` stays

#### Scenario: the library lists no collection from the tattoos
- **Key:** `tattoo:library:the-library-lists-no-collection-from-it`
- **Layers:** unit
- **WHEN** the library holds `.tattoos/`
- **THEN** no collection is listed from it

#### Scenario: no route renames a tattoo
- **Key:** `tattoo:library:no-route-renames`
- **Layers:** unit
- **WHEN** the application's routes are read
- **THEN** none under `/api/tattoos` renames a tattoo, and `DELETE /api/tattoos/{name}` is the one that removes

## MODIFIED Requirements

### Requirement: A tattoo is cut from a photograph

The system SHALL keep a cut: a tattoo with no image of its own, whose record names the digest of the photograph
it is cut from, and whose outline is in that photograph's pixels.
It SHALL keep it under `.tattoos/.cuts/<digest>/<name>/`, so it is listed and named on that photograph's renders alone.
It SHALL start from the newest cut of the same photograph's tone, its neutral, depth and white point,
else from the photograph's defaults. A cut SHALL serve only the renders of its own photograph.

A cut carries that photograph's light and angle, so it is no input for another photograph;
another photograph takes an uploaded tattoo.

#### Scenario: a cut holds no image and names its photograph
- **Key:** `tattoo:cut:a-cut-holds-no-image`
- **Layers:** unit
- **WHEN** a tattoo is cut from a photograph's digest under a name
- **THEN** `.tattoos/.cuts/<digest>/<name>/` holds a record naming that digest and no image

#### Scenario: a first cut starts from the photograph's defaults
- **Key:** `tattoo:cut:a-first-cut-starts-from-the-defaults`
- **Layers:** unit
- **WHEN** a photograph's first cut is kept
- **THEN** its outline file holds neutral on, the photograph's depth and the automatic white point, and no points

#### Scenario: a second cut starts from the first cut's tone
- **Key:** `tattoo:cut:a-second-cut-starts-from-the-first-cuts-tone`
- **Layers:** unit
- **WHEN** a first cut of a photograph has neutral off, depth 1.2 and a white scale of 0.9,
  and a second is cut from the same photograph
- **THEN** the second holds neutral off, depth 1.2 and a white scale of 0.9, and no points

#### Scenario: a cut serves only its own photograph
- **Key:** `tattoo:cut:a-cut-serves-only-its-own-photograph`
- **Layers:** unit
- **WHEN** the ink view of a cut is asked on another photograph's digest
- **THEN** it is refused, naming the photograph the cut is from

## REMOVED Requirements

### Requirement: A tattoo is kept in the library, whole and never deleted

**Reason:** A tattoo can now be removed, and a cut is kept by its photograph, so the title and the rule it states no longer hold.
**Migration:** *A tattoo is kept in the library, whole until it is removed* carries each of its scenarios under the same keys, adds the folders of a cut, the names, the digest and the removal, and replaces *no route deletes or renames* with *no route renames*.
