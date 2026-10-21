"""Forest floor dressing: ferns, grass, moss patches and glowing mushrooms."""
from __future__ import annotations

import math
import random

import bmesh
import bpy
from mathutils import Vector

from . import config, terrain, util

TAU = math.pi * 2.0


# ---------------------------------------------------------------------------
# Placement helpers
# ---------------------------------------------------------------------------

def _surface_z(x: float, y: float) -> float:
    """Top of the arena tiers inside the ring, terrain outside."""
    r = math.hypot(x, y)
    if r < config.INNER_R:
        return 0.0
    if r < config.OUTER_R:
        tier = min(config.TIER_COUNT - 1,
                   int((r - config.INNER_R) / config.TIER_TREAD))
        return (tier + 1) * config.TIER_RISE
    return terrain.height_at(x, y)


def _tree_centres():
    out = []
    for ang, rad in zip(config.HERO_TREE_ANGLES, config.HERO_TREE_RADII):
        a = math.radians(ang)
        out.append((math.cos(a) * rad, math.sin(a) * rad))
    return out


_TREES = _tree_centres()


def _clear_of_trees(x, y, pad=1.7):
    return all((x - tx) ** 2 + (y - ty) ** 2 > (pad + 1.0) ** 2
               for tx, ty in _TREES)


def _camera_wedge(x, y, pad_deg=17.0):
    ang = math.degrees(math.atan2(y, x))
    delta = abs((ang - (-69.0) + 180.0) % 360.0 - 180.0)
    return math.hypot(x, y) > 9.4 and delta < pad_deg


def _accept_outer(x, y, r):
    if y > 6.8 and abs(x) < 2.7:          # north stair approach
        return False
    if x > 9.8 and abs(y) < 2.2:          # east arch approach
        return False
    if _camera_wedge(x, y):
        return False
    return _clear_of_trees(x, y)


def _accept_apron(x, y, r):
    return _accept_outer(x, y, r)


# ---------------------------------------------------------------------------
# Card meshes
# ---------------------------------------------------------------------------

def _card(verts, faces, base, width, height, yaw, tilt):
    fwd = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    right = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    up = Vector((0.0, 0.0, 1.0))
    tip = (up * math.cos(tilt) + fwd * math.sin(tilt)).normalized()
    b = Vector(base)
    v0 = b - right * (width * 0.5)
    v1 = b + right * (width * 0.5)
    v3 = v0 + tip * height
    v2 = v1 + tip * height
    off = len(verts)
    verts.extend([tuple(v0), tuple(v1), tuple(v2), tuple(v3)])
    faces.append((off, off + 1, off + 2, off + 3))


def _add_clump(verts, faces, x, y, z, height, width, rng, cards=4):
    phase = rng.uniform(0, TAU)
    for i in range(cards):
        yaw = phase + TAU * i / cards + rng.uniform(-0.25, 0.25)
        tilt = rng.uniform(0.10, 0.38)
        h = height * rng.uniform(0.82, 1.18)
        w = width * rng.uniform(0.82, 1.18)
        _card(verts, faces, (x, y, z - 0.03), w, h, yaw, tilt)


def _set_card_uvs(obj):
    mesh = obj.data
    uv = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        if len(poly.loop_indices) == 4:
            uv.data[poly.loop_indices[0]].uv = (0.0, 0.0)
            uv.data[poly.loop_indices[1]].uv = (1.0, 0.0)
            uv.data[poly.loop_indices[2]].uv = (1.0, 1.0)
            uv.data[poly.loop_indices[3]].uv = (0.0, 1.0)


def _planar_uv(obj, scale=1.5):
    mesh = obj.data
    uv = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        co = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (co.x / scale, co.y / scale)


def _finalize_cards(name, verts, faces, mat, collection):
    obj = util.mesh_object(name, verts, faces, collection, mat)
    _set_card_uvs(obj)
    util.link_object(obj, config.C_EXPORT)
    return obj


# ---------------------------------------------------------------------------
# Mushrooms
# ---------------------------------------------------------------------------

def _mushroom_parts(x, y, z, scale, rng):
    sides = 10
    h = rng.uniform(0.12, 0.30) * scale
    stem_r = rng.uniform(0.010, 0.020) * scale
    cap_r = rng.uniform(0.055, 0.115) * scale
    lean = rng.uniform(-0.03, 0.03) * scale

    sv, sf = util.make_tube(
        [(x, y, z - 0.02), (x + lean, y, z + h * 0.55),
         (x + lean * 1.6, y, z + h)],
        [stem_r * 1.25, stem_r, stem_r * 0.9], sides=6, caps=True)

    rings = []
    for rr, dz in ((1.00, 0.0), (0.92, 0.28), (0.62, 0.62), (0.18, 0.92)):
        ring = []
        for s in range(sides):
            a = TAU * s / sides
            ring.append((x + lean * 1.6 + math.cos(a) * cap_r * rr,
                         y + math.sin(a) * cap_r * rr,
                         z + h + cap_r * 0.55 + cap_r * dz))
        rings.append(ring)
    cv, cf = util.loft_rings(rings, caps=True)
    return (sv, sf), (cv, cf)


