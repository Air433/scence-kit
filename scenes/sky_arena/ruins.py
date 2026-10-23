"""Broken colonnade, parapet, collapsed sky gate and rubble."""
from __future__ import annotations

import math

from arena_kit import config, util

from . import geometry as geo
from . import layout

TAU = math.pi * 2.0
R_COL = 16.7
BAY = 14
TALL_H = 7.6
SPRING = 6.9
OPEN_HALF = 2.15
GATE_CY = 19.75
GATE_FRONT = GATE_CY - 1.18
GATE_BACK = GATE_CY + 1.18
GATE_TOP_L = 10.90
GATE_TOP_R = 8.50

# (kind, total height above the terrace) for the 12 surviving positions.
STATES = [
    ("tall", TALL_H), ("tall", TALL_H), ("broken", 3.4), ("broken", 5.2),
    ("missing", 0.0), ("tall", TALL_H), ("tall", TALL_H), ("broken", 1.8),
    ("broken", 4.8), ("tall", TALL_H), ("missing", 0.0), ("broken", 2.6),
]


def _column_positions():
    out = []
    for i in range(BAY):
        a = TAU * i / BAY
        d = abs(((a - math.pi * 0.5 + math.pi) % TAU) - math.pi)
        if d < math.radians(16.0):
            continue
        out.append(a)
    return out


def _column(a, idx, kind, height, stone, warm, gold, rune):
    rng = util.sub_rng(f"sky_column_{idx}")
    x, y = R_COL * math.cos(a), R_COL * math.sin(a)
    z = layout.TERRACE_Z
    stone.append(geo.box(x, y, z, z + 0.24, 1.34, 1.34, a))
    warm.append(geo.box(x, y, z + 0.20, z + 0.28, 1.44, 1.44, a))
    if kind == "missing":
        stone.append(geo.prism(x, y, z + 0.28, z + 0.46, 0.62, 0.50, 18, a))
        return

    stone.append(geo.prism(x, y, z + 0.28, z + 0.46, 0.60, 0.50, 20))
    gold.append(geo.torus_z(0.54, 0.028, z + 0.47, 40, 5, x, y))
    base_top = z + 0.46
    top = z + height

    if kind == "tall":
        shaft_top = top - 0.60
        stone.append(geo.prism(x, y, base_top, shaft_top, 0.45, 0.39, 20))
        gold.append(geo.prism(x, y, shaft_top, shaft_top + 0.13,
                              0.42, 0.50, 20))
        stone.append(geo.box(x, y, shaft_top + 0.13, top, 1.18, 1.18, a))
        gold.append(geo.box(x, y, top - 0.045, top + 0.02,
                            1.26, 1.26, a))
    else:
        stone.append(geo.broken_column(x, y, base_top, top, 0.45, 0.41,
                                       20, rng, jag=min(0.85, 0.28 + 0.1 * height)))

    if idx % 3 == 0:
        rune.append(geo.torus_z(0.475, 0.032, z + 1.95, 40, 5, x, y))
        rune.append(geo.torus_z(0.455, 0.024, z + 2.35, 40, 5, x, y))


def _architrave(a0, a1, stone, warm, gold, rune, frac=1.0):
    span = a1 - a0
    b0 = a0 + span * 0.035
    b1 = a0 + span * (frac - 0.035)
    segs = max(8, int(abs(span) / TAU * 180))

    stone.append(geo.arc_slab(R_COL - 0.58, R_COL + 0.58, 7.90, 8.62,
                              b0, b1, segs))
    gold.append(geo.arc_slab(R_COL - 0.63, R_COL + 0.63, 7.85, 7.93,
                             b0, b1, segs))
    gold.append(geo.arc_slab(R_COL - 0.63, R_COL + 0.63, 8.58, 8.67,
                             b0, b1, segs))
    warm.append(geo.arc_slab(R_COL - 0.50, R_COL + 0.50, 8.62, 9.04,
                             b0 + span * 0.01, b1 - span * 0.01, segs))

    # Dentils and a rune medallion on the frieze.
    steps = max(3, int(abs(span) / TAU * 90))
    for k in range(steps):
        t = (k + 0.5) / steps
        a = b0 + (b1 - b0) * t
        gold.append(geo.box(R_COL * math.cos(a), R_COL * math.sin(a),
                            7.76, 7.88, 0.70, 0.20, a))
        if k % 2 == 0:
            gold.append(geo.torus_facing(
                (R_COL - 0.52) * math.cos(a),
                (R_COL - 0.52) * math.sin(a), 8.83, a, 0.20, 0.035, 20, 5))
            rune.append(geo.diamond((R_COL - 0.53) * math.cos(a),
                                    (R_COL - 0.53) * math.sin(a),
                                    8.83, 0.055, 0.15, 4))

    if frac < 0.99:
        a = b1
        stone.append(geo.box(R_COL * math.cos(a), R_COL * math.sin(a),
                             7.62, 8.45, 1.15, 0.55, a))
        gold.append(geo.box(R_COL * math.cos(a), R_COL * math.sin(a),
                            8.42, 8.50, 1.20, 0.60, a))


