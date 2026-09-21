#!/usr/bin/env python3
"""Re-derive `scripts/field_map.json` from the authored spec below.

**Stdlib, offline, no network.** The route the roadmap credited to Danbooru's
`search[name_matches]` wildcard needs no Danbooru at all: a wildcard intersected
with the pinned vocabulary **is** a match against the pinned vocabulary, and the
240 candidates the API would return are the 74% that get thrown away (design.md
D15). If this script ever appears to need an HTTP call, that is a halt.

Run it from the repository root:

    uv run python scripts/derive_field_map.py            # rewrite the table
    uv run python scripts/derive_field_map.py --report   # and print the expansion

**The expansion is dirty by construction and the report is the point.** Seven
seeds for *hair silhouette* reach 57 tags beyond the suffix group, and at least
six of them are bunny costumes and a festival. Printing what each seed pulled in
is what lets the operator's pruning pass see the junk rather than inherit it.

**Three sources of group content, and they are not the same kind of thing.**

1. **The suffix walk** — a criterion whose schema entry declares a suffix owns
   every tag that *is* that suffix or *ends in* `" " + suffix`. Not substring:
   substring gives `hair` 265 rather than 103.
2. **The seven seed lists** — `clothes`, `pose` and `body_shape` hold 102 of the
   200 tags the operator approved over the v0.20 batch and not one of them
   declares a suffix, so the criteria that carry the weight are exactly the ones
   the suffix walk cannot reach. A seed is a **stem**, matched on word boundaries
   against its own inflections.
3. **The dead briefing's own examples** — `flows/conjure-v1/sheet.briefing.md`
   names 41 example tags across ten criteria, and it is the only authored group
   content that exists anywhere in either tree. This version carries that file
   dead (design.md D22), so it is harvested here before it stops being read.

**One primary per tag, decided in three steps (design.md D30 ③).** The operator's
own filings decide first, because a tag he approved and then rendered is
render-tested and no ordering is; then the declared precedence order settles what
he has never filed; then phase 8 overrides individual tags by hand. Every
criterion that loses a tag keeps it under `also`, so nothing is hidden from
browsing and exactly one criterion routes it.

**Every input this script reads is tracked or pinned, so the table re-derives
byte-identically anywhere.** The filings are `FILED`, transcribed below; the
vocabulary is the pinned, digested `models/wd14/selected_tags.csv`; the field
names come from the flows' own schemas. `.data/` is read by `--refresh` alone,
which prints a diff and writes nothing.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path

# Run as a script from the repository root, `scripts/` is on the path and the
# root is not -- the same hop `derive_eval_manifest.py` makes, for the same reason.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from isekai.foundation.run import read_artifact  # noqa: E402
from isekai.shared.field_map import FIELD_MAP_PATH, declared_fields  # noqa: E402
from isekai.shared.vocabulary import Vocabulary, load  # noqa: E402

# The table's own monotonic counter. There is no upstream revision to name --
# the artifact is authored here -- so it is bumped by whoever edits this spec.
# Phase 1 shipped 1, phase 2 the seeded table; this is the operator's pass.
REVISION = 3

# Where the operator's approved sheets live. Gitignored, and read by `--refresh`
# and by nothing else: this script's *output* is committed, so an input that
# exists on one machine would make the committed table unreproducible on every
# other. What the sheets said is transcribed into `FILED` instead.
APPROVED = ".data/v0.20/runs/*/summon-open-v1/review/*.approved.json"

# A `hair` tag whose non-suffix words carry one of these takes `hair_colour`;
# every other takes `hair_silhouette`. Both list all 103, so nothing is hidden
# from browsing -- the split is the router's, not the cheatsheet's (design.md
# D16). The operator's own sheets prove it separates cleanly: `brown hair` x5,
# `blonde hair` x2, `black hair` against `long hair` x7, `wavy hair` x6,
# `straight hair` x2, `medium hair`.
COLOUR_WORDS = frozenset(
    """aqua black blond blonde blue brown colored gradient gray green grey
    multicolored orange pink purple rainbow red silver split-color streaked
    two-tone white yellow""".split()
)

# The suffix each criterion's schema entry declares, authored here rather than
# read from `Field.suffix`: after this version's cascade retires, that key has no
# runtime consumer at all and reading it here would resurrect one (design.md D28).
SUFFIXES: Mapping[str, str] = {
    "skin_ancestry": "skin",
    "hair_colour": "hair",
    "hair_silhouette": "hair",
    "bangs": "bangs",
    "eye_colour": "eyes",
    "eyebrows": "eyebrows",
    "eyelashes": "eyelashes",
    "nose": "nose",
    "lips": "lips",
    "background": "background",
}

# A stem list per criterion, and an explicit list beside it. The second exists
# because a tag reachable only by a stem that would pull in hundreds -- `from`,
# `no`, `body` -- has to be named rather than reached.
SEEDS: Mapping[str, tuple[str, tuple[str, ...]]] = {
    "clothes": (
        """shirt blouse dress skirt shorts pants trousers jeans sweater cardigan
        jacket coat hoodie vest robe kimono uniform swimsuit bikini leotard
        bodysuit lingerie bra panties underwear thong pantyhose thighhighs
        stockings socks garter footwear shoes boots heels sandals gloves sleeves
        collar belt apron cape corset camisole top tank crop fishnet lace strap
        hem bare cleavage midriff navel expose lift pull open unbutton unzip
        see-through sheer torn wet shoulder""",
        (),
    ),
    "pose": (
        """stand sit kneel lie lying squat crouch lean walk run jump stretch arm
        hand leg knee foot toes finger head tilt bend cross spread raise hold hug
        touch cover support bed side back front lift pull""",
        ("from behind", "from side", "from above", "from below"),
    ),
    "body_shape": (
        """breasts hips waist thighs stomach abs shoulder collarbone navel nipples
        ass butt muscular slim curvy plump petite build body""",
        (),
    ),
    "expression": (
        """smile grin smirk frown pout blush laugh cry tears sad angry surprised
        embarrass serious expressionless mouth lips tongue teeth lick wink sweat
        sigh yawn closed""",
        (),
    ),
    "gaze": ("look gaze glance stare", ("eye contact",)),
    "framing": (
        "shot portrait close-up crop focus selfie view angle foreshortening",
        ("out of frame", "upper body", "full body", "lower body"),
    ),
    "background": (
        """background indoors outdoors sky cloud sun moon night day forest beach
        ocean city cityscape street room bedroom bathroom kitchen office wall
        window door floor ceiling bed pillow curtain chair table tree grass water
        rain snow station building interior exterior""",
        (),
    ),
}

# Tags no criterion can hold. **A list this script writes, not one the table
# keeps**: a hand-edit of `field_map.json` is destroyed by the next run, so the
# authored home for an exclusion is here. The definition is semantic and not
# empirical -- *never a criterion*, rather than *WD14 was wrong about it on this
# photograph* -- because the second kind would silently shrink `clothes` by seven
# ordinary garments (design.md D8).
#
# **One entry, at the operator's call, and it is a start rather than a survey.**
# `photorealistic` describes how the picture was rendered and not the person in
# it, so no identity criterion can hold it -- and the router drops it either way.
# What the entry buys is the record: the absence is a decision somebody took
# rather than a gap nobody had looked at. `realistic` 19,111 is the same kind of
# tag and appeared on all eight of the v0.20 photographs; it is deliberately not
# here yet, because the operator named one.
EXCLUDED: tuple[str, ...] = ("photorealistic",)

# The 41 example tags `flows/conjure-v1/sheet.briefing.md` names, by the field it
# names them under. Transcribed rather than parsed: the briefing is prose with no
# machine-readable structure, and this version is the last one that reads it at
# all. Every one is held against the vocabulary before it is written.
BRIEFING: Mapping[str, tuple[str, ...]] = {
    "count": ("1girl", "1boy", "2girls", "multiple girls"),
    "skin_ancestry": ("pale skin", "tan", "dark skin"),
    "bangs": (
        "blunt bangs",
        "parted bangs",
        "swept bangs",
        "choppy bangs",
        "short bangs",
        "long bangs",
    ),
    "eyebrows": ("thick eyebrows", "short eyebrows", "curly eyebrows"),
    "eyelashes": ("long eyelashes", "thick eyelashes"),
    "nose": ("long nose", "big nose", "pointy nose"),
    "lips": ("thick lips", "parted lips", "pink lips", "red lips"),
    "facial_hair": ("beard", "mustache", "stubble", "goatee"),
    "gaze": (
        "looking at viewer",
        "looking to the side",
        "looking at another",
        "looking down",
    ),
    "framing": (
        "portrait",
        "upper body",
        "cowboy shot",
        "full body",
        "close-up",
        "from behind",
        "from above",
        "feet out of frame",
    ),
}

# What the operator filed, transcribed. **The table is derived from tracked
# inputs only, and this constant is why.** The filings are the strongest signal
# the table can be built from -- a tag he approved and then rendered is
# render-tested, which no precedence order is (design.md D30 (3)) -- and they
# live in `.data/`, which is gitignored and exists on one machine. Reading them
# at derivation time made the committed table unreproducible off that machine:
# 17 tags changed or lost their primary and `accessories` emptied. So they are
# transcribed here, exactly as `BRIEFING` above transcribes the dead briefing's
# 41 examples, and `filings()` below is kept as an authoring aid that prints the
# drift rather than as an input.
#
# 113 tags over the ten approved sheets of the v0.20 batch, as
# `tag -> criterion -> how often`. The counts are load-bearing and not decoration:
# they are what puts `collarbone` in `pose` (3 against `body_shape` 1), `navel` in
# `clothes` (2 against one each) and `standing` in `pose` (7 against `framing` 1).
# Refresh it with `--refresh` after a batch, never by hand.
FILED: Mapping[str, Mapping[str, int]] = {
    "1girl": {"count": 10},
    "arm support": {"pose": 1},
    "ass": {"pose": 2},
    "bare arms": {"pose": 1},
    "bare shoulders": {"clothes": 6},
    "bed": {"background": 1},
    "bedroom": {"background": 1},
    "black bra": {"clothes": 1},
    "black footwear": {"clothes": 1},
    "black hair": {"hair_colour": 1},
    "black leotard": {"clothes": 1},
    "black panties": {"clothes": 1},
    "black shorts": {"clothes": 1},
    "blonde hair": {"hair_colour": 2},
    "blue eyes": {"eye_colour": 2},
    "blue sweater": {"clothes": 1},
    "breasts": {"body_shape": 5},
    "breasts apart": {"pose": 1},
    "breasts out": {"pose": 1},
    "brown eyes": {"eye_colour": 5},
    "brown hair": {"hair_colour": 7},
    "cleavage": {"clothes": 3},
    "clothes lift": {"clothes": 2},
    "clothes pull": {"clothes": 1},
    "collarbone": {"body_shape": 1, "pose": 3},
    "cowboy shot": {"framing": 5},
    "crop top": {"clothes": 3},
    "dark": {"eyebrows": 1},
    "dress lift": {"clothes": 1},
    "expressionless": {"expression": 1},
    "finger to mouth": {"pose": 1},
    "fishnet pantyhose": {"clothes": 1},
    "foot out of frame": {"pose": 1},
    "from behind": {"pose": 1},
    "from side": {"pose": 1},
    "full body": {"framing": 2},
    "garter belt": {"clothes": 1},
    "garter straps": {"clothes": 1},
    "gold bracelet": {"accessories": 1},
    "gold necklace": {"accessories": 1},
    "grin": {"expression": 1},
    "hands on own chest": {"pose": 2},
    "hands on own hips": {"pose": 2},
    "head tilt": {"pose": 1},
    "holding phone": {"pose": 1},
    "indoors": {"background": 4},
    "kneeling": {"pose": 1},
    "lace-trimmed bra": {"clothes": 1},
    "large breasts": {"body_shape": 2},
    "legs": {"pose": 3},
    "licking": {"expression": 1},
    "lifted by self": {"pose": 1},
    "light": {"skin_ancestry": 2},
    "light smile": {"expression": 3},
    "lingerie": {"clothes": 1},
    "lips": {"expression": 2},
    "long hair": {"hair_silhouette": 9},
    "looking at phone": {"gaze": 1},
    "looking at viewer": {"gaze": 9},
    "looking back": {"gaze": 2},
    "lying": {"pose": 1},
    "medium breasts": {"body_shape": 4},
    "medium hair": {"hair_silhouette": 1},
    "midriff": {"clothes": 3},
    "navel": {"body_shape": 1, "clothes": 2, "pose": 1},
    "nipples": {"body_shape": 1},
    "no bra": {"clothes": 1},
    "no panties": {"clothes": 1},
    "no pants": {"clothes": 1},
    "off shoulder": {"clothes": 3},
    "on bed": {"pose": 1},
    "on side": {"pose": 1},
    "open mouth": {"expression": 1},
    "panties": {"clothes": 1},
    "parted lips": {"expression": 4},
    "pillow": {"background": 1},
    "pink skirt": {"clothes": 2},
    "pulling": {"pose": 1},
    "red bra": {"clothes": 1},
    "red panties": {"clothes": 1},
    "selfie": {"framing": 2},
    "shirt": {"clothes": 1},
    "shoes": {"clothes": 1},
    "short dress": {"clothes": 2},
    "short shorts": {"clothes": 1},
    "simple background": {"background": 1},
    "sitting": {"pose": 1},
    "skirt": {"clothes": 2},
    "small breasts": {"body_shape": 1},
    "smile": {"expression": 3},
    "solo": {"count": 10},
    "standing": {"framing": 1, "pose": 7},
    "stomach": {"body_shape": 1},
    "stone wall": {"background": 1},
    "straight hair": {"hair_silhouette": 2},
    "sweater lift": {"clothes": 1},
    "teeth": {"expression": 1},
    "thighs": {"pose": 1},
    "thong": {"clothes": 1},
    "toes": {"pose": 1},
    "tongue out": {"expression": 2},
    "train station": {"background": 2},
    "tube dress": {"clothes": 2},
    "underwear": {"clothes": 3},
    "underwear only": {"clothes": 2},
    "upper body": {"framing": 2},
    "wavy hair": {"hair_silhouette": 8},
    "white background": {"background": 2},
    "white bra": {"clothes": 1},
    "white dress": {"clothes": 3},
    "white panties": {"clothes": 1},
    "white shirt": {"clothes": 1},
    "white thighhighs": {"clothes": 1},
}


# Which criterion owns a tag two of them claim, where the operator has never
# filed it. **It is a tie-break and not a claim to be right.** Measured against
# the seventeen collisions he has filed, eleven is the ceiling for any of the
# 5,040 orderings of the seven seeded criteria and 210 of them reach it, so the
# head of this list was picked from the winners rather than reasoned to.
#
# The tail is the builder's and is reasoned to: **a seeded criterion beats a
# suffix one**, because a suffix group is a *lexical* claim -- the tag ends in
# "hair" -- while a seed group is a semantic one. It is right far more often than
# its inverse: `hand in own hair`, `covering own eyes`, `closed eyes` and
# `parted lips` all land where the operator puts them, where suffix-first would
# misfile all four and twenty-three more.
PRECEDENCE: tuple[str, ...] = (
    "gaze",
    "clothes",
    "pose",
    "body_shape",
    "expression",
    "framing",
    "background",
    "hair_colour",
    "hair_silhouette",
    "bangs",
    "eye_colour",
    "eyebrows",
    "eyelashes",
    "nose",
    "lips",
    "skin_ancestry",
    "facial_hair",
    "marks",
    "accessories",
    "count",
    "age_band",
)

_VOWELS = "aeiou"


def inflect(word: str) -> set[str]:
    """Return `word` with the endings an English stem takes in a tag.

    `-s/-es/-ing/-ed`, not only the plural. Plurals alone leave twelve of the
    operator's 113 approved tags unreachable -- `pulling` from `pull`, `licking`
    from `lick`, `lifted by self` from `lift` -- so the drop-`e` and
    consonant-doubling cases are handled too (design.md D30 (1)).
    """
    forms = {word}
    forms.add(word + "es" if word.endswith(("s", "x", "z", "ch", "sh")) else word + "s")
    if word.endswith("e"):
        forms.update({word[:-1] + "ing", word + "d"})
    else:
        forms.update({word + "ing", word + "ed"})
    if word.endswith("y") and len(word) > 1 and word[-2] not in _VOWELS:
        forms.update({word[:-1] + "ies", word[:-1] + "ied"})
    if (
        len(word) >= 3
        and word[-1] not in _VOWELS + "wxy"
        and word[-2] in _VOWELS
        and word[-3] not in _VOWELS
    ):
        forms.update({word + word[-1] + "ing", word + word[-1] + "ed"})
    return forms


def forms(stem: str) -> set[str]:
    """Return every form of `stem`, inflecting its last word only."""
    head, _, last = stem.rpartition(" ")
    return {f"{head} {form}".strip() for form in inflect(last)}


def matcher(stems: Iterable[str]) -> re.Pattern[str]:
    r"""Return a word-boundary pattern over every form of every stem.

    Word boundaries rather than `in`, which is the defect the roadmap flagged:
    `scar` matches `scarf` as a substring and `\\bscar\\b` takes 44 matches to 15.
    Inflections rather than bare boundaries, which is the defect the roadmap's own
    remedy would have introduced: `\\bbraid\\b` alone loses `twin braids` 153,036
    and seven more (design.md D18).
    """
    alternatives = sorted({f for stem in stems for f in forms(stem)})
    return re.compile(r"\b(?:" + "|".join(re.escape(a) for a in alternatives) + r")\b")


def expand(stems: Iterable[str], vocabulary: Vocabulary) -> set[str]:
    """Return every tag in `vocabulary` any of `stems` reaches."""
    pattern = matcher(stems)
    return {tag for tag in vocabulary.counts if pattern.search(tag)}


def by_suffix(suffix: str, vocabulary: Vocabulary) -> set[str]:
    """Return every tag that is `suffix` or ends in a space and `suffix`."""
    return {
        tag for tag in vocabulary.counts if tag == suffix or tag.endswith(" " + suffix)
    }


def claims(vocabulary: Vocabulary, fields: Iterable[str]) -> dict[str, set[str]]:
    """Return every criterion's candidate tags, from all three sources."""
    groups: dict[str, set[str]] = {field: set() for field in fields}
    for field, suffix in SUFFIXES.items():
        if suffix == "hair":
            continue
        groups[field] |= by_suffix(suffix, vocabulary)
    hair = by_suffix("hair", vocabulary)
    coloured = {tag for tag in hair if COLOUR_WORDS & set(tag.split()[:-1])}
    groups["hair_colour"] |= coloured
    groups["hair_silhouette"] |= hair - coloured
    for field, (stems, explicit) in SEEDS.items():
        groups[field] |= expand(stems.split(), vocabulary)
        groups[field] |= {tag for tag in explicit if tag in vocabulary}
    for field, examples in BRIEFING.items():
        groups[field] |= {tag for tag in examples if tag in vocabulary}
    return groups


