#!/usr/bin/env python3
"""PROTOTYPE — a contact sheet: the photograph, then each candidate, per subject.

Reading a ladder from seven directories of full-resolution PNGs is the slow part
of a session, and the comparison that matters -- *this arm against the control,
on the same face* -- is the one a directory tree makes hardest. One row per
subject, the photograph first, every arm beside it under its own name.

Thumbnails are written rather than the originals embedded: 24 renders at ~1.9 MB
is a 45 MB page, and the whole point is that it opens. Each cell links to its own
full-resolution PNG, so the detail is one click away and never inlined.

The measured linework rides under each cell, because an eye comparing two faces
and a number describing their register are two different judgements and the page
should not force the reader to hold one of them in memory.

    PYTHONPATH=. uv run --extra eval python prototype/contact_sheet.py \
        --sheet n8_combined
    open prototype/derived/<UTC-date>/n8_combined_contact_sheet.html
"""

import argparse
import html
import json
import re
from pathlib import Path

from prototype.face_ladder import SUBJECTS as LADDER_SUBJECTS
from prototype.fromnoise import PHOTOS
from prototype.fromnoise import SUGGESTED as ALL_SUBJECTS
from prototype.paths import derived_dir, resolve_render
from prototype.real_photo import PHOTOS as REAL_PHOTOS
from prototype.real_photo import SUBJECTS as REAL_SUBJECTS

# `2026-09-08` -- a UTC date bucket under `renders/`, stripped from thumbnail names.
DATE_BUCKET = re.compile(r"\d{4}-\d{2}-\d{2}")

