"""Tropical stone arena: tiered ring, brass sun compass, torches, string lights."""
from __future__ import annotations

import json
import math
import random

from mathutils import Vector

from arena_kit import config, util

from . import layout
from .geo import (
    MeshBuilder, annular_sector, box, catenary, cylinder_at, disc,
    uv_sphere,
)

TAU = math.pi * 2.0
SOUTH = -math.pi * 0.5
ENTRANCE_GAP = math.radians(46.0)


def _sector_mesh(z0, z1, r0, r1, a0, a1, segs, mat, mb, top_jitter=0.0,
                 rng=None):
    if top_jitter and rng is not None:
        z1 = z1 + rng.uniform(-top_jitter, top_jitter)
    v, f = annular_sector(r0, r1, z0, z1, a0, a1, segs=segs)
    mb.add(v, f, mat, smooth=False)


def _build_foundation(mb, mats):
    v, f = cylinder_at(0, 0, layout.ARENA_Z - 1.1, layout.ARENA_Z - 0.04,
                       layout.OUTER_R + 1.7, layout.OUTER_R + 1.35, sides=64)
    mb.add(v, f, mats["rock"], smooth=False)


def _build_floor(mb, mats, rng):
    bounds = [0.0, 1.0, 2.2, 3.4, 4.6, 5.8, 7.0, config.INNER_R + 0.06]
    for ri in range(len(bounds) - 1):
        r0, r1 = bounds[ri], bounds[ri + 1]
        if r0 < 1e-4:
            v, f = disc(0, 0, layout.ARENA_Z, r1, sides=32)
            mb.add(v, f, mats["stone"], smooth=False)
            continue
        rm = (r0 + r1) * 0.5
        sectors = max(8, int(TAU * rm / 1.5))
        gap = 0.028 / max(rm, 0.4)
        phase = rng.uniform(0, TAU)
        for s in range(sectors):
            a0 = phase + TAU * s / sectors + gap
            a1 = phase + TAU * (s + 1) / sectors - gap
            z = layout.ARENA_Z + rng.uniform(-0.012, 0.006)
            _sector_mesh(layout.ARENA_Z - 0.28, z, r0 + 0.02, r1 - 0.02,
                         a0, a1, 3, mats["stone"], mb)


def _build_tiers(mb, mats, rng):
    for i in range(config.TIER_COUNT):
        r_in = config.INNER_R + i * config.TIER_TREAD
        r_out = r_in + config.TIER_TREAD
        top = layout.ARENA_Z + (i + 1) * config.TIER_RISE
        blocks = 22
        for b in range(blocks):
            a0 = SOUTH + ENTRANCE_GAP + (TAU - 2 * ENTRANCE_GAP) * b / blocks
            a1 = SOUTH + ENTRANCE_GAP + (TAU - 2 * ENTRANCE_GAP) * (b + 1) / blocks
            gap = 0.012
            _sector_mesh(top - 0.42, top, r_in + 0.02, r_out - 0.02,
                         a0 + gap, a1 - gap, 4, mats["stone"], mb,
                         top_jitter=0.008, rng=rng)
        # dark shadow reveal under each tier lip
        a0 = SOUTH + ENTRANCE_GAP
        a1 = SOUTH + TAU - ENTRANCE_GAP
        _sector_mesh(top - 0.14, top - 0.08, r_out - 0.05, r_out + 0.04,
                     a0, a1, 96, mats["rock"], mb)


def _build_parapet(mb, mats, rng):
    r = layout.OUTER_R + 0.95
    blocks = 30
    for b in range(blocks):
        a = TAU * b / blocks
        # Keep the south entrance and the north-east path open.
        d_south = abs((a - SOUTH + math.pi) % TAU - math.pi)
        d_path = abs((a - math.radians(42)) + math.pi) % TAU - math.pi
        if d_south < math.radians(25) or abs(d_path) < math.radians(9):
            continue
        h = 0.82 + rng.uniform(-0.03, 0.03)
        _sector_mesh(layout.ARENA_Z, layout.ARENA_Z + h,
                     r, r + 0.48,
                     a + 0.012, a + TAU / blocks - 0.012, 4,
                     mats["stone"], mb)
        # cap
        _sector_mesh(layout.ARENA_Z + h, layout.ARENA_Z + h + 0.10,
                     r - 0.04, r + 0.54,
                     a + 0.006, a + TAU / blocks - 0.006, 4,
                     mats["stone"], mb)


