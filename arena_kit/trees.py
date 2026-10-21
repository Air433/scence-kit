"""Procedural giant trees, buttress roots, branches and leaf-card canopy."""
from __future__ import annotations

import math
import random

from mathutils import Vector

from . import config, terrain, util

TAU = math.pi * 2.0


# ---------------------------------------------------------------------------
# Card helpers
# ---------------------------------------------------------------------------

def _basis(yaw: float, pitch: float):
    direction = Vector((math.cos(yaw) * math.cos(pitch),
                        math.sin(yaw) * math.cos(pitch),
                        math.sin(pitch)))
    up = Vector((0, 0, 1))
    if abs(direction.dot(up)) > 0.97:
        up = Vector((0, 1, 0))
    side = direction.cross(up).normalized()
    up2 = side.cross(direction).normalized()
    return direction, side, up2


def _add_card(verts, faces, center, size, yaw, pitch, rng):
    _, side, up = _basis(yaw, pitch)
    roll = rng.uniform(0, TAU)
    cr, sr = math.cos(roll), math.sin(roll)
    s2 = side * cr + up * sr
    u2 = up * cr - side * sr
    h = size * 0.5
    c = Vector(center)
    verts.extend([
        tuple(c - s2 * h - u2 * h),
        tuple(c + s2 * h - u2 * h),
        tuple(c + s2 * h + u2 * h),
        tuple(c - s2 * h + u2 * h),
    ])
    off = len(verts) - 4
    faces.append((off, off + 1, off + 2, off + 3))


def _add_cluster(verts, faces, center, size, rng):
    for i in range(3):
        yaw = rng.uniform(0, TAU) + i * (TAU / 3.0)
        pitch = rng.uniform(-0.55, 0.55)
        _add_card(verts, faces, center, size * rng.uniform(0.85, 1.15),
                  yaw, pitch, rng)


# ---------------------------------------------------------------------------
# Trunk / roots / branches
# ---------------------------------------------------------------------------

def _trunk(rng, height, radius, verts, faces):
    levels = 15
    pts = []
    phase = rng.uniform(0, TAU)
    for i in range(levels):
        t = i / (levels - 1)
        z = height * t
        wob_x = math.sin(t * 2.3 + phase) * radius * 0.55 * t
        wob_y = math.cos(t * 1.9 + phase) * radius * 0.45 * t
        pts.append((wob_x, wob_y, z))
    radii = []
    for i in range(levels):
        t = i / (levels - 1)
        flare = 1.0 + 0.42 * max(0.0, 1.0 - t * 5.0) ** 2
        radii.append(radius * (1.0 - 0.80 * t) * flare)
    v, f = util.make_tube(pts, radii, sides=16, caps=True)
    off = len(verts)
    verts.extend(v)
    faces.extend(tuple(i + off for i in face) for face in f)
    return pts, radii


def _buttress_roots(rng, radius, verts, faces):
    count = rng.randint(6, 9)
    for k in range(count):
        a = TAU * k / count + rng.uniform(-0.18, 0.18)
        ca, sa = math.cos(a), math.sin(a)
        r1 = radius
        pts = [
            (ca * r1 * 0.55, sa * r1 * 0.55, 3.2),
            (ca * r1 * 0.95, sa * r1 * 0.95, 2.3),
            (ca * r1 * 1.7, sa * r1 * 1.7, 1.35),
            (ca * r1 * 2.7, sa * r1 * 2.7, 0.6),
            (ca * r1 * 3.8, sa * r1 * 3.8, 0.12),
            (ca * r1 * 4.9, sa * r1 * 4.9, -0.08),
        ]
        radii = [radius * 0.42, radius * 0.36, radius * 0.27,
                 radius * 0.18, radius * 0.11, 0.05]
        v, f = util.make_tube(pts, radii, sides=6, caps=True)
        off = len(verts)
        verts.extend(v)
        faces.extend(tuple(i + off for i in face) for face in f)


def _grow_branch(rng, start, direction, length, radius, depth,
                 bark_v, bark_f, leaf_points, sides=6):
    n = 5
    pts = [Vector(start)]
    d = Vector(direction).normalized()
    for i in range(1, n):
        d = (d + Vector((rng.uniform(-0.22, 0.22),
                         rng.uniform(-0.22, 0.22),
                         rng.uniform(-0.10, 0.28)))).normalized()
        pts.append(pts[-1] + d * (length / (n - 1)))
    radii = [max(0.018, radius * (1.0 - 0.70 * i / (n - 1))) for i in range(n)]
    v, f = util.make_tube(pts, radii, sides=sides, caps=True)
    off = len(bark_v)
    bark_v.extend(v)
    bark_f.extend(tuple(i + off for i in face) for face in f)

    if depth <= 1:
        for i in range(2, n):
            if rng.random() < 0.8:
                leaf_points.append(pts[i])
    if depth <= 0:
        leaf_points.append(pts[-1])
        return

    for _ in range(rng.randint(2, 3)):
        idx = rng.randint(2, n - 1)
        cs = pts[idx]
        out = Vector((cs.x, cs.y, 0.0))
        if out.length < 1e-4:
            out = Vector((1, 0, 0))
        out.normalize()
        child_dir = (out * rng.uniform(0.55, 1.0)
                     + Vector((rng.uniform(-0.35, 0.35),
                               rng.uniform(-0.35, 0.35),
                               rng.uniform(0.55, 1.25)))).normalized()
        _grow_branch(rng, cs, child_dir, length * rng.uniform(0.55, 0.78),
                     radius * 0.55, depth - 1, bark_v, bark_f, leaf_points,
                     sides=max(4, sides - 1))