def _build_mushrooms(rng, count):
    caps_v, caps_f = [], []
    stems_v, stems_f = [], []
    total = 0
    pts = util.poisson_disc(count, 10.4, 24.0, 2.6, rng, accept=_accept_outer)
    for x, y in pts:
        for _ in range(rng.randint(4, 9)):
            mx = x + rng.uniform(-0.65, 0.65)
            my = y + rng.uniform(-0.65, 0.65)
            mz = _surface_z(mx, my)
            (sv, sf), (cv, cf) = _mushroom_parts(mx, my, mz,
                                                 rng.uniform(0.7, 1.5), rng)
            off = len(stems_v)
            stems_v.extend(sv)
            stems_f.extend(tuple(i + off for i in f) for f in sf)
            off = len(caps_v)
            caps_v.extend(cv)
            caps_f.extend(tuple(i + off for i in f) for f in cf)
            total += 1
    return (caps_v, caps_f), (stems_v, stems_f), total


# ---------------------------------------------------------------------------
# Moss patches
# ---------------------------------------------------------------------------

def _build_moss(rng, count=40):
    bm = bmesh.new()

    def add_patch(x, y, z, radius, height_scale=1.0):
        rings = []
        for rr, dz in ((1.0, 0.0), (0.62, 0.05 * height_scale),
                       (0.12, 0.08 * height_scale)):
            ring = []
            sides = 12
            for s in range(sides):
                a = TAU * s / sides
                wob = 1.0 + 0.16 * math.sin(a * 3.0 + x + y)
                ring.append((x + math.cos(a) * radius * rr * wob,
                             y + math.sin(a) * radius * rr * wob,
                             z + dz))
            rings.append(ring)
        v, f = util.loft_rings(rings, caps=True)
        bv = [bm.verts.new(vv) for vv in v]
        for ff in f:
            try:
                bm.faces.new([bv[i] for i in ff])
            except ValueError:
                pass

    pts = util.poisson_disc(count, 12.6, 21.0, 1.1, rng,
                            accept=lambda x, y, r: _accept_outer(x, y, r))
    for x, y in pts:
        add_patch(x, y, terrain.height_at(x, y), rng.uniform(0.35, 1.05))

    # moss creeping out of the flagstone joints on the arena floor and tiers
    for ring_r in (3.8, 5.1, 6.4, 7.7, 8.98, 9.88, 10.78, 11.68):
        for _ in range(rng.randint(16, 24)):
            a = rng.uniform(0, TAU)
            r = ring_r + rng.uniform(-0.05, 0.05)
            x, y = math.cos(a) * r, math.sin(a) * r
            add_patch(x, y, _surface_z(x, y) + 0.004,
                      rng.uniform(0.07, 0.22), 0.45)

    # moss around the feet of the colonnade
    for i in range(16):
        ang = TAU * i / 16
        if abs(((ang - math.pi * 0.5 + math.pi) % TAU) - math.pi) < math.radians(16):
            continue
        x = math.cos(ang) * config.COLONNADE_R
        y = math.sin(ang) * config.COLONNADE_R
        for _ in range(2):
            a = rng.uniform(0, TAU)
            rr = rng.uniform(0.55, 0.85)
            px, py = x + math.cos(a) * rr, y + math.sin(a) * rr
            add_patch(px, py, _surface_z(px, py) + 0.004,
                      rng.uniform(0.10, 0.26), 0.5)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ---------------------------------------------------------------------------
# Fallen leaves
# ---------------------------------------------------------------------------

def _build_leaf_litter(rng, count=430):
    verts, faces = [], []
    pillars = [(math.cos(TAU * i / 16) * config.COLONNADE_R,
                math.sin(TAU * i / 16) * config.COLONNADE_R)
               for i in range(16)]
    placed = 0
    for _ in range(count):
        x = y = 0.0
        ok = False
        for _try in range(12):
            r = math.sqrt(rng.uniform(3.9 ** 2, 15.5 ** 2))
            a = rng.uniform(0, TAU)
            x, y = math.cos(a) * r, math.sin(a) * r
            if abs(x) < 2.1 and 6.2 < y < 8.9:
                continue
            if any((x - px) ** 2 + (y - py) ** 2 < 0.8 ** 2 for px, py in pillars):
                continue
            ok = True
            break
        if not ok:
            continue
        z = _surface_z(x, y) + 0.022
        w = rng.uniform(0.10, 0.24)
        h = w * rng.uniform(1.0, 1.5)
        _card(verts, faces, (x, y, z), w, h,
              rng.uniform(0, TAU), math.pi * 0.5 + rng.uniform(-0.04, 0.04))
        placed += 1
        # a few companion leaves in the same drift
        for _ in range(rng.choice((0, 0, 0, 1, 2))):
            dx, dy = rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35)
            w2 = rng.uniform(0.09, 0.20)
            _card(verts, faces,
                  (x + dx, y + dy, _surface_z(x + dx, y + dy) + 0.022),
                  w2, w2 * rng.uniform(1.0, 1.5), rng.uniform(0, TAU),
                  math.pi * 0.5 + rng.uniform(-0.04, 0.04))
            placed += 1
    print(f"[foliage] {placed} fallen leaves")
    return verts, faces


