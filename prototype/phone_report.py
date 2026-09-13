#!/usr/bin/env python3
"""PROTOTYPE -- N42: one page per phone subject, photograph + both flows + the score.

The instrument the operator actually reads. One row per subject: the source
photograph, flow `A` (InstantID + OpenPose + the sheet), flow `D` (the sheet
alone), and the identity result for each.

**Two numbers per render, and they answer different questions.** `own` is the
rank of the render's own source photograph in the 10-way identification --
`notes/IDENTITY.md`'s method. `person` is whether the top-ranked photograph
depicts the right *person*, which the operator-confirmed grouping in
`inputs/real/phone/groups.json` is what makes askable. A render can miss the
first and hit the second, and two of the ten do exactly that.

Thumbnails are generated into the page's own directory so it is self-contained
and loads without holding 2112x1536 renders in memory. Everything it reads and
writes is gitignored: these are photographs of real people (design.md D14).

    PYTHONPATH=. uv run --extra eval python prototype/phone_report.py
"""

import argparse
import html
import json
import os.path
from pathlib import Path

from prototype.paths import derived_dir
from prototype.sheet import photo_for

ARMS = (("1_a", "A"), ("2_d", "D"))
THUMB_WIDTH = 340


def full(src: Path, page_dir: Path) -> str:
    """Return a link from the page to the full-size original.

    **Derived from where the page lands, never hardcoded.** Nine contact sheets
    were rewritten on 2026-09-10 because their links were written `../..`-relative
    and broke the moment a page moved a level deeper; the fix was to compute the
    depth, and this is that fix rather than a second copy of the bug.
    """
    return html.escape(os.path.relpath(src.resolve(), page_dir.resolve()))


def thumb(src: Path, dest_dir: Path, name: str) -> str | None:
    """Write a width-limited JPEG beside the page and return its relative name."""
    from PIL import Image  # noqa: PLC0415 -- the [eval] extra, imported where used

    if not src.exists():
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / name
    with Image.open(src) as im:
        im = im.convert("RGB")
        w, h = im.size
        im = im.resize((THUMB_WIDTH, max(1, round(h * THUMB_WIDTH / w))), Image.LANCZOS)
        im.save(out, "JPEG", quality=88)
    return name


def rows_by_subject(results: dict) -> dict[str, dict[str, dict]]:
    """Return subject -> arm letter -> its result row."""
    out: dict[str, dict[str, dict]] = {}
    for arm, data in results["arms"].items():
        for row in data["rows"]:
            out.setdefault(row["subject"], {})[arm] = row
    return out


def verdict(row: dict, sid: str, who: dict[str, str], flow: str
            ) -> tuple[str, str, str]:
    """Return (own-rank text, person-level text, css class) for one render.

    **Flow `D` is graded as a control, not against a bar.** It never reads the
    photograph, so it has no mechanism by which identity could survive -- a `D`
    render landing on a stranger is the expected outcome and colouring it red
    would report the arm as failing a test it was never given. Its chance
    expectation on this set is 2.6 of 10, and it scores 2. **That is what makes
    flow `A`'s result readable**: if `D` scored well, identity would be coming
    from the prompt and there would be no way to tell the two apart.
    """
    if not row.get("scored"):
        return ("not scored", "—", "control")
    rank = row["rank_of_correct"]
    top = row["ranking"][0]
    same = who[top] == who[sid]
    own = f"own photo #{rank}" + (" ✓" if rank == 1 else "")
    if flow == "D":
        landed = "the right person" if same else html.escape(who[top])
        return (own, f"at chance — landed on {landed}", "control")
    person = (
        f"top-1 is {html.escape(top)} — SAME PERSON ✓"
        if same
        else f"top-1 is {html.escape(top)} — different person ✗"
    )
    return (person, own, "hit" if same else "miss")