def _build_pillars(mb, mats):
    r = layout.OUTER_R + 1.55
    for k in range(12):
        a = TAU * k / 12 + math.radians(15)
        d_south = abs((a - SOUTH + math.pi) % TAU - math.pi)
        d_path = abs((a - math.radians(42)) + math.pi) % TAU - math.pi
        if d_south < math.radians(28) or abs(d_path) < math.radians(11):
            continue
        x, y = math.cos(a) * r, math.sin(a) * r
        z = layout.terrain_height(x, y)
        mb.add(*box(x, y, z - 0.2, z + 1.45, 0.44, 0.44, a), mats["stone"],
               smooth=False)
        mb.add(*box(x, y, z + 1.45, z + 1.62, 0.66, 0.66, a), mats["stone"],
               smooth=False)
        mb.add(*box(x, y, z + 1.62, z + 1.72, 0.56, 0.56, a), mats["stone"],
               smooth=False)


def _build_apron(mb, mats):
    """Fill the entrance gap at floor level so the ring has no hole."""
    a0 = SOUTH + ENTRANCE_GAP
    a1 = SOUTH + TAU - ENTRANCE_GAP
    _sector_mesh(layout.ARENA_Z - 0.55, layout.ARENA_Z - 0.015,
                 config.INNER_R - 0.06, layout.OUTER_R + 1.55,
                 a0, a1, 72, mats["stone"], mb)
    # Two low cheek walls framing the approach.
    for side in (-1.0, 1.0):
        a = SOUTH + side * ENTRANCE_GAP
        r = layout.OUTER_R + 0.9
        x, y = math.cos(a) * r, math.sin(a) * r
        mb.add(*box(x, y, layout.ARENA_Z, layout.ARENA_Z + 0.72,
                    1.5, 0.55, a + math.pi * 0.5),
               mats["stone"], smooth=False)


def _build_compass(mb, mats):
    z = layout.ARENA_Z + 0.018
    # two rings + fine outer ticks
    _sector_mesh(z, z + 0.022, 3.42, 3.60, 0, TAU, 96, mats["compass"], mb)
    _sector_mesh(z, z + 0.018, 1.02, 1.14, 0, TAU, 64, mats["compass"], mb)
    for k in range(24):
        a = TAU * k / 24
        length = 0.52 if k % 6 == 0 else 0.30
        mx = math.cos(a) * (3.12 - length * 0.5)
        my = math.sin(a) * (3.12 - length * 0.5)
        v, f = box(mx, my, z, z + 0.014, length, 0.055, a)
        mb.add(v, f, mats["compass"], smooth=False)
    # long cardinal rays
    for k in range(8):
        a = TAU * k / 8
        length = 1.75 if k % 2 == 0 else 1.25
        r0 = 1.30
        mx = math.cos(a) * (r0 + length * 0.5)
        my = math.sin(a) * (r0 + length * 0.5)
        v, f = box(mx, my, z, z + 0.016, length, 0.075, a)
        mb.add(v, f, mats["compass"], smooth=False)
        # arrowhead
        tx = math.cos(a) * (r0 + length + 0.14)
        ty = math.sin(a) * (r0 + length + 0.14)
        v, f = box(tx, ty, z, z + 0.016, 0.34, 0.34, a + math.pi * 0.25)
        mb.add(v, f, mats["compass"], smooth=False)
    v, f = disc(0, 0, z + 0.004, 0.92, sides=48)
    mb.add(v, f, mats["compass"], smooth=False)


def _build_torch(mats, i, x, y, z):
    mb = MeshBuilder()
    # post, collar, basket
    v, f = cylinder_at(x, y, z - 0.25, z + 2.55, 0.11, 0.075, sides=10)
    mb.add(v, f, mats["wood"], smooth=True)
    v, f = cylinder_at(x, y, z + 2.42, z + 2.56, 0.19, 0.16, sides=12)
    mb.add(v, f, mats["metal"], smooth=True)
    v, f = cylinder_at(x, y, z + 2.56, z + 2.78, 0.25, 0.34, sides=12)
    mb.add(v, f, mats["metal"], smooth=True)
    obj = mb.build(f"PROP_Torch_{i:02d}", config.C_ARENA, uv="smart")

    fb = MeshBuilder()
    # stylised teardrop flame: three lobes
    for k, (dz, r) in enumerate(((0.0, 0.20), (0.18, 0.15), (0.33, 0.08))):
        v, f = uv_sphere(x + (k - 1) * 0.035, y, z + 2.94 + dz,
                         r, sides=10, rings=6, scale=(1.0, 1.0, 1.7))
        fb.add(v, f, mats["flame"], smooth=True)
    flame = fb.build(f"PROP_TorchFlame_{i:02d}", config.C_ARENA, uv="planar")
    return obj, flame


