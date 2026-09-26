#!/usr/bin/env python3
"""Re-derive `config/vocabulary.json` -- the tag list the pipeline fills sheets from.

The third manifest, and a sibling of the other two rather than a section of
either. `models.json` answers what **the graph** needs on the pod and
`eval_models.json` answers what **the scorer** loads on the operator's machine;
this one answers what **the sorting stage** fills a sheet from. Three questions,
three files (design.md D9, D10).

Run it from the repository root:

    uv run python scripts/derive_vocabulary.py

It rewrites `config/vocabulary.json` in place, and re-running without editing the
spec below must leave the file byte-identical --
`git diff --exit-code config/vocabulary.json` is the check.

**Two entries, and they are one artifact split in two.** This file carried one
entry until v0.20, on the argument that `selected_tags.csv` is published
*alongside* a tagger model which this repository did not run -- so that the two
were different artifacts with different consumers, and a manifest carrying both
would make swapping the vocabulary a decision about a model nobody loads. **That
argument was correct when it was written and `isekai/boundary/wd14.py`
falsifies it.**

The CSV is not published alongside the model. It **is** the model's output
layer: row N names output neuron N of the ONNX graph, so a CSV and a `model.onnx`
from different revisions mislabel every tag, silently, and nothing downstream
could notice -- the vector has the right length and every name in it is a real
tag. A manifest holding one half without the other is a manifest that cannot
detect the one failure that matters, which is why both are pinned here, at the
one revision `TAGGER` names, and why a test asserts that they agree
(design.md D18, D24).

The retired argument is kept rather than deleted, because it names the case this
rule does not cover: while no build loads the model, the vocabulary really does
outlive any particular tagger.

**Two corrections to how the CSV was being obtained**, both made at v0.18 and both
still standing. It was reaching the tree as a side effect of downloading the
tagger, on a mutable reference, which the repository's own pinning rule forbids
-- so it is pinned to an immutable revision here. And at roughly 300 KB it is not
stored as a large file, so Hugging Face publishes no digest to read and there is
nothing to look up: its bytes are fetched and hashed, through the `blob_digest`
strategy `scripts/manifest.py` gives every deriver. The graph beside it takes the
other route, and its entry's `lfs` says so.
"""

from pathlib import Path

from manifest import Manifest, ManifestEntry, Source, Spec, entry_for, write

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "config" / "vocabulary.json"

# The date the revision below was taken. Bumping the revision means bumping this.
PINNED = "2026-09-14"

# Hugging Face orgs that publish the artifact they serve. SmilingWolf trains the
# WD taggers and publishes the tag list with them, so this entry's primary is a
# publisher and needs no alternate -- the same rule the other two manifests are
# held to.
PUBLISHERS = ("SmilingWolf",)

# WD SwinV2 Tagger v3: the vocabulary and, since v0.20, the tagger this repository
# actually loads. `selected_tags.csv` is 10,861 rows, of which 8,106 are general
# tags with their Danbooru post counts -- the counts are what the mapping cascade
# ranks candidates by, so the file is the vocabulary and not merely a list of
# legal strings, and it is simultaneously the graph's output layer.
#
# Every v3 tagger in the family -- `wd-vit-tagger-v3`, `wd-vit-large-tagger-v3`,
# `wd-eva02-large-tagger-v3` -- publishes the CSV byte for byte identically,
# checked on the date above. They are still not declared as alternates, and the
# reason is now stronger rather than weaker: an alternate is for availability,
# and the CSV has to come from the same repository as the `model.onnx` beside it
# or the pair stops being one artifact. A sibling's CSV happens to be identical;
# relying on that would be relying on a coincidence to keep neuron N named right.
TAGGER = "627aef95638667ddcaa3ac8ae625e88ea5b02f51"

# The two halves, at the one revision `TAGGER` names. `lfs` differs between them
# and is stated rather than sniffed, as `manifest.py` requires: at roughly 300 KB
# the CSV is a plain git blob, so it has no published object id and its bytes are
# fetched and hashed, while the 467 MB graph is an LFS object whose id **is** its
# SHA-256 -- so pinning it reads one API response and downloads nothing.
SPECS: tuple[Spec, ...] = (
    Spec(
        "wd14/selected_tags.csv",
        (Source("SmilingWolf/wd-swinv2-tagger-v3", TAGGER, "selected_tags.csv"),),
        lfs=False,
    ),
    Spec(
        "wd14/model.onnx",
        (Source("SmilingWolf/wd-swinv2-tagger-v3", TAGGER, "model.onnx"),),
    ),
)


def derive() -> Manifest:
    """Build the vocabulary manifest, each entry by the digest route it declares."""
    entries: list[ManifestEntry] = [entry_for(spec) for spec in SPECS]
    return {
        "pinned": PINNED,
        "publishers": list(PUBLISHERS),
        "entries": entries,
    }


def main() -> None:
    """Derive the vocabulary manifest and write it to `config/vocabulary.json`."""
    write(derive(), MANIFEST_PATH)


if __name__ == "__main__":
    main()
