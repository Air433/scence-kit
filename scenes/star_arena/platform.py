"""Floating marble platform shell and warm underside machinery."""
from __future__ import annotations

import math

from arena_kit import config, util

from . import geometry as geo

TAU = math.pi * 2.0
DECK_R = 25.2
TERRACE_OUT = 22.4


def _deck(marble, marble_warm, gold):
    marble.append(geo.ring_slab(TERRACE_OUT - 0.1, DECK_R, -0.10, 0.28, 192))
    marble_warm.append(geo.ring_slab(24.55, DECK_R, -2.00, -0.10, 192))
    gold.append(geo.torus_z(DECK_R - 0.06, 0.10, 0.22, 192, 6))
    gold.append(geo.torus_z(DECK_R - 0.06, 0.07, -0.35, 192, 6))
    gold.append(geo.torus_z(DECK_R - 0.06, 0.06, -1.20, 192, 6))
    gold.append(geo.torus_z(24.58, 0.08, -1.95, 192, 6))
    gold.append(geo.torus_z(22.55, 0.06, 0.24, 192, 6))

    for i in range(24):
        a = TAU * i / 24.0
        gold.append(geo.box(24.05 * math.cos(a), 24.05 * math.sin(a),
                            -0.04, 0.02, 1.60, 0.07, a + math.pi * 0.5))


def _underside(marble_warm, dark, gold, glow):
    marble_warm.append(geo.cylinder(0.0, 0.0, -1.55, -0.85, TERRACE_OUT, 160,
                                    r_top=TERRACE_OUT))
    marble_warm.append(geo.prism(0.0, 0.0, -4.10, -1.55, 7.8, 13.6, 96))
    dark.append(geo.prism(0.0, 0.0, -7.60, -4.10, 2.4, 7.8, 64))
    dark.append(geo.cylinder(0.0, 0.0, -8.40, -7.60, 1.15, 32))

    gold.append(geo.torus_z(13.65, 0.11, -1.58, 160, 6))
    gold.append(geo.torus_z(11.60, 0.09, -2.10, 128, 6))
    gold.append(geo.torus_z(9.20, 0.08, -2.80, 128, 6))
    gold.append(geo.torus_z(7.75, 0.07, -4.15, 96, 6))
    gold.append(geo.torus_z(2.30, 0.07, -4.55, 64, 6))
    for z, R in ((-5.10, 2.15), (-5.70, 1.95), (-6.30, 1.75), (-7.00, 1.55)):
        gold.append(geo.torus_z(R, 0.055, z, 48, 6))
    glow.append(geo.torus_z(2.10, 0.05, -5.10, 64, 6))
    glow.append(geo.diamond(0.0, 0.0, -8.55, 0.55, 1.05, 8))

    for i in range(8):
        a = TAU * i / 8.0
        marble_warm.append(geo.box(10.8 * math.cos(a), 10.8 * math.sin(a),
                                   -1.50, -1.40, 11.0, 0.42, a))


def build_platform(mats):
    util.reset_collection(config.C_TERRAIN)
    marble, marble_warm, dark, gold, glow = [], [], [], [], []
    _deck(marble, marble_warm, gold)
    _underside(marble_warm, dark, gold, glow)

    deck = geo.merged_mesh("PLATFORM_Marble", marble, mats["marble"],
                           config.C_TERRAIN)
    util.cube_uv(deck, 3.0)
    under = geo.merged_mesh("PLATFORM_UnderMarble", marble_warm,
                            mats["marble_warm"], config.C_TERRAIN)
    util.cube_uv(under, 4.0)
    geo.merged_mesh("PLATFORM_Dark", dark, mats["stone_dark"], config.C_TERRAIN)
    gold_obj = geo.merged_mesh("PLATFORM_Gold", gold, mats["gold"],
                               config.C_TERRAIN)
    util.shade_smooth_by_angle(gold_obj, 35.0)
    geo.merged_mesh("PLATFORM_Glow", glow, mats["glow"], config.C_TERRAIN)
    print("[platform] floating ivory deck, gold rim, hanging star")
    return {"radius": DECK_R}
