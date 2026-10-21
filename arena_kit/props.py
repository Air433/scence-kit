"""Set dressing: boulders, fallen logs, vines, hanging lanterns, fireflies."""
from __future__ import annotations

import math
import random

import bmesh
import bpy
import json
from mathutils import Vector, noise

from . import config, terrain, util

TAU = math.pi * 2.0


def _surface_z(x: float, y: float) -> float:
    r = math.hypot(x, y)
    if r < config.INNER_R:
        return 0.0
    if r < config.OUTER_R:
        tier = min(config.TIER_COUNT - 1,
                   int((r - config.INNER_R) / config.TIER_TREAD))
        return (tier + 1) * config.TIER_RISE
    return terrain.height_at(x, y)


def _clear_of_trees(x, y, pad=1.0):
    for ang, rad in zip(config.HERO_TREE_ANGLES, config.HERO_TREE_RADII):
        a = math.radians(ang)
        tx, ty = math.cos(a) * rad, math.sin(a) * rad
        if (x - tx) ** 2 + (y - ty) ** 2 < (2.0 + pad) ** 2:
            return False
    return True


def _accept_prop(x, y, r):
    if y > 6.8 and abs(x) < 2.3:
        return False
    if x > 10.2 and abs(y) < 1.9:
        return False
    return _clear_of_trees(x, y)


# ---------------------------------------------------------------------------
# Boulders
# ---------------------------------------------------------------------------

def _build_boulders(rng):
    bm = bmesh.new()
    pts = util.poisson_disc(config.BOULDER_COUNT, 12.2, 29.0, 1.35, rng,
                            accept=_accept_prop)
    for x, y in pts:
        ret = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        vs = ret["verts"]
        amp = rng.uniform(0.08, 0.20)
        off = Vector((rng.uniform(0, 20), rng.uniform(0, 20), rng.uniform(0, 20)))
        for v in vs:
            v.co += noise.noise_vector(v.co * 1.35 + off) * amp
        sx = rng.uniform(0.35, 1.15)
        sy = rng.uniform(0.32, 1.00)
        sz = rng.uniform(0.26, 0.78)
        yaw = rng.uniform(0, TAU)
        ca, sa = math.cos(yaw), math.sin(yaw)
        min_z = 1e9
        for v in vs:
            v.co.x *= sx
            v.co.y *= sy
            v.co.z *= sz
            v.co.x, v.co.y = v.co.x * ca - v.co.y * sa, v.co.x * sa + v.co.y * ca
            min_z = min(min_z, v.co.z)
        ground = _surface_z(x, y)
        dz = ground - min_z - 0.05
        for v in vs:
            v.co.x += x
            v.co.y += y
            v.co.z += dz
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ---------------------------------------------------------------------------
# Logs and stumps
# ---------------------------------------------------------------------------

def _add_tube(verts, faces, pts, radii, sides=7):
    v, f = util.make_tube(pts, radii, sides=sides, caps=True)
    off = len(verts)
    verts.extend(v)
    faces.extend(tuple(i + off for i in face) for face in f)


def _build_logs(rng):
    verts = []
    faces = []
    for _ in range(3):
        a = rng.uniform(0, TAU)
        r = rng.uniform(14.5, 20.0)
        cx, cy = math.cos(a) * r, math.sin(a) * r
        yaw = rng.uniform(0, TAU)
        length = rng.uniform(5.5, 8.0)
        rad = rng.uniform(0.32, 0.48)
        n = 8
        pts = []
        for i in range(n):
            t = -0.5 + i / (n - 1)
            bend = math.sin(t * math.pi) * 0.35
            px = cx + math.cos(yaw) * length * t - math.sin(yaw) * bend
            py = cy + math.sin(yaw) * length * t + math.cos(yaw) * bend
            pz = terrain.height_at(px, py) + rad * 0.55
            pts.append((px, py, pz))
        radii = [rad * (0.62 + 0.38 * math.sin(math.pi * i / (n - 1)))
                 for i in range(n)]
        _add_tube(verts, faces, pts, radii, sides=8)
        # broken branch stubs
        for _ in range(rng.randint(2, 3)):
            i = rng.randint(1, n - 2)
            p = Vector(pts[i])
            d = Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6),
                        rng.uniform(0.5, 1.0))).normalized()
            stub = [tuple(p), tuple(p + d * 0.7), tuple(p + d * 1.2)]
            _add_tube(verts, faces, stub, [rad * 0.34, rad * 0.22, 0.04], sides=6)

    for _ in range(4):
        a = rng.uniform(0, TAU)
        r = rng.uniform(13.2, 17.0)
        x, y = math.cos(a) * r, math.sin(a) * r
        z = _surface_z(x, y)
        h = rng.uniform(0.55, 1.35)
        rad = rng.uniform(0.34, 0.58)
        _add_tube(verts, faces,
                  [(x, y, z - 0.15), (x + 0.03, y, z + h * 0.5), (x, y, z + h)],
                  [rad * 1.15, rad, rad * 0.92], sides=9)
    return verts, faces


