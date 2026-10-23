"""Paved fighting floor, terraced steps, rune dais and braziers."""
from __future__ import annotations

import math

from arena_kit import config, util

from . import geometry as geo
from . import layout

TAU = math.pi * 2.0
DAIS_R = 4.9
BRAZIER_R = 10.8
BRAZIER_Z = 2.28


def brazier_positions():
    return [(BRAZIER_R * math.cos(TAU * (i + 0.5) / 4.0),
             BRAZIER_R * math.sin(TAU * (i + 0.5) / 4.0), BRAZIER_Z)
            for i in range(4)]


def _floor(mats):
    floor = geo.mesh("PLAZA_Floor",
                     *geo.cylinder(0.0, 0.0, -0.55, 0.0, layout.ARENA_R, 128),
                     mats["paving"], config.C_ARENA)
    util.cube_uv(floor, 5.0)
    util.shade_smooth_by_angle(floor, 24.0)

    step1 = geo.mesh("PLAZA_Step1",
                     *geo.ring_slab(layout.ARENA_R - 0.05, layout.STEP1_R,
                                    0.0, 0.17, 160),
                     mats["limestone_warm"], config.C_ARENA)
    util.cube_uv(step1, 2.0)
    step2 = geo.mesh("PLAZA_Step2",
                     *geo.ring_slab(layout.STEP1_R, layout.STEP2_R + 0.02,
                                    0.0, layout.TERRACE_Z, 160),
                     mats["limestone_warm"], config.C_ARENA)
    util.cube_uv(step2, 2.0)
    terrace = geo.mesh("PLAZA_Terrace",
                       *geo.ring_slab(layout.TERRACE_IN,
                                      layout.TERRACE_OUT,
                                      0.0, layout.TERRACE_Z, 200),
                       mats["limestone"], config.C_ARENA)
    util.cube_uv(terrace, 4.0)

    nosings = []
    nosings.append(geo.ring_slab(layout.ARENA_R - 0.08,
                                 layout.ARENA_R + 0.015,
                                 0.155, 0.178, 160))
    nosings.append(geo.ring_slab(layout.STEP1_R - 0.08,
                                 layout.STEP1_R + 0.015,
                                 0.325, 0.348, 160))
    nosings.append(geo.ring_slab(layout.TERRACE_IN - 0.06,
                                 layout.TERRACE_IN + 0.05,
                                 0.325, 0.348, 200))
    geo.merged_mesh("PLAZA_Nosings", nosings, mats["gold"], config.C_ARENA)


def _inlays(mats):
    gold_rings = []
    for r, w in ((5.9, 0.11), (9.2, 0.085), (12.25, 0.16)):
        gold_rings.append(geo.ring_slab(r - w * 0.5, r + w * 0.5,
                                        0.002, 0.012, 180))
    for i in range(24):
        a = TAU * i / 24.0
        gold_rings.append(geo.box(10.75 * math.cos(a), 10.75 * math.sin(a),
                                  0.002, 0.009, 2.95, 0.075, a))
    for i in range(16):
        a = TAU * i / 16.0 + TAU / 32.0
        gold_rings.append(geo.box(7.55 * math.cos(a), 7.55 * math.sin(a),
                                  0.002, 0.010, 2.6, 0.06, a))
    # Compass spokes radiating from the dais ring to the outer gold band.
    for i in range(8):
        a = TAU * i / 8.0 + TAU / 16.0
        gold_rings.append(geo.box(7.55 * math.cos(a), 7.55 * math.sin(a),
                                  0.002, 0.011, 3.20, 0.09, a))
    geo.merged_mesh("PLAZA_GoldInlays", gold_rings, mats["gold"],
                    config.C_ARENA)

    runes = []
    for i in range(12):
        a = TAU * i / 12.0
        runes.append(geo.box(11.1 * math.cos(a), 11.1 * math.sin(a),
                             0.003, 0.011, 0.72, 0.15, a))
        runes.append(geo.diamond(11.55 * math.cos(a), 11.55 * math.sin(a),
                                 0.010, 0.11, 0.30, 4))
    for i in range(16):
        a = TAU * i / 16.0 + TAU / 32.0
        runes.append(geo.diamond(7.55 * math.cos(a), 7.55 * math.sin(a),
                                 0.010, 0.07, 0.19, 4))
    geo.merged_mesh("PLAZA_RuneMarks", runes, mats["rune"], config.C_ARENA)


