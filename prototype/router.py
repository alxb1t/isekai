#!/usr/bin/env python3
"""PROTOTYPE — N39/N40: the router, and the eval round 4 never had.

Round 4 decided JoyCaption's place: it **describes**, an LLM **routes** the prose
into sixteen Danbooru fields, and the operator **reviews**. Two of those three
exist. This is the third, and its harness.

### Why the harness comes before the model

`vlm_reader.py` scores a **reader** — photograph in, sheet out. **Nothing scores a
router** — prose in, sheet out. So the only router number this project owns is one
hand-routing of five subjects, done in a chat session by a hand that is not a
reproducible component either. **That is the objection round 4 opened with**, and
shipping a second irreproducible stage to fix the first one would be the same
mistake twice. The measurement goes first; then a candidate is a `--model` flag.

### The reframe: this is not a knowledge problem

**The vocabulary is closed at 8,106 tags.** So the router does not need a model
that knows Danbooru — it needs one that can pick from a list and fill sixteen
slots. Two consequences:

- **Structure is enforced, not requested.** Ollama's `format` takes a JSON schema,
  so the sixteen keys are guaranteed present and the output is guaranteed to
  parse. That is what killed the earlier `fields` arm: asked for sixteen labelled
  fields, JoyCaption returned a flat bag and ignored the structure entirely. A
  schema makes that impossible rather than unlikely.
- **The vocabulary is still only validated, not constrained.** A GBNF grammar over
  `selected_tags.csv` would make an invalid tag *structurally impossible*; Ollama's
  JSON-schema mode cannot express that, so invalid tags are counted here instead
  and reported as `invented`. **Recorded as the gap it is** — the stronger
  guarantee is available in llama.cpp and is not being used yet.

### The two jobs, and the second one is not optional

1. **Sort prose into the sixteen fields.**
2. **Strip absence clauses.** F44: JoyCaption is *licensed* to write "no tattoos
   are visible" — that is what stopped it confabulating — and CLIP has no
   negation, so that sentence put `tattoos` in a positive prompt and the render
   came back with tattoos. **The router is the seam where negation dies.** Its
   briefing says so explicitly, and `absence_leak()` measures whether it obeyed.

    PYTHONPATH=. uv run python prototype/router.py --schema
    PYTHONPATH=. uv run python prototype/router.py --model mistral-small-3.2
    PYTHONPATH=. uv run python prototype/router.py --score
"""

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

from prototype.joycaption import EVAL, HOST
from prototype.sheet import ORDER, fields_of, vocabulary
from prototype.vlm_reader import SCORED, tags

# The prose the router reads. The EVALUATION's captions, not `n35`'s: these were
# written with the identity-coverage block `prompts.md` carries, so every one of
# them was at least ASKED for the seven scored criteria. Scoring a router on prose
# that never mentioned `marks` would measure the captioner, not the router.
CAPTIONS = EVAL / "captions" / "descriptive"

# The hand-routed sheets, and what they are: **the incumbent**. Claude, by hand,
# in a chat session, from these exact captions. Not reproducible -- which is the
# whole point of replacing it -- but it is the number to beat, the way the agent
# session's 0.795 was the number for the reader.
INCUMBENT = EVAL / "sheet"

DRAFTS = Path("prototype/derived/router_drafts")

# Negation and absence language. If any of these survives into a field value the
# router has failed its second job, and F44 says what that costs downstream.
#
# **Checked per tag and only against tags the vocabulary does NOT know**, because
# fifty-four canonical Danbooru tags contain one of these words and every one of
# them is a legitimate POSITIVE: `no bra` (93,761), `no shoes` (77,591),
# `eyes visible through hair` (62,070), `eyebrows hidden by hair` (22,440),
# `invisible chair` (11,163). A detector that flagged the string would call the
# vocabulary a bug -- so a real tag is never a leak, however it reads.
ABSENCE = (
    "no ",
    "not ",
    "none",
    "absent",
    "invisible",
    "n/a",
    "unknown",
    "nothing",
    "without",
    "hidden",
    "unclear",
    "cannot",
    "visible",
)

