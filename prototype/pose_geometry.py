#!/usr/bin/env python3
"""PROTOTYPE — N27's second layer: does the render stand the way the photograph did.

N27's first instrument reads the **face**. Identity is more than a face: hair
silhouette, proportion, and where the limbs are. This measures the last of those,
and it is the one flow `A` has a dedicated mechanism for.

**Two numbers, because one of them is a trap on its own.**

    PCK          fraction of keypoints landing within 5% of the person box's
                 diagonal of where the photograph put them. Direct, and the
                 measure this repository already had.

    joint angle  the angle at elbow, shoulder, knee and hip, in degrees, and the
                 mean absolute error against the photograph's.

**PCK alone would repeat F4's mistake in a new place.** An anime figure has
different proportions from a photograph -- longer legs, smaller head -- so a
*perfect* pose match still displaces every keypoint, and a position-based score
penalises correct stylization. **Joint angles are proportion-invariant**: a figure
with longer legs held in the same pose has the same elbow angle. When the two
measures disagree, the angle is the one describing the pose and PCK is describing
the physique.

The worked example is `arms_up`, where the operator's eye caught what a coarse
reading missed: the control puts both arms behind the head, the ablation lets the
left arm hang. That is a left-shoulder angle of roughly 180 degrees against
roughly 20 -- a different pose, not a slightly displaced one.

---

**The expectation is pre-registered, and that is what makes this falsifiable.**
The operator judged N25's contact sheet before this existed and named six subjects
where the control beats the ablation: `arms_on_hips_legs_wide`, `arms_up`,
`arms_up_legs_crossed`, `sitting_on_knees`, `standing_turn`, `walking` -- with
flow `D` worst overall.

**If this instrument ranks the ablation above the control, the instrument is
wrong.** F1 is this project's record of building an evaluator before the thing it
judged and getting a coin flip back; the ordering here is deliberately the other
way round. The four subjects the operator did not call are where a disagreement is
informative rather than damning.

    PYTHONPATH=. uv run --extra eval python prototype/pose_geometry.py
"""

import argparse
import json
import math
from pathlib import Path

from prototype.paths import derived_dir, resolve_render
from prototype.pose_ablation import ARMS as POSE_ARMS
from prototype.pose_ablation import PHOTOS as POSE_PHOTOS
from prototype.pose_ablation import SUBJECTS as POSE_SUBJECTS

# A second run set: F35's hires arms, whose pose was never scored because the
# instrument did not exist when they rendered. Same subjects, same seed, one
# variable -- the second sampler pass.
HIRES_SUBJECTS = ("00003", "00014", "00033", "00050", "00059", "00072")
HIRES_PHOTOS = Path("inputs/synthetic")
HIRES_ARMS = {
    "1_no_hires": "prototype/renders/n18_position/3_wai/{sid}/0.png",
    "2_hires_035": "prototype/renders/n19_hires/2_hires_035/{sid}/0.png",
    "3_hires_050": "prototype/renders/n19_hires/3_hires_050/{sid}/0.png",
}
POSE_ARM_PATHS = {
    a: "prototype/renders/n25_pose/" + a + "/{sid}/0.png" for a in POSE_ARMS
}

# N28's pair: flow `A` with and without the second pass, on the ten hard poses.
# The control is N25's own `1_a_control` -- identical seed, prompt and dials --
# so the pair differs by the hires stage and nothing else.
N28_ARMS = {
    "1_a_control": "prototype/renders/n25_pose/1_a_control/{sid}/0.png",
    "4_a_hires_035": "prototype/renders/n25_pose/4_a_hires_035/{sid}/0.png",
}

# N29's held-out portraits. **Expected to be weak, and that is a property of the
# inputs rather than the flow**: eight of the ten are upper body or headshot, so
# DWPose has no legs to read and drops most keypoints. `15_01` and `16_01` are the
# only full-body subjects. Reported anyway, because "the instrument could not see
# enough to say" is a result and silence is not.
N29_SUBJECTS = (
    "02_00", "03_01", "05_01", "06_01", "08_00",
    "10_01", "14_00", "15_01", "16_01", "19_01",
)
N29_ARMS = {
    "1_a": "prototype/renders/n29_portfolio/1_a/{sid}/0.png",
    "2_d": "prototype/renders/n29_portfolio/2_d/{sid}/0.png",
}

