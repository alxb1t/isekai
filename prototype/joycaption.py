#!/usr/bin/env python3
"""PROTOTYPE — N32/N33: the pinned bytes of the open reader, and proof it can see.

Round 4's question is **reproducibility, not quality**. The reader that turns a
photograph into a criteria sheet is an agent session: it scores 0.78 and it is not
reproducible by anyone without the transcript that produced it. `notes/READER.md`
surveyed the open candidates and `notes/JOYCAPTION.md` is the trial plan, with its
bar stated before anything was downloaded.

**This file is that trial's seam.** N32 pinned and verified; N33 hosts the model
and proves it can see; N34 grows this into the client that writes drafts. Kept in
one file because they are one seam — the thing that turns a photograph into
`<id>.json` — and split across three tasks because each is separately falsifiable.

### Why the hash is streamed, and it is not a micro-optimisation

`criteria_eval.verified()` does `path.read_bytes()`, which is correct there: the
WD14 tagger is 467 MB. **The Q4_K quant is 4.92 GB on a machine with 16 GiB of
RAM**, and the projector has to fit beside it. Reading it whole to hash it is a
6% chance of swapping to prove a digest. So this is the same guard, chunked.

It is a separate function from `criteria_eval.verified()` rather than a shared
one for the reason that file already states: `isekai.eval_models.resolve`
resolves against the **tracked** manifest and correctly refuses what that file
does not declare. Weakening a real guard so a prototype can borrow it trades a
control for a convenience.

### The sight gate, and why "describe this photograph" is not one

**A LLaVA-family model without its vision projector loads, answers fluently, and
cannot see the image.** `READER.md` records two of the three most-cited
quantisations shipping no `mmproj`; `JOYCAPTION.md` §9 records the source
repository's own README naming the 16 GB full-precision *text* model as the
projector. Both failures are silent, and **a digest cannot catch either** — it
only proves the file is the file we pinned.

Nor can a plausible caption. A blind 8B Llama asked to describe a portrait writes
a portrait, because that is what the prompt implies. **So the gate has to be a
question whose answer varies with the image and cannot be inferred from the
prompt**, scored against ground truth this project already reviewed by hand:

    GATE 1  eye colour, ten synthetic portraits, against their reviewed sheets
            four classes on this set (brown 4 · green 3 · blue 2 · grey 1), so a
            blind model's best constant answer is `brown` and scores 4/10.
            PASS at >= 8/10.

    GATE 2  sex, seventeen real photographs, against their sheets' `count` tag
            14 female · 3 male. A blind model's best constant answer is `female`
            and scores 14/17 overall -- and **0/3 on the men**, which is the
            whole point of the gate.
            PASS requires 3/3 on the men AND >= 12/14 on the women.

**Both pass conditions are written here before the gate was first run**, which is
the only reason they mean anything (F1 is this project's record of doing it the
other way). Gate 2 is the decisive one: a constant answer clears its aggregate
and fails its stated condition, so the aggregate is deliberately not the bar.

### The transport, and the dependency rule it respects

**The HTTP call is stdlib `urllib` against a localhost port** — no OpenAI SDK, no
`ollama` package, which is what `JOYCAPTION.md` §2 meant by hosting keeping
`CLAUDE.md`'s *deps minimal and human-gated* rule intact. Downscaling uses PIL,
which is **already** in this branch's `[eval]` extra and which `style_axis.py`
reads every render through, so it adds nothing. That matters: N30's real
photographs are 21-28 MB each, and F41 measured the uploads rather than the GPU
making 34 renders take 27 minutes.

Sampling is pinned — `temperature 0`, a fixed `seed`. A reader whose output moves
between runs cannot replace a transcript on the grounds of reproducibility.

    PYTHONPATH=. uv run --extra eval python prototype/joycaption.py --verify
    PYTHONPATH=. uv run --extra eval python prototype/joycaption.py --see
"""

import argparse
import base64
import hashlib
import io
import json
import urllib.error
import urllib.request
from collections.abc import Container
from pathlib import Path

from prototype.sheet import fields_of
from prototype.vlm_reader import PHOTOS, SUBJECTS

MODELS = Path("models")
MANIFEST = Path("prototype/styles/joycaption_models.json")

# 1 MiB. Large enough that the syscall overhead is noise against 4.92 GB, small
# enough that the resident set does not matter on a 16 GiB machine.
CHUNK = 1 << 20

QUANT = "joycaption/Llama-Joycaption-Beta-One-Hf-Llava-Q4_K.gguf"
MMPROJ = "joycaption/llama-joycaption-beta-one-llava-mmproj-model-f16.gguf"

# Built by `ollama create` from the two pinned files. Ollama's blob store is
# content-addressed, so its two layers carry OUR digests -- checked in N33.
HOST = "http://127.0.0.1:11434"
MODEL = "joycaption-beta-one-q4k"

# The vision tower is SigLIP2 at patch14-384, so the pixels beyond this are
# thrown away by the encoder anyway. 1024 leaves eye colour legible and turns a
# 21 MB upload into a ~200 KB one.
LONG_SIDE = 1024

# **There are two input trees and this is a real trap.** Round 1/2's baseline and
# the tuned-on ten live at the REPOSITORY ROOT's `inputs/`; round 3's portfolio,
# pose and real sets live under `prototype/inputs/`. The ten are therefore taken
# from `vlm_reader.PHOTOS`, which is the authority the incumbent's 0.78 was
# measured through -- guessing `prototype/inputs/synthetic` found three of ten and
# looked exactly like seven deleted photographs.
REAL = Path("prototype/inputs/real")

EYE_PROMPT = (
    "Look at this photograph. What colour are the subject's eyes? "
    "Answer with exactly one word."
)
SEX_PROMPT = (
    "Look at this photograph. Is the person male or female? "
    "Answer with exactly one word: male or female."
)

# **Verbatim from the project's own README**, read 2026-09-12, and it must stay
# verbatim: `READER.md` records that JoyCaption's "modes" are prompt strings and
# not an API, so the mode IS this string. Paraphrasing it would silently test a
# different mode and the result would not be JoyCaption's Danbooru mode at all.
#
# The project's own note on it: **"This mode has lower accuracy and overall
# performance than the other modes."** Recorded before the probe ran.
DANBOORU_PROMPT = (
    "Generate only comma-separated Danbooru tags (lowercase_underscores). "
    "Strict order: `artist:`, `copyright:`, `character:`, `meta:`, then general "
    "tags. Include counts (1girl), appearance, clothing, accessories, pose, "
    "expression, actions, background. Use precise Danbooru syntax. No extra text."
)

# The operator's ten, named explicitly on 2026-09-12. A deliberately small set:
# the question here is what the raw dump LOOKS like, which is read by eye, and
# ten is what one person can actually read.
#
# **Subject ids, not paths, and that is the fix for a real bug.** Keyed by path
# first, the three synthetics resolved to a stem of `synthetic_portrait_00003_`
# where their sheet and draft are filed under `00003` -- so the incumbent column
# came out empty for exactly those three and populated for the seven real ones.
# `sheet.photo_for` is the repository's own id-to-photograph resolver: it knows
# round 2's generator filename is the exception, searches four extensions, and
# prefers `prototype/inputs/` over the root tree, which is the copy the operator
# named. One id now reaches the pixels, the sheet AND the draft.
BOORU_SET = (
    "00003",
    "00035",
    "00072",
    "cowboy_shot_1",
    "cowboy_shot_3",
    "face_1",
    "face_4",
    "ful_height_1",
    "full_height_2",
    "male_cowboy_shot_1",
)

# **The two modes the project itself calls most accurate**, verbatim from its
# README, read 2026-09-12: "`Descriptive Caption` and `Straightforward` are the
# most useful, with the other modes being interesting but a little less stable."
# Danbooru mode is the one it flags as "lower accuracy" -- which is what the
# probe measured, so this is confirmation rather than a new hypothesis.
#
# Both are run because the comparison between them is the finding. STRAIGHTFORWARD
# is the one engineered for this job -- concrete colour, shape, texture and
# spatial relationships, mood and speculation explicitly excluded -- where
# DESCRIPTIVE covers more and editorialises. Which matters more for a router
# feeding sixteen Danbooru fields is exactly the open question.
DESCRIBE_PROMPTS = {
    "straightforward": (
        "Write a straightforward caption for this image. Begin with the main "
        "subject and medium. Mention pivotal elements—people, objects, scenery—"
        "using confident, definite language. Focus on concrete details like "
        "color, shape, texture, and spatial relationships. Show how elements "
        "interact. Omit mood and speculative wording. If text is present, quote "
        "it exactly. Note any watermarks, signatures, or compression artifacts. "
        "Never mention what's absent, resolution, or unobservable details. Vary "
        "your sentence structure and keep the description concise, without "
        "starting with \u201cThis image is\u2026\u201d or similar phrasing."
    ),
    "descriptive": "Write a long detailed description for this image.",
}

# Gate 1's floor: the modal answer on this set is `brown` at 4 of 10.
GATE1_PASS = 8
# Gate 2's floor is deliberately not an aggregate -- see the module docstring.
GATE2_MEN = 3
GATE2_WOMEN = 12


def manifest() -> dict:
    """Return the pinned manifest, or say where it should be."""
    if not MANIFEST.exists():
        raise SystemExit(f"{MANIFEST} is missing; N32 writes it before any download")
    return json.loads(MANIFEST.read_text())


def digest(path: Path) -> str:
    """Return `path`'s sha256, read a chunk at a time.

    `hashlib.file_digest` would do this in one call, and is not used: it landed in
    3.11 and this repository's stdlib-only habit is worth more than four lines.
    """
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(CHUNK):
            sha.update(block)
    return sha.hexdigest()