# **Few-shot examples, and where they come from matters.** Two subjects from the
# `n35` probe -- `00072` and `male_cowboy_shot_1` -- which are NOT among the five
# the router is scored on, so nothing leaks. One female upper body and one male,
# because `count` is a field rather than a constant and a male subject is the case
# a single example would silently omit.
#
# The briefing had rules and no examples until now, which for a format-mapping
# task is the largest untried lever there was.
SHOTS = (
    (
        "The photograph shows a young woman with fair skin and long, wavy blonde "
        "hair. She has striking blue eyes and a serious expression. She is wearing "
        "a black choker necklace and a delicate gold chain necklace with a blue "
        "heart pendant. Her attire includes a black sleeveless top. The background "
        "is dark and blurred, with a hint of a window on the right side.",
        {
            "count": "1girl, solo",
            "hair colour": "blonde hair",
            "hair silhouette": "long hair, wavy hair",
            "eye colour": "blue eyes",
            "clothes": "tank top, black tank top, bare shoulders",
            "accessories": "choker, black choker, necklace, pendant, heart, jewelry",
            "expression": "closed mouth",
            "framing": "upper body",
            "body shape": "medium breasts",
            "background": "indoors, blurry background, window",
        },
    ),
    (
        "The photograph shows a young Asian man with short, black, slightly "
        "tousled hair. He has a serious expression. He is wearing a black, "
        "double-breasted suit with a deep V-neck, which is slightly open. The "
        "background is a gradient from light blue to white.",
        {
            "count": "1boy, solo",
            "hair colour": "black hair",
            "hair silhouette": "short hair",
            "clothes": (
                "suit, black suit, formal, double-breasted, open clothes, v-neck"
            ),
            "expression": "closed mouth",
            "pose": "standing",
            "background": "gradient background, simple background, male focus",
        },
    ),
)


def shots() -> str:
    """Return the worked examples, rendered as the briefing shows them."""
    blocks = []
    for prose, sheet in SHOTS:
        filled = {field: sheet.get(field, "") for field in ORDER}
        blocks.append(f"Description:\n{prose}\n\nTags:\n{json.dumps(filled, indent=2)}")
    return "\n\n---\n\n".join(blocks)


BRIEFING = """You convert an English description of a photograph into Danbooru tags.

Fill in every field below. Each value is a comma-separated list of Danbooru tags,
or an empty string.

Fields: {fields}

Rules:
- Use ONLY real Danbooru tags: lowercase, spaces not underscores. A tag that does
  not exist on Danbooru does nothing at all in the image generator.
- Prefer the common tag over the precise-sounding one.
- Danbooru uses `own` for self-touching: `hand on own hip`, `hand in own hair`,
  `arms behind head`. Never `hand on hip`.
- `count` is `1girl, solo` for a woman and `1boy, solo` for a man.
- NEVER write a negation or an absence. If the description says "no tattoos are
  visible" or "her eyes are hidden", the correct value is an EMPTY STRING for that
  field. Do not write "no tattoos", "none", "not visible" or anything like it --
  the generator has no concept of negation and would draw the thing you named.
- Describe only what the description states. Do not add, infer or embellish.
- Output nothing but the JSON object.
{examples}
The description:
{prose}"""


def briefing(prose: str, examples: bool = False) -> str:
    """Return the router's prompt for one caption, with or without examples."""
    block = f"\nWorked examples:\n\n{shots()}\n" if examples else ""
    return BRIEFING.format(fields=", ".join(ORDER), prose=prose, examples=block)


# How many tags the constrained schema offers, commonest first. The whole
# vocabulary is 8,106; a grammar over all of it is what we would like and may be
# too slow to compile, so this is the knob that finds out.
ENUM_SIZE = 8106

# Per-field ceiling in the constrained schema. See `schema()` for why it exists.
MAX_TAGS = 10


