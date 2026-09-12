#!/usr/bin/env python3
"""PROTOTYPE — N40: map free English phrases onto canonical Danbooru tags.

**This exists because constrained decoding solved the wrong half of the problem.**
An enum grammar over `selected_tags.csv` makes an invalid tag unemittable, and
measurement showed what that actually does: the model starts writing the English
word it meant, logit masking permits only tokens that continue *some* valid tag,
and it lands on the nearest tag sharing that prefix.

    the caption said          unconstrained wrote     the grammar forced
    ----------------          -------------------     ------------------
    "tucked into her jeans"   tuck into jeans         tucked penis  (640 posts)
    "shoulder-length"         shoulder length         shoulder blades
    "white blinds"            white blinds            white bloomers
    "body slightly angled"    body slightly angled    body armor
    "faces front"             front                   front ponytail

**Every one is a prefix collision, and the valid-but-wrong tag is worse than the
invalid one** — `tuck into jeans` is caught by `sheet.py check`, `tucked penis`
passes every guard in this project and gets rendered. So the grammar converts a
visible failure into an invisible one, and the honest fix is to stop constraining
generation and start matching *meaning* after it.

### Three passes, cheapest first, and no new dependency

1. **Exact.** The phrase is already a tag. `wavy hair`, `high heels`.
2. **Suffix.** The vocabulary's convention, per field: `blonde` -> `blonde hair`,
   `blue` -> `blue eyes`, `tan` -> `tan skin`. This is the single commonest
   failure and it is one rule.
3. **Token containment.** Take the tag whose every word appears in the phrase,
   longest first. This is what turns `tuck into jeans` into `jeans` -- **by
   shared words, not shared prefix**, which is the whole point. Containment
   rather than a ratio, because a ratio let `white shirt open collar` return
   `white sailor collar`: two of three words matched and `sailor` came free.

### And a curated map, because lexical matching cannot reach a synonym

`shoulder length` and `medium hair` share no words. `directed at camera` and
`looking at viewer` share only `at`. No amount of string arithmetic connects
them, so the pairs that matter are written down. **This is the deterministic,
bounded, open router `notes/JOYCAPTION.md` §5 predicted would be "real work, and
it has to be maintained"** -- it is small on purpose, it covers the phrasings
JoyCaption actually produces, and every entry is auditable by eye.

    PYTHONPATH=. uv run python prototype/tagmap.py
"""

import re

from prototype.sheet import vocabulary

# Per-field suffix conventions. `hair silhouette` is deliberately absent: its
# values are shapes rather than colours, and appending ` hair` to `long` is right
# while appending it to `bob cut` is not -- the curated map handles that field.
# Bare words that are canonical tags and are nearly always a stranded modifier.
STRANDED = frozenset(
    {
        "light",
        "dark",
        "bright",
        "white",
        "black",
        "blue",
        "red",
        "green",
        "grey",
        "gray",
        "brown",
        "pink",
        "purple",
        "orange",
        "yellow",
        "blonde",
        "tan",
        "pale",
        "long",
        "short",
        "small",
        "large",
        "high",
        "low",
        "open",
    }
)

SUFFIX = {
    "hair colour": ("hair",),
    "eye colour": ("eyes",),
    "skin / ancestry": ("skin",),
}