def main() -> None:
    """Build the page from a scored run and the confirmed grouping."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--results",
        type=Path,
        default=Path("prototype/evaluations/2026-09-13/t4_phone_likeness/results.json"),
    )
    p.add_argument(
        "--groups", type=Path, default=Path("prototype/inputs/real/phone/groups.json")
    )
    p.add_argument("--renders", type=Path, default=None)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    groups = json.loads(args.groups.read_text())["groups"]
    who = {sid: person for person, sids in groups.items() for sid in sids}
    results = json.loads(args.results.read_text())
    by_subject = rows_by_subject(results)
    renders = args.renders or Path("prototype/renders/2026-09-13/n42_phone")
    out = args.out or (derived_dir() / "n42_phone_report.html")
    assets = out.parent / "n42_phone_assets"

    parts = [
        "<!doctype html><meta charset=utf-8>",
        "<title>N42 — phone photographs, both flows, scored</title>",
        "<style>",
        "body{background:#14151a;color:#e8e8ee;font:14px/1.5 -apple-system,sans-serif;",
        "margin:0;padding:28px}",
        "h1{font-size:19px;margin:0 0 4px}p.sub{color:#9aa;margin:0 0 22px}",
        "table{border-collapse:collapse;width:100%}",
        "td,th{border-top:1px solid #2c2e38;padding:12px 10px;vertical-align:top}",
        "th{text-align:left;color:#9aa;font-weight:600;font-size:12px;",
        "text-transform:uppercase;letter-spacing:.06em}",
        "img{width:100%;max-width:340px;border-radius:6px;display:block}",
        ".sid{font:13px ui-monospace,monospace;color:#8ab4ff}",
        ".person{font:12px ui-monospace,monospace;color:#c0a0ff}",
        ".hit{color:#7ee08a}.miss{color:#ff8f8f}.control{color:#8b90a0}",
        ".note{margin-bottom:14px}",
        ".tag{font-size:10px;text-transform:uppercase;letter-spacing:.07em;",
        "border:1px solid #3a3d4a;border-radius:3px;padding:1px 6px;margin-left:7px;",
        "color:#8b90a0;vertical-align:1px}",
        "td:last-child{min-width:270px}",
        "p.legend{color:#6b6f7d;font-size:12px;margin:18px 0 0;max-width:74em}",
        ".num{font:12px ui-monospace,monospace;color:#9aa}",
        ".flow{font-weight:600}",
        "a{text-decoration:none}",
        "a:hover img{outline:2px solid #8ab4ff;outline-offset:2px}",
        ".full{font-size:11px;color:#6b6f7d;margin-top:4px}",
        "a:hover+.full{color:#8ab4ff}",
        "</style>",
        "<h1>N42 — ten phone photographs of four people, both flows, scored</h1>",
        f"<p class=sub>chance {results['chance']:.0%} · "
        f"flow A {results['arms']['a']['hits']}/{results['arms']['a']['of']} "
        f"own-photograph top-1, p={results['arms']['a']['p_value']:.4f} · "
        f"flow D {results['arms']['d']['hits']}/{results['arms']['d']['of']} "
        "(the control — D never reads the photograph)</p>",
        "<table><tr><th>photograph</th><th>flow A — identity</th>",
        "<th>flow D — style (control)</th><th>identity result</th></tr>",
    ]

    for sid in sorted(by_subject):
        photo = Path(photo_for(sid))
        cells = [
            f"<td><span class=sid>{html.escape(sid)}</span> "
            f"<span class=person>{who.get(sid, '?')}</span>"
        ]
        name = thumb(photo, assets, f"{sid}_photo.jpg")
        cells[0] += (
            f"<a href='{full(photo, out.parent)}' target=_blank rel=noopener>"
            f"<img src='n42_phone_assets/{name}' loading=lazy></a>"
            "<div class=full>full size &#8599;</div></td>"
            if name
            else "<br>missing</td>"
        )
        notes = []
        for arm, flow in ARMS:
            src = renders / arm / sid / "0.png"
            name = thumb(src, assets, f"{sid}_{arm}.jpg")
            cells.append(
                f"<td><a href='{full(src, out.parent)}' target=_blank rel=noopener>"
                f"<img src='n42_phone_assets/{name}' loading=lazy></a>"
                "<div class=full>full size &#8599;</div></td>"
                if name
                else "<td>missing</td>"
            )
            row = by_subject[sid].get(arm[-1], {})
            headline, detail, css = verdict(row, sid, who, flow)
            cos = row.get("cosine_correct")
            label = "identity" if flow == "A" else "control · no photo read"
            notes.append(
                f"<div class=note><span class=flow>{flow}</span>"
                f"<span class=tag>{label}</span><br>"
                f"<span class={css}>{headline}</span><br>"
                f"<span class=num>{detail}"
                + (f" · cos {cos:.3f}" if cos is not None else "")
                + "</span></div>"
            )
        cells.append("<td>" + "<br>".join(notes) + "</td>")
        parts.append("<tr>" + "".join(cells) + "</tr>")

    parts.append("</table>")
    parts.append(
        "<p class=legend><b>Flow D is a control, not a competitor.</b> It never "
        "reads the photograph &mdash; it renders from the criteria sheet alone "
        "&mdash; so nothing in it could carry identity, and its renders cluster by "
        "<i>tags</i> rather than by <i>person</i>. Chance on this set is 2.6 of 10 "
        "and D scores 2. <b>That is what makes flow A&rsquo;s result readable:</b> "
        "if D scored well, identity would be coming from the prompt and there "
        "would be no way to tell the two mechanisms apart.</p>"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