# Arm directory -> the column heading a reader needs. Spelled out here rather
# than derived from the directory name: `4_cn_0.8` is a path, not a description,
# and a contact sheet whose headings need decoding is not a contact sheet.
#
# **N6's `2_ip_1.2` and `3_ip_1.5` are deliberately absent.** The operator rejected
# both on sight -- they do not render cleanly -- which settles F25's ip_weight arms
# on the eye as well as on the numbers. The renders stay on disk and the evidence
# stays in F25; what is gone is their claim on a column, because a comparison table
# is for choosing between live candidates.
#
# Each column is (path template, heading, the one line a reader needs). The
# template takes `sid`, so a column may come from any run rather than only from
# the arms of one -- which is what lets N8 sit beside the N3 it has to beat.
#
# **The templates name no date.** `prototype/renders/` is bucketed by UTC day, but
# a column is a claim about *which run*, not about which morning it was rendered
# on; every template is passed through `resolve_render`, which finds the run under
# whichever bucket holds it. So a sheet written before the bucketing still reads,
# and re-bucketing again would need no edit here.
SHEETS: dict[str, tuple[str, dict[str, tuple[str, str]]]] = {
    "n6_face": (
        "the photograph, then every arm",
        {
            "prototype/renders/n6_face/1_control/{sid}/0.png": (
                "control",
                "ip 0.9 · cn 0.5 · cfg 7 — reproduces F24",
            ),
            "prototype/renders/n6_face/4_cn_0.8/{sid}/0.png": (
                "cn_strength 0.8",
                "the keypoint ControlNet, pushed",
            ),
            "prototype/renders/n6_face/5_cfg_5/{sid}/0.png": (
                "cfg 5",
                "back to the pre-N2 value",
            ),
            "prototype/renders/n6_face/6_skin/{sid}/0.png": (
                "skin tag ×1.4",
                "emphasis on the sheet's skin field",
            ),
            "prototype/renders/n6_face/7_age/{sid}/0.png": (
                "age tag ×1.4",
                "emphasis on the sheet's age field",
            ),
        },
    ),
    "n24_real_photo_final": (
        "the reviewed sheets: both flows, speck fix, medium breasts",
        {
            "prototype/renders/n21_real_photo_v2/2_flow_a_hires/{sid}/0.png": (
                "A + hires \u00b7 before",
                "reviewed tables, but `narrow waist` and no speck fix",
            ),
            "prototype/renders/n24_real_photo_final/1_flow_a/{sid}/0.png": (
                "A",
                "cn 0.8 \u00b7 cfg 5 \u00b7 no hires",
            ),
            "prototype/renders/n24_real_photo_final/2_flow_a_hires/{sid}/0.png": (
                "A + hires",
                "+ the second pass at denoise 0.50",
            ),
            "prototype/renders/n24_real_photo_final/3_flow_d/{sid}/0.png": (
                "D",
                "prompt only \u2014 the photograph is never read",
            ),
            "prototype/renders/n24_real_photo_final/4_flow_d_hires/{sid}/0.png": (
                "D + hires",
                "prompt only, plus the second pass",
            ),
        },
    ),
    "n21_real_photo": (
        "both flows on photographs of a real person, after the sheet fixes",
        {
            "prototype/renders/n21_real_photo_v1/2_flow_a_hires/{sid}/0.png": (
                "A + hires \u00b7 before",
                "the first sheets: `pale skin`, `messy hair`, thin background",
            ),
            "prototype/renders/n21_real_photo_v2/1_flow_a/{sid}/0.png": (
                "A",
                "fixed sheets \u00b7 cn 0.8 \u00b7 cfg 5 \u00b7 no hires",
            ),
            "prototype/renders/n21_real_photo_v2/2_flow_a_hires/{sid}/0.png": (
                "A + hires",
                "the same, plus the second pass at denoise 0.50",
            ),
            "prototype/renders/n21_real_photo_v2/3_flow_d/{sid}/0.png": (
                "D",
                "prompt only \u2014 the photograph is never read",
            ),
            "prototype/renders/n21_real_photo_v2/4_flow_d_hires/{sid}/0.png": (
                "D + hires",
                "prompt only, plus the second pass",
            ),
        },
    ),
    "n19_hires": (
        "the hires pass WAI recommends, on both kept flows",
        {
            "prototype/renders/n18_position/3_wai/{sid}/0.png": (
                "A \u00b7 no hires",
                "flow A at its best prompt \u2014 1024x1472",
            ),
            "prototype/renders/n19_hires/2_hires_035/{sid}/0.png": (
                "A \u00b7 hires 0.35",
                "R-ESRGAN 4x+ Anime6B \u2192 1.5x \u2192 20 steps at denoise 0.35",
            ),
            "prototype/renders/n19_hires/3_hires_050/{sid}/0.png": (
                "A \u00b7 hires 0.50",
                "the same, at the recommendation's upper denoise",
            ),
            "prototype/renders/n18_position/5_d_wai/{sid}/0.png": (
                "D \u00b7 no hires",
                "prompt-only flow at its best prompt",
            ),
            "prototype/renders/n19_hires/5_d_hires_035/{sid}/0.png": (
                "D \u00b7 hires 0.35",
                "prompt-only + the hires pass \u2014 the best of both axes together",
            ),
        },
    ),
    "n18_position": (
        "where the quality ladder goes, and both kept flows",
        {
            "prototype/renders/n18_position/1_baseline/{sid}/0.png": (
                "A · baseline",
                "flow A, quality tags last \u2014 the reference",
            ),
            "prototype/renders/n18_position/2_front/{sid}/0.png": (
                "A · ladder first",
                "the same three quality tags moved to the front",
            ),
            "prototype/renders/n18_position/3_wai/{sid}/0.png": (
                "A · WAI's string",
                "+ `newest` \u2014 the publisher's exact quality string",
            ),
            "prototype/renders/n18_position/4_d_baseline/{sid}/0.png": (
                "D · baseline",
                "prompt only, quality tags last",
            ),
            "prototype/renders/n18_position/5_d_wai/{sid}/0.png": (
                "D · WAI's string",
                "prompt only, publisher's string at the front",
            ),
        },
    ),
    "n16_prompt": (
        "the four ILLUSTRIOUS.md prompt changes, one at a time",
        {
            "prototype/renders/n12_canonical/1_full/{sid}/0.png": (
                "N12 — before",
                "canonical sheets, `pale skin`, `worst detail` still in the negative",
            ),
            "prototype/renders/n16_prompt/1_baseline/{sid}/0.png": (
                "baseline",
                "+ skin tags corrected, `worst detail` removed \u2014 the reference",
            ),
            "prototype/renders/n16_prompt/2_negative/{sid}/0.png": (
                "long negative",
                "the community Illustrious negative, built from real ladder rungs",
            ),
            "prototype/renders/n16_prompt/3_schema/{sid}/0.png": (
                "rating + year",
                "the paper's two never-filled caption slots: `general`, `newest`",
            ),
            "prototype/renders/n16_prompt/4_underscore/{sid}/0.png": (
                "underscores",
                "every Danbooru tag in its stored spelling",
            ),
            "prototype/renders/n16_prompt/5_all/{sid}/0.png": (
                "all stacked",
                "every change at once",
            ),
        },
    ),
    "n12_canonical": (
        "canonical Danbooru sheets: the two kept flows, before and after",
        {
            "prototype/renders/n9_ablation/1_full/{sid}/0.png": (
                "A · before",
                "both legs · prose-ish sheets, ~half the tags non-canonical",
            ),
            "prototype/renders/n12_canonical/1_full/{sid}/0.png": (
                "A · canonical",
                "both legs · every tag canonical — the flow chosen",
            ),
            "prototype/renders/n9_ablation/4_prompt_only/{sid}/0.png": (
                "D · before",
                "prompt only · same sheets as A · before",
            ),
            "prototype/renders/n12_canonical/4_prompt_only/{sid}/0.png": (
                "D · canonical",
                "prompt only · the photograph is never read at render time",
            ),
        },
    ),
    "n9_ablation": (
        "the legs, one at a time: do they fight the tags or carry them",
        {
            "prototype/renders/n8_combined/{sid}/0.png": (
                "N8 — before enrichment",
                "both legs · the sheets before background, midriff, smile, breasts",
            ),
            "prototype/renders/n9_ablation/1_full/{sid}/0.png": (
                "A · both legs",
                "enriched sheets — the prompt work, measured alone against N8",
            ),
            "prototype/renders/n9_ablation/2_no_instantid/{sid}/0.png": (
                "B · no InstantID",
                "OpenPose only — the face left to the tags",
            ),
            "prototype/renders/n9_ablation/3_no_openpose/{sid}/0.png": (
                "C · no OpenPose",
                "InstantID only — the pose left to the tags",
            ),
            "prototype/renders/n9_ablation/4_prompt_only/{sid}/0.png": (
                "D · prompt only",
                "the photograph is never read — reproducible from the sheet alone",
            ),
        },
    ),
    "n8_combined": (
        "before and after: the two picks together, on booru sheets",
        {
            "prototype/renders/n3_fromnoise/{sid}/0.png": (
                "N3 — where we were",
                "cn 0.5 · cfg 7 · prose sheets, no gaze tag",
            ),
            "prototype/renders/n8_combined/{sid}/0.png": (
                "N8 — cfg 5 + cn 0.8",
                "your two picks, and every sheet field in booru tags",
            ),
        },
    ),
}
THUMB_WIDTH = 260

