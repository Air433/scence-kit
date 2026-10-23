"""Ivory plaza: floor, gold inlays, arena railing and braziers."""
from __future__ import annotations

import math

from arena_kit import config, util

from . import geometry as geo

TAU = math.pi * 2.0
PLAZA_R = 15.9
ARENA_R = 12.4
TERRACE_IN = 16.8
TERRACE_OUT = 22.4


def _floor(mats):
    floor = geo.mesh("PLAZA_Floor", *geo.cylinder(0.0, 0.0, -0.55, 0.0,
                                                 PLAZA_R, 128),
                     mats["marble"], config.C_ARENA)
    util.cube_uv(floor, 4.0)
    util.shade_smooth_by_angle(floor, 20.0)

    step_a = geo.mesh("PLAZA_StepA", *geo.ring_slab(15.3, 16.1, 0.0, 0.12, 160),
                      mats["marble"], config.C_ARENA)
    util.cube_uv(step_a, 2.0)
    step_b = geo.mesh("PLAZA_StepB", *geo.ring_slab(16.1, 16.9, 0.0, 0.24, 160),
                      mats["marble"], config.C_ARENA)
    util.cube_uv(step_b, 2.0)
    terrace = geo.mesh("PLAZA_Terrace",
                       *geo.ring_slab(TERRACE_IN, TERRACE_OUT, 0.0, 0.30, 180),
                       mats["marble_warm"], config.C_ARENA)
    util.cube_uv(terrace, 3.0)


def _inlays(mats):
    rings = []
    for r, w in ((3.4, 0.10), (6.0, 0.10), (8.6, 0.12), (11.2, 0.10),
                 (12.35, 0.18), (14.6, 0.08)):
        rings.append(geo.ring_slab(r - w * 0.5, r + w * 0.5, 0.002, 0.012, 180))
    for r, w in ((2.4, 0.08), (2.7, 0.04), (0.60, 0.05)):
        rings.append(geo.ring_slab(r - w * 0.5, r + w * 0.5, 0.014, 0.022, 96))
    geo.merged_mesh("PLAZA_GoldRings", rings, mats["gold"], config.C_ARENA)

    spokes = []
    for i in range(24):
        a = TAU * i / 24.0
        spokes.append(geo.box(7.87 * math.cos(a), 7.87 * math.sin(a),
                              0.002, 0.010, 8.94, 0.055, a))
    for i in range(12):
        a = TAU * i / 12.0 + TAU / 24.0
        spokes.append(geo.box(13.7 * math.cos(a), 13.7 * math.sin(a),
                              0.002, 0.010, 1.8, 0.045, a))
    geo.merged_mesh("PLAZA_GoldSpokes", spokes, mats["gold_deep"], config.C_ARENA)

    petals = []
    for i in range(16):
        a = TAU * i / 16.0
        petals.append(geo.box(1.65 * math.cos(a), 1.65 * math.sin(a),
                              0.004, 0.014, 1.30, 0.20, a))
        petals.append(geo.diamond(2.55 * math.cos(a), 2.55 * math.sin(a),
                                  0.03, 0.13, 0.05, 4))
    geo.merged_mesh("PLAZA_Rosette", petals, mats["gold"], config.C_ARENA)

    geo.mesh("PLAZA_RosetteCore", *geo.cylinder(0.0, 0.0, 0.016, 0.030, 0.42, 48),
             mats["gold"], config.C_ARENA)
    geo.mesh("PLAZA_RosetteGlow", *geo.ring_slab(0.44, 0.54, 0.016, 0.030, 64),
             mats["sconce"], config.C_ARENA)


def _railing(mats):
    marble, gold = [], []
    for i in range(48):
        a = TAU * i / 48.0
        x, y = ARENA_R * math.cos(a), ARENA_R * math.sin(a)
        marble.append(geo.box(x, y, 0.0, 1.10, 0.17, 0.17, a))
        gold.append(geo.box(x, y, 1.10, 1.17, 0.23, 0.23, a))
        gold.append(geo.box(x, y, 0.0, 0.08, 0.22, 0.22, a))
        for k in range(5):
            aa = a + TAU / 48.0 * (k + 1) / 6.0
            bx, by = ARENA_R * math.cos(aa), ARENA_R * math.sin(aa)
            gold.append(geo.cylinder(bx, by, 0.18, 1.00, 0.022, 8))
    gold.append(geo.ring_tube(ARENA_R, 1.03, 0.055, 8, 192))
    gold.append(geo.ring_tube(ARENA_R, 0.16, 0.035, 6, 192))
    gold.append(geo.ring_tube(ARENA_R, 0.62, 0.028, 6, 192))

    # Gilded urns crown the main railing posts.
    for i in range(8):
        a = TAU * i / 8.0
        x, y = ARENA_R * math.cos(a), ARENA_R * math.sin(a)
        gold.append(geo.box(x, y, 1.17, 1.26, 0.26, 0.26, a))
        gold.append(geo.prism(x, y, 1.26, 1.33, 0.15, 0.21, 12, a))
        gold.append(geo.prism(x, y, 1.33, 1.55, 0.23, 0.09, 12, a))
        gold.append(geo.cylinder(x, y, 1.55, 1.62, 0.11, 10))
        gold.append(geo.diamond(x, y, 1.76, 0.09, 0.28, 4))

    rail = geo.merged_mesh("PLAZA_RailingMarble", marble, mats["marble"],
                           config.C_ARENA)
    util.cube_uv(rail, 1.0)
    geo.merged_mesh("PLAZA_RailingGold", gold, mats["gold"], config.C_ARENA)


def _brazier(mats):
    gold, glow = [], []
    for i in range(4):
        a = TAU * (i + 0.5) / 4.0
        x, y = 11.55 * math.cos(a), 11.55 * math.sin(a)
        gold.append(geo.prism(x, y, 0.0, 0.16, 0.34, 0.28, 8, a))
        gold.append(geo.prism(x, y, 0.16, 0.28, 0.20, 0.15, 8, a))
        gold.append(geo.cylinder(x, y, 0.28, 1.42, 0.075, 10))
        gold.append(geo.prism(x, y, 1.42, 1.58, 0.16, 0.46, 12, a))
        gold.append(geo.prism(x, y, 1.58, 1.68, 0.46, 0.43, 12, a))
        for k in range(3):
            aa = a + TAU * k / 3.0
            gold.append(geo.cylinder(x + 0.30 * math.cos(aa),
                                     y + 0.30 * math.sin(aa),
                                     0.0, 0.22, 0.045, 6))
        glow.append(geo.diamond(x, y, 1.96, 0.22, 0.62, 6))
        glow.append(geo.diamond(x, y, 2.10, 0.11, 0.38, 6))
    geo.merged_mesh("PLAZA_Braziers", gold, mats["gold_deep"], config.C_ARENA)
    geo.merged_mesh("PLAZA_BrazierFlames", glow, mats["sconce"], config.C_ARENA)


def build_plaza(mats):
    util.reset_collection(config.C_ARENA)
    _floor(mats)
    _inlays(mats)
    _railing(mats)
    _brazier(mats)
    print("[plaza] marble floor, gold inlays, arena railing and braziers")
    return {"plaza_radius": PLAZA_R, "arena_radius": ARENA_R}
