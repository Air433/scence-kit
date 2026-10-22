"""Procedural coconut palms.

Each palm exports three meshes (trunk, fronds, coconuts) sharing one origin and
identity rotation.  The Godot wind shader sways the fronds using UV.y, so the
frond mesh must stay in local space with its base at UV.y = 0.
"""
from __future__ import annotations

import math
import random

from mathutils import Vector

from arena_kit import config, util

from . import layout
from .geo import MeshBuilder, cylinder_at, uv_sphere

TAU = math.pi * 2.0


def _trunk_mesh(height, base_r, lean_dir, lean, rng, bend_phase):
    levels = 17
    pts = []
    radii = []
    for i in range(levels):
        t = i / (levels - 1)
        lateral = lean * (t ** 1.65)
        wobble = math.sin(t * 3.2 + bend_phase) * 0.18 * t
        dx = math.cos(lean_dir) * lateral - math.sin(lean_dir) * wobble
        dy = math.sin(lean_dir) * lateral + math.cos(lean_dir) * wobble
        z = height * t
        pts.append((dx, dy, z))
        flare = 1.0 + 0.60 * max(0.0, 1.0 - t * 7.0) ** 2
        radii.append(base_r * (1.0 - 0.54 * t) * flare)
    v, f = util.make_tube(pts, radii, sides=12, caps=True)
    return v, f, pts[-1]


def _frond_ribbon(base, yaw, length, pitch, droop, width, rng):
    rows = 16
    cols = 3
    verts = []
    faces = []
    dirx, diry = math.cos(yaw), math.sin(yaw)
    sidex, sidey = -diry, dirx
    lateral = rng.uniform(-0.45, 0.45)
    for i in range(rows + 1):
        t = i / rows
        # horizontal sweep + a gentle lateral curl
        s = length * 0.96 * t
        lat = lateral * math.sin(math.pi * t) * 0.5 * length * 0.28
        x = base[0] + dirx * s + sidex * lat
        y = base[1] + diry * s + sidey * lat
        z = base[2] + length * (math.sin(pitch) * t - droop * t * t)
        # width: petiole -> broad mid -> tapered tip
        if t < 0.08:
            w = width * (0.06 + t * 0.5)
        elif t < 0.55:
            w = width * (0.10 + (t - 0.08) / 0.47 * 0.90)
        else:
            w = width * (1.0 - (t - 0.55) / 0.45) ** 1.15
        w = max(w, 0.015)
        ridge = w * 0.14
        # slight roll so fronds look less like flat cards
        roll = math.sin(t * 4.0 + yaw) * 0.16
        for c, off in enumerate((-0.5, 0.0, 0.5)):
            zz = z + (ridge if c == 1 else 0.0) + abs(off) * roll
            verts.append((x + sidex * w * off, y + sidey * w * off, zz))
    for i in range(rows):
        for c in range(cols - 1):
            a = i * cols + c
            b = (i + 1) * cols + c
            faces.append((a, b, b + 1, a + 1))
    uvs = []
    for i in range(rows + 1):
        t = i / rows
        for c, u in enumerate((0.0, 0.5, 1.0)):
            uvs.append((u, t))
    return verts, faces, uvs


