"""Elven ruins: fluted pillars, broken arches, altar and rubble."""
from __future__ import annotations

import math
import random

import bmesh
from mathutils import Vector

from . import config, terrain, util

TAU = math.pi * 2.0


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _merge(parts):
    """parts: list of (verts, faces) -> merged (verts, faces)."""
    verts = []
    faces = []
    for v, f in parts:
        off = len(verts)
        verts.extend(v)
        faces.extend(tuple(i + off for i in face) for face in f)
    return verts, faces


def _box_rot_z(cx, cy, z0, z1, sx, sy, angle):
    hx, hy = sx * 0.5, sy * 0.5
    ca, sa = math.cos(angle), math.sin(angle)
    base = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    verts = []
    for z in (z0, z1):
        for x, y in base:
            verts.append((cx + x * ca - y * sa, cy + x * sa + y * ca, z))
    faces = [(0, 1, 2, 3), (7, 6, 5, 4),
             (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return verts, faces


def _box_rot_y(cx, cy, cz, sx, sy, sz, angle):
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    ca, sa = math.cos(angle), math.sin(angle)
    verts = []
    for dz in (-hz, hz):
        for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
            x = dx * ca + dz * sa
            z = -dx * sa + dz * ca
            verts.append((cx + x, cy + dy, cz + z))
    faces = [(0, 1, 2, 3), (7, 6, 5, 4),
             (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return verts, faces


def _cylinder(radius, z0, z1, sides=20, r_bottom=None):
    rb = r_bottom if r_bottom is not None else radius
    verts = []
    for z, r in ((z0, rb), (z1, radius)):
        for s in range(sides):
            a = TAU * s / sides
            verts.append((r * math.cos(a), r * math.sin(a), z))
    faces = []
    for s in range(sides):
        b = (s + 1) % sides
        faces.append((s, b, sides + b, sides + s))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(range(sides, 2 * sides)))
    return verts, faces


def _fluted_shaft(radius, z0, height, broken, rng, sides=20, segments=16):
    rings = []
    break_frac = rng.uniform(0.55, 0.82) if broken else 1.0
    top = z0 + height * break_frac
    for i in range(segments + 1):
        t = i / segments
        z = z0 + (top - z0) * t
        taper = 1.0 - 0.10 * t
        flare = 1.0 + 0.16 * max(0.0, 1.0 - t * 6.0) ** 2
        ring = []
        for s in range(sides):
            a = TAU * s / sides
            flute = 1.0 - 0.045 * (0.5 + 0.5 * math.cos(8.0 * a))
            r = radius * taper * flare * flute
            if i == segments and broken:
                zz = z + rng.uniform(-0.28, 0.10)
            else:
                zz = z
            ring.append((r * math.cos(a), r * math.sin(a), zz))
        rings.append(ring)
    verts, faces = util.loft_rings(rings, caps=True)
    return verts, faces, top


def _pillar(rng, height, radius, broken, stump=False):
    parts = []
    z0 = 0.0
    # square footing
    parts.append(_box_rot_z(0, 0, -0.12, 0.24, radius * 3.0, radius * 3.0, 0.0))
    # round base
    parts.append(_cylinder(radius * 1.42, 0.18, 0.46, 16, r_bottom=radius * 1.55))

    if stump:
        h = rng.uniform(0.55, 1.25)
        v, f, top = _fluted_shaft(radius, 0.44, h, True, rng)
        parts.append((v, f))
        return parts, top + 0.44

    shaft_height = height - 0.46 - 0.55
    v, f, top = _fluted_shaft(radius, 0.46, shaft_height, broken, rng)
    parts.append((v, f))

    if not broken:
        # flared capital
        parts.append(_cylinder(radius * 1.48, top, top + 0.26, 20, r_bottom=radius * 1.05))
        # square abacus
        parts.append(_box_rot_z(0, 0, top + 0.26, top + 0.50,
                                radius * 3.1, radius * 3.1, 0.0))
        top = top + 0.50

    # carved vine relief on intact pillars
    if not broken and not stump and rng.random() < 0.65:
        pts = []
        turns = rng.uniform(2.2, 3.4)
        for i in range(48):
            t = i / 47.0
            a = t * turns * TAU + rng.uniform(-0.2, 0.2)
            r = radius * (1.02 - 0.03 * t)
            pts.append((r * math.cos(a), r * math.sin(a), 0.7 + t * (shaft_height - 0.5)))
        tv, tf = util.make_tube(pts, [0.032] * len(pts), sides=5, caps=True)
        parts.append((tv, tf))

    return parts, top


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _build_pillars(rng):
    verts = []
    faces = []
    count = 16
    for i in range(count):
        ang = TAU * i / count
        # keep the north entrance open
        if abs(((ang - math.pi * 0.5 + math.pi) % TAU) - math.pi) < math.radians(16):
            continue
        x = math.cos(ang) * config.COLONNADE_R
        y = math.sin(ang) * config.COLONNADE_R
        z = terrain.height_at(x, y)
        radius = rng.uniform(0.34, 0.46)
        height = rng.uniform(4.4, 6.1)
        roll = rng.random()
        if roll < 0.20:
            parts, _ = _pillar(rng, height, radius, broken=False, stump=True)
            height = 1.0
        elif roll < 0.48:
            parts, _ = _pillar(rng, height, radius, broken=True)
        else:
            parts, _ = _pillar(rng, height, radius, broken=False)
        v, f = _merge(parts)
        ca, sa = math.cos(ang), math.sin(ang)
        world = []
        for vx, vy, vz in v:
            # local x is radial/tangential neutral; rotate around Z
            world.append((x + vx * ca - vy * sa, y + vx * sa + vy * ca, z + vz))
        off = len(verts)
        verts.extend(world)
        faces.extend(tuple(idx + off for idx in face) for face in f)
    return verts, faces


def _build_arches(rng):
    verts = []
    faces = []

    def add_arch(cx, cy, cz, span, spring_h, rot_z, broken):
        R = span * 0.5
        ca, sa = math.cos(rot_z), math.sin(rot_z)

        def place(lx, ly, lz):
            return (cx + lx * ca - ly * sa, cy + lx * sa + ly * ca, cz + lz)

        # two pillars
        for sx in (-1, 1):
            parts, _ = _pillar(rng, spring_h, 0.38, broken=False)
            v, f = _merge(parts)
            off = len(verts)
            for vx, vy, vz in v:
                verts.append(place(sx * R + vx, vy, vz))
            faces.extend(tuple(idx + off for idx in face) for face in f)

        # voussoirs
        blocks = 11
        for k in range(blocks):
            if broken and 6 <= k <= 8:
                continue
            a = math.pi * k / (blocks - 1)
            bx = R * math.cos(a)
            bz = spring_h + R * math.sin(a)
            arc = (math.pi * R / (blocks - 1)) * 1.02
            phi = -a - math.pi * 0.5
            v, f = _box_rot_y(bx, 0.0, bz, arc, 0.62, 0.52, phi)
            off = len(verts)
            for vx, vy, vz in v:
                verts.append(place(vx, vy, vz))
            faces.extend(tuple(i + off for i in face) for face in f)

        # fallen blocks for a broken arch
        if broken:
            for _ in range(5):
                lx = rng.uniform(-R - 1.0, R + 1.0)
                ly = rng.uniform(-1.0, 1.0)
                px, py, _ = place(lx, ly, 0.0)
                bz = terrain.height_at(px, py) + 0.25 - cz
                v, f = _box_rot_y(lx, ly, bz, rng.uniform(0.5, 1.0),
                                  rng.uniform(0.35, 0.6), 0.42,
                                  rng.uniform(0, TAU))
                off = len(verts)
                for vx, vy, vz in v:
                    verts.append(place(vx, vy, vz))
                faces.extend(tuple(i + off for i in face) for face in f)

    # north main arch
    ny = 13.3
    add_arch(0.0, ny, terrain.height_at(0, ny), 5.8, 5.0, 0.0, True)
    # east arch
    ex = 13.4
    add_arch(ex, 0.0, terrain.height_at(ex, 0), 4.6, 4.2, math.pi * 0.5, False)

    return verts, faces


def _build_altar(rng):
    parts = []
    # steps
    parts.append(_box_rot_z(0, 0, -0.10, 0.16, 3.8, 2.6, 0.0))
    parts.append(_box_rot_z(0, 0, 0.12, 0.32, 3.2, 2.2, 0.0))
    parts.append(_box_rot_z(0, 0, 0.28, 0.50, 2.7, 1.9, 0.0))
    # pedestal
    parts.append(_box_rot_z(0, 0.05, 0.45, 1.42, 2.05, 1.05, 0.0))
    # broken back slab (jagged top)
    w, d = 3.0, 0.34
    x0, x1 = -w * 0.5, w * 0.5
    y0, y1 = 0.22, 0.22 + d
    base_z = 0.35
    top_l = 3.15
    top_r = 3.70
    mid_l = 3.40
    verts = [
        (x0, y0, base_z), (x1, y0, base_z), (x1, y1, base_z), (x0, y1, base_z),
        (x0, y0, top_l), (x1, y0, top_r), (x1, y1, top_r - 0.12), (x0, y1, top_l - 0.10),
    ]
    faces = [
        (0, 1, 2, 3), (7, 6, 5, 4),
        (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0),
    ]
    parts.append((verts, faces))
    # side wings
    parts.append(_box_rot_z(-1.75, 0.4, 0.45, 1.9, 0.55, 1.4, 0.0))
    parts.append(_box_rot_z(1.75, 0.4, 0.45, 1.9, 0.55, 1.4, 0.0))
    return _merge(parts)


def _build_altar_runes():
    """Glowing elven sigil engraved on the altar's camera-facing face."""
    parts = []

    def arc(radius, a0, a1, steps, tube, y=0.195, cz=2.35):
        pts = []
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            pts.append((math.cos(a) * radius, y, cz + math.sin(a) * radius))
        parts.append(util.make_tube(pts, [tube] * len(pts), sides=5, caps=True))

    arc(0.56, 0.0, TAU, 44, 0.030)
    arc(0.37, math.radians(205), math.radians(335), 22, 0.020)
    for a in (math.radians(90), math.radians(210), math.radians(330)):
        r0, r1 = 0.10, 0.30
        parts.append(util.make_tube(
            [(math.cos(a) * r0, 0.195, 2.35 + math.sin(a) * r0),
             (math.cos(a) * r1, 0.195, 2.35 + math.sin(a) * r1)],
            [0.018, 0.018], sides=5, caps=True))
    # stem running down to the pedestal
    parts.append(util.make_tube(
        [(0.0, 0.195, 1.79), (0.0, 0.195, 1.46)],
        [0.024, 0.024], sides=5, caps=True))
    # centre dot
    parts.append(util.make_tube(
        [(-0.035, 0.195, 2.35), (0.035, 0.195, 2.35)],
        [0.030, 0.030], sides=6, caps=True))
    return _merge(parts)


def _build_rubble(rng):
    verts = []
    faces = []
    pts = util.poisson_disc(26, 10.0, 17.0, 1.3, rng,
                            accept=lambda x, y, r: not (y > 8.0 and abs(x) < 2.2))
    for x, y in pts:
        z = terrain.height_at(x, y)
        sx = rng.uniform(0.35, 1.15)
        sy = rng.uniform(0.3, 0.9)
        sz = rng.uniform(0.25, 0.7)
        parts = _box_rot_z(0, 0, -0.10, sz, sx, sy, 0.0)
        ca, sa = math.cos(rng.uniform(0, TAU)), math.sin(rng.uniform(0, TAU))
        off = len(verts)
        for vx, vy, vz in parts[0]:
            verts.append((x + vx * ca - vy * sa, y + vx * sa + vy * ca, z + vz))
        faces.extend(tuple(i + off for i in face) for face in parts[1])
    return verts, faces


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_architecture(mats):
    util.reset_collection(config.C_ARCH)
    rng = util.sub_rng("arch")

    pillars = util.mesh_object("ARCH_Pillars", *_build_pillars(rng), config.C_ARCH,
                               mats["stone_warm"], smooth=True)
    arches = util.mesh_object("ARCH_Arches", *_build_arches(rng), config.C_ARCH,
                              mats["stone_warm"], smooth=True)
    altar = util.mesh_object("ARCH_Altar", *_build_altar(rng), config.C_ARCH,
                             mats["stone_warm"], smooth=True)
    altar.location = (0.0, 7.3, 0.0)
    altar_runes = util.mesh_object("ARCH_AltarRunes", *_build_altar_runes(),
                                   config.C_ARCH, mats["rune"], smooth=True)
    altar_runes.location = (0.0, 7.3, 0.0)
    rubble = util.mesh_object("ARCH_Rubble", *_build_rubble(rng), config.C_ARCH,
                              mats["stone"])

    for obj in (pillars, arches, altar, altar_runes, rubble):
        util.apply_transform(obj, scale=True, rotation=True, location=False)
        util.cube_uv(obj, 2.0)
        util.shade_smooth_by_angle(obj, 32.0)
        util.link_object(obj, config.C_EXPORT)

    print("[architecture] pillars, 2 arches, altar, rubble")
    return {"pillars": pillars, "arches": arches, "altar": altar, "rubble": rubble}