def column_layout():
    """(angle, kind, height) for every surviving colonnade bay."""
    return [(a, kind, height)
            for a, (kind, height) in zip(_column_positions(), STATES)]


def architrave_spans():
    angles = _column_positions()
    return [(angles[0], angles[1], 0.97), (angles[5], angles[6], 0.62)]


def parapet_specs():
    """(index, a0, a1, mid, top_z) for each standing parapet segment."""
    out = []
    gaps = {4, 5, 14, 20, 21}
    for i in range(24):
        a0 = TAU * i / 24.0
        a1 = TAU * (i + 1) / 24.0
        mid = (a0 + a1) * 0.5
        d = abs(((mid - math.pi * 0.5 + math.pi) % TAU) - math.pi)
        if d < math.radians(24.0) or i in gaps:
            continue
        top = 1.12 + 0.14 * math.sin(3.0 * mid + 1.2)
        if i in (8, 18):
            top = 0.72
        out.append((i, a0, a1, mid, top))
    return out


def _parapet(stone, warm, gold):
    for i, a0, a1, mid, top in parapet_specs():
        stone.append(geo.arc_slab(20.03, 20.54, layout.TERRACE_Z, top,
                                  a0 + 0.012, a1 - 0.012, 8))
        warm.append(geo.arc_slab(19.97, 20.60, top, top + 0.10,
                                 a0 + 0.012, a1 - 0.012, 8))
        for k in range(2):
            a = a0 + (a1 - a0) * (0.28 + 0.44 * k)
            gold.append(geo.box(20.27 * math.cos(a), 20.27 * math.sin(a),
                                top + 0.10, top + 0.16, 0.55, 0.16, a))
        if top > 1.0:
            merlon_a = a0 + (a1 - a0) * 0.5
            stone.append(geo.box(20.28 * math.cos(merlon_a),
                                 20.28 * math.sin(merlon_a),
                                 top + 0.10, top + 0.34,
                                 0.56, 0.34, merlon_a))
            warm.append(geo.box(20.28 * math.cos(merlon_a),
                                20.28 * math.sin(merlon_a),
                                top + 0.34, top + 0.40,
                                0.62, 0.40, merlon_a))


def _arch_fragment(stone, gold, y, spring, radius, band_w, depth):
    rings = []
    segs = 18
    for i in range(segs + 1):
        th = math.pi * 0.5 + (math.pi * 0.5) * i / segs
        cx = radius * math.cos(th)
        cz = spring + radius * math.sin(th)
        rx, rz = math.cos(th), math.sin(th)
        ring = []
        for dy in (-depth * 0.5, depth * 0.5):
            for dr in (-band_w * 0.5, band_w * 0.5):
                ring.append((cx + rx * dr, y + dy, cz + rz * dr))
        rings.append(ring)
    stone.append(util.loft_rings(rings, caps=True))

    pts = []
    for i in range(segs + 1):
        th = math.pi * 0.5 + (math.pi * 0.5) * i / segs
        pts.append((radius * math.cos(th), y - depth * 0.5 - 0.02,
                    spring + radius * math.sin(th)))
    gold.append(util.make_tube(pts, [0.045] * len(pts), sides=5, caps=True))