def _build_string_lights(mats, rng):
    x0, x1 = -6.2, 6.2
    y = -16.0
    z0 = layout.terrain_height(x0, y)
    z1 = layout.terrain_height(x1, y)
    pole_h = 4.7
    mb = MeshBuilder()
    for x, z in ((x0, z0), (x1, z1)):
        v, f = cylinder_at(x, y, z - 0.25, z + pole_h, 0.12, 0.09, sides=10)
        mb.add(v, f, mats["wood"], smooth=True)
        v, f = box(x, y, z + pole_h - 0.15, z + pole_h - 0.02, 0.7, 0.12)
        mb.add(v, f, mats["wood"], smooth=False)
    poles = mb.build("PROP_StringPoles", config.C_PROPS, uv="smart")

    p0 = (x0, y, z0 + pole_h - 0.10)
    p1 = (x1, y, z1 + pole_h - 0.10)
    pts = catenary(p0, p1, 1.25, segments=24)
    v, f = util.make_tube(pts, 0.018, sides=5, caps=True)
    cb = MeshBuilder()
    cb.add(v, f, mats["metal"], smooth=True)
    cable = cb.build("PROP_StringCable", config.C_PROPS, uv="planar")

    bb = MeshBuilder()
    import math
    for k in range(1, 17):
        t = k / 17.0
        x = p0[0] + (p1[0] - p0[0]) * t
        z = p0[2] + (p1[2] - p0[2]) * t - 1.25 * math.sin(math.pi * t)
        v, f = uv_sphere(x, y, z - 0.10, 0.055, sides=8, rings=5)
        bb.add(v, f, mats["bulb"], smooth=True)
    bulbs = bb.build("PROP_StringBulbs", config.C_PROPS, uv="planar")
    return poles, cable, bulbs


def build_arena(mats):
    util.reset_collection(config.C_ARENA)
    util.reset_collection(config.C_PROPS)
    rng = util.sub_rng("island_arena")

    stone = MeshBuilder()
    _build_foundation(stone, mats)
    _build_floor(stone, mats, rng)
    _build_tiers(stone, mats, rng)
    _build_parapet(stone, mats, rng)
    _build_pillars(stone, mats)
    _build_apron(stone, mats)
    arena_obj = stone.build("ARENA_Structure", config.C_ARENA, uv="planar",
                            uv_scale=5.5)
    util.bevel(arena_obj, 0.025, segments=2, angle_deg=32.0)
    util.apply_modifiers(arena_obj)
    util.cube_uv(arena_obj, 4.0)

    compass = MeshBuilder()
    _build_compass(compass, mats)
    compass_obj = compass.build("ARENA_Compass", config.C_ARENA,
                                uv="planar", uv_scale=4.0)

    torches = []
    flames = []
    for i, deg in enumerate((22.5, 67.5, 112.5, 157.5, 202.5, 247.5,
                             292.5, 337.5)):
        a = math.radians(deg)
        r = layout.OUTER_R + 2.15
        x, y = math.cos(a) * r, math.sin(a) * r
        z = layout.terrain_height(x, y)
        torch, flame = _build_torch(mats, i, x, y, z)
        torches.append((x, y, z + 3.06))
        flames.append(flame)

    poles, cable, bulbs = _build_string_lights(mats, rng)
    for obj in (poles, cable, bulbs):
        util.link_object(obj, config.C_EXPORT)

    arena_obj["torch_lights"] = json.dumps(torches)
    print(f"[arena] tiers + compass + {len(torches)} torches + string lights")
    return {
        "arena": arena_obj, "compass": compass_obj,
        "torches": torches, "flames": flames,
        "string_lights": [poles, cable, bulbs],
    }