def filings(root: Path = Path(".")) -> dict[str, Counter[str]]:
    """Return, per tag, how often the operator filed it under each criterion.

    **Nothing in the derivation calls this.** It is what `--refresh` diffs
    `FILED` against after a batch, and `FILED` is what the table is built from --
    the runs are gitignored, so a derivation that read them here would be
    reproducible on exactly one machine. An absent directory returns nothing,
    which `--refresh` reports as an absent aid rather than as drift.
    """
    filed: dict[str, Counter[str]] = defaultdict(Counter)
    for path in sorted(root.glob(APPROVED)):
        # Through the pipeline's own reader, which refuses an artifact written
        # to a schema version this build does not know -- the table is committed,
        # so a silently mis-parsed sheet would be committed with it.
        document = read_artifact(path)
        for field, tags in document["fields"].items():
            for tag in tags:
                filed[tag][field] += 1
    return filed


def resolve(groups: Mapping[str, set[str]]) -> dict[str, str]:
    """Return `tag -> primary criterion`, by the operator's filings then the order.

    `FILED` rather than a parameter: a parameter is a seam only if something else
    is passed through it, and since the filings are transcribed there is exactly
    one thing to pass.
    """
    filed = FILED
    rank = {field: index for index, field in enumerate(PRECEDENCE)}
    candidates: dict[str, set[str]] = defaultdict(set)
    for field, tags in groups.items():
        for tag in tags:
            candidates[tag].add(field)
    for tag, counts in filed.items():
        candidates[tag] |= set(counts)
    primary = {}
    for tag, fields in candidates.items():
        if tag in filed:
            # `best` comes from these counts, so at least one field matches.
            best = max(filed[tag].values())
            fields = {f for f in filed[tag] if filed[tag][f] == best}
        primary[tag] = min(fields, key=lambda field: rank[field])
    return primary


