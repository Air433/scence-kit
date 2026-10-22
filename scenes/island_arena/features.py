"""Landmarks and beach dressing: lighthouse, keeper's cottage, rocks, path.

These are the exports the Godot layer animates by name:
``LIGHTHOUSE_BeamOrigin`` (beam pivot), ``LIGHTHOUSE_Glass`` and
``COTTAGE_Windows`` (emissive glass).
"""
from __future__ import annotations

import math

import bpy

from arena_kit import config, util

from . import layout
from .geo import MeshBuilder, box, cone, cylinder_at, uv_sphere

TAU = math.pi * 2.0
LX = layout.LIGHTHOUSE_X
LY = layout.LIGHTHOUSE_Y
LZ = layout.LIGHTHOUSE_BASE_Z

COTTAGE_X = 26.35
COTTAGE_Y = 17.75
COTTAGE_Z = 6.75


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _circle_points(cx, cy, z, r, n=40):
    return [(cx + r * math.cos(TAU * i / n),
             cy + r * math.sin(TAU * i / n), z) for i in range(n + 1)]


def _rock_blob(cx, cy, cz, rx, ry, rz, rng, sides=9, rings=4, jag=0.18):
    """Lumpy low-poly boulder sharing its vertices (no cracks)."""
    verts = []
    for j in range(1, rings):
        phi = math.pi * j / rings
        sp, cp = math.sin(phi), math.cos(phi)
        for s in range(sides):
            th = TAU * s / sides
            bump = 1.0 + rng.uniform(-jag, jag) + 0.10 * math.sin(th * 3.0 + j)
            verts.append((
                cx + sp * math.cos(th) * rx * bump,
                cy + sp * math.sin(th) * ry * bump,
                cz + cp * rz * bump,
            ))
    top = len(verts)
    verts.append((cx + rng.uniform(-0.12, 0.12) * rx,
                  cy + rng.uniform(-0.12, 0.12) * ry,
                  cz + rz * (1.0 + rng.uniform(-jag * 0.4, jag * 0.4))))
    bot = len(verts)
    verts.append((cx + rng.uniform(-0.10, 0.10) * rx,
                  cy + rng.uniform(-0.10, 0.10) * ry,
                  cz - rz * (1.0 + rng.uniform(-jag * 0.4, jag * 0.4))))
    faces = []
    for j in range(rings - 2):
        for s in range(sides):
            a = j * sides + s
            b = j * sides + (s + 1) % sides
            c = (j + 1) * sides + (s + 1) % sides
            d = (j + 1) * sides + s
            faces.append((a, b, c, d))
    base = (rings - 2) * sides
    for s in range(sides):
        faces.append((top, (s + 1) % sides, s))
        faces.append((bot, base + s, base + (s + 1) % sides))
    return verts, faces


def _stone_slab(cx, cy, z, rx, ry, yaw, thickness=0.10, sides=10, phase=0.0):
    ca, sa = math.cos(yaw), math.sin(yaw)
    bot, top = [], []
    for i in range(sides):
        a = phase + TAU * i / sides
        lx, ly = rx * math.cos(a), ry * math.sin(a)
        for ring, zz in ((bot, z), (top, z + thickness)):
            ring.append((cx + lx * ca - ly * sa, cy + lx * sa + ly * ca, zz))
    faces = []
    for i in range(sides):
        n = (i + 1) % sides
        faces.append((i, n, sides + n, sides + i))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(range(sides, 2 * sides)))
    return bot + top, faces


def _gable_roof(cx, cy, w, d, eave, ridge):
    hw, hd = w * 0.5, d * 0.5
    a = (cx - hw, cy - hd, eave)
    b = (cx + hw, cy - hd, eave)
    c = (cx, cy - hd, ridge)
    dd = (cx - hw, cy + hd, eave)
    e = (cx + hw, cy + hd, eave)
    f = (cx, cy + hd, ridge)
    verts = [a, b, c, dd, e, f]
    faces = [
        (0, 2, 5, 3),   # west slope
        (1, 4, 5, 2),   # east slope
        (0, 1, 2),      # south gable
        (3, 5, 4),      # north gable
    ]
    return verts, faces


# ---------------------------------------------------------------------------
# Lighthouse
# ---------------------------------------------------------------------------