# ---------------------------------------------------------------------------
# Vines
# ---------------------------------------------------------------------------

def _leaf_card(verts, faces, center, size, yaw, pitch, rng):
    up = Vector((0.0, 0.0, 1.0))
    d = Vector((math.cos(yaw) * math.cos(pitch),
                math.sin(yaw) * math.cos(pitch),
                math.sin(pitch)))
    side = d.cross(up)
    if side.length < 1e-5:
        side = Vector((1, 0, 0))
    side.normalize()
    up2 = side.cross(d).normalized()
    roll = rng.uniform(0, TAU)
    cr, sr = math.cos(roll), math.sin(roll)
    s2 = side * cr + up2 * sr
    u2 = up2 * cr - side * sr
    h = size * 0.5
    c = Vector(center)
    off = len(verts)
    verts.extend([tuple(c - s2 * h - u2 * h), tuple(c + s2 * h - u2 * h),
                  tuple(c + s2 * h + u2 * h), tuple(c - s2 * h + u2 * h)])
    faces.append((off, off + 1, off + 2, off + 3))


def _build_vines(rng, trees):
    stems_v, stems_f = [], []
    leaf_v, leaf_f = [], []

    def add_vine(points, rad):
        _add_tube(stems_v, stems_f, points, [rad] * len(points), sides=5)
        for i in range(1, len(points) - 1, 2):
            p = points[i]
            for _ in range(2):
                c = (p[0] + rng.uniform(-0.18, 0.18),
                     p[1] + rng.uniform(-0.18, 0.18),
                     p[2] + rng.uniform(-0.15, 0.15))
                _leaf_card(leaf_v, leaf_f, c, rng.uniform(0.35, 0.7),
                           rng.uniform(0, TAU), rng.uniform(-0.7, 0.7), rng)

    # vines hanging from the broken north arch
    cz = terrain.height_at(0.0, 13.3)
    R = 2.9
    for i, lx in enumerate((2.10, 1.35, 0.60, -0.20)):
        top = cz + 5.0 + math.sqrt(max(0.0, R * R - lx * lx)) - 0.20
        bottom = top - rng.uniform(2.8, 4.4)
        pts = []
        for j in range(12):
            t = j / 11.0
            sway = math.sin(t * 5.2 + i) * 0.16
            pts.append((lx + sway, 13.3 + math.cos(t * 4.0 + i) * 0.10,
                        top + (bottom - top) * t))
        add_vine(pts, rng.uniform(0.022, 0.040))

    # vines creeping down the hero trunks
    for idx in (1, 2, 3, 4, 6):
        if idx >= len(trees):
            continue
        tr = trees[idx]
        for k in range(2):
            a0 = rng.uniform(0, TAU)
            top = tr["z"] + tr["height"] * rng.uniform(0.24, 0.36)
            bottom = tr["z"] + rng.uniform(0.25, 0.8)
            pts = []
            for j in range(16):
                t = j / 15.0
                zz = top + (bottom - top) * t
                tt = max(0.0, min(1.0, (zz - tr["z"]) / tr["height"]))
                flare = 1.0 + 0.42 * max(0.0, 1.0 - tt * 5.0) ** 2
                rr = tr["radius"] * (1.0 - 0.80 * tt) * flare + 0.05
                ang = a0 + t * 2.0 + k * 2.4
                pts.append((tr["x"] + math.cos(ang) * rr,
                            tr["y"] + math.sin(ang) * rr, zz))
            add_vine(pts, rng.uniform(0.020, 0.034))

    # ivy climbing the surviving colonnade
    for i in range(16):
        ang = TAU * i / 16
        if abs(((ang - math.pi * 0.5 + math.pi) % TAU) - math.pi) < math.radians(16):
            continue
        if rng.random() > 0.62:
            continue
        x = math.cos(ang) * config.COLONNADE_R
        y = math.sin(ang) * config.COLONNADE_R
        z0 = terrain.height_at(x, y)
        top = z0 + rng.uniform(1.9, 3.8)
        start = rng.uniform(0, TAU)
        pts = []
        for j in range(14):
            t = j / 13.0
            a = start + t * rng.uniform(1.3, 2.1) * TAU
            rr = 0.46 - 0.05 * t
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr,
                        z0 + 0.48 + (top - z0 - 0.48) * t))
        add_vine(pts, rng.uniform(0.018, 0.030))

    # vines spilling down the altar's front face (the camera-facing side)
    for i, ax in enumerate((-1.05, -0.15, 0.75, 1.25)):
        top = rng.uniform(2.6, 3.35)
        pts = []
        for j in range(13):
            t = j / 12.0
            pts.append((ax + math.sin(t * 3.4 + i) * 0.07,
                        7.49 + math.sin(t * 5.0 + i) * 0.025,
                        top - t * (top - 0.55)))
        add_vine(pts, rng.uniform(0.016, 0.028))

    # thick roots gripping the sides of the altar
    for pts, radii in (
        ([(-1.58, 7.20, 0.00), (-1.38, 7.42, 0.55), (-1.22, 7.50, 1.15),
          (-1.32, 7.49, 1.72)],
         [0.12, 0.095, 0.06, 0.03]),
        ([(1.62, 7.16, 0.00), (1.42, 7.44, 0.50), (1.30, 7.51, 1.10),
          (1.44, 7.50, 1.62)],
         [0.11, 0.085, 0.055, 0.028]),
        ([(0.82, 7.36, 1.42), (0.32, 7.30, 1.46), (-0.18, 7.33, 1.43),
          (-0.62, 7.38, 1.40)],
         [0.075, 0.06, 0.045, 0.025]),
    ):
        _add_tube(stems_v, stems_f, pts, radii, sides=6)

    return (stems_v, stems_f), (leaf_v, leaf_f)