def schema(known: dict | None = None, size: int = ENUM_SIZE) -> dict:
    """Return the JSON schema the router's output must satisfy.

    Two modes, and the difference between them is the experiment.

    **Unconstrained** (`known=None`): sixteen string fields. Guarantees the keys
    are present and the JSON parses, and says nothing about what goes in them.
    Qwen3-8B scored **0.033** here with **68 of 88 tags outside the vocabulary** --
    and the failures were `blonde` for `blonde hair`, `brown` for `brown eyes`,
    `body slightly angled to the right` for a pose. **It did the semantic job and
    failed the surface job**, because it has never seen `selected_tags.csv`.

    **Constrained** (`known` given): every field is an ARRAY whose items are an
    `enum` of real Danbooru tags. Ollama compiles the schema into a llama.cpp
    grammar, so `blonde` becomes **unemittable** rather than merely wrong. This is
    the difference between validating after the fact and making the failure
    impossible, and it is why `README.md`'s N40 says this is not a knowledge
    problem: the vocabulary is closed, so the model only has to pick from it.

    The enum is shared across all sixteen fields via `$defs`/`$ref` rather than
    repeated -- one list, sixteen references, because a 16x copy of 8,106 strings
    is a megabyte of schema for no added constraint. **It therefore does NOT stop
    a tag landing in the wrong field**, which was a third of Qwen3's failures.
    Per-field enums would; they need curation, and that is N40's real work.
    """
    if known is None:
        return {
            "type": "object",
            "properties": {field: {"type": "string"} for field in ORDER},
            "required": list(ORDER),
        }
    allowed = [tag for tag, _ in sorted(known.items(), key=lambda kv: -kv[1])[:size]]
    return {
        "type": "object",
        "$defs": {"tag": {"type": "string", "enum": allowed}},
        "properties": {
            field: {
                "type": "array",
                "items": {"$ref": "#/$defs/tag"},
                # **A grammar stops invalid tokens and does not stop looping.**
                # On the first constrained run `full_height_2` emitted
                # `"white robe"` forty times until it exhausted `num_predict`
                # and the JSON was truncated mid-string -- `done_reason:
                # length`. A context-free grammar cannot express "no repeats",
                # so the bound is on LENGTH: no field on any reviewed sheet in
                # this project carries more than nine tags, and ten leaves
                # headroom without leaving room for a loop.
                "maxItems": MAX_TAGS,
            }
            for field in ORDER
        },
        "required": list(ORDER),
    }