def _lighthouse(mats):
    mb = MeshBuilder()
    b = MeshBuilder()  # glass
    w = MeshBuilder()  # warm windows

    # Stone footing and a stepped torus-like collar.
    mb.add(*cylinder_at(LX, LY, LZ - 1.4, LZ + 0.42, 3.25, 2.80, 48),
           mats["stone"], smooth=False)
    mb.add(*cylinder_at(LX, LY, LZ + 0.42, LZ + 0.68, 2.92, 2.70, 48),
           mats["stone"], smooth=False)

    bands = 6
    band_h = 2.30
    z = LZ + 0.68
    r_bottom, r_top = 2.48, 1.48
    for i in range(bands):
        t0, t1 = i / bands, (i + 1) / bands
        r0 = r_bottom + (r_top - r_bottom) * t0
        r1 = r_bottom + (r_top - r_bottom) * t1
        mat = mats["paint_red"] if i in (2, 5) else mats["plaster"]
        mb.add(*cylinder_at(LX, LY, z, z + band_h, r0, r1, 48),
               mat, smooth=True)
        if i < bands - 1:
            mb.add(*cylinder_at(LX, LY, z + band_h - 0.07,
                                z + band_h + 0.06, r1 + 0.05, r1 + 0.07, 48),
                   mats["plaster"], smooth=False)
        z += band_h

    shaft_top = z
    # Gallery corbels and deck.
    for k in range(16):
        a = TAU * k / 16
        x, y = LX + 2.10 * math.cos(a), LY + 2.10 * math.sin(a)
        mb.add(*box(x, y, shaft_top - 0.42, shaft_top - 0.02, 0.26, 0.46, a),
               mats["stone"], smooth=False)
    mb.add(*cylinder_at(LX, LY, shaft_top, shaft_top + 0.30, 2.46, 2.40, 48),
           mats["stone"], smooth=False)
    deck = shaft_top + 0.30

    # Railing posts + two rings.
    for k in range(16):
        a = TAU * k / 16
        x, y = LX + 2.24 * math.cos(a), LY + 2.24 * math.sin(a)
        mb.add(*box(x, y, deck, deck + 1.02, 0.075, 0.075, a),
               mats["metal"], smooth=False)
    for zr in (deck + 0.56, deck + 1.02):
        pts = _circle_points(LX, LY, zr, 2.24, 48)
        v, f = util.make_tube(pts, 0.035, sides=6, caps=False)
        mb.add(v, f, mats["metal"], smooth=True)

    # Lantern room base, mullions, glass, roof.
    mb.add(*cylinder_at(LX, LY, deck, deck + 0.24, 1.58, 1.42, 40),
           mats["metal"], smooth=True)
    glass_z0 = deck + 0.24
    glass_z1 = glass_z0 + 1.95
    for k in range(8):
        a = TAU * k / 8
        x, y = LX + 1.30 * math.cos(a), LY + 1.30 * math.sin(a)
        mb.add(*box(x, y, glass_z0, glass_z1, 0.085, 0.13, a),
               mats["metal"], smooth=False)
    b.add(*cylinder_at(LX, LY, glass_z0, glass_z1, 1.27, 1.27, 32),
          mats["lighthouse_glass"], smooth=True)
    mb.add(*cylinder_at(LX, LY, glass_z1, glass_z1 + 0.18, 1.55, 1.62, 40),
           mats["metal"], smooth=False)
    mb.add(*cone(LX, LY, glass_z1 + 0.18, glass_z1 + 1.55, 1.72, 40),
           mats["paint_red"], smooth=True)
    mb.add(*cylinder_at(LX, LY, glass_z1 + 1.50, glass_z1 + 2.05,
                        0.055, 0.045, 10), mats["metal"], smooth=True)
    mb.add(*uv_sphere(LX, LY, glass_z1 + 2.12, 0.11, sides=10, rings=6),
           mats["metal"], smooth=True)

    # Door facing the path (-Y).
    door_z0 = LZ + 0.70
    mb.add(*box(LX, LY - 2.34, door_z0, door_z0 + 2.05, 1.08, 0.36),
           mats["wood"], smooth=False)
    for sx in (-0.68, 0.68):
        mb.add(*box(LX + sx, LY - 2.36, door_z0 - 0.12, door_z0 + 2.22,
                    0.22, 0.42), mats["stone"], smooth=False)
    mb.add(*box(LX, LY - 2.36, door_z0 + 2.05, door_z0 + 2.30,
                1.62, 0.44), mats["stone"], smooth=False)

    # Tower windows climb the south face.
    for zw in (4.6, 8.4, 12.0):
        zc = LZ + 0.7 + zw
        t = (zc - (LZ + 0.68)) / (band_h * bands)
        r = r_bottom + (r_top - r_bottom) * max(0.0, min(1.0, t))
        wy = LY - r + 0.03
        w.add(*box(LX, wy, zc, zc + 0.82, 0.34, 0.22),
              mats["window"], smooth=False)
        mb.add(*box(LX, wy, zc - 0.12, zc, 0.52, 0.30),
               mats["stone"], smooth=False)
        mb.add(*box(LX, wy, zc + 0.82, zc + 0.94, 0.52, 0.30),
               mats["stone"], smooth=False)

    structure = mb.build("LIGHTHOUSE_Structure", config.C_ARCH, uv="smart")
    util.shade_smooth_by_angle(structure, 34.0)
    glass = b.build("LIGHTHOUSE_Glass", config.C_ARCH, uv="planar")
    windows = w.build("LIGHTHOUSE_Windows", config.C_ARCH, uv="planar")
    for obj in (structure, glass, windows):
        util.link_object(obj, config.C_EXPORT)

    light_z = glass_z0 + 1.1
    empty = bpy.data.objects.new("LIGHTHOUSE_BeamOrigin", None)
    empty.empty_display_type = "SPHERE"
    empty.empty_display_size = 0.6
    empty.location = (LX, LY, light_z)
    util.link_object(empty, config.C_ARCH)
    util.link_object(empty, config.C_EXPORT)

    print(f"[features] lighthouse {LZ + 19.9:.1f}m top at ({LX}, {LY})")
    return {
        "structure": structure,
        "glass": glass,
        "windows": windows,
        "beam_origin": empty,
        "light_pos": (LX, LY, light_z),
        "top_z": glass_z1 + 2.1,
    }