BLURB = (
    "One row per subject. Every arm is <b>one change</b> from the control, never two. "
    "Percentages are linework against this row&rsquo;s first render; the cross-pod "
    "determinism floor is about <b>1%</b>, so anything smaller is noise. "
    "Click any image for the full-resolution PNG."
)

STYLE = """
:root { color-scheme: dark; }
body { margin: 0; padding: 24px; background: #14161a; color: #e6e8ec;
       font: 14px/1.5 ui-sans-serif, system-ui, -apple-system, sans-serif; }
h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
p.sub { margin: 0 0 20px; color: #9aa1ad; }
table { border-collapse: separate; border-spacing: 0; }
th, td { padding: 6px; vertical-align: top; }
thead th { position: sticky; top: 0; z-index: 2; background: #14161a;
           text-align: left; border-bottom: 1px solid #2a2f37; }
th.arm .name { display: block; font-weight: 600; }
th.arm .note { display: block; color: #9aa1ad; font-weight: 400; font-size: 12px; }
th.photo .name { color: #ffd479; }
tbody th { position: sticky; left: 0; z-index: 1; background: #14161a;
           text-align: left; font-weight: 600; white-space: nowrap; }
tbody tr + tr th, tbody tr + tr td { border-top: 1px solid #2a2f37; }
img { display: block; width: 260px; height: auto; border-radius: 6px;
      background: #0d0f12; }
a { text-decoration: none; }
td.photo img { outline: 2px solid #ffd479; outline-offset: -2px; }
.metric { margin-top: 4px; color: #9aa1ad; font-variant-numeric: tabular-nums;
          font-size: 12px; }
.metric b { color: #e6e8ec; font-weight: 600; }
.up { color: #7ee787; } .down { color: #ff9f9f; }
.missing { width: 260px; height: 180px; display: grid; place-items: center;
           color: #6b727d; background: #0d0f12; border-radius: 6px; }
"""