# Phrases lexical matching cannot reach, and their tags. Keyed by the phrasing
# JoyCaption actually writes -- read off its captions rather than imagined.
# A `None` value means **drop it**: the phrase carries no renderable content, and
# emitting nothing is correct where emitting something is F44's failure.
PHRASES: dict[str, tuple[str, ...] | None] = {
    # --- gaze, where the prose is always a sentence and the tag never is -----
    "directed at camera": ("looking at viewer",),
    "at the camera": ("looking at viewer",),
    "directly at the camera": ("looking at viewer",),
    "straight at the camera": ("looking at viewer",),
    "gaze right": ("looking to the side",),
    "gaze left": ("looking to the side",),
    "to the side": ("looking to the side",),
    "slightly to the right": ("looking to the side",),
    "slightly to the left": ("looking to the side",),
    "front": ("looking at viewer",),
    "forward": ("looking at viewer",),
    # `eye contact` is a real tag (39,730) and a correct reading of the prose;
    # the reviewed sheets use `looking at viewer` throughout, so the router has to
    # agree with the sheets rather than merely be defensible.
    "eye contact": ("looking at viewer",),
    "direct gaze": ("looking at viewer",),
    "front gaze": ("looking at viewer",),
    "gaze": None,
    # --- hair length, which has no `length` tags at all ----------------------
    "shoulder length": ("medium hair",),
    "shoulder-length": ("medium hair",),
    "past her shoulders": ("long hair",),
    "reaches past her shoulders": ("long hair",),
    "tied back": ("hair up",),
    "slight wave": ("wavy hair",),
    "slightly wavy": ("wavy hair",),
    "long straight": ("long hair", "straight hair"),
    "long wavy": ("long hair", "wavy hair"),
    # --- framing, the field that collected backgrounds ----------------------
    "full length": ("full body",),
    "head to toe": ("full body",),
    "close up": ("close-up",),
    "waist up": ("cowboy shot",),
    "forward facing": None,
    "sharp focus": None,
    "high contrast": None,
    "bright lighting": None,
    "soft lighting": None,
    "blurred background": ("blurry background",),
    "blurred": ("blurry background",),
    "gray border": ("letterboxed",),
    "grey border": ("letterboxed",),
    # --- clothes and objects -------------------------------------------------
    "tuck into jeans": ("jeans",),
    "tucked into": None,
    "button up": ("collared shirt",),
    "button-up": ("collared shirt",),
    "short sleeve": ("short sleeves",),
    "short-sleeved": ("short sleeves",),
    "skinny jeans": ("jeans", "denim"),
    "high waisted": None,
    "high-waisted": None,
    "open toe": None,
    "open-toed": None,
    "white blinds": ("window",),
    "blinds": ("window",),
    "upholstered couch": ("couch",),
    "thin straps": ("spaghetti strap",),
    "lace bodice": ("lace",),
    "floral lace": ("lace",),
    "knee length": None,
    "knee-length": None,
    # --- expression ----------------------------------------------------------
    "subtle smile": ("light smile",),
    "slight smile": ("light smile",),
    "neutral": ("closed mouth",),
    "neutral expression": ("closed mouth",),
    "serious": ("closed mouth",),
    "relaxed": None,
    # --- pose ----------------------------------------------------------------
    "hand on her hip": ("hand on own hip",),
    "hand on hip": ("hand on own hip",),
    "hands on her hips": ("hands on own hips",),
    "hands on hips": ("hands on own hips",),
    "hand in her hair": ("hand in own hair",),
    "hand in hair": ("hand in own hair",),
    # Danbooru inserts `own` for every self-touch, and the caption never does.
    "hand on chin": ("hand on own chin",),
    "hand on her chin": ("hand on own chin",),
    "hand on knee": ("hand on own knee",),
    "hand on her knee": ("hand on own knee",),
    "hand on chest": ("hand on own chest",),
    "hand on her chest": ("hand on own chest",),
    "hand on neck": ("hand on own neck",),
    "hand on her neck": ("hand on own neck",),
    "hand on head": ("hand on own head",),
    "hand on her head": ("hand on own head",),
    "hands on her head": ("arms behind head",),
    "arms raised": ("arms up",),
    "arm relaxed by side": ("arms at sides",),
    "arms relaxed at sides": ("arms at sides",),
    "arm hanging by her side": ("arms at sides",),
    "body straight": ("standing",),
    "body slightly angled": None,
    "body slightly turned": None,
    "slightly tilted": ("head tilt",),
    "head slightly tilted": ("head tilt",),
    # --- and the absence clauses, which must die here (F44) ------------------
    "no distinguishing marks": None,
    "not visible": None,
    "none": None,
    "no marks": None,
}


def words(text: str) -> set[str]:
    """Return `text`'s lowercase word set, punctuation dropped."""
    return set(re.findall(r"[a-z0-9']+", text.lower()))


