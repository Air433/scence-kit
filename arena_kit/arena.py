"""Circular elven arena: floor, tiered seating, stairs and rune circle."""
from __future__ import annotations

import math
import random

import bmesh
import bpy
from mathutils import Vector

from . import config, util

TAU = math.pi * 2.0


# ---------------------------------------------------------------------------
# Primitive builders (combined into one bmesh per category)
# ---------------------------------------------------------------------------

def _add_verts_faces(bm, verts, faces):
    bmv = [bm.verts.new(tuple(v)) for v in verts]
    for f in faces:
        try:
            bm.faces.new([bmv[i] for i in f])
        except ValueError:
            pass


def _annular_sector(r_in, r_out, z0, z1, a0, a1, segs=2):
    verts = []
    faces = []
    rings = [(r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)]
    for r, z in rings:
        for s in range(segs + 1):
            a = a0 + (a1 - a0) * s / segs
            verts.append((r * math.cos(a), r * math.sin(a), z))
    n = segs + 1
    for s in range(segs):
        faces.append((0 * n + s, 0 * n + s + 1, 1 * n + s + 1, 1 * n + s))
        faces.append((1 * n + s, 1 * n + s + 1, 2 * n + s + 1, 2 * n + s))
        faces.append((2 * n + s, 2 * n + s + 1, 3 * n + s + 1, 3 * n + s))
        faces.append((3 * n + s, 3 * n + s + 1, 0 * n + s + 1, 0 * n + s))
    faces.append((0, 3, 2, 1))
    faces.append((segs, n + segs, 2 * n + segs, 3 * n + segs))
    return verts, faces


def _box(cx, cy, z0, z1, sx, sy, angle=0.0):
    hx, hy = sx * 0.5, sy * 0.5
    ca, sa = math.cos(angle), math.sin(angle)
    pts = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    verts = []
    for x, y in pts:
        verts.append((cx + x * ca - y * sa, cy + x * sa + y * ca, z0))
    for x, y in pts:
        verts.append((cx + x * ca - y * sa, cy + x * sa + y * ca, z1))
    faces = [
        (0, 1, 2, 3),          # bottom
        (7, 6, 5, 4),          # top
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    return verts, faces


def _cylinder(radius, z0, z1, sides=96):
    verts = []
    for z in (z0, z1):
        for s in range(sides):
            a = TAU * s / sides
            verts.append((radius * math.cos(a), radius * math.sin(a), z))
    faces = []
    for s in range(sides):
        a = s
        b = (s + 1) % sides
        faces.append((a, b, sides + b, sides + a))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(range(sides, 2 * sides)))
    return verts, faces


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------

def _build_underlay():
    bm = bmesh.new()
    v, f = _cylinder(config.INNER_R + 0.06, -0.32, -0.035, 128)
    _add_verts_faces(bm, v, f)
    return bm


def _build_tier_core():
    bm = bmesh.new()
    gap = 0.30
    a0 = math.pi * 0.5 + gap * 0.5
    a1 = math.pi * 0.5 + TAU - gap * 0.5
    for i in range(config.TIER_COUNT):
        r_in = config.INNER_R + i * config.TIER_TREAD
        r_out = r_in + config.TIER_TREAD
        h = (i + 1) * config.TIER_RISE
        v, f = _annular_sector(r_in, r_out, -0.22, h, a0, a1, segs=96)
        _add_verts_faces(bm, v, f)
    return bm


def _build_floor_slabs(rng: random.Random):
    bm = bmesh.new()
    # center hex slab
    v, f = _cylinder(1.22, -0.14, 0.0, 6)
    _add_verts_faces(bm, v, f)

    bounds = [1.22, 2.5, 3.8, 5.1, 6.4, 7.7, config.INNER_R]
    for ri in range(len(bounds) - 1):
        r0 = bounds[ri]
        r1 = bounds[ri + 1]
        rm = (r0 + r1) * 0.5
        sectors = max(8, int(TAU * rm / 1.45))
        gap_ang = 0.045 / max(rm, 0.5)
        phase = rng.uniform(0, TAU)
        for s in range(sectors):
            a0 = phase + TAU * s / sectors + gap_ang * 0.5
            a1 = phase + TAU * (s + 1) / sectors - gap_ang * 0.5
            z = rng.uniform(-0.009, 0.004)
            v, f = _annular_sector(r0 + 0.02, r1 - 0.02, -0.15, z, a0, a1, segs=2)
            _add_verts_faces(bm, v, f)
    return bm


def _build_tier_slabs(rng: random.Random):
    bm = bmesh.new()
    gap = 0.30
    north0 = math.pi * 0.5 + gap * 0.5
    north1 = math.pi * 0.5 + TAU - gap * 0.5
    for i in range(config.TIER_COUNT):
        r_in = config.INNER_R + i * config.TIER_TREAD
        r_out = r_in + config.TIER_TREAD
        h = (i + 1) * config.TIER_RISE
        rm = (r_in + r_out) * 0.5
        sectors = max(14, int(TAU * rm / 1.05))
        gap_ang = 0.035 / max(rm, 0.5)
        phase = rng.uniform(0, TAU)
        for s in range(sectors):
            a0 = phase + TAU * s / sectors + gap_ang * 0.5
            a1 = phase + TAU * (s + 1) / sectors - gap_ang * 0.5
            mid = (a0 + a1) * 0.5 % TAU
            # leave the north stair gap clear
            delta = (mid - math.pi * 0.5 + math.pi) % TAU - math.pi
            if abs(delta) < gap * 0.5:
                continue
            z = h + rng.uniform(-0.006, 0.004)
            v, f = _annular_sector(r_in + 0.025, r_out - 0.025, h - 0.09, z, a0, a1, segs=2)
            _add_verts_faces(bm, v, f)
    return bm