def build_palm(mats, index, x, y, z, angle_deg, radius, rng, bg=False):
    height = rng.uniform(6.4, 11.8) if not bg else rng.uniform(5.4, 8.2)
    base_r = rng.uniform(0.22, 0.31) * (height / 9.0) ** 0.4
    # Lean away from the island centre with a tangential bias.
    outward = math.radians(angle_deg) + rng.uniform(-0.65, 0.65)
    lean = rng.uniform(0.8, 2.2) * (height / 9.0)
    lean_dir = outward

    trunk_v, trunk_f, crown = _trunk_mesh(
        height, base_r, lean_dir, lean, rng, rng.uniform(0, TAU))
    trunk = util.mesh_object(f"TREE_Palm_{index:02d}_Trunk", trunk_v, trunk_f,
                             config.C_TREES, mats["palm_bark"], smooth=True)
    util.cylindrical_uv(trunk, 1.9)
    util.shade_smooth_by_angle(trunk, 42.0)
    trunk.location = (x, y, z - 0.12)
    util.link_object(trunk, config.C_EXPORT)

    crown_x, crown_y, crown_z = crown[0], crown[1], crown[2]
    frond_v, frond_f, frond_uv = [], [], []
    frond_count = rng.randint(10, 13) if not bg else 8
    base_phase = rng.uniform(0, TAU)

    def add_frond(yaw, length, pitch, droop, width):
        v, f, uv = _frond_ribbon((crown_x, crown_y, crown_z), yaw,
                                 length, pitch, droop, width, rng)
        off = len(frond_v)
        frond_v.extend(v)
        frond_uv.extend(uv)
        frond_f.extend(tuple(k + off for k in face) for face in f)

    for i in range(frond_count):
        yaw = base_phase + TAU * i / frond_count + rng.uniform(-0.14, 0.14)
        # Outer fronds droop harder; inner ones reach up.
        tier = i / max(1, frond_count - 1)
        pitch = rng.uniform(0.55, 1.05) * (1.0 - 0.28 * tier)
        droop = rng.uniform(0.95, 1.35)
        length = rng.uniform(2.5, 4.1) * (1.0 - 0.10 * tier)
        width = length * rng.uniform(0.42, 0.56)
        add_frond(yaw, length, pitch, droop, width)
    # Three young upright fronds in the crown.
    for i in range(3):
        yaw = base_phase + TAU * i / 3 + 0.3
        add_frond(yaw, rng.uniform(1.4, 2.0), rng.uniform(1.05, 1.25),
                  rng.uniform(0.15, 0.4), rng.uniform(0.55, 0.8))

    fronds = util.mesh_object(f"TREE_Palm_{index:02d}_Fronds", frond_v,
                              frond_f, config.C_CANOPY, mats["palm_frond"])
    uvl = fronds.data.uv_layers.new(name="UVMap")
    mesh = fronds.data
    for loop in mesh.loops:
        uvl.data[loop.index].uv = frond_uv[loop.vertex_index]
    for p in mesh.polygons:
        p.use_smooth = True
    fronds.location = (x, y, z - 0.12)
    util.link_object(fronds, config.C_EXPORT)

    # Coconuts clustered under the crown.
    cb = MeshBuilder()
    for _ in range(rng.randint(4, 7)):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(0.08, 0.35)
        cz = crown_z - rng.uniform(0.1, 0.45)
        v, f = uv_sphere(crown_x + math.cos(a) * rr,
                         crown_y + math.sin(a) * rr, cz,
                         rng.uniform(0.10, 0.15), sides=7, rings=5,
                         scale=(1.0, 1.0, 1.25))
        cb.add(v, f, mats["palm_bark"], smooth=True)
    coconuts = cb.build(f"TREE_Palm_{index:02d}_Coconuts", config.C_CANOPY,
                        uv="smart")
    coconuts.location = (x, y, z - 0.12)

    return trunk, fronds, coconuts


def build_palms(mats):
    util.reset_collection(config.C_TREES)
    util.reset_collection(config.C_CANOPY)
    rng = util.sub_rng("island_palms")
    trunks = []
    fronds = []
    nuts = []

    for i, (x, y, z, ang, radius) in enumerate(layout.palm_sites()):
        t, f, c = build_palm(mats, i, x, y, z, ang, radius, rng)
        trunks.append(t)
        fronds.append(f)
        nuts.append(c)

    for k in range(max(0, min(config.BG_TREE_COUNT, 6))):
        a = rng.uniform(0, TAU)
        r = rng.uniform(26.0, 31.0)
        x, y = math.cos(a) * r, math.sin(a) * r
        z = layout.terrain_height(x, y)
        if z < 0.55:
            continue
        t, f, c = build_palm(mats, 100 + k, x, y, z, math.degrees(a),
                             r, rng, bg=True)
        trunks.append(t)
        fronds.append(f)
        nuts.append(c)

    print(f"[palms] {len(trunks)} palms, {sum(len(x.data.polygons) for x in fronds)} frond cards")
    return {"trunks": trunks, "fronds": fronds, "coconuts": nuts}