def to_tags(
    phrase: str,
    field: str,
    known: dict,
    candidates: list[str] | None = None,
) -> list[str]:
    """Return the canonical tags `phrase` means in `field`, or an empty list.

    An empty list is a real answer and the common one: `high-waisted`,
    `sharp focus` and `no distinguishing marks` all carry nothing a generator can
    draw, and **F44 is the record of what happens when an absence is passed
    through instead of dropped.**
    """
    phrase = phrase.replace("_", " ").strip().lower().rstrip(".,")
    if not phrase:
        return []

    if phrase in PHRASES:
        return list(PHRASES[phrase] or ())
    if phrase in known:
        return [phrase]

    for suffix in SUFFIX.get(field, ()):
        if (joined := f"{phrase} {suffix}") in known:
            return [joined]

    # **The curated pass CONSUMES spans rather than returning on the first hit.**
    # Returning early was a real bug, measured: `white open toe high heels` hit
    # `open toe` -> None and the whole phrase was dropped, losing `high heels`.
    # A caption phrase routinely carries two or three concepts, so each match is
    # taken, its span removed, and what is left goes on to the overlap pass.
    out: list[str] = []
    residue = phrase
    for source, target in sorted(PHRASES.items(), key=lambda kv: -len(kv[0])):
        # **Word boundaries, and a length guard of four rather than seven.** The
        # old `len(source) > 6 and source in residue` test silently skipped every
        # short key -- `front`, `forward`, `serious`, `neutral` -- so `front gaze`
        # reached the fallback and was dropped, which is why `gaze` scored 0.00
        # with the mapper in place. Boundaries are what make a four-character key
        # safe: `front` no longer matches inside `frontal`.
        if len(source) >= 4 and re.search(rf"\b{re.escape(source)}\b", residue):
            out.extend(target or ())
            residue = re.sub(rf"\b{re.escape(source)}\b", " ", residue)

    pool = candidates if candidates is not None else list(known)
    seen = words(residue)
    # **Containment, not a ratio.** Scoring `|phrase ∩ tag| / |tag|` let a tag win
    # while containing a word the phrase never had: `white shirt open collar`
    # returned `white sailor collar` at 0.67, because two of its three words
    # matched and `sailor` was free. Requiring every word of the tag to appear in
    # the phrase makes that unreachable, and it needs no threshold.
    scored = [
        (len(words(tag)), known[tag], tag)
        for tag in pool
        if words(tag) and words(tag) <= seen
    ]
    # Single-word tags are accepted -- `clear sunny day` means `day` and
    # `blue couch` means `couch`, and requiring two words dropped both -- except
    # for bare colour and brightness words. Those are tags in their own right and
    # are almost always a modifier stranded from a compound the vocabulary does
    # not have: `light gray skinny jeans` yielded `light` (105,884 posts) for
    # exactly that reason.
    best = [
        row
        for row in scored
        if row[0] >= 2 or (row[2] not in STRANDED or words(row[2]) == seen)
    ]
    if not best:
        return out
    # **Longest match wins before commonest, and only ONE match is taken.**
    # Tie-breaking on post count alone preferred bare `shirt` over `white shirt`
    # and threw the colour away. Taking every above-threshold match instead
    # over-generated badly -- `white shirt open collar` returned four tags
    # including `white sailor collar`, because the later candidates were scored
    # against the whole phrase rather than against what was left of it.
    #
    # So the overlap pass is deliberately CONSERVATIVE: the curated map is the
    # precise instrument and this is the fallback, and a fallback that invents
    # three tags from four words is worse than one that returns a single right
    # one. Multi-concept phrases are handled by ADDING them to `PHRASES`, which
    # is auditable, rather than by making the heuristic cleverer.
    best.sort(key=lambda row: (-row[0], -row[1]))
    tag = best[0][2]
    if tag not in out and not any(words(tag) <= words(taken) for taken in out):
        out.append(tag)
    return out


def map_field(value: str, field: str, known: dict) -> str:
    """Map one comma-separated field value onto canonical tags, order kept."""
    out: list[str] = []
    for phrase in value.split(","):
        for tag in to_tags(phrase, field, known):
            if tag not in out:
                out.append(tag)
    return ", ".join(out)


def map_sheet(sheet: dict, known: dict) -> dict:
    """Return `sheet` with every field mapped onto canonical vocabulary."""
    return {field: map_field(value, field, known) for field, value in sheet.items()}


def main() -> None:
    """Show the mapper on the phrases the measured runs actually produced."""
    known = vocabulary()
    cases = [
        ("blonde", "hair colour"),
        ("brown", "eye colour"),
        ("long wavy", "hair silhouette"),
        ("shoulder length", "hair silhouette"),
        ("tuck into jeans", "clothes"),
        ("white shirt open collar", "clothes"),
        ("light gray skinny jeans", "clothes"),
        ("white open toe high heels", "clothes"),
        ("directed at camera", "gaze"),
        ("gaze right", "gaze"),
        ("forward facing", "framing"),
        ("blurred background", "framing"),
        ("body slightly angled to the right", "pose"),
        ("arms relaxed at sides", "pose"),
        ("hand on chin", "pose"),
        ("clear sunny day", "background"),
        ("white blinds", "background"),
        ("blue couch", "background"),
        ("no distinguishing marks", "marks"),
        ("young", "age band"),
    ]
    print(f"{'phrase':36s} {'field':17s} -> tags")
    print("-" * 86)
    for phrase, field in cases:
        got = to_tags(phrase, field, known)
        print(f"{phrase:36s} {field:17s} -> {', '.join(got) or '(dropped)'}")


if __name__ == "__main__":
    main()
