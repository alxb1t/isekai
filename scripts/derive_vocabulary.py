#!/usr/bin/env python3
"""Re-derive `scripts/vocabulary.json` -- the tag list the pipeline fills sheets from.

The third manifest, and a sibling of the other two rather than a section of
either. `models.json` answers what **the graph** needs on the pod and
`eval_models.json` answers what **the scorer** loads on the operator's machine;
this one answers what **the sorting stage** fills a sheet from. Three questions,
three files (design.md D9, D10).

Run it from the repository root:

    uv run python scripts/derive_vocabulary.py

It rewrites `scripts/vocabulary.json` in place, and re-running without editing the
spec below must leave the file byte-identical --
`git diff --exit-code scripts/vocabulary.json` is the check.

**One entry, and deliberately one.** `selected_tags.csv` is published alongside a
tagger model, and the tagger is not here: this repository does not run it, the
vocabulary outlives it, and a manifest that carried both would make swapping the
vocabulary a decision about a model nobody loads. The two are different artifacts
with different consumers.

**Two corrections to how this artifact was being obtained.** It was reaching the
tree as a side effect of downloading that unrelated model, on a mutable
reference, which the repository's own pinning rule forbids -- so it is pinned to
an immutable revision here. And at roughly 300 KB it is not stored as a large
file, so Hugging Face publishes no digest to read and there is nothing to look
up: the bytes are fetched and hashed, through the same `blob_digest` strategy
`scripts/manifest.py` gives every deriver.
"""

from pathlib import Path

from manifest import Manifest, ManifestEntry, Source, Spec, entry_for, write

MANIFEST_PATH = Path(__file__).resolve().parent / "vocabulary.json"

# The date the revision below was taken. Bumping the revision means bumping this.
PINNED = "2026-09-14"

# Hugging Face orgs that publish the artifact they serve. SmilingWolf trains the
# WD taggers and publishes the tag list with them, so this entry's primary is a
# publisher and needs no alternate -- the same rule the other two manifests are
# held to.
PUBLISHERS = ("SmilingWolf",)

# WD SwinV2 Tagger v3, whose `selected_tags.csv` is the vocabulary: 10,861 rows,
# of which 8,106 are general tags with their Danbooru post counts. The counts are
# what the mapping cascade ranks candidates by, so the file is the vocabulary and
# not merely a list of legal strings.
#
# Every v3 tagger in the family -- `wd-vit-tagger-v3`, `wd-vit-large-tagger-v3`,
# `wd-eva02-large-tagger-v3` -- publishes this file byte for byte identically,
# checked on the date above. They are not declared as alternates: an alternate is
# for availability, and naming three sibling models as sources for a file that is
# a property of the *dataset* would suggest the choice of tagger mattered here. It
# does not; this repository loads none of them.
TAGGER = "627aef95638667ddcaa3ac8ae625e88ea5b02f51"

SPECS: tuple[Spec, ...] = (
    Spec(
        "wd14/selected_tags.csv",
        (Source("SmilingWolf/wd-swinv2-tagger-v3", TAGGER, "selected_tags.csv"),),
        lfs=False,
    ),
)


def derive() -> Manifest:
    """Build the vocabulary manifest by fetching and hashing each entry's bytes."""
    entries: list[ManifestEntry] = [entry_for(spec) for spec in SPECS]
    return {
        "pinned": PINNED,
        "publishers": list(PUBLISHERS),
        "entries": entries,
    }


def main() -> None:
    """Derive the vocabulary manifest and write it to `scripts/vocabulary.json`."""
    write(derive(), MANIFEST_PATH)


if __name__ == "__main__":
    main()