def build(
    vocabulary: Vocabulary, fields: Iterable[str]
) -> tuple[dict[str, dict[str, list[str]]], dict[str, set[str]]]:
    """Return the table's `fields` document and the candidate groups behind it."""
    names = list(fields)
    groups = claims(vocabulary, names)
    primary = resolve(groups)
    browsable: dict[str, set[str]] = {field: set(groups[field]) for field in names}

    # Both hair criteria browse all 103. The split decides which one *routes* a
    # tag and nothing else; the operator is content to browse the whole group
    # together, and hiding half of it behind a colour test would be the router's
    # rule leaking into the cheatsheet (design.md D16).
    hair = by_suffix("hair", vocabulary)
    browsable["hair_colour"] |= hair
    browsable["hair_silhouette"] |= hair

    # Every criterion the operator has filed a tag under shows that tag, whether
    # or not it won the primary. He files `standing` under both framing and pose
    # and `navel` under all three of clothes, pose and body shape; one of those
    # routes it and the rest are how he finds it again.
    for tag, counts in FILED.items():
        if tag in vocabulary:
            for field in counts:
                browsable[field].add(tag)
    for tag, field in primary.items():
        if tag in vocabulary:
            browsable[field].add(tag)

    document = {
        field: {
            "primary": vocabulary.rank(
                t for t in browsable[field] if primary.get(t) == field
            ),
            "also": vocabulary.rank(
                t for t in browsable[field] if primary.get(t) != field
            ),
        }
        for field in sorted(names)
    }
    return document, groups