def thumb_name(sid: str, render: Path) -> str:
    """Return a thumbnail name unique to this exact render path.

    Derived from the whole path below `renders/` rather than from one component of
    it. The first version used the arm directory alone, and two runs of the same
    arm -- `n9_ablation/1_full` and `n12_canonical/1_full` -- collided on
    `<sid>_1_full.jpg`: the second thumbnail overwrote the first, so a
    before-and-after sheet showed the *same* image in both columns while the
    click-through links pointed at the two different renders. Caught by the
    operator, who noticed two columns that should have differed did not.

    The **date bucket is dropped** from the name. It disambiguates nothing a run
    name does not already disambiguate, and leaving it in would rename every
    thumbnail on the day a run is re-bucketed.
    """
    parts = render.parts
    tail = parts[parts.index("renders") + 1 :] if "renders" in parts else parts
    tail = [p for p in tail if not DATE_BUCKET.fullmatch(p)]
    return "_".join([sid, *(part for part in tail if part != f"{sid}")]).replace(
        ".png", ""
    )


def thumb(src: Path, dest_dir: Path, name: str) -> str | None:
    """Write a width-limited JPEG beside the page and return its relative path."""
    from PIL import Image
    from PIL.Image import Resampling

    if not src.exists():
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{name}.jpg"
    with Image.open(src) as im:
        im = im.convert("RGB")
        height = round(im.height * THUMB_WIDTH / im.width)
        im.resize((THUMB_WIDTH, height), Resampling.LANCZOS).save(dest, quality=88)
    return f"{dest_dir.name}/{dest.name}"


def linework(path: Path) -> float | None:
    """Return the render's linework, or None if it is not on disk."""
    import numpy as np
    from PIL import Image

    from prototype.style_axis import style

    if not path.exists():
        return None
    with Image.open(path) as im:
        return style(np.asarray(im.convert("RGB")))["linework"]


def cell(
    src: Path,
    href: Path,
    thumb_path: str | None,
    value: float | None,
    control: float | None,
) -> str:
    """Return one table cell: the thumbnail, its link, and its measured linework."""
    if thumb_path is None:
        return '<td><div class="missing">not rendered</div></td>'
    metric = ""
    if value is not None:
        delta = ""
        if control is not None and control != value:
            change = (value - control) / control
            cls = "up" if change > 0 else "down"
            delta = f' <span class="{cls}">{change:+.0%}</span>'
        metric = f'<div class="metric">linework <b>{value:.4f}</b>{delta}</div>'
    rel = html.escape(str(href))
    return (
        f'<td><a href="{rel}" target="_blank">'
        f'<img src="{html.escape(thumb_path)}" loading="lazy" alt=""></a>{metric}</td>'
    )