def _build_stairs():
    bm = bmesh.new()
    depth = (config.OUTER_R - config.INNER_R) / 5.0
    for k in range(5):
        yc = config.INNER_R + depth * (k + 0.5)
        top = 0.13 * (k + 1)
        v, f = _box(0.0, yc, -0.10, top, 2.35, depth + 0.01)
        _add_verts_faces(bm, v, f)
    # side cheek walls
    for sx in (-1.30, 1.30):
        v, f = _box(sx, (config.INNER_R + config.OUTER_R) * 0.5, -0.18,
                    0.72, 0.22, config.OUTER_R - config.INNER_R)
        _add_verts_faces(bm, v, f)
    return bm


def _build_rune(rng: random.Random):
    bm = bmesh.new()
    # outer and inner rings as thin annuli
    for radius, width in ((config.RUNE_R, 0.10), (1.15, 0.055)):
        for s in range(128):
            a0 = TAU * s / 128
            a1 = TAU * (s + 1) / 128
            v, f = _annular_sector(radius - width * 0.5, radius + width * 0.5,
                                   0.006, 0.018, a0, a1, segs=1)
            _add_verts_faces(bm, v, f)

    # glyphs: angular bars arranged around the ring
    patterns = [
        [((0, -0.5), (0, 0.5)), ((-0.35, -0.2), (0.35, 0.2)), ((-0.35, 0.35), (0.35, -0.35))],
        [((0, -0.5), (0, 0.5)), ((-0.35, 0.5), (0.35, 0.5)), ((0, 0), (0.35, -0.4))],
        [((-0.3, -0.5), (-0.3, 0.5)), ((0.3, -0.5), (0.3, 0.5)), ((-0.3, 0), (0.3, 0))],
        [((0, -0.5), (0, 0.5)), ((-0.4, 0.3), (0, 0)), ((0, 0), (0.4, 0.3))],
    ]
    for g in range(12):
        ang = TAU * g / 12 + 0.1
        cx = math.cos(ang) * 2.55
        cy = math.sin(ang) * 2.55
        tangent = ang + math.pi * 0.5
        pat = patterns[rng.randint(0, len(patterns) - 1)]
        for (x0, y0), (x1, y1) in pat:
            # local coordinates: x tangential, y radial
            p0 = (cx + math.cos(tangent) * x0 * 0.55 - math.cos(ang) * y0 * 0.55,
                  cy + math.sin(tangent) * x0 * 0.55 - math.sin(ang) * y0 * 0.55)
            p1 = (cx + math.cos(tangent) * x1 * 0.55 - math.cos(ang) * y1 * 0.55,
                  cy + math.sin(tangent) * x1 * 0.55 - math.sin(ang) * y1 * 0.55)
            mx, my = (p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5
            length = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            angle = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            v, f = _box(mx, my, 0.006, 0.018, length, 0.045, angle)
            _add_verts_faces(bm, v, f)

    # radial ticks
    for g in range(48):
        ang = TAU * g / 48
        r = (config.RUNE_R + 1.15) * 0.5
        cx, cy = math.cos(ang) * r, math.sin(ang) * r
        v, f = _box(cx, cy, 0.006, 0.018, 0.30, 0.025, ang)
        _add_verts_faces(bm, v, f)
    return bm


def build_arena(mats):
    util.reset_collection(config.C_ARENA)
    rng = util.sub_rng("arena")

    under = util.bmesh_object("ARENA_Underlay", _build_underlay(), config.C_ARENA,
                              mats["underlay"])
    core = util.bmesh_object("ARENA_TierCore", _build_tier_core(), config.C_ARENA,
                             mats["stone_dark"])
    floor = util.bmesh_object("ARENA_Flagstones", _build_floor_slabs(rng), config.C_ARENA,
                              mats["stone"])
    tiers = util.bmesh_object("ARENA_TierSlabs", _build_tier_slabs(rng), config.C_ARENA,
                              mats["stone"])
    stairs = util.bmesh_object("ARENA_Stairs", _build_stairs(), config.C_ARENA,
                               mats["stone_warm"])
    rune = util.bmesh_object("ARENA_Rune", _build_rune(rng), config.C_ARENA,
                             mats["rune"])

    for obj in (floor, tiers, stairs):
        util.bevel(obj, 0.014, segments=2, angle_deg=35.0)
        util.apply_modifiers(obj)
        util.cube_uv(obj, 2.0)
    util.cube_uv(core, 3.0)
    util.cube_uv(under, 3.0)
    util.shade_smooth_by_angle(floor, 35.0)
    util.shade_smooth_by_angle(tiers, 35.0)
    util.shade_smooth_by_angle(stairs, 35.0)

    for obj in (under, core, floor, tiers, stairs, rune):
        util.link_object(obj, config.C_EXPORT)

    print("[arena] built floor, 3 tiers, stairs, rune circle")
    return {
        "underlay": under, "core": core, "floor": floor,
        "tiers": tiers, "stairs": stairs, "rune": rune,
    }