def route(
    prose: str,
    model: str,
    host: str = HOST,
    known: dict | None = None,
    size: int = ENUM_SIZE,
    examples: bool = False,
    match: dict | None = None,
) -> dict:
    """Return the sixteen-field sheet a model builds from `prose`.

    `format` is the schema rather than the string `"json"`: the loose mode only
    promises valid JSON, where the schema also promises the sixteen keys. An
    absent key and an empty one are different failures and only one of them is
    the model's opinion.
    """
    body = json.dumps(
        {
            "model": model,
            "prompt": briefing(prose, examples),
            "format": schema(known, size),
            "stream": False,
            # **Thinking off, and not as an economy.** Qwen3 is a hybrid reasoning
            # model and its thinking tokens are drawn from the same `num_predict`
            # budget as the answer -- on the first run they truncated the JSON
            # mid-string on the third subject. Routing is slot-filling against a
            # closed vocabulary, not reasoning, so the budget belongs to the
            # answer. Models without a thinking mode ignore the flag.
            "think": False,
            "options": {
                "temperature": 0,
                "seed": 1,
                "num_predict": 2048,
                # Belt to `maxItems`' braces. At temperature 0 a model that
                # starts repeating has no sampling noise to break out of it, so
                # the penalty is the only thing acting inside a single array.
                "repeat_penalty": 1.15,
            },
        }
    ).encode()
    request = urllib.request.Request(
        f"{host}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            payload = json.loads(response.read())
    except urllib.error.URLError as error:
        raise SystemExit(f"{host} did not answer ({error}). Is `{model}` created?")
    raw = payload["response"]
    try:
        sheet = json.loads(raw)
        # The constrained schema returns arrays. Joined back to the
        # comma-separated strings every other reader in this project emits, so a
        # routed sheet is interchangeable with a drafted one and `sheet.py adopt`
        # needs no branch.
        sheet = {
            field: ", ".join(value) if isinstance(value, list) else value
            for field, value in sheet.items()
        }
        # **The mapper runs on the model's free text, not on a grammar's
        # output.** That is the whole point of `tagmap`: generation stays
        # unconstrained so the model writes what it means, and the mapping to
        # canonical vocabulary happens afterwards by shared WORDS rather than by
        # shared token prefix.
        if match is not None:
            from prototype.tagmap import map_sheet

            sheet = map_sheet(sheet, match)
        return sheet
    except json.JSONDecodeError as error:
        # **Say which failure this is.** A truncated sheet and a malformed one look
        # identical in a `JSONDecodeError`, and only the first is fixed by raising
        # the token budget. `done_reason` is Ollama's own answer to that question.
        raise SystemExit(
            f"{model} returned unparseable JSON ({error}).\n"
            f"  done_reason: {payload.get('done_reason')}\n"
            f"  eval_count:  {payload.get('eval_count')}\n"
            f"  raw tail:    ...{raw[-120:]!r}"
        ) from error


def absence_leak(sheet: dict, known: dict) -> list[str]:
    """Return the tags that carry negation and are not real Danbooru tags.

    Two conditions, and both are required. `no bra` reads like a negation and is a
    canonical tag with 93,761 posts, so it is a positive the generator draws
    correctly. `not visible` is neither canonical nor a tag, and F44 measured what
    it does to a render.
    """
    leaks = []
    for field in ORDER:
        for tag in tags(sheet.get(field, "")):
            lowered = tag.lower()
            if tag not in known and any(word in lowered for word in ABSENCE):
                leaks.append(f"{field}={tag!r}")
    return leaks


def score(sheets: dict[str, dict], label: str, known: dict) -> dict:
    """Print and return one router's scorecard against the reviewed sheets."""
    import statistics

    per: dict[str, list[float]] = {f: [] for f in SCORED}
    invented: list[tuple[str, str, str]] = []
    leaks: list[tuple[str, str]] = []
    for sid, sheet in sheets.items():
        reference = fields_of(sid)
        for field in ORDER:
            for tag in tags(sheet.get(field, "")):
                if tag not in known:
                    invented.append((sid, field, tag))
        for leak in absence_leak(sheet, known):
            leaks.append((sid, leak))
        for field in SCORED:
            want = tags(reference[field])
            if want:
                per[field].append(len(want & tags(sheet.get(field, ""))) / len(want))

    means = {f: statistics.mean(v) for f, v in per.items() if v}
    total = sum(len(tags(s.get(f, ""))) for s in sheets.values() for f in ORDER)
    result = {
        "mean": statistics.mean(means.values()) if means else 0.0,
        "per_field": means,
        "tags": total,
        "invented": len(invented),
        "absence_leaks": len(leaks),
        "subjects": len(sheets),
    }

    print(f"\n=== {label} · {len(sheets)} subjects ===")
    for field in SCORED:
        if field in means:
            print(f"  {field:20s} {means[field]:.2f}")
    print(f"  {'MEAN (7 scored)':20s} {result['mean']:.3f}")
    print(f"  {total} tags · {len(invented)} not in selected_tags.csv · ", end="")
    print(f"{len(leaks)} absence leaks")
    for sid, field, tag in invented[:8]:
        print(f"      invented  {sid} {field}: {tag}")
    for sid, leak in leaks[:8]:
        print(f"      LEAK      {sid} {leak}")
    return result


SHEET_STYLE = """
:root { color-scheme: dark; }
body { margin: 0; padding: 24px; background: #14161a; color: #e6e8ec;
       font: 14px/1.55 ui-sans-serif, system-ui, -apple-system, sans-serif; }
h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
p.sub { margin: 0 0 8px; color: #9aa1ad; }
p.legend { margin: 0 0 20px; color: #9aa1ad; font-size: 12px; max-width: 1180px; }
table { border-collapse: collapse; width: 100%; table-layout: fixed; }
th, td { padding: 5px 9px; vertical-align: top; }
thead th { position: sticky; top: 0; z-index: 2; background: #14161a;
           text-align: left; border-bottom: 1px solid #2a2f37; font-size: 12px; }
thead th.m { color: #7ee7d0; } thead th.q { color: #7fb2ff; }
thead th.f { color: #c98bff; }
thead th.c { color: #7ee787; }
/* One row per FIELD, so the three sheets share it and cannot drift apart. */
tr.field td, tr.field th { border-top: 1px solid #1a1d22; }
tr.first td, tr.first th { border-top: 2px solid #2a2f37; }
th.subject { width: 7%; text-align: left; font-size: 13px; font-weight: 600;
             vertical-align: top; border-right: 1px solid #2a2f37; }
td.photo { width: 11%; border-right: 1px solid #2a2f37; }
img { display: block; width: 100%; height: auto; border-radius: 6px;
      background: #0d0f12; position: sticky; top: 56px; }
a { text-decoration: none; }
th.fname { width: 8%; text-align: left; font-weight: 400; color: #7b828c;
           font-size: 11.5px; border-right: 1px solid #2a2f37; }
th.fname.scored { color: #ffd479; }
td.col { width: 17.5%; }
.tag { display: inline-block; padding: 0 6px; margin: 0 2px 2px 0;
       border-radius: 3px; font: 11.5px/1.55 ui-monospace, Menlo, monospace;
       background: #1d2127; color: #aeb4be; }
.tag.hit { background: #1e3325; color: #7ee787; }
.tag.slot { background: #3a1f22; color: #ff9f9f; }
.tag.dead { background: #2b2233; color: #cba6f7; text-decoration: underline dotted; }
.empty { color: #454b54; font-size: 11px; }
tr.total td { color: #9aa1ad; font-size: 11.5px; padding-bottom: 14px; }
tr.total td b { color: #e6e8ec; }
"""

# Fields whose canonical vocabulary is small and derivable, with the size of each
# set. **This is the per-field enum N40 proposes, used here only to COLOUR the
# page** -- a tag outside its field's set is marked, which is what makes
# wrong-slot errors visible as a class rather than as individual oddities.
# Deriving them properly is the open work; `marks` below catches `scarf` because
# it contains `scar`, which is exactly why a keyword rule is not enough.
FIELD_SHAPES = {
    "count": lambda t: t in {"1girl", "1boy", "solo", "2girls", "multiple girls"},
    "hair colour": lambda t: t.endswith(" hair"),
    "eye colour": lambda t: t.endswith(" eyes"),
    "gaze": lambda t: t.startswith("looking ") or t in {"eye contact", "looking away"},
    "framing": lambda t: (
        t
        in {
            "cowboy shot",
            "full body",
            "upper body",
            "portrait",
            "close-up",
            "lower body",
            "from above",
            "from below",
            "from side",
            "from behind",
            "profile",
            "dutch angle",
            "feet out of frame",
        }
    ),
    "body shape": lambda t: "breasts" in t or "hips" in t or "waist" in t,
}


def router_sheet(out: Path | None = None) -> Path:
    """Build the photograph / Qwen / Claude comparison page.

    **Three colours, three different failures**, because lumping them together is
    what made the first scorecard read as "Qwen is bad at this" when it is not:

    - **green** -- the tag is in the reviewed baseline for that field. Agreement.
    - **violet** -- not a real Danbooru tag. F28's failure mode, and the one the
      enum grammar removed entirely: the constrained column has none.
    - **red** -- a real tag in the WRONG FIELD. `gaze: front ponytail`,
      `expression: calico`, `age band: yandere` are all genuine Danbooru
      vocabulary in a slot that cannot mean them. **This is the whole remaining
      gap**, and it is the one a shared enum cannot close because it constrains
      the vocabulary without constraining the field.

    Only fields whose canonical set is small enough to state are checked for
    slotting -- `clothes`, `accessories` and `background` are open-ended, so an
    unexpected tag there is a disagreement rather than a category error.
    """
    import html as html_mod

    from prototype.joycaption import thumb
    from prototype.sheet import photo_for

    known = vocabulary()
    subjects = sorted(path.stem for path in CAPTIONS.glob("*.txt"))
    page = out or EVAL / "router_tags.html"
    thumbs = page.parent / "router_thumbs"
    up = "../" * len(page.parent.parts)

    columns = [
        ("qwen3_8b_fewshot_matched", "Qwen3-8B · few-shot + tag mapper", "m"),
        ("qwen3_8b_constrained8106", "Qwen3-8B · enum grammar", "q"),
        ("qwen3_8b", "Qwen3-8B · unconstrained", "f"),
    ]

    def chips(sheet: dict, base: dict, field: str) -> tuple[str, int, int, int]:
        """Return one field's chips for one sheet, plus its three counters."""
        mine = tags(sheet.get(field, ""))
        theirs = tags(base.get(field, ""))
        cells, dead, slot, hit = [], 0, 0, 0
        for tag in sorted(mine):
            if tag in theirs:
                kind = " hit"
                hit += 1
            elif tag not in known:
                kind = " dead"
                dead += 1
            elif field in FIELD_SHAPES and not FIELD_SHAPES[field](tag):
                kind = " slot"
                slot += 1
            else:
                kind = ""
            cells.append(f'<span class="tag{kind}">{html_mod.escape(tag)}</span>')
        return "".join(cells) or '<span class="empty">&mdash;</span>', hit, dead, slot

    sources = [(name, DRAFTS / directory) for directory, name, _ in columns]
    sources.append(("Claude, by hand", INCUMBENT))

    rows = []
    for sid in subjects:
        base = fields_of(sid)
        sheets = []
        for _, directory in sources:
            path = directory / f"{sid}.json"
            sheets.append(json.loads(path.read_text()) if path.exists() else {})

        # **The union, in ORDER.** Every column renders every field any of them
        # filled, so the three sheets share one row per field and a long `pose`
        # in one column cannot push `framing` out of alignment in the others.
        # That was the defect: the field label was repeated per column, so
        # nothing made the labels line up.
        present = [
            field
            for field in ORDER
            if tags(base[field]) or any(tags(s.get(field, "")) for s in sheets)
        ]
        want = sum(len(tags(base[f])) for f in SCORED if tags(base[f]))
        totals = [[0, 0, 0] for _ in sheets]

        art = thumb(Path(photo_for(sid)), thumbs, sid)
        image = (
            f'<a href="{html_mod.escape(up + photo_for(sid))}">'
            f'<img src="{html_mod.escape(art)}" loading="lazy" alt=""></a>'
            if art
            else '<span class="empty">no photograph</span>'
        )
        span = len(present) + 1

        for index, field in enumerate(present):
            cells = []
            for position, sheet in enumerate(sheets):
                body, hit, dead, slot = chips(sheet, base, field)
                if field in SCORED:
                    totals[position][0] += hit
                totals[position][1] += dead
                totals[position][2] += slot
                cells.append(f'<td class="col">{body}</td>')
            lead = ""
            if index == 0:
                lead = (
                    f'<th class="subject" rowspan="{span}">'
                    f"{html_mod.escape(sid)}</th>"
                    f'<td class="photo" rowspan="{span}">{image}</td>'
                )
            mark = " scored" if field in SCORED else ""
            first = " first" if index == 0 else ""
            rows.append(
                f'<tr class="field{first}">{lead}'
                f'<th class="fname{mark}">{field}</th>' + "".join(cells) + "</tr>"
            )

        summary = []
        for position, (_, directory) in enumerate(sources):
            hit, dead, slot = totals[position]
            extra = (
                ""
                if directory == INCUMBENT
                else f" · <b>{dead}</b> not real · <b>{slot}</b> wrong slot"
            )
            summary.append(f"<td><b>{hit}/{want}</b> scored{extra}</td>")
        rows.append(
            '<tr class="total"><th class="fname"></th>' + "".join(summary) + "</tr>"
        )

    page.write_text(
        "<!doctype html>\n<html><head><meta charset='utf-8'>"
        "<title>Qwen vs Claude &middot; the router</title>"
        f"<style>{SHEET_STYLE}</style></head><body>"
        "<h1>The router: Qwen3-8B against Claude, same prose in</h1>"
        f"<p class='sub'>{len(rows)} photographs &middot; every column built from "
        "the <b>same five <code>descriptive</code> captions</b> in "
        "<code>captions/descriptive/</code> &middot; temperature 0, seed 1 &middot; "
        "scored against the operator's reviewed sheet</p>"
        "<p class='legend'>Three colours because there are three different "
        "failures, and lumping them together is what made the first scorecard read "
        'as <i>"Qwen is bad at this"</i> when it is not. '
        "<span class='tag hit'>green</span> = the reviewed baseline has this tag in "
        "this field. <span class='tag dead'>violet</span> = not a real Danbooru tag "
        "&mdash; F28's failure mode, and the grammar column has <b>none</b>. "
        "<span class='tag slot'>red</span> = a <b>real tag in the wrong field</b>: "
        "<code>gaze: front ponytail</code>, <code>expression: calico</code> and "
        "<code>age band: yandere</code> are all genuine Danbooru vocabulary in a "
        "slot that cannot mean them. <b>Red is the entire remaining gap</b>, and a "
        "shared enum cannot close it &mdash; it constrains the vocabulary without "
        "constraining the field. Only fields with a small statable set are "
        "slot-checked; <code>clothes</code>, <code>accessories</code> and "
        "<code>background</code> are open-ended, so an unexpected tag there is a "
        "disagreement and not a category error. Amber field names are the seven "
        "scored criteria.</p>"
        "<table><thead><tr><th>subject</th><th>photograph</th><th>field</th>"
        + "".join(f"<th class='{c}'>{n}</th>" for _, n, c in columns)
        + "<th class='c'>Claude, by hand &mdash; the incumbent</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></body></html>\n"
    )
    return page


def main() -> None:
    """Route the captions with a model, or score whatever is already routed."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default=None, help="the Ollama model to route with")
    p.add_argument("--host", default=HOST)
    p.add_argument("--drafts", type=Path, default=DRAFTS)
    p.add_argument("--schema", action="store_true", help="print the briefing")
    p.add_argument(
        "--constrain",
        action="store_true",
        help="restrict output to real Danbooru tags with an enum grammar",
    )
    p.add_argument("--enum-size", type=int, default=ENUM_SIZE)
    p.add_argument("--fewshot", action="store_true", help="include two worked examples")
    p.add_argument(
        "--match",
        action="store_true",
        help="map the model's free text onto canonical tags (prototype/tagmap.py)",
    )
    p.add_argument("--score", action="store_true", help="score every routed set")
    p.add_argument(
        "--sheet", action="store_true", help="build the Qwen-vs-Claude HTML table"
    )
    args = p.parse_args()

    subjects = sorted(path.stem for path in CAPTIONS.glob("*.txt"))
    if not subjects:
        raise SystemExit(f"no captions at {CAPTIONS}")

    if args.sheet:
        print(router_sheet())
        return

    if args.schema:
        print(briefing("<the caption goes here>"))
        print(f"\nSchema: {json.dumps(schema())}")
        print(f"\nSubjects ({len(subjects)}): {', '.join(subjects)}")
        return

    known = vocabulary()

    if args.model:
        name = args.model.replace(":", "_").replace("/", "_")
        if args.constrain:
            name += f"_constrained{args.enum_size}"
        if args.fewshot:
            name += "_fewshot"
        if args.match:
            name += "_matched"
        out = args.drafts / name
        out.mkdir(parents=True, exist_ok=True)
        if args.constrain:
            print(f"  grammar over the {args.enum_size} commonest tags")
        for sid in subjects:
            # Resume rather than restart. A constrained subject costs ~70s, and
            # the first run died on the fourth of five -- re-rendering the three
            # that succeeded would have been four minutes to reproduce bytes
            # already on disk.
            if (out / f"{sid}.json").exists():
                print(f"  {sid:22s} skip, already routed")
                continue
            prose = (CAPTIONS / f"{sid}.txt").read_text().strip()
            sheet = route(
                prose,
                args.model,
                args.host,
                known if args.constrain else None,
                args.enum_size,
                args.fewshot,
                known if args.match else None,
            )
            (out / f"{sid}.json").write_text(json.dumps(sheet, indent=2) + "\n")
            missing = [f for f in ORDER if f not in sheet]
            note = f" MISSING {missing}" if missing else ""
            print(f"  {sid:22s} {len(json.dumps(sheet))} chars{note}")
        print(f"\nwrote {out}/")

    if args.model or args.score:
        boards = {}
        incumbent = {
            sid: json.loads((INCUMBENT / f"{sid}.json").read_text())
            for sid in subjects
            if (INCUMBENT / f"{sid}.json").exists()
        }
        if incumbent:
            boards["Claude, by hand (the incumbent)"] = score(
                incumbent, "Claude, by hand — the incumbent", known
            )
        for directory in sorted(args.drafts.glob("*")):
            if not directory.is_dir():
                continue
            routed = {
                sid: json.loads((directory / f"{sid}.json").read_text())
                for sid in subjects
                if (directory / f"{sid}.json").exists()
            }
            if routed:
                boards[directory.name] = score(routed, directory.name, known)

        print("\n=== the table ===")
        print(
            f"  {'router':34s} {'mean':>6s} {'tags':>6s} {'invented':>9s} {'leaks':>6s}"
        )
        for name, board in sorted(boards.items(), key=lambda kv: -kv[1]["mean"]):
            print(
                f"  {name:34s} {board['mean']:6.3f} {board['tags']:6d} "
                f"{board['invented']:9d} {board['absence_leaks']:6d}"
            )
        print("\n  `invented` is F28's failure mode; `leaks` is F44's, and a leak")
        print("  is worse than an invented tag because the generator draws it.")


if __name__ == "__main__":
    main()