def main() -> None:
    """Build the contact sheet for one ladder run."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sheet", choices=sorted(SHEETS), default="n8_combined")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    subtitle, columns = SHEETS[args.sheet]
    # A ladder is three subjects; a before-and-after is every subject that has
    # both sides. Derived from the columns rather than passed in, so a sheet
    # cannot claim a row it has no render for.
    # Which subjects a sheet can have rows for. Keyed by sheet rather than
    # inferred, because a ladder ran on three and a gallery on six and the real
    # photographs are a different set entirely.
    pool = {
        "n6_face": LADDER_SUBJECTS,
        "n21_real_photo": tuple(REAL_SUBJECTS),
        "n24_real_photo_final": tuple(REAL_SUBJECTS),
    }
    subjects = [
        sid
        for sid in pool.get(args.sheet, ALL_SUBJECTS)
        if all(resolve_render(t.format(sid=sid)).exists() for t in columns)
    ]
    args.out = args.out or derived_dir() / f"{args.sheet}_contact_sheet.html"

    thumbs = args.out.parent / f"{args.out.stem}_thumbs"
    args.out.parent.mkdir(parents=True, exist_ok=True)

    head = [
        '<th class="photo"><span class="name">the photograph</span>'
        '<span class="note">the input, and the thing being compared to</span></th>'
    ]
    for name, note in columns.values():
        head.append(
            f'<th class="arm"><span class="name">{html.escape(name)}</span>'
            f'<span class="note">{html.escape(note)}</span></th>'
        )

    rows = []
    for sid in subjects:
        photo = (
            REAL_PHOTOS / REAL_SUBJECTS[sid]
            if sid in REAL_SUBJECTS
            else PHOTOS / f"synthetic_portrait_{sid}_.png"
        )
        # Relative to the page, so the file opens from disk with no server.
        # Derived from where the page actually lands rather than fixed at `../..`:
        # the page moved one level deeper when `derived/` was bucketed by date, and a
        # hardcoded depth would have silently broken every click-through link
        # while the thumbnails carried on rendering.
        up = Path(*([".."] * len(args.out.parent.parts)))
        cells = [
            cell(
                photo,
                up / photo,
                thumb(photo, thumbs, f"{sid}_photo"),
                linework(photo),
                None,
            )
        ]
        cells[0] = cells[0].replace("<td>", '<td class="photo">', 1)

        # The first column is the reference every percentage is read against.
        first = resolve_render(next(iter(columns)).format(sid=sid))
        control = linework(first)
        for template in columns:
            render = resolve_render(template.format(sid=sid))
            cells.append(
                cell(
                    render,
                    up / render,
                    thumb(render, thumbs, thumb_name(sid, render)),
                    linework(render),
                    control,
                )
            )
        rows.append(f"<tr><th>{html.escape(sid)}</th>" + "".join(cells) + "</tr>")

    run_name = html.escape(args.sheet)
    page = f"""<!doctype html>
<meta charset="utf-8">
<title>isekai — {run_name} contact sheet</title>
<style>{STYLE}</style>
<h1>isekai · <code>{run_name}</code> — {html.escape(subtitle)}</h1>
<p class="sub">{BLURB}</p>
<table>
  <thead><tr><th></th>{"".join(head)}</tr></thead>
  <tbody>{"".join(rows)}</tbody>
</table>
"""
    args.out.write_text(page)
    manifest = {
        "sheet": args.sheet,
        "subjects": subjects,
        "columns": {k: v[0] for k, v in columns.items()},
    }
    args.out.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {args.out} ({len(subjects)} rows x {len(columns) + 1} columns)")


if __name__ == "__main__":
    main()