# ---------------------------------------------------------------------------
# Keeper's cottage
# ---------------------------------------------------------------------------

def _cottage(mats):
    cx, cy = COTTAGE_X, COTTAGE_Y
    mb = MeshBuilder()
    wb = MeshBuilder()

    mb.add(*box(cx, cy, 4.6, COTTAGE_Z, 7.2, 5.4), mats["stone"],
           smooth=False)
    mb.add(*box(cx - 3.95, cy, 5.95, COTTAGE_Z - 0.05, 1.35, 2.4),
           mats["stone"], smooth=False)
    mb.add(*box(cx, cy, COTTAGE_Z, COTTAGE_Z + 0.22, 5.5, 4.05),
           mats["stone"], smooth=False)

    wall_z0 = COTTAGE_Z + 0.22
    wall_z1 = COTTAGE_Z + 2.55
    mb.add(*box(cx, cy, wall_z0, wall_z1, 5.1, 3.7), mats["plaster"],
           smooth=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.add(*box(cx + sx * 2.48, cy + sy * 1.78, wall_z0, wall_z1,
                        0.24, 0.24), mats["stone"], smooth=False)

    # Door + frame on the lighthouse-facing (west) wall.
    mb.add(*box(cx - 2.57, cy, wall_z0, wall_z0 + 2.05, 0.16, 1.02),
           mats["wood"], smooth=False)
    mb.add(*box(cx - 2.6, cy, wall_z0 + 2.05, wall_z0 + 2.25,
                0.22, 1.42), mats["stone"], smooth=False)

    # Two shuttered windows on the west wall, one on the south wall.
    def window_at(x, y, zc, yaw):
        ca, sa = math.cos(yaw), math.sin(yaw)
        # opening (emissive)
        wb.add(*box(x, y, zc, zc + 0.82, 0.72, 0.16, yaw), mats["window"],
               smooth=False)
        # trim
        for off in (-0.48, 0.48):
            tx = x + ca * off
            ty = y + sa * off
            mb.add(*box(tx, ty, zc - 0.1, zc + 0.92, 0.16, 0.22, yaw),
                   mats["stone"], smooth=False)
        mb.add(*box(x, y, zc + 0.82, zc + 0.94, 0.98, 0.20, yaw),
               mats["stone"], smooth=False)
        # red shutters on either side
        for off in (-0.62, 0.62):
            sx = x + ca * off
            sy = y + sa * off
            mb.add(*box(sx, sy, zc + 0.02, zc + 0.80, 0.32, 0.10, yaw),
                   mats["paint_red"], smooth=False)

    window_at(cx - 2.56, cy - 1.05, wall_z0 + 0.62, math.pi * 0.5)
    window_at(cx - 2.56, cy + 1.05, wall_z0 + 0.62, math.pi * 0.5)
    window_at(cx + 1.15, cy - 1.86, wall_z0 + 0.62, 0.0)

    # Roof + ridge + chimney.
    rv, rf = _gable_roof(cx, cy, 5.85, 4.35, wall_z1 - 0.08, wall_z1 + 1.28)
    mb.add(rv, rf, mats["paint_red"], smooth=False)
    mb.add(*box(cx, cy, wall_z1 + 1.22, wall_z1 + 1.34, 0.28, 4.5),
           mats["paint_red"], smooth=False)
    mb.add(*box(cx + 1.65, cy + 1.18, wall_z1 - 0.4, wall_z1 + 1.55,
                0.62, 0.62), mats["stone"], smooth=False)
    mb.add(*box(cx + 1.65, cy + 1.18, wall_z1 + 1.55, wall_z1 + 1.68,
                0.78, 0.78), mats["stone"], smooth=False)

    structure = mb.build("COTTAGE_Structure", config.C_ARCH, uv="smart")
    windows = wb.build("COTTAGE_Windows", config.C_ARCH, uv="planar")
    for obj in (structure, windows):
        util.link_object(obj, config.C_EXPORT)
    print("[features] keeper's cottage on the headland")
    return {"structure": structure, "windows": windows}


# ---------------------------------------------------------------------------
# Rocks, sea stacks, driftwood, path
# ---------------------------------------------------------------------------

def _sea_stacks(mats, rng):
    mb = MeshBuilder()
    specs = [
        (30.0, 39.0, 0.85), (57.0, 43.0, 1.30), (62.0, 48.5, 0.72),
        (91.0, 45.0, 1.05), (119.0, 47.0, 1.40), (127.0, 41.0, 0.68),
        (145.0, 50.0, 0.95),
    ]
    for a_deg, radius, scale in specs:
        a = math.radians(a_deg)
        x, y = math.cos(a) * radius, math.sin(a) * radius
        ground = layout.terrain_height(x, y)
        base = max(ground + 0.8, -2.2)
        layers = [
            (1.0, 3.4, 3.0, 2.4),
            (3.1, 2.6, 2.3, 2.2),
            (5.0, 1.8, 1.6, 1.9),
            (6.5, 1.0, 0.9, 1.4),
        ]
        for dz, rx, ry, rz in layers:
            _sea_stack_blob(mb, mats, x, y, base, dz, rx * scale, ry * scale,
                            rz * scale, rng)
    obj = mb.build("PROP_SeaStacks", config.C_ARCH, uv="cube", uv_scale=3.0)
    return obj


def _sea_stack_blob(mb, mats, x, y, base, dz, rx, ry, rz, rng):
    cx = x + rng.uniform(-0.35, 0.35) * rx
    cy = y + rng.uniform(-0.35, 0.35) * ry
    cz = base + dz + rz * 0.15
    v, f = _rock_blob(cx, cy, cz, rx, ry, rz, rng, sides=9, rings=4,
                      jag=0.22)
    mb.add(v, f, mats["rock"], smooth=False)


def _shore_rocks(mats, rng):
    mb = MeshBuilder()
    placed = 0
    for _ in range(90):
        a = rng.uniform(0, TAU)
        rr = layout.shore_radius(a) * rng.uniform(0.88, 1.03)
        x, y = math.cos(a) * rr, math.sin(a) * rr
        z = layout.terrain_height(x, y)
        if z < -2.4 or z > 1.4:
            continue
        size = rng.uniform(0.30, 0.95)
        if rng.random() < 0.14:
            size *= 1.7
        v, f = _rock_blob(
            x, y, z + size * 0.25,
            size * rng.uniform(1.0, 1.5), size * rng.uniform(0.9, 1.35),
            size * rng.uniform(0.55, 0.85), rng, sides=8, rings=4, jag=0.24)
        mb.add(v, f, mats["rock"], smooth=False)
        placed += 1

    # Rocky outcrops at the base of the lighthouse headland.
    for a_deg in (30.0, 37.0, 44.0, 52.0, 60.0, 67.0):
        for _ in range(3):
            a = math.radians(a_deg + rng.uniform(-3.5, 3.5))
            rr = rng.uniform(32.0, 37.5)
            x, y = math.cos(a) * rr, math.sin(a) * rr
            z = layout.terrain_height(x, y)
            size = rng.uniform(0.8, 2.2)
            v, f = _rock_blob(
                x, y, z + size * 0.3,
                size * rng.uniform(1.1, 1.7), size * rng.uniform(0.9, 1.4),
                size * rng.uniform(0.6, 1.0), rng, sides=8, rings=4, jag=0.22)
            mb.add(v, f, mats["rock"], smooth=False)
            placed += 1

    obj = mb.build("PROP_ShoreRocks", config.C_ARCH, uv="cube", uv_scale=2.4)
    print(f"[features] {placed} shoreline boulders")
    return obj


def _driftwood(mats, rng):
    mb = MeshBuilder()
    specs = [(-152.0, 0.965, 5.4), (-24.0, 0.972, 6.8), (205.0, 0.958, 4.6)]
    for a_deg, rf, length in specs:
        a = math.radians(a_deg)
        r = layout.shore_radius(a) * rf
        cx, cy = math.cos(a) * r, math.sin(a) * r
        yaw = a + math.pi * 0.5 + rng.uniform(-0.5, 0.5)
        ca, sa = math.cos(yaw), math.sin(yaw)
        z = layout.terrain_height(cx, cy) + 0.24
        pts, radii = [], []
        n = 9
        for i in range(n):
            t = i / (n - 1)
            off = (t - 0.5) * length
            dz = 0.10 * math.sin(t * math.pi) - 0.08 * abs(t - 0.5)
            pts.append((cx + ca * off - sa * 0.12 * math.sin(t * 4),
                        cy + sa * off + ca * 0.12 * math.sin(t * 4),
                        z + dz))
            radii.append(0.24 * (0.65 + 0.55 * math.sin(math.pi * min(1.0, t * 1.15))))
        v, f = util.make_tube(pts, radii, sides=9, caps=True)
        mb.add(v, f, mats["wood"], smooth=True)
        # two broken branch stubs
        for bt in (0.32, 0.63):
            idx = int(bt * (n - 1))
            bx, by, bz = pts[idx]
            ba = yaw + rng.choice((-1.0, 1.0)) * rng.uniform(1.0, 1.8)
            bl = rng.uniform(0.7, 1.3)
            bp = [(bx, by, bz),
                  (bx + math.cos(ba) * bl * 0.55, by + math.sin(ba) * bl * 0.55,
                   bz + 0.24),
                  (bx + math.cos(ba) * bl, by + math.sin(ba) * bl, bz + 0.42)]
            v, f = util.make_tube(bp, [0.09, 0.07, 0.02], sides=7, caps=True)
            mb.add(v, f, mats["wood"], smooth=True)
    obj = mb.build("PROP_Driftwood", config.C_ARCH, uv="cube", uv_scale=1.4)
    return obj


def _path_stones(mats, rng):
    pts = []
    base = layout.path_points()
    for i, p in enumerate(base):
        pts.append(p)
        if i + 1 < len(base):
            q = base[i + 1]
            pts.append(((p[0] + q[0]) * 0.5, (p[1] + q[1]) * 0.5))

    mb = MeshBuilder()
    for i, (x, y) in enumerate(pts):
        if i + 1 < len(pts):
            tx, ty = pts[i + 1][0] - x, pts[i + 1][1] - y
        else:
            tx, ty = x - pts[i - 1][0], y - pts[i - 1][1]
        yaw = math.atan2(ty, tx)
        z = layout.terrain_height(x, y)
        v, f = _stone_slab(x, y, z + 0.035, 0.55, 0.40, yaw,
                           thickness=0.075 + rng.uniform(0.0, 0.03),
                           sides=10, phase=rng.uniform(0, TAU))
        mb.add(v, f, mats["stone"], smooth=False)
        if i % 3 == 0:
            px = x - math.sin(yaw) * 0.72
            py = y + math.cos(yaw) * 0.72
            vz = layout.terrain_height(px, py)
            v, f = uv_sphere(px, py, vz + 0.08, 0.16 + rng.uniform(0, 0.08),
                             sides=7, rings=4, scale=(1.0, 0.9, 0.55))
            mb.add(v, f, mats["stone"], smooth=False)
    obj = mb.build("PROP_PathStones", config.C_ARCH, uv="planar",
                   uv_scale=1.6)
    print(f"[features] {len(pts)} stepping stones")
    return obj


def build_features(mats):
    util.reset_collection(config.C_ARCH)
    rng = util.sub_rng("island_features")

    lighthouse = _lighthouse(mats)
    cottage = _cottage(mats)
    stacks = _sea_stacks(mats, rng)
    rocks = _shore_rocks(mats, rng)
    drift = _driftwood(mats, rng)
    stones = _path_stones(mats, rng)

    return {
        "lighthouse": lighthouse,
        "cottage": cottage,
        "sea_stacks": stacks,
        "rocks": rocks,
        "driftwood": drift,
        "path": stones,
    }