# N30's real photographs. Framing is mixed on purpose -- 5 cowboy shot, 5 face,
# 4 full height, 3 male -- so the small-face limit can be read as a gradient
# rather than a binary. The face-only subjects will drop most keypoints, as N29's
# headshots did; that is the input, not the flow.
N30_SUBJECTS = (
    "cowboy_shot_1", "cowboy_shot_2", "cowboy_shot_3", "cowboy_shot_4",
    "cowboy_shot_5", "face_1", "face_2", "face_3", "face_4", "face_5",
    "ful_height_1", "full_height_2", "full_height_3", "full_height_4",
    "male_cowboy_shot_1", "male_cowboy_shot_2", "male_full_height",
)
N30_ARMS = {
    "1_a": "prototype/renders/n30_real/1_a/{sid}/0.png",
    "2_d": "prototype/renders/n30_real/2_d/{sid}/0.png",
}

RUNS = {
    "n30_real": (
        N30_SUBJECTS,
        Path("prototype/inputs/real"),
        "{sid}",  # extension varies; resolved below
        N30_ARMS,
    ),
    "n29_portfolio": (
        N29_SUBJECTS,
        Path("prototype/inputs/synthetic/portfolio"),
        "{sid}.png",
        N29_ARMS,
    ),
    "n25_pose": (POSE_SUBJECTS, POSE_PHOTOS, "{sid}.png", POSE_ARM_PATHS),
    "n28_pose_hires": (POSE_SUBJECTS, POSE_PHOTOS, "{sid}.png", N28_ARMS),
    "n28_hires": (
        HIRES_SUBJECTS,
        HIRES_PHOTOS,
        "synthetic_portrait_{sid}_.png",
        HIRES_ARMS,
    ),
}

# COCO-17 indices, which are the first seventeen of DWPose's 133 whole-body
# keypoints. Only the body is read: the hand and face points are far denser than
# anything here needs and would swamp the limb signal they are averaged with.
NOSE = 0
L_SHOULDER, R_SHOULDER = 5, 6
L_ELBOW, R_ELBOW = 7, 8
L_WRIST, R_WRIST = 9, 10
L_HIP, R_HIP = 11, 12
L_KNEE, R_KNEE = 13, 14
L_ANKLE, R_ANKLE = 15, 16
BODY = 17

# Each angle is (name, at, from, to) -- the vertex, and the two points whose rays
# the angle sits between. Shoulder uses the hip as its far point, so "arm raised"
# and "arm down" are 180 degrees apart rather than a few degrees.
ANGLES = (
    ("l_elbow", L_ELBOW, L_SHOULDER, L_WRIST),
    ("r_elbow", R_ELBOW, R_SHOULDER, R_WRIST),
    ("l_shoulder", L_SHOULDER, L_HIP, L_ELBOW),
    ("r_shoulder", R_SHOULDER, R_HIP, R_ELBOW),
    ("l_hip", L_HIP, L_SHOULDER, L_KNEE),
    ("r_hip", R_HIP, R_SHOULDER, R_KNEE),
    ("l_knee", L_KNEE, L_HIP, L_ANKLE),
    ("r_knee", R_KNEE, R_HIP, R_ANKLE),
)

# Below this, DWPose is guessing a coordinate. A guess scored is noise reported as
# a measurement, so such a point is dropped and the drop is counted.
MIN_CONFIDENCE = 0.3


def angle_at(points: tuple, at: int, a: int, b: int) -> float | None:
    """Return the angle in degrees at `at` between the rays to `a` and `b`."""
    p, q, r = points[at], points[a], points[b]
    if min(p.confidence, q.confidence, r.confidence) < MIN_CONFIDENCE:
        return None
    v1 = (q.x - p.x, q.y - p.y)
    v2 = (r.x - p.x, r.y - p.y)
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return None
    cos = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(cos))


def angle_error(photo: tuple, render: tuple) -> tuple[float | None, int, int, dict]:
    """Return the mean absolute joint-angle error, and the per-joint detail."""
    errors: dict[str, float] = {}
    dropped = 0
    for name, at, a, b in ANGLES:
        pa = angle_at(photo, at, a, b)
        ra = angle_at(render, at, a, b)
        if pa is None or ra is None:
            dropped += 1
            continue
        errors[name] = abs(pa - ra)
    if not errors:
        return None, 0, dropped, {}
    mean = sum(errors.values()) / len(errors)
    return mean, len(errors), dropped, {k: round(v, 1) for k, v in errors.items()}