# ---------------------------------------------------------------------------
# Lanterns
# ---------------------------------------------------------------------------

def _build_lanterns(rng):
    orbs_v, orbs_f = [], []
    wood_v, wood_f = [], []
    positions = []

    def add_lantern(x, y, z, cord_top, rng_):
        ret = bmesh.new()
        bmesh.ops.create_icosphere(ret, subdivisions=2, radius=0.085)
        for v in ret.verts:
            v.co.z *= 1.18
            v.co += Vector((x, y, z))
        ret.verts.index_update()
        tmp_v = [tuple(v.co) for v in ret.verts]
        tmp_f = [tuple(v.index for v in f.verts) for f in ret.faces]
        ret.free()
        off = len(orbs_v)
        orbs_v.extend(tmp_v)
        orbs_f.extend(tuple(i + off for i in f) for f in tmp_f)
        positions.append((x, y, z))

        # wooden cap
        _add_tube(wood_v, wood_f,
                  [(x, y, z + 0.088), (x, y, z + 0.135), (x, y, z + 0.175)],
                  [0.046, 0.060, 0.028], sides=8)

        # cord up into the canopy
        pts = []
        n = 6
        for j in range(n):
            t = j / (n - 1)
            sway = math.sin(t * 4.0 + x) * 0.07 * t
            pts.append((x + sway, y + sway * 0.6,
                        z + 0.175 + (cord_top - z - 0.175) * t))
        _add_tube(wood_v, wood_f, pts, [0.013] * n, sides=4)

    for i, ang in enumerate((24, 68, 141, 187, 232, 288, 336)):
        a = math.radians(ang)
        r = 12.1
        x, y = math.cos(a) * r, math.sin(a) * r
        z = 4.3 + rng.uniform(-0.35, 0.7)
        add_lantern(x, y, z, z + rng.uniform(3.2, 4.4), rng)

    cz = terrain.height_at(0.0, 13.2)
    for lx in (1.90, 0.85, -0.25):
        intrados = cz + 5.0 + math.sqrt(max(0.0, R_ARCH * R_ARCH - lx * lx))
        add_lantern(lx, 13.2, intrados - 0.55, intrados - 0.06, rng)
    return (orbs_v, orbs_f), (wood_v, wood_f), positions