def _dais(mats):
    lower = geo.mesh("DAIS_Lower",
                     *geo.prism(0.0, 0.0, 0.0, 0.13, DAIS_R, DAIS_R, 96),
                     mats["limestone_warm"], config.C_ARENA)
    util.cube_uv(lower, 2.5)
    mid = geo.mesh("DAIS_Mid",
                   *geo.prism(0.0, 0.0, 0.0, 0.26, 4.15, 4.15, 96),
                   mats["limestone"], config.C_ARENA)
    util.cube_uv(mid, 2.0)
    top = geo.mesh("DAIS_Top",
                   *geo.prism(0.0, 0.0, 0.0, 0.42, 3.42, 3.42, 96),
                   mats["limestone_warm"], config.C_ARENA)
    util.cube_uv(top, 2.0)
    cap = geo.mesh("DAIS_Cap",
                   *geo.cylinder(0.0, 0.0, 0.42, 0.45, 3.40, 96),
                   mats["paving"], config.C_ARENA)
    util.cube_uv(cap, 2.0)

    gold = [
        geo.ring_tube(DAIS_R - 0.02, 0.145, 0.055, 6, 160),
        geo.ring_tube(4.13, 0.275, 0.045, 6, 140),
        geo.ring_tube(3.40, 0.462, 0.050, 6, 128),
        geo.ring_slab(0.50, 0.64, 0.458, 0.472, 64),
    ]
    geo.merged_mesh("DAIS_Gold", gold, mats["gold"], config.C_ARENA)

    runes = [
        geo.ring_slab(2.74, 3.10, 0.452, 0.466, 128),
        geo.ring_slab(1.00, 1.07, 0.452, 0.466, 96),
    ]
    for i in range(12):
        a = TAU * i / 12.0 + TAU / 24.0
        runes.append(geo.box(1.82 * math.cos(a), 1.82 * math.sin(a),
                             0.452, 0.464, 1.22, 0.075, a))
        runes.append(geo.diamond(2.42 * math.cos(a), 2.42 * math.sin(a),
                                 0.466, 0.060, 0.17, 4))
    geo.merged_mesh("DAIS_Runes", runes, mats["rune"], config.C_ARENA)

    # Four small pedestals with floating celadon shards.
    stone, crystals = [], []
    for i in range(4):
        a = TAU * (i + 0.5) / 4.0
        x, y = 2.30 * math.cos(a), 2.30 * math.sin(a)
        stone.append(geo.box(x, y, 0.45, 0.92, 0.52, 0.52, a))
        stone.append(geo.prism(x, y, 0.92, 1.02, 0.24, 0.16, 8, a))
        crystals.append(geo.diamond(x, y, 1.24, 0.11, 0.34, 6))
    geo.merged_mesh("DAIS_Pedestals", stone, mats["limestone"],
                    config.C_ARENA)
    geo.merged_mesh("DAIS_Shards", crystals, mats["rune"], config.C_ARENA)

    # The suspended heart crystal and its two tilted-looking stone rings.
    heart = [geo.diamond(0.0, 0.0, 3.05, 0.62, 2.10, 8)]
    for i in range(3):
        a = TAU * i / 3.0 + 0.4
        heart.append(geo.diamond(1.62 * math.cos(a), 1.62 * math.sin(a),
                                 3.05 + 0.28 * math.sin(a), 0.13, 0.40, 6))
    geo.merged_mesh("DAIS_Heart", heart, mats["rune"], config.C_ARENA)

    gold = [
        geo.torus_z(1.28, 0.05, 2.15, 96, 6),
        geo.torus_z(0.98, 0.045, 3.85, 96, 6),
        geo.torus_z(0.42, 0.035, 4.25, 64, 5),
    ]
    geo.merged_mesh("DAIS_HeartRings", gold, mats["gold"], config.C_ARENA)

    # Slow-drifting rune motes orbiting the suspended crystal.
    rng = util.sub_rng("sky_rune_motes")
    motes = []
    for _ in range(20):
        a = rng.uniform(0.0, TAU)
        rr = rng.uniform(1.35, 2.85)
        z = rng.uniform(3.05, 5.30)
        s = rng.uniform(0.018, 0.052)
        motes.append(geo.diamond(rr * math.cos(a), rr * math.sin(a), z,
                                 s, s * rng.uniform(1.6, 2.6), 4))
    geo.merged_mesh("DAIS_Motes", motes, mats["rune"], config.C_ARENA)


def _braziers(mats):
    stone, gold, flames = [], [], []
    positions = brazier_positions()
    for i, (x, y, _z) in enumerate(positions):
        a = TAU * (i + 0.5) / 4.0
        stone.append(geo.prism(x, y, 0.0, 0.20, 0.52, 0.40, 8, a))
        stone.append(geo.prism(x, y, 0.20, 0.34, 0.30, 0.22, 8, a))
        stone.append(geo.cylinder(x, y, 0.34, 1.46, 0.10, 10))
        gold.append(geo.prism(x, y, 1.46, 1.58, 0.20, 0.58, 12, a))
        gold.append(geo.prism(x, y, 1.58, 1.68, 0.58, 0.58, 12, a))
        gold.append(geo.torus_z(0.50, 0.035, 1.69, 32, 5, x, y))
        for k in range(3):
            aa = a + TAU * k / 3.0
            stone.append(geo.cylinder(x + 0.34 * math.cos(aa),
                                      y + 0.34 * math.sin(aa),
                                      0.0, 0.26, 0.055, 6))
        flames.append(geo.diamond(x, y, 2.05, 0.30, 0.74, 6))
        flames.append(geo.diamond(x, y, 2.22, 0.14, 0.42, 6))
    geo.merged_mesh("PLAZA_BrazierStone", stone, mats["limestone"],
                    config.C_ARENA)
    geo.merged_mesh("PLAZA_BrazierBronze", gold, mats["gold_deep"],
                    config.C_ARENA)
    geo.merged_mesh("PLAZA_BrazierFlames", flames, mats["flame"],
                    config.C_ARENA)
    return positions


def build_plaza(mats):
    util.reset_collection(config.C_ARENA)
    _floor(mats)
    _inlays(mats)
    _dais(mats)
    positions = _braziers(mats)
    print("[plaza] paved floor, gold inlays, rune dais and 4 braziers")
    return {"braziers": positions, "dais_radius": DAIS_R}