def report(vocabulary: Vocabulary, groups: Mapping[str, set[str]]) -> None:
    """Print what each seed pulled in, and every collision, for the pruning pass."""
    filed = FILED
    print("== the suffix walk ==")
    for field, suffix in SUFFIXES.items():
        print(f"  {field:16} {suffix:12} {len(by_suffix(suffix, vocabulary)):5}")
    print(
        f"  hair splits on a colour word: {len(groups['hair_colour']):>3} colour, "
        f"{len(groups['hair_silhouette']):>3} silhouette, both list all 103"
    )

    print("\n== the seven seed lists, per seed ==")
    for field, (stems, explicit) in SEEDS.items():
        reached = expand(stems.split(), vocabulary)
        print(f"\n  {field} -- {len(reached)} from stems, {len(explicit)} explicit")
        for stem in stems.split():
            pulled = expand([stem], vocabulary)
            listed = ", ".join(
                f"{tag} {vocabulary.count(tag)}"
                for tag in sorted(pulled, key=lambda t: -vocabulary.count(t))[:6]
            )
            print(f"    {stem:16} {len(pulled):5}  {listed}")

    print("\n== the briefing's own examples ==")
    for field, examples in BRIEFING.items():
        print(f"  {field:16} {len(examples):3}  {', '.join(examples)}")

    collisions = defaultdict(list)
    for tag in {tag for tags in groups.values() for tag in tags}:
        claimed = tuple(sorted(f for f in groups if tag in groups[f]))
        if len(claimed) > 1:
            collisions[claimed].append(tag)
    total = sum(len(tags) for tags in collisions.values())
    settled = sum(1 for tags in collisions.values() for tag in tags if tag in filed)
    print(f"\n== {total} collisions: {settled} settled by the operator's filings ==")
    print(f"   the rest by {' > '.join(PRECEDENCE[:7])} > the suffix criteria")
    for claimed, tags in sorted(collisions.items(), key=lambda kv: -len(kv[1])):
        unfiled = sorted(
            (t for t in tags if t not in filed), key=lambda t: -vocabulary.count(t)
        )
        print(f"\n  {' + '.join(claimed)} -- {len(tags)}, {len(unfiled)} unfiled")
        print("    " + ", ".join(unfiled[:12]))

    print(f"\n== {len(filed)} tags the operator has filed, over the v0.20 batch ==")