def _hero_tree(rng, height, radius, hero=True):
    bark_v, bark_f = [], []
    trunk_pts, trunk_radii = _trunk(rng, height, radius, bark_v, bark_f)
    _buttress_roots(rng, radius, bark_v, bark_f)

    leaf_points = []
    branch_heights = [0.34, 0.50, 0.66] if hero else [0.55, 0.74]
    for bt in branch_heights:
        idx = min(len(trunk_pts) - 1, max(1, int(bt * (len(trunk_pts) - 1))))
        start = Vector(trunk_pts[idx])
        base_radius = trunk_radii[idx]
        count = rng.randint(2, 3) if hero else 1
        for k in range(count):
            a = TAU * (k / count + rng.uniform(-0.12, 0.12)) + rng.uniform(0, TAU)
            direction = Vector((math.cos(a), math.sin(a), rng.uniform(0.35, 0.95)))
            _grow_branch(rng, start, direction,
                         rng.uniform(2.2, 4.0) * (1.0 if hero else 0.8),
                         max(0.08, base_radius * 0.42),
                         3 if hero else 2, bark_v, bark_f, leaf_points)

    # crown filler
    crown_z = height * 0.66
    crown_r = radius * (7.0 if hero else 4.5)
    for _ in range(26 if hero else 18):
        a = rng.uniform(0, TAU)
        rr = crown_r * math.sqrt(rng.random())
        leaf_points.append(Vector((math.cos(a) * rr, math.sin(a) * rr,
                                   crown_z + rng.uniform(-2.5, 3.5))))

    leaf_v, leaf_f = [], []
    cards_per_point = 1 if hero else 1
    for p in leaf_points:
        for _ in range(cards_per_point):
            center = p + Vector((rng.uniform(-0.7, 0.7), rng.uniform(-0.7, 0.7),
                                 rng.uniform(-0.5, 0.5)))
            _add_cluster(leaf_v, leaf_f, center,
                         rng.uniform(1.2, 2.4) * (1.0 if hero else 1.15), rng)
    return bark_v, bark_f, leaf_v, leaf_f


# ---------------------------------------------------------------------------
# Materials / UV
# ---------------------------------------------------------------------------

def _finalize_bark(name, verts, faces, mats):
    obj = util.mesh_object(name, verts, faces, config.C_TREES, mats["bark"],
                           smooth=True)
    util.cylindrical_uv(obj, 2.2)
    util.shade_smooth_by_angle(obj, 40.0)
    util.link_object(obj, config.C_EXPORT)
    return obj


def _finalize_leaf(name, verts, faces, mats):
    obj = util.mesh_object(name, verts, faces, config.C_CANOPY, mats["leaf"])
    mesh = obj.data
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        if len(poly.loop_indices) == 4:
            uv.data[poly.loop_indices[0]].uv = (0.0, 0.0)
            uv.data[poly.loop_indices[1]].uv = (1.0, 0.0)
            uv.data[poly.loop_indices[2]].uv = (1.0, 1.0)
            uv.data[poly.loop_indices[3]].uv = (0.0, 1.0)
    util.link_object(obj, config.C_EXPORT)
    return obj


def build_trees(mats):
    util.reset_collection(config.C_TREES)
    util.reset_collection(config.C_CANOPY)
    rng = util.sub_rng("trees")

    hero_angles = config.HERO_TREE_ANGLES
    hero_radii = config.HERO_TREE_RADII
    tree_data = []

    for i, (ang, r) in enumerate(zip(hero_angles, hero_radii)):
        a = math.radians(ang)
        x = math.cos(a) * r
        y = math.sin(a) * r
        z = terrain.height_at(x, y) - 0.06
        height = rng.uniform(27.0, 32.0)
        radius = rng.uniform(0.85, 1.35)
        bv, bf, lv, lf = _hero_tree(rng, height, radius, hero=True)
        bark = _finalize_bark(f"TREE_Hero_{i:02d}_Bark", bv, bf, mats)
        leaf = _finalize_leaf(f"TREE_Hero_{i:02d}_Canopy", lv, lf, mats)
        bark.location = (x, y, z)
        leaf.location = (x, y, z)
        bark["tree_index"] = i
        bark["tree_height"] = height
        bark["tree_radius"] = radius
        tree_data.append({
            "name": f"TREE_Hero_{i:02d}", "x": x, "y": y, "z": z,
            "height": height, "radius": radius,
        })

    # background trees, merged into a few meshes
    bg_bark_v, bg_bark_f = [], []
    bg_leaf_v, bg_leaf_f = [], []
    for i in range(config.BG_TREE_COUNT):
        a = rng.uniform(0, TAU)
        r = rng.uniform(24.0, 31.5)
        x, y = math.cos(a) * r, math.sin(a) * r
        z = terrain.height_at(x, y) - 0.08
        height = rng.uniform(16.0, 24.0)
        radius = rng.uniform(0.55, 1.0)
        bv, bf, lv, lf = _hero_tree(rng, height, radius, hero=False)
        # bake the placement into the merged vertices
        for v in bv:
            bg_bark_v.append((v[0] + x, v[1] + y, v[2] + z))
        off = len(bg_bark_v) - len(bv)
        bg_bark_f.extend(tuple(idx + off for idx in face) for face in bf)
        for v in lv:
            bg_leaf_v.append((v[0] + x, v[1] + y, v[2] + z))
        off = len(bg_leaf_v) - len(lv)
        bg_leaf_f.extend(tuple(idx + off for idx in face) for face in lf)

    _finalize_bark("TREE_Background_Bark", bg_bark_v, bg_bark_f, mats)
    _finalize_leaf("TREE_Background_Canopy", bg_leaf_v, bg_leaf_f, mats)

    print(f"[trees] {len(hero_angles)} hero + {config.BG_TREE_COUNT} background trees")
    return tree_data