def _gate(mats, stone, warm, dark, gold, rune):
    # Three steps up to the threshold.
    for k, (yc, z1) in enumerate(((16.55, 0.46), (17.15, 0.58),
                                  (17.75, 0.70))):
        stone.append(geo.box(0.0, yc, layout.TERRACE_Z, z1, 9.8, 0.62))
        gold.append(geo.box(0.0, yc - 0.30, z1 - 0.025, z1 + 0.005,
                            9.6, 0.06))

    stone.append(geo.box(0.0, GATE_CY, 0.70, 0.88, 9.2, 2.62))
    gold.append(geo.box(0.0, GATE_CY, 0.86, 0.90, 9.3, 2.70))

    for sx, top, kind in ((-1.0, GATE_TOP_L, "tall"),
                          (1.0, GATE_TOP_R, "broken")):
        cx = sx * 3.15
        stone.append(geo.box(cx, GATE_CY, 0.88, top, 2.06, 2.36))
        warm.append(geo.box(cx, GATE_CY, 0.80, 1.04, 2.38, 2.66))
        gold.append(geo.box(cx, GATE_CY, 1.02, 1.08, 2.42, 2.70))

        # Dark inlay panel with a gold frame and a vertical rune line.
        dark.append(geo.box(cx, GATE_FRONT + 0.005, 1.55, top - 1.10,
                            1.18, 0.035))
        gold.append(geo.box(cx, GATE_FRONT - 0.015, top - 1.12,
                            top - 1.02, 1.34, 0.06))
        gold.append(geo.box(cx, GATE_FRONT - 0.015, 1.47, 1.57,
                            1.34, 0.06))
        for side in (-1.0, 1.0):
            gold.append(geo.box(cx + side * 0.66, GATE_FRONT - 0.015,
                                1.47, top - 1.02, 0.07, 0.06))
        for z in (2.45, 3.75, 5.05, 6.35):
            if z < top - 1.2:
                rune.append(geo.diamond(cx, GATE_FRONT - 0.045, z,
                                        0.075, 0.24, 4))

        if kind == "tall":
            warm.append(geo.box(cx, GATE_CY, top, top + 0.26,
                                2.42, 2.72))
            gold.append(geo.box(cx, GATE_CY, top + 0.26, top + 0.34,
                                2.52, 2.82))
        else:
            for k in range(5):
                w = 0.38
                x = cx - 0.82 + k * 0.41
                z0 = top
                z1 = top + 0.18 + 0.22 * math.sin(k * 1.7 + 0.4)
                stone.append(geo.box(x, GATE_CY, z0, z1, w, 2.30))
            warm.append(geo.box(cx, GATE_CY, top + 0.22, top + 0.36,
                                1.30, 2.40))

    # Main lintel, still resting on the tall west pylon, snapped at x ~ +0.5.
    stone.append(geo.box(-1.80, GATE_CY, 11.24, 12.40, 5.00, 2.46))
    warm.append(geo.box(-1.80, GATE_CY, 12.40, 12.72, 5.10, 2.54))
    gold.append(geo.box(-1.80, GATE_CY, 12.72, 12.80, 5.20, 2.62))
    gold.append(geo.box(-1.80, GATE_CY, 11.18, 11.26, 5.16, 2.58))
    for k in range(4):
        x = 0.58 + k * 0.16
        stone.append(geo.box(x, GATE_CY, 11.30 + k * 0.22,
                             12.10 + k * 0.16, 0.34, 2.36))

    # The dropped east section sits on the broken pylon.
    stone.append(geo.box(2.70, GATE_CY, 8.68, 9.52, 3.50, 2.42))
    warm.append(geo.box(2.70, GATE_CY, 9.52, 9.72, 3.58, 2.50))
    gold.append(geo.box(2.70, GATE_CY, 9.72, 9.79, 3.66, 2.56))
    stone.append(geo.box(0.98, GATE_CY, 8.90, 9.36, 0.55, 2.30))

    # Rune medallion on the main lintel.
    gold.append(geo.torus_facing(-1.80, GATE_FRONT - 0.02, 11.78,
                                 math.pi * 0.5, 0.42, 0.045, 32, 6))
    gold.append(geo.torus_facing(-1.80, GATE_FRONT - 0.02, 11.78,
                                 math.pi * 0.5, 0.26, 0.028, 24, 5))
    rune.append(geo.diamond(-1.80, GATE_FRONT - 0.05, 11.78, 0.13, 0.34, 4))

    _arch_fragment(stone, gold, GATE_FRONT - 0.08, SPRING,
                   OPEN_HALF, 0.42, 0.46)

    # Two rune obelisks flank the stair.
    for sx in (-1.0, 1.0):
        x, y = sx * 5.25, 17.15
        stone.append(geo.box(x, y, layout.TERRACE_Z, 0.72, 0.90, 0.90))
        stone.append(geo.prism(x, y, 0.72, 3.15, 0.32, 0.22, 4))
        warm.append(geo.box(x, y, 3.15, 3.27, 0.52, 0.52))
        gold.append(geo.box(x, y, 3.27, 3.33, 0.58, 0.58))
        rune.append(geo.diamond(x, y, 3.52, 0.16, 0.42, 6))
        rune.append(geo.box(x, y - 0.24, 1.45, 2.55, 0.045, 0.02))