def refresh(root: Path = Path(".")) -> None:
    """Print how `FILED` differs from the approved sheets that are on disk.

    The one place the gitignored runs are read, and it writes nothing. A batch
    the operator has just approved is transcribed into `FILED` by hand from this
    output, so the crossing from `.data/` into a tracked file is a deliberate
    edit rather than a side effect of re-running the deriver.
    """
    on_disk = filings(root)
    if not on_disk:
        print(f"\n== no approved sheets under {APPROVED}; nothing to diff ==")
        return
    drifted = sorted(
        tag
        for tag in set(on_disk) | set(FILED)
        if dict(on_disk.get(tag, {})) != dict(FILED.get(tag, {}))
    )
    print(f"\n== {len(on_disk)} tags on disk against {len(FILED)} transcribed ==")
    if not drifted:
        print("    FILED matches the approved sheets exactly")
    for tag in drifted:
        print(
            f"    {tag:24} disk {dict(on_disk.get(tag, {}))} "
            f"!= FILED {dict(FILED.get(tag, {}))}"
        )


def main() -> None:
    """Rewrite the table, and print the expansion when asked for it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report", action="store_true", help="print the expansion and the collisions"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="diff FILED against the operator's approved sheets, if they are on disk",
    )
    arguments = parser.parse_args()

    vocabulary = load()
    fields = sorted({name for names in declared_fields().values() for name in names})
    document, groups = build(vocabulary, fields)

    FIELD_MAP_PATH.write_text(
        json.dumps(
            {
                "name": "scripts/field_map.json",
                "revision": REVISION,
                "fields": document,
                "excluded": list(vocabulary.rank(EXCLUDED)),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    if arguments.report:
        report(vocabulary, groups)
    if arguments.refresh:
        refresh()
    sizes = ", ".join(
        f"{field} {len(entry['primary'])}"
        for field, entry in sorted(
            document.items(), key=lambda kv: -len(kv[1]["primary"])
        )
    )
    print(f"\nwrote {FIELD_MAP_PATH.name} revision {REVISION}: {sizes}")


if __name__ == "__main__":
    main()