def person_box(points: tuple) -> tuple[float, float, float, float]:
    """Return the bounding box of the confident body keypoints."""
    xs = [p.x for p in points[:BODY] if p.confidence >= MIN_CONFIDENCE]
    ys = [p.y for p in points[:BODY] if p.confidence >= MIN_CONFIDENCE]
    if not xs:
        raise SystemExit("no confident keypoints to bound")
    return min(xs), min(ys), max(xs), max(ys)


def main() -> None:
    """Score every arm's pose against its photograph, on both measures."""
    from isekai.eval_backends import DwPoseReader
    from isekai.evaluate import canvas_for, pck

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", choices=sorted(RUNS), default="n25_pose")
    p.add_argument("--models", type=Path, default=Path("models"))
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    subjects, photo_root, photo_name, arms = RUNS[args.run]
    out = args.out or derived_dir() / f"{args.run}_geometry.json"

    results: dict = {"subjects": {}, "arms": {}}
    per_arm: dict[str, list[tuple[float | None, float | None]]] = {a: [] for a in arms}

    for sid in subjects:
        photo = photo_root / photo_name.format(sid=sid)
        if not photo.exists():  # real photographs vary in extension
            from prototype.sheet import photo_for

            photo = Path(photo_for(sid))
        canvas = canvas_for(str(photo))
        reader = DwPoseReader(args.models, canvas)
        photo_pts = reader.keypoints(str(photo))
        if photo_pts is None:
            print(f"  {sid}: DWPose read nothing in the photograph — skipped")
            continue
        box = person_box(photo_pts)

        row: dict = {}
        for arm, template in arms.items():
            render = resolve_render(template.format(sid=sid))
            pts = reader.keypoints(str(render))
            if pts is None:
                row[arm] = {"read": False}
                per_arm[arm].append((None, None))
                continue
            value, used, dropped = pck(photo_pts[:BODY], pts[:BODY], box)
            mean, n, ndrop, detail = angle_error(photo_pts, pts)
            row[arm] = {
                "read": True,
                "pck": round(value, 4) if value is not None else None,
                "pck_used": used,
                "pck_dropped": dropped,
                "angle_error_deg": round(mean, 1) if mean is not None else None,
                "angles_used": n,
                "angles_dropped": ndrop,
                "per_joint_deg": detail,
            }
            per_arm[arm].append((value, mean))
        results["subjects"][sid] = row

    for arm, pairs in per_arm.items():
        pcks = [v for v, _ in pairs if v is not None]
        angs = [m for _, m in pairs if m is not None]
        results["arms"][arm] = {
            "subjects": len(pcks),
            "mean_pck": round(sum(pcks) / len(pcks), 4) if pcks else None,
            "mean_angle_error_deg": round(sum(angs) / len(angs), 1) if angs else None,
        }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2) + "\n")

    print(f"\n{'arm':16s}{'PCK ↑':>10s}{'angle err ↓':>14s}")
    for arm, row in results["arms"].items():
        pv = "—" if row["mean_pck"] is None else f"{row['mean_pck']:.3f}"
        av = (
            "—"
            if row["mean_angle_error_deg"] is None
            else f"{row['mean_angle_error_deg']:.1f}°"
        )
        print(f"{arm:16s}{pv:>10s}{av:>14s}")

    print(f"\n{'subject':24s}" + "".join(f"{a[:11]:>13s}" for a in arms))
    print(f"{'':24s}" + "".join(f"{'angle err':>13s}" for _ in arms))
    for sid, row in results["subjects"].items():
        cells = ""
        best = min(
            (r["angle_error_deg"] for r in row.values() if r.get("angle_error_deg")),
            default=None,
        )
        for arm in arms:
            v = row.get(arm, {}).get("angle_error_deg")
            mark = "*" if v is not None and v == best else " "
            cells += f"{('—' if v is None else f'{v:.1f}°') + mark:>13s}"
        print(f"{sid:24s}{cells}")
    print("\n* = best arm for that subject")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