def verified(dest: str, models_dir: Path = MODELS) -> Path:
    """Return the artifact's path, having checked its bytes against the manifest.

    Size is checked before the digest **because it is free and it is the failure
    that actually happens**: an interrupted 4.92 GB download leaves a short file,
    and saying so takes no time where hashing it takes half a minute to reach the
    same conclusion less clearly.
    """
    entry = next((e for e in manifest()["entries"] if e["dest"] == dest), None)
    if entry is None:
        raise SystemExit(f"{MANIFEST} does not declare {dest}")
    path = models_dir / dest
    if not path.exists():
        raise SystemExit(f"{path} is missing; sources are in {MANIFEST}")
    size = path.stat().st_size
    if size != entry["bytes"]:
        short = " (a truncated download, most likely)" if size < entry["bytes"] else ""
        raise SystemExit(
            f"{path}: {size:,} bytes != the manifest's {entry['bytes']:,}{short}"
        )
    found = digest(path)
    if found != entry["sha256"]:
        raise SystemExit(f"{path}: sha256 {found} != the manifest's {entry['sha256']}")
    return path


def encoded(photo: Path, long_side: int = LONG_SIDE) -> str:
    """Return `photo` downscaled to `long_side` and base64-encoded, as JPEG.

    Re-encoded rather than passed through **because the payload is the cost**, not
    the pixels: F41's photographs are 21-28 MB and base64 adds a third again.
    JPEG at 92 is visually lossless at this scale and the encoder sees 384px.
    """
    from PIL import Image

    with Image.open(photo) as image:
        image = image.convert("RGB")
        scale = long_side / max(image.size)
        if scale < 1:
            size = (round(image.width * scale), round(image.height * scale))
            image = image.resize(size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=92)
    return base64.b64encode(buffer.getvalue()).decode()