# ---------------------------------------------------------------------------
# Distant undergrowth
# ---------------------------------------------------------------------------

def _build_distant_undergrowth(rng, count=240):
    """Low bush mass ringing the clearing so the horizon never reads empty."""
    verts, faces = [], []
    for _ in range(count):
        a = rng.uniform(0, TAU)
        r = rng.uniform(24.0, 38.0)
        x, y = math.cos(a) * r, math.sin(a) * r
        z = terrain.height_at(x, y) - 0.18
        h = rng.uniform(1.6, 4.4)
        w = h * rng.uniform(1.15, 1.75)
        yaw = rng.uniform(0, TAU)
        for k in range(rng.randint(2, 3)):
            _card(verts, faces, (x, y, z), w, h * rng.uniform(0.85, 1.15),
                  yaw + TAU * k / 3 + rng.uniform(-0.25, 0.25),
                  rng.uniform(-0.10, 0.10))
    return verts, faces


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_foliage(mats):
    util.reset_collection(config.C_FOLIAGE)
    rng = util.sub_rng("foliage")

    fern_v, fern_f = [], []
    outer = util.poisson_disc(int(config.FERN_CLUMPS * 0.86), 12.0, 27.5, 0.62,
                              rng, accept=_accept_outer)
    for x, y in outer:
        z = terrain.height_at(x, y)
        _add_clump(fern_v, fern_f, x, y, z,
                   rng.uniform(1.15, 2.15), rng.uniform(1.1, 2.0), rng, cards=4)
    apron = util.poisson_disc(90, 9.3, 12.2, 0.50, rng, accept=_accept_apron)
    for x, y in apron:
        z = _surface_z(x, y)
        _add_clump(fern_v, fern_f, x, y, z,
                   rng.uniform(0.75, 1.35), rng.uniform(0.7, 1.2), rng, cards=4)
    ferns = _finalize_cards("FOLIAGE_Ferns", fern_v, fern_f, mats["fern"],
                            config.C_FOLIAGE)

    grass_v, grass_f = [], []
    gout = util.poisson_disc(int(config.GRASS_CLUMPS * 0.83), 11.9, 29.0, 0.40,
                             rng, accept=_accept_outer)
    for x, y in gout:
        z = terrain.height_at(x, y)
        _add_clump(grass_v, grass_f, x, y, z,
                   rng.uniform(0.45, 1.05), rng.uniform(0.5, 1.0), rng, cards=3)
    gapron = util.poisson_disc(300, 9.2, 12.3, 0.34, rng, accept=_accept_apron)
    for x, y in gapron:
        z = _surface_z(x, y)
        _add_clump(grass_v, grass_f, x, y, z,
                   rng.uniform(0.30, 0.70), rng.uniform(0.35, 0.7), rng, cards=3)

    # weeds pushing up through the flagstone joints
    for ring_r in (3.8, 5.1, 6.4, 7.7, 8.98, 9.88, 10.78, 11.68):
        for _ in range(rng.randint(9, 15)):
            a = rng.uniform(0, TAU)
            r = ring_r + rng.uniform(-0.045, 0.045)
            x, y = math.cos(a) * r, math.sin(a) * r
            _add_clump(grass_v, grass_f, x, y, _surface_z(x, y),
                       rng.uniform(0.16, 0.36), rng.uniform(0.16, 0.30),
                       rng, cards=3)
    grass = _finalize_cards("FOLIAGE_Grass", grass_v, grass_f, mats["grass"],
                            config.C_FOLIAGE)

    caps, stems, mushroom_count = _build_mushrooms(rng, config.MUSHROOM_CLUSTERS)
    mushrooms = util.mesh_object("FOLIAGE_Mushrooms", caps[0], caps[1],
                                 config.C_FOLIAGE, mats["mushroom"], smooth=True)
    mushroom_stems = util.mesh_object("FOLIAGE_MushroomStems", stems[0], stems[1],
                                      config.C_FOLIAGE, mats["wood"], smooth=True)
    util.cylindrical_uv(mushroom_stems, 1.2)
    moss = util.bmesh_object("FOLIAGE_MossPatches", _build_moss(rng),
                             config.C_FOLIAGE, mats["moss"])
    _planar_uv(moss, 1.4)

    litter = _finalize_cards("FOLIAGE_LeafLitter", *_build_leaf_litter(rng),
                             mats["litter"], config.C_FOLIAGE)

    undergrowth = _finalize_cards("FOLIAGE_Undergrowth",
                                  *_build_distant_undergrowth(rng),
                                  mats["leaf"], config.C_FOLIAGE)

    for obj in (mushrooms, mushroom_stems, moss):
        util.link_object(obj, config.C_EXPORT)

    print(f"[foliage] ferns {len(outer) + len(apron)} clumps, "
          f"grass {len(gout) + len(gapron)} clumps, "
          f"{mushroom_count} mushrooms")
    return {"ferns": ferns, "grass": grass, "mushrooms": mushrooms,
            "litter": litter}