def _fallen(stone, warm, gold):
    drums = [
        (13.6, -3.4, 2.4, 0.45, 0.42),
        (17.9, -6.2, 1.8, 2.10, 0.36),
        (-14.9, -8.6, 2.2, -0.70, 0.40),
        (-18.4, 4.8, 1.6, 1.30, 0.38),
        (8.2, 14.8, 2.0, 2.70, 0.36),
        (19.2, 9.6, 1.9, -0.30, 0.36),
    ]
    for x, y, length, ang, rad in drums:
        stone.append(geo.lying_drum(x, y, layout.TERRACE_Z + rad * 0.92,
                                    rad, length, ang))

    blocks = [
        (-11.4, 11.6, 2.6, 0.9, 0.55),
        (13.9, 8.9, 2.2, 1.2, 0.48),
        (-19.0, -2.4, 1.9, 2.5, 0.42),
    ]
    for x, y, sx, sy, h in blocks:
        stone.append(geo.box(x, y, layout.TERRACE_Z, layout.TERRACE_Z + h,
                             sx, sy, 0.4))
        gold.append(geo.box(x, y, layout.TERRACE_Z + h - 0.05,
                            layout.TERRACE_Z + h, sx * 0.96, sy * 0.96, 0.4))


def _rubble(stone, gold):
    rng = util.sub_rng("sky_rubble")
    for i in range(config.BOULDER_COUNT):
        a = rng.uniform(0, TAU)
        r = rng.uniform(13.9, 20.2)
        x, y = r * math.cos(a), r * math.sin(a)
        if layout.in_gate_corridor(x, y, 0.6):
            continue
        size = rng.uniform(0.12, 0.42)
        z0 = layout.TERRACE_Z
        stone.append(geo.prism(x, y, z0, z0 + size * rng.uniform(0.45, 0.95),
                               size, size * rng.uniform(0.35, 0.8),
                               rng.choice([5, 6, 7]), rng.uniform(0, TAU)))
        if rng.random() < 0.25:
            gold.append(geo.box(x, y, z0 + 0.01, z0 + 0.035,
                                size * 1.2, size * 0.16, a))


def build_ruins(mats):
    util.reset_collection(config.C_ARCH)
    stone, warm, dark, gold, rune = [], [], [], [], []

    angles = _column_positions()
    for idx, (a, (kind, height)) in enumerate(zip(angles, STATES)):
        _column(a, idx, kind, height, stone, warm, gold, rune)

    _architrave(angles[0], angles[1], stone, warm, gold, rune, frac=0.97)
    _architrave(angles[5], angles[6], stone, warm, gold, rune, frac=0.62)
    _parapet(stone, warm, gold)
    _gate(mats, stone, warm, dark, gold, rune)
    _fallen(stone, warm, gold)
    _rubble(stone, gold)

    stone_obj = geo.merged_mesh("RUINS_Stone", stone, mats["limestone"],
                                config.C_ARCH)
    util.cube_uv(stone_obj, 2.5)
    util.shade_smooth_by_angle(stone_obj, 28.0)

    warm_obj = geo.merged_mesh("RUINS_Trim", warm, mats["limestone_warm"],
                               config.C_ARCH)
    util.cube_uv(warm_obj, 2.0)
    util.shade_smooth_by_angle(warm_obj, 28.0)

    dark_obj = geo.merged_mesh("RUINS_Inlays", dark, mats["stone_dark"],
                               config.C_ARCH)
    gold_obj = geo.merged_mesh("RUINS_Gold", gold, mats["gold"],
                               config.C_ARCH)
    util.shade_smooth_by_angle(gold_obj, 32.0)
    geo.merged_mesh("RUINS_Runes", rune, mats["rune"], config.C_ARCH)

    print(f"[ruins] {len(angles)} columns, 2 architrave spans, gate "
          f"{GATE_TOP_L:.1f}/{GATE_TOP_R:.1f} m")
    return {"gate_light": (0.0, 18.3, 11.7),
            "dais_light": (0.0, 0.0, 1.0)}