R_ARCH = 2.9


# ---------------------------------------------------------------------------
# Fireflies
# ---------------------------------------------------------------------------

def _build_fireflies(rng):
    bm = bmesh.new()
    count = config.FIREFLY_COUNT
    for i in range(count):
        if i < int(count * 0.65):
            r = math.sqrt(rng.uniform(2.0 ** 2, 8.6 ** 2))
            a = rng.uniform(0, TAU)
            x, y = math.cos(a) * r, math.sin(a) * r
            z = rng.uniform(0.7, 4.8)
        else:
            r = rng.uniform(10.0, 16.5)
            a = rng.uniform(0, TAU)
            x, y = math.cos(a) * r, math.sin(a) * r
            z = rng.uniform(0.6, 3.6)
        ret = bmesh.ops.create_icosphere(bm, subdivisions=1,
                                         radius=rng.uniform(0.010, 0.022))
        for v in ret["verts"]:
            v.co += Vector((x, y, z))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_props(mats, trees):
    util.reset_collection(config.C_PROPS)
    rng = util.sub_rng("props")

    boulders = util.bmesh_object("PROP_Boulders", _build_boulders(rng),
                                 config.C_PROPS, mats["stone"], smooth=True)
    util.cube_uv(boulders, 2.2)
    util.shade_smooth_by_angle(boulders, 34.0)
    util.link_object(boulders, config.C_EXPORT)

    log_v, log_f = _build_logs(rng)
    logs = util.mesh_object("PROP_Logs", log_v, log_f, config.C_PROPS,
                            mats["bark"], smooth=True)
    util.cylindrical_uv(logs, 2.0)
    util.shade_smooth_by_angle(logs, 38.0)
    util.link_object(logs, config.C_EXPORT)

    (vine_v, vine_f), (vleaf_v, vleaf_f) = _build_vines(rng, trees)
    vines = util.mesh_object("PROP_Vines", vine_v, vine_f, config.C_PROPS,
                             mats["bark"], smooth=True)
    util.cylindrical_uv(vines, 1.4)
    util.link_object(vines, config.C_EXPORT)
    vine_leaves = util.mesh_object("PROP_VineLeaves", vleaf_v, vleaf_f,
                                   config.C_PROPS, mats["leaf"])
    mesh = vine_leaves.data
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        if len(poly.loop_indices) == 4:
            uv.data[poly.loop_indices[0]].uv = (0.0, 0.0)
            uv.data[poly.loop_indices[1]].uv = (1.0, 0.0)
            uv.data[poly.loop_indices[2]].uv = (1.0, 1.0)
            uv.data[poly.loop_indices[3]].uv = (0.0, 1.0)
    util.link_object(vine_leaves, config.C_EXPORT)

    (orb_v, orb_f), (wood_v, wood_f), lanterns = _build_lanterns(rng)
    orbs = util.mesh_object("PROP_LanternOrbs", orb_v, orb_f, config.C_PROPS,
                            mats["lantern"], smooth=True)
    orbs["lantern_json"] = json.dumps(lanterns)
    util.link_object(orbs, config.C_EXPORT)
    wood = util.mesh_object("PROP_LanternWood", wood_v, wood_f, config.C_PROPS,
                            mats["wood"], smooth=True)
    util.cylindrical_uv(wood, 1.0)
    util.link_object(wood, config.C_EXPORT)

    flies = util.bmesh_object("PROP_Fireflies", _build_fireflies(rng),
                              config.C_PROPS, mats["firefly"])
    util.link_object(flies, config.C_EXPORT)

    print(f"[props] {config.BOULDER_COUNT} boulders, 3 logs, "
          f"{len(lanterns)} lanterns, {config.FIREFLY_COUNT} fireflies")
    return {"lanterns": lanterns, "boulders": boulders}