def ask(
    prompt: str,
    photo: Path,
    model: str = MODEL,
    host: str = HOST,
    predict: int = 24,
) -> str:
    """Return the model's answer about `photo`, sampling pinned to be repeatable.

    `stream: false` so one request is one answer. `predict` defaults low because
    the sight gates ask for one word and an 8B Llama will happily write a
    paragraph past the answer, which costs seconds per photograph. **A tag dump
    needs far more**, and truncating one would look exactly like a model that
    saw less than it did -- so the booru probe raises it rather than sharing it.
    """
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "images": [encoded(photo)],
            "stream": False,
            "options": {"temperature": 0, "seed": 1, "num_predict": predict},
        }
    ).encode()
    request = urllib.request.Request(
        f"{host}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read())["response"].strip()
    except urllib.error.URLError as error:
        raise SystemExit(
            f"{host} did not answer ({error}).\n"
            "Is the Ollama server running, and is the model created?\n"
            f"  ollama create {model} -f models/joycaption/Modelfile"
        ) from error


def said(answer: str, want: str) -> bool:
    """Return whether `answer` contains the ground-truth word `want`.

    Substring rather than equality, and on purpose: the prompts ask for one word
    and this model does not reliably give one. **A looser match makes the gate
    harder to fail, so it is the conservative direction for a sight test** — the
    risk being guarded against is calling a blind model sighted, and a blind model
    does not accidentally contain the right colour ten times out of ten.
    """
    return want in answer.lower()


def gate_one(model: str, host: str) -> tuple[int, int]:
    """Ask eye colour of the ten synthetic portraits. Returns (hits, total)."""
    print("\n=== GATE 1 · eye colour, ten synthetic portraits ===")
    print(f"  a blind model's best constant answer scores 4/10. Pass: {GATE1_PASS}/10")
    hits = 0
    for sid in SUBJECTS:
        photo = PHOTOS / f"synthetic_portrait_{sid}_.png"
        want = fields_of(sid)["eye colour"].replace(" eyes", "").strip()
        answer = ask(EYE_PROMPT, photo, model, host)
        good = said(answer, want)
        hits += good
        print(f"  {'OK ' if good else '   '} {sid}  want {want:6s}  said {answer!r}")
    print(f"  → {hits}/{len(SUBJECTS)}")
    return hits, len(SUBJECTS)


def gate_two(model: str, host: str) -> tuple[int, int, int, int]:
    """Ask the sex of the seventeen real photographs. Returns men/women hits."""
    print("\n=== GATE 2 · sex, seventeen real photographs ===")
    print("  a blind model scores 14/17 overall and 0/3 on the men.")
    print(f"  Pass: {GATE2_MEN}/3 men AND {GATE2_WOMEN}/14 women — NOT the aggregate")
    men = women = men_hit = women_hit = 0
    for photo in sorted(REAL.iterdir()):
        if photo.name.startswith("."):
            continue
        sid = photo.stem
        want = "male" if "1boy" in fields_of(sid)["count"] else "female"
        answer = ask(SEX_PROMPT, photo, model, host)
        # `female` contains `male`, so a male answer must not merely match.
        got = "female" if "female" in answer.lower() else "male"
        good = got == want
        if want == "male":
            men += 1
            men_hit += good
        else:
            women += 1
            women_hit += good
        print(f"  {'OK ' if good else '   '} {sid:24s} want {want:6s} said {answer!r}")
    print(f"  → men {men_hit}/{men} · women {women_hit}/{women}")
    return men_hit, men, women_hit, women


def booru(model: str, host: str) -> None:
    """Dump JoyCaption's own Danbooru tag mode over the operator's ten photographs.

    **A probe, not N35.** N35 scores a run against the reviewed sheets with
    `vlm_reader.py`; this prints the raw dump so the operator can read what the
    mode actually produces before any of it is routed into sixteen fields. The
    vocabulary column is the one measurement here, and it is free:
    `sheet.vocabulary()` is the same `selected_tags.csv` gate every prompt in this
    project already passes through, and **F28's law is that a tag outside it does
    nothing at all** -- so a dump's canonical share is the ceiling on how much of
    it could ever reach a render.

    Raw output is written to `derived/<UTC-date>/n35_booru_probe/` because it is
    free to regenerate and because reading ten dumps off a terminal scroll is not
    reading them.
    """
    from prototype.paths import derived_dir
    from prototype.sheet import vocabulary

    known = vocabulary()
    out = derived_dir() / "n35_booru_probe"
    out.mkdir(parents=True, exist_ok=True)
    print(f"\n=== JoyCaption Danbooru tag mode · {len(BOORU_SET)} photographs ===")
    print("  the project's own note: this mode has LOWER accuracy than the others")
    print(f"  raw dumps → {out}/")

    from prototype.sheet import photo_for

    rows = []
    for sid in BOORU_SET:
        photo = Path(photo_for(sid))
        if not photo.exists():
            raise SystemExit(f"no photograph for {sid} (resolved to {photo})")
        answer = ask(DANBOORU_PROMPT, photo, model, host, predict=512)
        (out / f"{sid}.txt").write_text(answer + "\n")

        # Normalised the way `JOYCAPTION.md` §6 says a client must: underscores
        # to spaces (F32 measured underscores 0.013 worse, six times the
        # determinism floor). Counted, not applied -- the raw text is what ships
        # to disk, so the cleanup can be judged rather than assumed.
        tags = [t.strip() for t in answer.replace("_", " ").split(",") if t.strip()]
        meta = [t for t in tags if ":" in t or "(medium)" in t]
        good = [t for t in tags if t in known and t not in meta]
        unknown = [t for t in tags if t not in known and t not in meta]
        rows.append((sid, len(tags), len(good), len(unknown), len(meta)))

        print(f"\n--- {sid}  ({photo.name})")
        print(f"    {answer}")
        if unknown:
            print(
                f"    NOT in selected_tags.csv ({len(unknown)}): {', '.join(unknown)}"
            )
        if meta:
            print(f"    meta/prefixed ({len(meta)}): {', '.join(meta)}")

    print("\n=== vocabulary, per photograph ===")
    print(f"  {'photo':26s} {'tags':>5s} {'canon':>6s} {'unknown':>8s} {'meta':>5s}")
    for name, total, good, unknown_n, meta_n in rows:
        print(f"  {name:26s} {total:5d} {good:6d} {unknown_n:8d} {meta_n:5d}")
    total = sum(r[1] for r in rows)
    canon = sum(r[2] for r in rows)
    share = canon / total if total else 0.0
    print(f"\n  {canon}/{total} tags are canonical Danbooru — {share:.0%}")
    print("  F28: a tag outside selected_tags.csv does nothing at all in a render.")


SHEET_STYLE = """
:root { color-scheme: dark; }
body { margin: 0; padding: 24px; background: #14161a; color: #e6e8ec;
       font: 14px/1.5 ui-sans-serif, system-ui, -apple-system, sans-serif; }
h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
p.sub { margin: 0 0 8px; color: #9aa1ad; }
p.prompt { margin: 0 0 20px; padding: 10px 12px; background: #0d0f12;
           border-left: 3px solid #ffd479; color: #c3c9d4; font-size: 13px;
           max-width: 960px; }
table { border-collapse: separate; border-spacing: 0; width: 100%; }
th, td { padding: 10px; vertical-align: top; }
thead th { position: sticky; top: 0; z-index: 2; background: #14161a;
           text-align: left; border-bottom: 1px solid #2a2f37; }
tbody tr + tr th, tbody tr + tr td { border-top: 1px solid #2a2f37; }
tbody th { text-align: left; font-weight: 600; white-space: nowrap;
           vertical-align: top; }
img { display: block; width: 220px; height: auto; border-radius: 6px;
      background: #0d0f12; }
td.tags { width: 34%; }
a { text-decoration: none; }
td.tags { font: 13px/1.9 ui-monospace, SFMono-Regular, Menlo, monospace; }
.tag { display: inline-block; padding: 1px 7px; margin: 0 3px 3px 0;
       border-radius: 4px; background: #1d2127; color: #cdd3dd; }
.tag.bad { background: #3a1f22; color: #ff9f9f; }
.tag.meta { background: #3a3320; color: #ffd479; }
.count { display: block; margin-top: 8px; color: #9aa1ad; font-size: 12px;
         font-family: ui-sans-serif, system-ui, sans-serif; }
.count b { color: #e6e8ec; }
.legend { margin: 0 0 20px; color: #9aa1ad; font-size: 12px; }
.missing { width: 220px; height: 140px; display: grid; place-items: center;
           color: #6b727d; background: #0d0f12; border-radius: 6px; }
"""


def describe(model: str, host: str) -> None:
    """Run both accurate caption modes over the probe set and write the prose.

    **Stage one of the two-stage the operator proposed**: an open, pinned, local
    model does the *seeing*, and a text-only model turns its prose into Danbooru
    tags. The cost case for that is weak on its own -- roughly a quarter off a
    per-photograph cost already measured in tenths of a cent. The real case is
    that **stage two may not need a vision model at all**, which is what takes
    the closed component off the perception and makes it pinnable.

    The prediction recorded before this first ran: a prose intermediate fixes
    every FORMAT and VOCABULARY error the Danbooru mode made -- dead tags,
    `photo (medium)`, `hands on hips` for `hands on own hips`, `shirt` for
    `tank top` -- and fixes NO perception error. `00003` and `00060` were called
    brown-eyed against reviewed sheets that say green, twice, by two different
    prompts. Prose cannot recover what the vision tower did not see.
    """
    from prototype.paths import derived_dir
    from prototype.sheet import photo_for

    for mode, prompt in DESCRIBE_PROMPTS.items():
        out = derived_dir() / f"n35_describe_{mode}"
        out.mkdir(parents=True, exist_ok=True)
        print(f"\n=== JoyCaption · {mode} · {len(BOORU_SET)} photographs ===")
        print(f"  → {out}/")
        for sid in BOORU_SET:
            photo = Path(photo_for(sid))
            if not photo.exists():
                raise SystemExit(f"no photograph for {sid} (resolved to {photo})")
            # 1024 tokens: a "long detailed description" runs well past the 512
            # a tag dump needs, and a caption truncated mid-sentence would be
            # scored as a reader that saw less than it did.
            answer = ask(prompt, photo, model, host, predict=1024)
            (out / f"{sid}.txt").write_text(answer + "\n")
            print(f"\n--- {sid}  ({len(answer.split())} words)")
            print(f"    {answer}")


def chips(values: list[str], known: Container[str]) -> tuple[str, int, int]:
    """Return (html, total, canonical) for one column's tags.

    Shared by both columns on purpose: **the colouring is the comparison.** Two
    renderers would let the two readers be judged by two rules, which is the
    whole failure mode `IDENTITY.md` §1 records for the earlier scoreboards.
    """
    import html as html_mod

    out = []
    canon = 0
    for tag in values:
        spaced = tag.replace("_", " ").strip()
        if not spaced:
            continue
        if ":" in spaced or "(medium)" in spaced:
            kind = " meta"
        elif spaced in known:
            kind = ""
            canon += 1
        else:
            kind = " bad"
        out.append(f'<span class="tag{kind}">{html_mod.escape(spaced)}</span>')
    return "".join(out), len(out), canon


def incumbent(sid: str) -> list[str] | None:
    """Return the agent session's draft for `sid`, flattened in field order.

    Flattened rather than shown per field, because the column beside it is a flat
    dump and **a comparison between two shapes is not a comparison.** The field
    structure is the incumbent's actual advantage and it is not lost -- it is in
    the JSON on disk, and N36 is where it gets scored.
    """
    from prototype.paths import draft_path
    from prototype.sheet import ORDER

    path = draft_path(sid)
    if not path.exists():
        return None
    draft = json.loads(path.read_text())
    return [
        tag.strip()
        for field in ORDER
        for tag in draft.get(field, "").split(",")
        if tag.strip()
    ]


def booru_sheet(out: Path | None = None) -> Path:
    """Build an HTML page of photograph beside raw Danbooru dump, from disk.

    **Reads the dumps rather than re-running the model**, which is the split
    `paths.py` is built around: the dump costs inference, the page costs a couple
    of seconds of CPU, so the page is free to rebuild and the dump is not. Bucketed
    under `derived/<UTC-date>/` for the same reason every other artifact here is.

    Non-canonical tags are marked red and `meta:`-prefixed ones amber, because
    **that is the whole reading of this page**: F28's law is that a tag outside
    `selected_tags.csv` does nothing at all, and `photo (medium)` does something
    worse than nothing -- it instructs an anime model to render a photograph.
    """
    import html as html_mod

    from prototype.paths import derived_dir
    from prototype.sheet import vocabulary

    known = vocabulary()
    dumps = derived_dir() / "n35_booru_probe"
    if not dumps.exists():
        raise SystemExit(f"no dumps at {dumps}; run --booru first")
    page = out or derived_dir() / "n35_booru_probe_sheet.html"
    thumbs = page.parent / f"{page.stem}_thumbs"

    # `BOORU_SET`'s paths are REPOSITORY-ROOT relative, so the climb out of the
    # page's directory is its full depth -- not depth minus one, which is the
    # off-by-one that produced `prototype/prototype/inputs/...` on the first
    # build. Derived from the page's own location rather than hardcoded, which is
    # the defect the 2026-09-10 housekeeping pass fixed across nine pages: a
    # `../..` literal breaks the moment a page moves a level deeper.
    up = "../" * len(page.parent.parts)

    from prototype.sheet import photo_for

    rows = []
    for sid in BOORU_SET:
        photo = Path(photo_for(sid))
        dump = dumps / f"{sid}.txt"
        if not dump.exists():
            continue
        raw = [t.strip() for t in dump.read_text().strip().split(",")]
        jc_html, jc_n, jc_canon = chips(raw, known)

        drafted = incumbent(sid)
        if drafted is None:
            cl_html, cl_n, cl_canon = '<div class="missing">no draft</div>', 0, 0
        else:
            cl_html, cl_n, cl_canon = chips(drafted, known)

        # Overlap on the NORMALISED form, because underscores are a client's job
        # and comparing `hands_on_hips` to `hands on own hips` as strings would
        # report a disagreement that is really two separate defects.
        jc_set = {t.replace("_", " ").strip() for t in raw if t.strip()}
        cl_set = {t.strip() for t in (drafted or [])}
        shared = len(jc_set & cl_set)

        art = thumb(photo, thumbs, sid)
        image = (
            f'<a href="{html_mod.escape(up + str(photo))}">'
            f'<img src="{html_mod.escape(art)}" loading="lazy" alt=""></a>'
            if art
            else '<div class="missing">no photograph</div>'
        )
        rows.append(
            f"<tr><th>{html_mod.escape(sid)}</th>"
            f"<td>{image}</td>"
            f'<td class="tags">{jc_html}'
            f'<span class="count"><b>{jc_n}</b> tags · '
            f"<b>{jc_canon}</b> canonical · "
            f"<b>{jc_n - jc_canon}</b> dead or meta · "
            f"<b>{shared}</b> shared</span></td>"
            f'<td class="tags">{cl_html}'
            f'<span class="count"><b>{cl_n}</b> tags · '
            f"<b>{cl_canon}</b> canonical · "
            f"<b>{cl_n - cl_canon}</b> dead or meta · "
            f"<b>{shared}</b> shared</span></td></tr>"
        )

    page.write_text(
        "<!doctype html>\n<html><head><meta charset='utf-8'>"
        "<title>JoyCaption · Danbooru tag mode</title>"
        f"<style>{SHEET_STYLE}</style></head><body>"
        "<h1>JoyCaption Beta One · Danbooru tag mode</h1>"
        f"<p class='sub'>{MODEL} at Q4_K, hosted on Ollama · temperature 0, seed 1 · "
        f"{len(rows)} photographs · raw dumps in <code>{dumps.name}/</code></p>"
        "<p class='prompt'>Generate only comma-separated Danbooru tags "
        "(lowercase_underscores). Strict order: <code>artist:</code>, "
        "<code>copyright:</code>, <code>character:</code>, <code>meta:</code>, then "
        "general tags. Include counts (1girl), appearance, clothing, accessories, "
        "pose, expression, actions, background. Use precise Danbooru syntax. No "
        "extra text.</p>"
        "<p class='legend'>Underscores shown as spaces, as a client must convert them "
        "(F32: underscores measured 0.013 worse, six times the determinism floor). "
        "<span class='tag bad'>red</span> = not in selected_tags.csv, so F28 says it "
        "does nothing in a render. <span class='tag meta'>amber</span> = meta or "
        "prefixed; <code>photo (medium)</code> is worse than useless — it instructs "
        "an anime model to render a photograph.</p>"
        "<p class='legend'><b>The right-hand column is the incumbent</b> — the agent "
        "session <code>vlm_reader.py --schema</code> briefs, flattened out of its "
        "sixteen fields so the two columns have the same shape. It scores 0.78 and is "
        "not reproducible without its transcript, which is the only reason JoyCaption "
        "is being trialled at all. <b>Caveat:</b> for the seven real subjects the "
        "reviewed sheet was seeded by <code>sheet.py adopt</code> from this very "
        "draft, so it is not an independent reference for them — only the three "
        "synthetics have an incumbent draft written independently of the sheet.</p>"
        "<table><thead><tr><th>subject</th><th>photograph</th>"
        "<th>JoyCaption · Danbooru tag mode</th>"
        "<th>Claude · the agent session (incumbent)</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></body></html>\n"
    )
    return page


# **Phase 1 of `JOYCAPTION.md` §4, in three arms.** The reader was never asked
# for the sixteen fields -- it was asked for a generic tag dump and then for
# prose -- and the fields it scored worst on are the ones nobody requested:
# `marks` 0.00 (the prose never says "freckles"), `framing` 0.30, `gaze` 0.56.
# So this is F36's law one level up: **most apparent reader failures are
# BRIEFING failures.** What it will not fix is perception; eye colour has come
# back 0.30 under two different prompts and is expected to stay there.
#
# Three arms because §8 named the fork and said not to resolve it by rewriting:
#   verbatim   `vlm_reader.INSTRUCTIONS` exactly as the agent gets it. The ONLY
#              arm directly comparable to the incumbent's 0.795, and deliberately
#              awkward -- it tells the reader to write JSON files to a directory,
#              which a captioner cannot do. That awkwardness is the honest cost
#              of a fair comparison, not a bug to smooth over.
#   fields     the same sixteen fields, shaped for a captioner: labelled lines,
#              no file I/O, no JSON. §8 says a rewrite is a second arm rather
#              than a correction, so it is one.
#   identity   ONLY the seven scored criteria -- `CRITERIA.md`'s identity bar is
#              6 of 7 with pose and hair silhouette mandatory, so these seven are
#              what identity is actually measured on. The shortest prompt of the
#              three, which matters: the model card warns instruction-following
#              is its weak point, and nine unscored fields are nine chances to
#              drift.
SCHEMA_ARMS = ("verbatim", "fields", "identity")


def schema_prompt(arm: str) -> str:
    """Return the briefing for one phase-1 arm."""
    from prototype.sheet import ORDER
    from prototype.vlm_reader import INSTRUCTIONS, SCORED

    if arm == "verbatim":
        return INSTRUCTIONS.format(
            fields="\n".join(f"- {f}" for f in ORDER),
            photos="the photograph attached to this message",
        )

    rules = (
        "Rules:\n"
        "- Every tag MUST be a real Danbooru tag, lowercase, spaces not "
        "underscores.\n"
        "- Describe THIS photograph, not the person in general.\n"
        "- Prefer the common tag over the precise-sounding one.\n"
        "- Leave a field blank ONLY if the photograph genuinely does not show it.\n"
        "- No quality tags, no style tags, no `photo (medium)`, no `artist:` or "
        "`copyright:` prefixes.\n"
        "- Output nothing but the lines themselves, one per field, in this order."
    )
    if arm == "fields":
        fields = "\n".join(f"{f}:" for f in ORDER)
        return (
            "Read this photograph and fill in every field below with "
            "comma-separated Danbooru tags.\n\n" + fields + "\n\n" + rules
        )

    fields = "\n".join(f"{f}:" for f in SCORED)
    return (
        "Read this photograph and fill in every field below with comma-separated "
        "Danbooru tags. These seven are what decides whether a stylised render is "
        "still the same person, so be specific and do not leave one blank if the "
        "photograph shows it at all. `marks` means freckles, moles, scars, "
        "tattoos and piercings.\n\n" + fields + "\n\n" + rules
    )


def schema(model: str, host: str, arms: tuple[str, ...] = SCHEMA_ARMS) -> None:
    """Brief JoyCaption with our own fields, in each arm, over the probe set."""
    from prototype.paths import derived_dir
    from prototype.sheet import photo_for

    for arm in arms:
        prompt = schema_prompt(arm)
        out = derived_dir() / f"n36_schema_{arm}"
        out.mkdir(parents=True, exist_ok=True)
        print(f"\n=== phase 1 · arm {arm!r} · {len(BOORU_SET)} photographs ===")
        print(f"  prompt is {len(prompt)} chars · → {out}/")
        for sid in BOORU_SET:
            photo = Path(photo_for(sid))
            if not photo.exists():
                raise SystemExit(f"no photograph for {sid} (resolved to {photo})")
            answer = ask(prompt, photo, model, host, predict=768)
            (out / f"{sid}.txt").write_text(answer + "\n")
            print(f"\n--- {sid}\n{answer}")


# The evaluation this file drives when `--eval` is passed. A directory rather
# than a date, because `paths.derived_dir()` means "today" and an evaluation is
# a named thing that may be re-scored on a later day.
EVAL = Path("prototype/evaluations/2026-09-12/descriptive_and_booru")

EVAL_SUBJECTS = (
    "cowboy_shot_1",
    "full_height_2",
    "face_4",
    "full_height_3",
    "00003",
)


def eval_prompts(evaluation: Path = EVAL) -> dict[str, str]:
    """Return the arm prompts parsed out of the evaluation's own `prompts.md`.

    **Parsed rather than duplicated in code, and that is the point.**
    `prompts.md` is the artifact the operator read and approved; a second copy in
    a Python constant is a second thing to keep in sync, and the first time they
    drift the run is no longer the run that was approved. So the reviewed
    document is the source of truth and this reads it.
    """
    import re

    source = evaluation / "prompts.md"
    if not source.exists():
        raise SystemExit(f"{source} is missing; it is the approved source of truth")
    found = {
        arm: body.strip()
        for _, arm, body in re.findall(
            r"## Arm (\d) · `(\w+)`.*?\n```\n(.*?)\n```", source.read_text(), re.S
        )
    }
    if set(found) != {"descriptive", "straightforward"}:
        raise SystemExit(f"{source}: expected two arms, parsed {sorted(found)}")
    return found


def eval_captions(model: str, host: str, evaluation: Path = EVAL) -> None:
    """Run both approved arms over the evaluation's five photographs."""
    from prototype.sheet import photo_for

    prompts = eval_prompts(evaluation)
    for arm, prompt in prompts.items():
        out = evaluation / "captions" / arm
        out.mkdir(parents=True, exist_ok=True)
        print(f"\n=== {arm} · {len(EVAL_SUBJECTS)} photographs ===")
        print(f"  prompt {len(prompt.split())} words, from prompts.md · → {out}/")
        for sid in EVAL_SUBJECTS:
            photo = Path(photo_for(sid))
            if not photo.exists():
                raise SystemExit(f"no photograph for {sid} (resolved to {photo})")
            answer = ask(prompt, photo, model, host, predict=1024)
            (out / f"{sid}.txt").write_text(answer + "\n")
            print(f"\n--- {sid}  ({len(answer.split())} words)\n{answer}")


RESULTS_STYLE = """
:root { color-scheme: dark; }
body { margin: 0; padding: 24px; background: #14161a; color: #e6e8ec;
       font: 14px/1.55 ui-sans-serif, system-ui, -apple-system, sans-serif; }
h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
p.sub { margin: 0 0 8px; color: #9aa1ad; }
p.legend { margin: 0 0 20px; color: #9aa1ad; font-size: 12px; max-width: 1200px; }
table { border-collapse: separate; border-spacing: 0; width: 100%;
        table-layout: fixed; }
th, td { padding: 8px; vertical-align: top; }
thead th { position: sticky; top: 0; z-index: 2; background: #14161a;
           text-align: left; border-bottom: 1px solid #2a2f37; font-size: 12px; }
thead th.o { color: #e6e8ec; } thead th.d { color: #7fb2ff; }
thead th.m { color: #7ee7d0; }
thead th.s { color: #ffd479; } thead th.r { color: #b98bff; }
thead th.b { color: #7ee787; }
tbody tr + tr th, tbody tr + tr td { border-top: 1px solid #2a2f37; }
tbody th { text-align: left; font-weight: 600; font-size: 13px; width: 8%; }
td { width: 15.6%; }
img { display: block; width: 100%; height: auto; border-radius: 6px;
      background: #0d0f12; }
td.photo img { outline: 2px solid #ffd479; outline-offset: -2px; }
a { text-decoration: none; }
.miss { display: grid; place-items: center; aspect-ratio: 3/4;
        color: #6b727d; background: #0d0f12; border-radius: 6px; font-size: 12px; }
.m { display: block; margin-top: 6px; font-size: 11.5px; color: #9aa1ad;
     font-variant-numeric: tabular-nums; }
.m b { color: #e6e8ec; }
.m .up { color: #7ee787; } .m .down { color: #ff9f9f; }
.tok { color: #c9a227; }
"""


def results_sheet(evaluation: Path = EVAL, out: Path | None = None) -> Path:
    """Build the five-column render comparison: photograph then the four arms.

    **The baseline column is the rightmost and it is the reference.** Every other
    column is read against it, and the per-render numbers underneath are the two
    style axes read at the PHOTOGRAPH's canvas -- F35's law, whose sign flipped
    when it was violated, so `load_canvas_pixels(path, canvas_for(photo))` and
    never `Image.open` at native size.

    Scored here rather than in `results.json` alone because the page is the
    instrument the operator actually reads (F30), and a number he has to open a
    second file to see is a number he will not check against the image beside it.
    """
    import html as html_mod

    from isekai.eval_backends import load_canvas_pixels
    from isekai.evaluate import canvas_for
    from prototype.sheet import photo_for
    from prototype.style_axis import style

    prompts = json.loads((evaluation / "prompts.json").read_text())
    renders = evaluation / "renders"
    page = out or evaluation / "results.html"
    thumbs = page.parent / "result_thumbs"
    up = "../" * len(page.parent.parts)

    # **`6_claude` supersedes `3_booru` where it exists, and only `00003` has
    # it.** One field of Claude's hand-routed sheet was corrected, so only that
    # subject was re-rendered -- spending a pod to reproduce four unchanged
    # prompts would have bought nothing. The column therefore reads "Claude's
    # sheet, as reviewed", which is true of all five with different provenance
    # for one of them, and `arm.json` beside each render records which.
    arms = (
        ("5_qwen", "5_qwen", "m"),
        ("3_booru", "booru", "r"),
        ("4_baseline", "baseline", "b"),
        ("1_descriptive", "descriptive", "d"),
        ("2_straightforward", "straightforward", "s"),
    )
    supersede = {"3_booru": "6_claude"}

    def axes(path: Path, photo: Path) -> tuple[float, float] | None:
        """Return (posterisation, linework) read at the photograph's canvas.

        **F35's law, and it is not optional.** Both axes are resolution-sensitive:
        read natively, the hires pass looked like a linework *loss*; read at the
        photograph's canvas it is a 43-47% gain. The sign flipped. So every image
        on this page -- render and photograph alike -- is measured through
        `load_canvas_pixels(path, canvas_for(photo))`.
        """
        if not path.exists():
            return None
        measures = style(load_canvas_pixels(str(path), canvas_for(str(photo))))
        return measures["posterisation"], measures["linework"]

    measured: dict[str, dict[str, tuple[float, float] | None]] = {}
    rows = []
    for sid in prompts:
        photo = Path(photo_for(sid))
        measured[sid] = {}
        art = thumb(photo, thumbs, f"{sid}_photo")
        cells = [
            f'<td class="photo"><a href="{html_mod.escape(up + str(photo))}">'
            f'<img src="{html_mod.escape(art)}" loading="lazy" alt=""></a>'
            '<span class="m">the photograph</span></td>'
            if art
            else '<td class="photo"><div class="miss">no photograph</div></td>'
        ]
        base = axes(renders / "4_baseline" / f"{sid}.png", photo)
        for arm, key, _ in arms:
            better = supersede.get(arm)
            if better and (renders / better / f"{sid}.png").exists():
                arm, key = better, better
            image = renders / arm / f"{sid}.png"
            entry = prompts[sid]["arms"].get(key)
            if entry is None:
                cells.append('<td><div class="miss">no prompt</div></td>')
                continue
            tokens = entry["estimated_clip_tokens"]
            got = axes(image, photo)
            measured[sid][arm] = got
            if not image.exists():
                cells.append(
                    f'<td><div class="miss">not rendered</div>'
                    f'<span class="m tok">~{tokens} tokens</span></td>'
                )
                continue
            art = thumb(image, thumbs, f"{sid}_{arm}")
            if art is None:  # unreadable despite existing -- say so, do not hide it
                cells.append(
                    f'<td><div class="miss">unreadable</div>'
                    f'<span class="m tok">~{tokens} tokens</span></td>'
                )
                continue
            note = f'<span class="m tok">~{tokens} tokens</span>'
            if got:
                post, line = got
                delta = ""
                if base and arm != "4_baseline":
                    dp, dl = post - base[0], line - base[1]
                    cp = "up" if dp >= 0 else "down"
                    cl = "up" if dl >= 0 else "down"
                    delta = (
                        f' <span class="{cp}">{dp:+.3f}</span>'
                        f' <span class="{cl}">{dl:+.4f}</span>'
                    )
                note = (
                    f'<span class="m">post <b>{post:.3f}</b> · line '
                    f"<b>{line:.4f}</b>{delta}</span>" + note
                )
            cells.append(
                f'<td><a href="{html_mod.escape(up + str(image))}">'
                f'<img src="{html_mod.escape(art)}" loading="lazy" alt=""></a>'
                f"{note}</td>"
            )
        rows.append(f"<tr><th>{html_mod.escape(sid)}</th>{''.join(cells)}</tr>")

    (evaluation / "results.json").write_text(
        json.dumps(
            {
                sid: {
                    arm: (
                        None if v is None else {"posterisation": v[0], "linework": v[1]}
                    )
                    for arm, v in per.items()
                }
                for sid, per in measured.items()
            },
            indent=2,
        )
        + "\n"
    )

    page.write_text(
        "<!doctype html>\n<html><head><meta charset='utf-8'>"
        "<title>results &middot; descriptive_and_booru</title>"
        f"<style>{RESULTS_STYLE}</style></head><body>"
        "<h1>Does Illustrious read prose? &mdash; the renders</h1>"
        f"<p class='sub'>flow <code>A</code>, settled configuration, one seed "
        "&middot; only the body of the positive prompt differs between columns "
        "&middot; <code>evaluations/2026-09-12/descriptive_and_booru/</code></p>"
        "<p class='legend'>The <span style='color:#7ee787'>baseline</span> column "
        "is the reference, not a competitor: it is the operator's reviewed sheet, "
        "the register that produced F41's 14-of-17. Under each render, "
        "<b>post</b> is posterisation and <b>line</b> is linework, both read at "
        "<b>the photograph's canvas</b> &mdash; F35's law, where reading natively "
        "flipped the sign of the hires result. The signed pair beside them is the "
        "delta against that subject's baseline render. Determinism floors: "
        "linework &plusmn;0.0003, posterisation &plusmn;0.0020 &mdash; anything "
        "smaller is GPU noise. <span class='tok'>Amber</span> is the estimated "
        "CLIP token count against a 77-token window; the prose arms run 2.3&ndash;"
        "2.8 windows and are chunked and averaged by ComfyUI.</p>"
        "<table><thead><tr><th>subject</th><th class='o'>photograph</th>"
        "<th class='m'>Qwen3-8B sheet, reviewed</th>"
        "<th class='r'>Claude sheet, reviewed</th>"
        "<th class='b'>baseline sheet &mdash; the anchor</th>"
        "<th class='d'>descriptive prose</th>"
        "<th class='s'>straightforward prose</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></body></html>\n"
    )
    return page


RENDER_STYLE = """
:root { color-scheme: dark; }
body { margin: 0; padding: 24px; background: #14161a; color: #e6e8ec;
       font: 14px/1.55 ui-sans-serif, system-ui, -apple-system, sans-serif; }
h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
p.sub { margin: 0 0 8px; color: #9aa1ad; }
p.legend { margin: 0 0 16px; color: #9aa1ad; font-size: 12px; max-width: 1200px; }
p.neg { margin: 0 0 20px; padding: 8px 10px; background: #0d0f12; font-size: 12px;
        border-left: 3px solid #ff9f9f; color: #c3c9d4; max-width: 1200px; }
table { border-collapse: separate; border-spacing: 0; width: 100%;
        table-layout: fixed; }
th, td { padding: 10px; vertical-align: top; }
thead th { position: sticky; top: 0; z-index: 2; background: #14161a;
           text-align: left; border-bottom: 1px solid #2a2f37; font-size: 12px; }
thead th.d { color: #7fb2ff; } thead th.s { color: #ffd479; }
thead th.r { color: #b98bff; } thead th.b { color: #7ee787; }
tbody tr + tr th, tbody tr + tr td { border-top: 1px solid #2a2f37; }
tbody th { text-align: left; font-weight: 600; font-size: 13px; width: 8%; }
td.photo { width: 14%; }
img { display: block; width: 100%; height: auto; border-radius: 6px;
      background: #0d0f12; }
a { text-decoration: none; }
td.p { width: 19.5%; font: 12px/1.6 ui-monospace, SFMono-Regular, Menlo, monospace; }
.lad { color: #7ee787; } .cnt { color: #ffd479; } .tra { color: #7fb2ff; }
.bod { color: #dfe3ea; }
.budget { display: block; margin-top: 8px; padding-top: 6px;
          border-top: 1px solid #2a2f37; font-family: ui-sans-serif, system-ui;
          font-size: 11.5px; color: #9aa1ad; }
.budget b { color: #e6e8ec; }
.budget.over b { color: #ff9f9f; }
.bar { display: block; height: 4px; margin-top: 4px; border-radius: 2px;
       background: linear-gradient(90deg, #7ee787 0 var(--w), #33201f var(--w) 100%); }
"""


def render_prompts_sheet(evaluation: Path = EVAL, out: Path | None = None) -> Path:
    """Render the four prompts per photograph, for review before a pod exists.

    **This page is a spending gate, not a record.** Fifteen to twenty renders
    driven by four prompt registers is exactly the run where "which text made
    this image" gets lost, so `prompts.json` is written first and this renders it
    for a human to read. `README.md` §7 step ⑤ is this page.

    The WAI structure is coloured rather than described: green is the quality
    ladder F34 measured at +0.013, amber the count tag Danbooru front-loads,
    plain white the body that differs between arms, blue the shipped graph's own
    trailer. **Only the body differs between arms** -- if a prose arm loses, it
    cannot be because it was denied the structure.
    """
    import html as html_mod

    from prototype.sheet import QUALITY, TRAILER, photo_for

    data = json.loads((evaluation / "prompts.json").read_text())
    page = out or evaluation / "render_prompts.html"
    thumbs = page.parent / "thumbs"
    up = "../" * len(page.parent.parts)
    ladder_text = ", ".join(QUALITY)
    trailer_text = ", ".join(TRAILER)

    def cell(arm: dict, count: str) -> str:
        positive, tokens = arm["positive"], arm["estimated_clip_tokens"]
        body = positive
        for prefix in (f"{ladder_text}, {count}, ", f"{ladder_text}, "):
            if body.startswith(prefix):
                body = body[len(prefix) :]
                break
        shown_count = count if f"{ladder_text}, {count}, " in positive else ""
        if body.endswith(f", {trailer_text}"):
            body = body[: -len(f", {trailer_text}")]
        windows = tokens / 77
        over = " over" if windows > 1 else ""
        head = f'<span class="lad">{html_mod.escape(ladder_text)}</span>, '
        if shown_count:
            head += f'<span class="cnt">{html_mod.escape(shown_count)}</span>, '
        return (
            f'{head}<span class="bod">{html_mod.escape(body)}</span>, '
            f'<span class="tra">{html_mod.escape(trailer_text)}</span>'
            f'<span class="budget{over}">~<b>{tokens}</b> CLIP tokens · '
            f"<b>{windows:.1f}</b> windows of 77"
            f'<span class="bar" style="--w:{min(100, 100 / max(windows, 1)):.0f}%">'
            "</span></span>"
        )

    rows = []
    for sid, entry in data.items():
        arms = entry["arms"]
        count = "1boy, solo" if "1boy" in arms["baseline"] else "1girl, solo"
        art = thumb(Path(photo_for(sid)), thumbs, sid)
        image = (
            f'<a href="{html_mod.escape(up + photo_for(sid))}">'
            f'<img src="{html_mod.escape(art)}" loading="lazy" alt=""></a>'
            if art
            else "<span>no photograph</span>"
        )
        rows.append(
            f"<tr><th>{html_mod.escape(sid)}</th>"
            f'<td class="photo">{image}</td>'
            + "".join(
                f'<td class="p">{cell(arms[a], count)}</td>'
                for a in ("descriptive", "straightforward", "booru", "baseline")
            )
            + "</tr>"
        )

    negative = next(iter(data.values()))["negative"]
    page.write_text(
        "<!doctype html>\n<html><head><meta charset='utf-8'>"
        "<title>render prompts &middot; descriptive_and_booru</title>"
        f"<style>{RENDER_STYLE}</style></head><body>"
        "<h1>The render prompts &mdash; review gate before the pod</h1>"
        f"<p class='sub'>{len(rows)} photographs &times; 4 arms = "
        f"<b>{len(rows) * 4} renders</b> &middot; flow <code>A</code> at the "
        "settled configuration &middot; one seed &middot; "
        "<code>prompts.json</code> is the machine-readable copy</p>"
        "<p class='legend'>Every arm carries <b>WAI's published structure</b>: "
        f"<span class='lad'>{html_mod.escape(ladder_text)}</span> leads "
        "(F34 measured the ladder at +0.013 in front), then "
        f"<span class='cnt'>the count tag</span> Danbooru front-loads, then the "
        "body, then <span class='tra'>the shipped graph's own trailer</span>. "
        "<b>Only the body differs between arms</b> &mdash; so if a prose arm "
        "loses, it cannot be because it was denied the structure. The bar under "
        "each prompt is how much of it fits CLIP's first 77-token window; "
        "anything past 1.0 is chunked and averaged by ComfyUI.</p>"
        f"<p class='neg'><b>Negative, identical on all four arms and all five "
        f"photographs:</b> {html_mod.escape(negative)}</p>"
        "<table><thead><tr><th>subject</th><th>photograph</th>"
        "<th class='d'>arm 1 &middot; descriptive prose</th>"
        "<th class='s'>arm 2 &middot; straightforward prose</th>"
        "<th class='r'>arm 3 &middot; sheet routed from descriptive</th>"
        "<th class='b'>arm 4 &middot; baseline sheet (the anchor)</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></body></html>\n"
    )
    return page


EVAL_STYLE = """
:root { color-scheme: dark; }
body { margin: 0; padding: 24px; background: #14161a; color: #e6e8ec;
       font: 14px/1.55 ui-sans-serif, system-ui, -apple-system, sans-serif; }
h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
p.sub { margin: 0 0 8px; color: #9aa1ad; }
p.legend { margin: 0 0 20px; color: #9aa1ad; font-size: 12px; max-width: 1200px; }
table { border-collapse: separate; border-spacing: 0; width: 100%;
        table-layout: fixed; }
th, td { padding: 10px; vertical-align: top; }
thead th { position: sticky; top: 0; z-index: 2; background: #14161a;
           text-align: left; border-bottom: 1px solid #2a2f37; font-size: 12px; }
thead th.d { color: #7fb2ff; } thead th.s { color: #ffd479; }
thead th.r { color: #b98bff; } thead th.b { color: #7ee787; }
tbody tr + tr th, tbody tr + tr td { border-top: 1px solid #2a2f37; }
tbody th { text-align: left; font-weight: 600; font-size: 13px; width: 9%; }
td.photo { width: 15%; }
img { display: block; width: 100%; height: auto; border-radius: 6px;
      background: #0d0f12; }
a { text-decoration: none; }
td.text { width: 20%; font-size: 12.5px; color: #cdd3dd; }
td.tags { width: 18%; }
.field { display: grid; grid-template-columns: 82px 1fr; gap: 5px;
         padding: 2px 0; border-top: 1px solid #1a1d22; }
.field:first-child { border-top: 0; }
.fname { color: #7b828c; font-size: 11px; padding-top: 3px; }
.fname.scored { color: #ffd479; }
.tag { display: inline-block; padding: 0 6px; margin: 0 2px 2px 0;
       border-radius: 3px; font: 11.5px/1.55 ui-monospace, Menlo, monospace;
       background: #1d2127; color: #aeb4be; }
.tag.hit { background: #1e3325; color: #7ee787; }
.tag.diff { background: #2b2233; color: #cba6f7; }
.tag.missed { background: #33201f; color: #ff9f9f;
              text-decoration: line-through; }
.empty { color: #4a5058; font-size: 11px; padding-top: 3px; }
.note { display: block; margin-top: 8px; padding-top: 6px;
        border-top: 1px solid #2a2f37; color: #9aa1ad; font-size: 11.5px; }
.note b { color: #e6e8ec; }
"""


def eval_sheet(evaluation: Path = EVAL, out: Path | None = None) -> Path:
    """Photograph · both captions · the routed sheet · the baseline sheet.

    **Five columns, and the two sheet columns are coloured against each other
    rather than against a third thing.** The baseline sheet IS the reference --
    it is the operator-reviewed description that drove F41's 14-of-17 -- so
    "agreement" here means agreement with it, and the page says so instead of
    implying a neutral judge exists.

    The routed sheet is built from the `descriptive` caption only, on the
    operator's instruction of 2026-09-12. `straightforward` is shown because the
    two arms disagree with each other on four of the five subjects, and a
    disagreement between two runs of the same model at temperature 0 is a
    reliability fact worth seeing beside the sheet.
    """
    import html as html_mod

    from prototype.sheet import ORDER, fields_of, photo_for
    from prototype.vlm_reader import SCORED, tags

    routed_dir = evaluation / "sheet"
    captions = {
        "descriptive": evaluation / "captions" / "descriptive",
        "straightforward": evaluation / "captions" / "straightforward",
    }
    if not routed_dir.exists():
        raise SystemExit(f"no routed sheets at {routed_dir}")
    page = out or evaluation / "captions.html"
    thumbs = page.parent / "thumbs"
    up = "../" * len(page.parent.parts)

    rows = []
    for sid in EVAL_SUBJECTS:
        routed_path = routed_dir / f"{sid}.json"
        if not routed_path.exists():
            continue
        routed = json.loads(routed_path.read_text())
        base = fields_of(sid)

        def column(source: dict, against: dict, mark_missing: bool) -> str:
            lines = []
            for field in ORDER:
                mine = tags(source.get(field, ""))
                theirs = tags(against.get(field, ""))
                if not (mine or theirs):
                    continue
                cells = [
                    f'<span class="tag{" hit" if t in theirs else " diff"}">'
                    f"{html_mod.escape(t)}</span>"
                    for t in sorted(mine)
                ]
                if mark_missing:
                    cells += [
                        f'<span class="tag missed">{html_mod.escape(t)}</span>'
                        for t in sorted(theirs - mine)
                    ]
                mark = " scored" if field in SCORED else ""
                body = "".join(cells) or '<span class="empty">&mdash;</span>'
                lines.append(
                    f'<div class="field"><div class="fname{mark}">{field}</div>'
                    f"<div>{body}</div></div>"
                )
            return "".join(lines)

        hits = total = 0
        for field in SCORED:
            want = tags(base[field])
            if want:
                hits += len(want & tags(routed.get(field, "")))
                total += len(want)

        art = thumb(Path(photo_for(sid)), thumbs, sid)
        image = (
            f'<a href="{html_mod.escape(up + photo_for(sid))}">'
            f'<img src="{html_mod.escape(art)}" loading="lazy" alt=""></a>'
            if art
            else '<span class="empty">no photograph</span>'
        )

        texts = {}
        for arm, directory in captions.items():
            path = directory / f"{sid}.txt"
            words = path.read_text().strip() if path.exists() else "(missing)"
            texts[arm] = (
                f"<p>{html_mod.escape(words)}</p>"
                f'<span class="note"><b>{len(words.split())}</b> words</span>'
            )

        rows.append(
            f"<tr><th>{html_mod.escape(sid)}</th>"
            f'<td class="photo">{image}</td>'
            f'<td class="text">{texts["descriptive"]}</td>'
            f'<td class="text">{texts["straightforward"]}</td>'
            f'<td class="tags">{column(routed, base, True)}'
            f'<span class="note">scored fields: <b>{hits}/{total}</b> of the '
            f"baseline's tags</span></td>"
            f'<td class="tags">{column(base, routed, False)}</td></tr>'
        )

    page.write_text(
        "<!doctype html>\n<html><head><meta charset='utf-8'>"
        "<title>descriptive_and_booru &middot; captions and sheets</title>"
        f"<style>{EVAL_STYLE}</style></head><body>"
        "<h1>Prose &rarr; sheet, against the baseline that works</h1>"
        f"<p class='sub'>{MODEL} at Q4_K on Ollama &middot; temperature 0, seed 1 "
        "&middot; prompts parsed from <code>prompts.md</code> &middot; "
        f"{len(rows)} photographs &middot; "
        "<code>evaluations/2026-09-12/descriptive_and_booru/</code></p>"
        "<p class='legend'>The <span style='color:#b98bff'>routed sheet</span> is "
        "built from the <span style='color:#7fb2ff'>descriptive</span> caption "
        "<b>only</b>. <span style='color:#ffd479'>straightforward</span> is shown "
        "because the two arms <b>disagree with each other</b> at temperature 0, "
        "which is a reliability fact worth reading beside the sheet. The "
        "<span style='color:#7ee787'>baseline sheet</span> is the reference, not a "
        "rival: it is the operator-reviewed description that drove F41's 14-of-17. "
        "So &mdash; <span class='tag hit'>green</span> = the two sheets agree, "
        "<span class='tag diff'>violet</span> = the routed sheet has it and the "
        "baseline does not (a disagreement, and F36 proved three baselines wrong), "
        "<span class='tag missed'>red</span> = the baseline has it and the prose "
        "lost it. Amber field names are the seven scored criteria.</p>"
        "<table><thead><tr><th>subject</th><th>photograph</th>"
        "<th class='d'>JoyCaption &middot; descriptive</th>"
        "<th class='s'>JoyCaption &middot; straightforward</th>"
        "<th class='r'>sheet routed from descriptive</th>"
        "<th class='b'>baseline sheet (proved)</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></body></html>\n"
    )
    return page


COMPARE_STYLE = """
:root { color-scheme: dark; }
body { margin: 0; padding: 24px; background: #14161a; color: #e6e8ec;
       font: 14px/1.55 ui-sans-serif, system-ui, -apple-system, sans-serif; }
h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
p.sub { margin: 0 0 8px; color: #9aa1ad; }
p.legend { margin: 0 0 20px; color: #9aa1ad; font-size: 12px; max-width: 1150px; }
table { border-collapse: separate; border-spacing: 0; width: 100%; }
th, td { padding: 10px; vertical-align: top; }
thead th { position: sticky; top: 0; z-index: 2; background: #14161a;
           text-align: left; border-bottom: 1px solid #2a2f37; font-size: 13px; }
thead th.jc { color: #ffd479; } thead th.cl { color: #7fb2ff; }
tbody tr + tr th, tbody tr + tr td { border-top: 1px solid #2a2f37; }
tbody th { text-align: left; font-weight: 600; white-space: nowrap; }
img { display: block; width: 190px; height: auto; border-radius: 6px;
      background: #0d0f12; }
a { text-decoration: none; }
td.col { width: 31%; }
.tag { display: inline-block; padding: 1px 7px; margin: 0 3px 3px 0;
       border-radius: 4px; font: 12px/1.6 ui-monospace, Menlo, monospace;
       background: #1d2127; color: #8c929c; }
.tag.hit { background: #1e3325; color: #7ee787; }
.tag.meta { background: #33301f; color: #c9a227; }
.prose { margin: 10px 0 0; padding-top: 8px; border-top: 1px solid #1d2127;
         color: #9aa1ad; font-size: 12px; }
.prose b { display: block; color: #ffd479; font-size: 11px;
           text-transform: uppercase; letter-spacing: .06em; }
.score { display: block; margin-top: 10px; padding-top: 8px;
         border-top: 1px solid #2a2f37; color: #9aa1ad; font-size: 12px; }
.score b { color: #e6e8ec; }
.neither { margin-top: 10px; padding: 8px 10px; background: #201618;
           border-left: 3px solid #ff9f9f; border-radius: 4px; }
.neither .lbl { display: block; color: #ff9f9f; font-size: 11px;
                text-transform: uppercase; letter-spacing: .06em;
                margin-bottom: 4px; }
.neither .tag { background: #33201f; color: #ff9f9f; }
"""


def compare_sheet(out: Path | None = None) -> Path:
    """Photograph, JoyCaption's best arm, and Claude's sheet, scored one way.

    **Both columns are coloured by the same rule and scored by the same measure,
    and that is the whole design.** JoyCaption's best arm is a flat bag -- it
    ignored the sixteen-field structure it was asked for -- so it cannot be
    scored per field. Colouring the bag by "appears anywhere in the reviewed
    sheet" and Claude's draft per field would judge two readers by two rules,
    which is exactly the failure `IDENTITY.md` §1 records for round 1 and round
    2's scoreboards. So the bag rule applies to both: a tag is green if the
    reviewed sheet carries it anywhere. That is GENEROUS to JoyCaption, since a
    bag cannot misfile a tag, and generous in the direction that makes the
    conclusion harder to reach rather than easier.

    The third element is the one worth reading: **what neither reader found.**
    """
    import html as html_mod

    from prototype.paths import derived_dir, draft_path
    from prototype.sheet import ORDER, fields_of, photo_for
    from prototype.vlm_reader import tags

    day = derived_dir()
    # The best arm of five, measured: 0.518 on the three independent references
    # against the plain Danbooru mode's 0.501. Shown rather than the `identity`
    # arm, which scored 0.307 and invented nineteen identity marks.
    arm = day / "n36_schema_fields"
    prose = day / "n35_describe_straightforward"
    if not arm.exists():
        raise SystemExit(f"no phase-1 dumps at {arm}; run --schema first")
    page = out or day / "n36_compare_sheet.html"
    thumbs = page.parent / f"{page.stem}_thumbs"
    up = "../" * len(page.parent.parts)

    def chip(tag: str, sheet: set[str]) -> str:
        if ":" in tag or "(medium)" in tag:
            kind = " meta"
        elif tag in sheet:
            kind = " hit"
        else:
            kind = ""
        return f'<span class="tag{kind}">{html_mod.escape(tag)}</span>'

    rows = []
    for sid in BOORU_SET:
        dump = arm / f"{sid}.txt"
        if not dump.exists():
            continue
        reference = fields_of(sid)
        sheet = {t for field in ORDER for t in tags(reference[field])}

        jc = [
            t.strip()
            for t in dump.read_text().replace("_", " ").split(",")
            if t.strip()
        ]
        jc_real = [t for t in jc if ":" not in t and "(medium)" not in t]

        drafted = draft_path(sid)
        cl = (
            [
                tag.strip()
                for field in ORDER
                for tag in json.loads(drafted.read_text()).get(field, "").split(",")
                if tag.strip()
            ]
            if drafted.exists()
            else []
        )

        jc_hits = len(set(jc_real) & sheet)
        cl_hits = len(set(cl) & sheet)
        missed = sorted(sheet - set(jc_real) - set(cl))

        text = prose / f"{sid}.txt"
        prose_html = (
            '<p class="prose"><b>straightforward prose</b>'
            f"{html_mod.escape(text.read_text().strip())}</p>"
            if text.exists()
            else ""
        )

        art = thumb(Path(photo_for(sid)), thumbs, sid)
        image = (
            f'<a href="{html_mod.escape(up + photo_for(sid))}">'
            f'<img src="{html_mod.escape(art)}" loading="lazy" alt=""></a>'
            if art
            else "<span>no photograph</span>"
        )
        neither = (
            '<div class="neither"><span class="lbl">neither reader found these'
            f"</span>{''.join(chip(t, set()) for t in missed)}</div>"
            if missed
            else ""
        )
        rows.append(
            f"<tr><th>{html_mod.escape(sid)}</th><td>{image}{neither}</td>"
            f'<td class="col">{"".join(chip(t, sheet) for t in jc)}'
            f'<span class="score"><b>{jc_hits}</b> of the sheet\'s '
            f"<b>{len(sheet)}</b> tags · {len(jc_real)} tags emitted</span>"
            f"{prose_html}</td>"
            f'<td class="col">{"".join(chip(t, sheet) for t in cl)}'
            f'<span class="score"><b>{cl_hits}</b> of the sheet\'s '
            f"<b>{len(sheet)}</b> tags · {len(cl)} tags emitted</span></td></tr>"
        )

    page.write_text(
        "<!doctype html>\n<html><head><meta charset='utf-8'>"
        "<title>JoyCaption vs Claude</title>"
        f"<style>{COMPARE_STYLE}</style></head><body>"
        "<h1>JoyCaption vs the agent session</h1>"
        f"<p class='sub'>{MODEL} at Q4_K on Ollama, temperature 0, seed 1 "
        f"&middot; {len(rows)} photographs &middot; both columns scored by the "
        "same measure against the operator's reviewed sheets</p>"
        "<p class='legend'>JoyCaption is its <b>best of five prompts</b> &mdash; "
        "the phase-1 sixteen-field briefing, 0.518 on the three independent "
        "references against 0.501 for its own Danbooru mode. It <b>ignored the "
        "field structure</b> and returned a flat bag, so both columns are "
        "coloured and counted the same way: <span class='tag hit'>green</span> = "
        "the reviewed sheet carries this tag <i>anywhere</i>, "
        "<span class='tag'>grey</span> = it does not, "
        "<span class='tag meta'>amber</span> = meta or prefixed. That bag rule is "
        "<b>generous to JoyCaption</b>, because a bag cannot misfile a tag &mdash; "
        "generous in the direction that makes the conclusion harder to reach. "
        "<b>Caveat:</b> for the seven real subjects the reviewed sheet was seeded "
        "by <code>sheet.py adopt</code> from Claude's own draft, so only "
        "<code>00003</code>, <code>00035</code> and <code>00072</code> are "
        "independent references.</p>"
        "<table><thead><tr><th>subject</th><th>photograph</th>"
        "<th class='jc'>JoyCaption &middot; phase-1 <code>fields</code> arm</th>"
        "<th class='cl'>Claude &middot; the agent session</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></body></html>\n"
    )
    return page


ROUTER_STYLE = """
:root { color-scheme: dark; }
body { margin: 0; padding: 24px; background: #14161a; color: #e6e8ec;
       font: 14px/1.55 ui-sans-serif, system-ui, -apple-system, sans-serif; }
h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
p.sub { margin: 0 0 8px; color: #9aa1ad; }
p.legend { margin: 0 0 20px; color: #9aa1ad; font-size: 12px; max-width: 1100px; }
table { border-collapse: separate; border-spacing: 0; width: 100%; }
th, td { padding: 10px; vertical-align: top; }
thead th { position: sticky; top: 0; z-index: 2; background: #14161a;
           text-align: left; border-bottom: 1px solid #2a2f37; font-size: 13px; }
tbody tr + tr th, tbody tr + tr td { border-top: 1px solid #2a2f37; }
tbody th { text-align: left; font-weight: 600; white-space: nowrap; }
img { display: block; width: 200px; height: auto; border-radius: 6px;
      background: #0d0f12; }
a { text-decoration: none; }
td.prose { width: 26%; font-size: 13px; }
td.sheet { width: 40%; }
.mode { margin: 0 0 10px; }
.mode .lbl { display: block; color: #ffd479; font-size: 11px;
             text-transform: uppercase; letter-spacing: .06em;
             margin-bottom: 2px; }
.mode.alt .lbl { color: #7fb2ff; }
.mode p { margin: 0; color: #cdd3dd; }
.field { display: grid; grid-template-columns: 120px 1fr; gap: 6px;
         padding: 3px 0; border-top: 1px solid #1d2127; }
.field:first-child { border-top: 0; }
.fname { color: #9aa1ad; font-size: 12px; padding-top: 3px; }
.fname.scored { color: #ffd479; }
.tag { display: inline-block; padding: 1px 7px; margin: 0 3px 3px 0;
       border-radius: 4px; font: 12px/1.6 ui-monospace, Menlo, monospace;
       background: #1d2127; color: #cdd3dd; }
.tag.hit { background: #1e3325; color: #7ee787; }
.tag.missed { background: #33201f; color: #ff9f9f;
              text-decoration: line-through; }
.empty { color: #4d545e; font-size: 12px; padding-top: 3px; }
.score { display: block; margin-top: 10px; padding-top: 8px;
         border-top: 1px solid #2a2f37; color: #9aa1ad; font-size: 12px; }
.score b { color: #e6e8ec; }
"""


def router_sheet(out: Path | None = None) -> Path:
    """Photograph, JoyCaption's prose, and the Danbooru sheet routed out of it.

    **The page has to say which prose the tags came from**, because two modes are
    on disk and only one was routed. Routing from both would make the result
    unreadable: a field that only `descriptive` mentioned would score as a win
    for a pipeline nobody could reproduce. So the tags are from `straightforward`
    alone, `descriptive` is shown beside it as the control, and the label says so.

    Colour is the measurement. Green is a tag the reviewed sheet also has, red
    struck-through is one the sheet has and the routing missed, grey is a tag the
    routing produced that the sheet does not carry -- **and grey is not a
    failure**: F36 proved three reference sheets wrong, so an extra tag is a
    disagreement to read, not an error to count.
    """
    import html as html_mod

    from prototype.paths import derived_dir
    from prototype.sheet import ORDER, fields_of, photo_for
    from prototype.vlm_reader import SCORED, tags

    day = derived_dir()
    routed = Path("prototype/derived/vlm_drafts_jc_router")
    prose = {
        "straightforward": day / "n35_describe_straightforward",
        "descriptive": day / "n35_describe_descriptive",
    }
    if not routed.exists():
        raise SystemExit(f"no routed drafts at {routed}")
    page = out or day / "n35_router_sheet.html"
    thumbs = page.parent / f"{page.stem}_thumbs"
    up = "../" * len(page.parent.parts)

    rows = []
    for sid in BOORU_SET:
        draft_path = routed / f"{sid}.json"
        if not draft_path.exists():
            continue
        draft = json.loads(draft_path.read_text())
        reference = fields_of(sid)

        blocks = []
        for mode, directory in prose.items():
            text = directory / f"{sid}.txt"
            if not text.exists():
                continue
            alt = "" if mode == "straightforward" else " alt"
            label = f"{mode} &mdash; routed" if mode == "straightforward" else mode
            blocks.append(
                f'<div class="mode{alt}"><span class="lbl">{label}</span>'
                f"<p>{html_mod.escape(text.read_text().strip())}</p></div>"
            )

        lines = []
        hits = total = 0
        for field in ORDER:
            want = tags(reference[field])
            got = tags(draft.get(field, ""))
            if not (want or got):
                continue
            cells = [
                f'<span class="tag{" hit" if tag in want else ""}">'
                f"{html_mod.escape(tag)}</span>"
                for tag in sorted(got)
            ] + [
                f'<span class="tag missed">{html_mod.escape(tag)}</span>'
                for tag in sorted(want - got)
            ]
            if field in SCORED and want:
                hits += len(want & got)
                total += len(want)
            mark = " scored" if field in SCORED else ""
            body = "".join(cells) or '<span class="empty">&mdash;</span>'
            lines.append(
                f'<div class="field"><div class="fname{mark}">{field}</div>'
                f"<div>{body}</div></div>"
            )

        art = thumb(Path(photo_for(sid)), thumbs, sid)
        image = (
            f'<a href="{html_mod.escape(up + photo_for(sid))}">'
            f'<img src="{html_mod.escape(art)}" loading="lazy" alt=""></a>'
            if art
            else '<div class="empty">no photograph</div>'
        )
        share = f"{hits}/{total}" if total else "&mdash;"
        rows.append(
            f"<tr><th>{html_mod.escape(sid)}</th><td>{image}</td>"
            f'<td class="prose">{"".join(blocks)}</td>'
            f'<td class="sheet">{"".join(lines)}'
            f'<span class="score">scored fields: <b>{share}</b> of the '
            f"reviewed sheet's tags recovered</span></td></tr>"
        )

    page.write_text(
        "<!doctype html>\n<html><head><meta charset='utf-8'>"
        "<title>JoyCaption prose &rarr; Danbooru tags</title>"
        f"<style>{ROUTER_STYLE}</style></head><body>"
        "<h1>JoyCaption prose &rarr; Danbooru sheet</h1>"
        f"<p class='sub'>{MODEL} at Q4_K on Ollama &middot; temperature 0, seed 1 "
        f"&middot; {len(rows)} photographs &middot; the two modes the project "
        "calls most accurate</p>"
        "<p class='legend'>The tag column is routed <b>from the "
        "<span style='color:#ffd479'>straightforward</span> prose only</b> &mdash; "
        "<span style='color:#7fb2ff'>descriptive</span> is shown as the control and "
        "was not used, so a field it alone mentions cannot score. "
        "<span class='tag hit'>green</span> = the reviewed sheet has it too. "
        "<span class='tag missed'>red</span> = the sheet has it and the routing "
        "missed it. <span class='tag'>grey</span> = routed but not in the sheet "
        "&mdash; <b>not necessarily wrong</b>: F36 proved three reference sheets "
        "wrong, so read it as a disagreement. Amber field names are the seven "
        "scored fields; the rest are recorded but not in the mean.</p>"
        "<table><thead><tr><th>subject</th><th>photograph</th>"
        "<th>JoyCaption &middot; prose</th>"
        "<th>Danbooru sheet, routed from the prose</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></body></html>\n"
    )
    return page


def thumb(src: Path, dest_dir: Path, name: str) -> str | None:
    """Write a width-limited JPEG beside the page and return its relative path.

    The same shape as `contact_sheet.thumb` and deliberately not imported from it:
    that module builds forty render columns and pulls in the style axes to do it,
    where this needs eleven lines. Importing it to save them would make a probe
    page depend on the measurement stack.
    """
    from PIL import Image
    from PIL.Image import Resampling

    if not src.exists():
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{name}.jpg"
    with Image.open(src) as image:
        image = image.convert("RGB")
        height = round(image.height * 520 / image.width)
        image.resize((520, height), Resampling.LANCZOS).save(dest, quality=88)
    return f"{dest_dir.name}/{dest.name}"


def main() -> None:
    """Verify the pinned artifacts, run the sight gates, or dump the booru mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, default=MODELS)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--host", default=HOST)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="check every entry's bytes against the manifest and exit",
    )
    parser.add_argument(
        "--see",
        action="store_true",
        help="run both sight gates against the hosted model",
    )
    parser.add_argument(
        "--booru",
        action="store_true",
        help="dump JoyCaption's Danbooru tag mode over the ten probe photographs",
    )
    parser.add_argument(
        "--describe",
        action="store_true",
        help="run both accurate caption modes (straightforward + descriptive)",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="phase 1: brief JoyCaption with our own fields, in three arms",
    )
    parser.add_argument(
        "--eval",
        action="store_true",
        help="run the approved evaluation arms over its five photographs",
    )
    parser.add_argument(
        "--results",
        action="store_true",
        help="build the render comparison page and results.json (free)",
    )
    parser.add_argument(
        "--render-prompts",
        action="store_true",
        help="render prompts.json as the pre-pod review page (free)",
    )
    parser.add_argument(
        "--eval-sheet",
        action="store_true",
        help="build the evaluation's captions/sheet comparison page (free)",
    )
    parser.add_argument(
        "--compare-sheet",
        action="store_true",
        help="build the JoyCaption-vs-Claude page (free, no inference)",
    )
    parser.add_argument(
        "--router-sheet",
        action="store_true",
        help="build the photo / prose / routed-tags page (free, no inference)",
    )
    parser.add_argument(
        "--booru-sheet",
        action="store_true",
        help="build the HTML page from dumps already on disk (free, no inference)",
    )
    args = parser.parse_args()

    if not (
        args.verify
        or args.see
        or args.booru
        or args.booru_sheet
        or args.describe
        or args.router_sheet
        or args.schema
        or args.compare_sheet
        or args.eval
        or args.eval_sheet
        or args.render_prompts
        or args.results
    ):
        parser.error(
            "pass --verify (N32), --see (N33), --booru, --describe or "
            "--booru-sheet; the client is N34"
        )

    if args.verify:
        pinned = manifest()
        print(f"\n=== {MANIFEST} · pinned {pinned['pinned']} ===")
        print(f"  revision {pinned['revision']}")
        for entry in pinned["entries"]:
            path = verified(entry["dest"], args.models)
            print(f"  OK  {path}  {entry['bytes'] / 2**30:.2f} GiB")

        print("\n=== recorded and deliberately NOT fetched ===")
        for entry in pinned["not_fetched"]:
            name = entry["dest"].split("/")[-1]
            print(f"  --  {name}  {entry['bytes'] / 2**30:.2f} GiB")

        print("\n=== licence ===")
        print(f"  {pinned['licence']['summary']}")
        for layer in pinned["licence"]["layers"]:
            print(f"    {layer['what']:26s} {layer['declared']}")
        print(
            "\nProvenance is proven. Vision is NOT: a projector-less LLaVA answers "
            "fluently and sees nothing.\nRun --see for that."
        )

    if args.see:
        print(f"\nhost {args.host} · model {args.model}")
        eyes, eyes_n = gate_one(args.model, args.host)
        men_hit, men, women_hit, women = gate_two(args.model, args.host)

        one = eyes >= GATE1_PASS
        two = men_hit >= GATE2_MEN and women_hit >= GATE2_WOMEN
        print("\n=== verdict, against conditions stated before the first run ===")
        print(f"  GATE 1  {eyes}/{eyes_n} eye colour      {'PASS' if one else 'FAIL'}")
        print(
            f"  GATE 2  {men_hit}/{men} men, {women_hit}/{women} women  "
            f"{'PASS' if two else 'FAIL'}"
        )
        if one and two:
            print("\n  The model sees. The projector is attached and N33 is closed.")
        else:
            print(
                "\n  NOT proven sighted. Before blaming the model, check the "
                "projector:\n  `ollama show` must list `vision` under Capabilities "
                "and a `Projector` block."
            )
            raise SystemExit(1)

    if args.booru:
        booru(args.model, args.host)

    if args.describe:
        describe(args.model, args.host)

    if args.booru_sheet:
        print(f"\n{booru_sheet()}")

    if args.schema:
        schema(args.model, args.host)

    if args.router_sheet:
        print(f"\n{router_sheet()}")

    if args.eval:
        eval_captions(args.model, args.host)

    if args.eval_sheet:
        print(f"\n{eval_sheet()}")

    if args.render_prompts:
        print(f"\n{render_prompts_sheet()}")

    if args.results:
        print(f"\n{results_sheet()}")

    if args.compare_sheet:
        print(f"\n{compare_sheet()}")


if __name__ == "__main__":
    main()
