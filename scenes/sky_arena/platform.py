"""Floating stone deck, its jagged rim and the rock hull below."""
from __future__ import annotations

import math

from arena_kit import config, util

from . import geometry as geo
from . import layout

TAU = math.pi * 2.0


def _rock_chunk(cx, cy, cz, size, rng, sides=7):
    ring = []
    for s in range(sides):
        a = TAU * s / sides + rng.uniform(-0.15, 0.15)
        r = size * rng.uniform(0.55, 1.0)
        ring.append((cx + r * math.cos(a), cy + r * math.sin(a),
                     cz + rng.uniform(-0.25, 0.25) * size))
    top = (cx + rng.uniform(-0.2, 0.2) * size,
           cy + rng.uniform(-0.2, 0.2) * size,
           cz + size * rng.uniform(0.55, 0.9))
    bot = (cx + rng.uniform(-0.2, 0.2) * size,
           cy + rng.uniform(-0.2, 0.2) * size,
           cz - size * rng.uniform(0.75, 1.2))
    verts = ring + [top, bot]
    faces = []
    for s in range(sides):
        t = (s + 1) % sides
        faces.append((s, t, sides))
        faces.append((sides + 1, t, s))
    return verts, faces


def _deck(mats, limestone, warm, dark):
    lip = geo.deck_ring(layout.TERRACE_OUT - 0.10, layout.edge_radius,
                        layout.LIP_Z, -0.62, 200)
    obj = geo.mesh("DECK_Lip", *lip, limestone, config.C_TERRAIN)
    util.cube_uv(obj, 3.0)

    warm.append(geo.ring_slab(layout.TERRACE_OUT - 0.18,
                              layout.TERRACE_OUT + 0.10,
                              layout.LIP_Z - 0.02, layout.TERRACE_Z + 0.015,
                              200))
    dark.append(geo.ring_slab(16.2, layout.TERRACE_OUT + 0.08,
                              -1.45, -0.58, 180))

    # Corbels under the rim and small gold brackets on the edge.
    gold = []
    for i in range(18):
        a = TAU * i / 18.0 + 0.06
        r = layout.edge_radius(a) - 0.30
        warm.append(geo.box(r * math.cos(a), r * math.sin(a),
                            -1.95, -0.55, 1.25, 0.52, a))
    for i in range(12):
        a = TAU * i / 12.0 + 0.11
        r = layout.edge_radius(a) - 0.18
        gold.append(geo.box(r * math.cos(a), r * math.sin(a),
                            -0.52, -0.20, 0.80, 0.30, a))

    geo.merged_mesh("DECK_WarmTrim", warm, mats["limestone_warm"],
                    config.C_TERRAIN)
    dark_obj = geo.merged_mesh("DECK_UnderDark", dark, mats["stone_dark"],
                               config.C_TERRAIN)
    if dark_obj is not None:
        util.cube_uv(dark_obj, 4.0)
    gold_obj = geo.merged_mesh("DECK_GoldBrackets", gold, mats["gold_deep"],
                               config.C_TERRAIN)
    util.shade_smooth_by_angle(gold_obj, 30.0)


def _hull(mats):
    rng = util.sub_rng("sky_hull")
    edge = lambda a: layout.edge_radius(a) * 0.985
    shell = geo.rock_shell(edge, -0.55, -17.5, rng, rings=10, segs=80)
    obj = geo.mesh("HULL_Rock", *shell, mats["rock"], config.C_TERRAIN)
    util.cube_uv(obj, 6.0)
    util.shade_smooth_by_angle(obj, 40.0)

    # Three hanging spurs keep the silhouette from reading as a flat disc.
    spurs = []
    for a, r, z0, z1, rad in ((3.55, 5.2, -7.8, -15.6, 2.1),
                              (0.80, 7.6, -6.2, -12.8, 1.7),
                              (5.15, 4.4, -8.6, -14.2, 1.5)):
        spurs.append(geo.prism(r * math.cos(a), r * math.sin(a), z0, z1,
                               rad, 0.18, 9, a))
    spur_obj = geo.merged_mesh("HULL_Spurs", spurs, mats["rock"],
                               config.C_TERRAIN)
    util.cube_uv(spur_obj, 5.0)

    # Boulders clinging to the underside and small rocks drifting nearby.
    chunks = []
    for a, r, z, size in ((0.35, 13.5, -2.8, 1.5), (2.35, 15.2, -3.5, 1.1),
                          (4.60, 11.8, -2.2, 1.3), (5.75, 16.6, -4.0, 0.9)):
        chunks.append(_rock_chunk(r * math.cos(a), r * math.sin(a), z,
                                  size, rng))
    for a, r, z, size in ((1.10, 27.0, -3.2, 1.6), (2.75, 26.0, -6.0, 1.0),
                          (4.25, 28.5, -2.4, 1.3), (0.20, 25.0, -7.5, 0.8),
                          (5.40, 25.8, -4.6, 1.1)):
        chunks.append(_rock_chunk(r * math.cos(a), r * math.sin(a), z,
                                  size, rng))
    chunk_obj = geo.merged_mesh("HULL_Chunks", chunks, mats["rock"],
                                config.C_TERRAIN)


def build_platform(mats):
    util.reset_collection(config.C_TERRAIN)
    warm = []
    _deck(mats, mats["limestone"], warm, [])
    _hull(mats)
    print("[platform] floating deck r~23 m, broken rim, 17.5 m rock hull")
    return {"deck_radius": layout.edge_radius(0.0)}
