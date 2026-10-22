"""Beach grass and shrub cards.

Cards keep their base at UV.y = 0 so the Godot wind shader can bend them by
vertex height.  Geometry stays in world space because whole clumps are baked
into one mesh for draw-call efficiency.
"""
from __future__ import annotations

import math

from arena_kit import config, util

from . import layout

TAU = math.pi * 2.0


def _add_card(verts, faces, uvs, cx, cy, cz, yaw, width, height, lean,
              segments=3, bend=0.0):
    dirx, diry = math.cos(yaw), math.sin(yaw)
    sidex, sidey = -diry, dirx
    off = len(verts)
    for i in range(segments + 1):
        t = i / segments
        w = width * 0.5 * (1.0 - 0.80 * t) + 0.004
        droop = -height * 0.18 * t * t
        px = cx + dirx * lean * t * t + sidex * bend * math.sin(math.pi * t)
        py = cy + diry * lean * t * t + sidey * bend * math.sin(math.pi * t)
        pz = cz + height * t + droop
        verts.append((px - sidex * w, py - sidey * w, pz))
        verts.append((px + sidex * w, py + sidey * w, pz))
        uvs.append((0.0, t))
        uvs.append((1.0, t))
    for i in range(segments):
        a = off + i * 2
        faces.append((a, a + 2, a + 3, a + 1))


def _make_object(name, verts, faces, uvs, mat):
    obj = util.mesh_object(name, verts, faces, config.C_FOLIAGE, mat)
    uvl = obj.data.uv_layers.new(name="UVMap")
    for loop in obj.data.loops:
        uvl.data[loop.index].uv = uvs[loop.vertex_index]
    util.link_object(obj, config.C_EXPORT)
    return obj


def _path_samples():
    pts = layout.path_points()
    out = []
    for i, p in enumerate(pts):
        out.append(p)
        if i + 1 < len(pts):
            q = pts[i + 1]
            out.append(((p[0] + q[0]) * 0.5, (p[1] + q[1]) * 0.5))
    return out


def _near_path(x, y, samples, limit=1.15):
    d2 = limit * limit
    return any((x - px) ** 2 + (y - py) ** 2 < d2 for px, py in samples)


def _grass_ok(x, y, r, path_samples):
    z = layout.terrain_height(x, y)
    if z < 0.55:
        return False
    if r < layout.PLATEAU_R + 1.3:
        return False
    if layout.slope_at(x, y, 0.4) > 0.62:
        return False
    if _near_path(x, y, path_samples):
        return False
    if math.hypot(x - layout.LIGHTHOUSE_X,
                  y - layout.LIGHTHOUSE_Y) < 3.4:
        return False
    return True


def _bush_ok(x, y, r, path_samples):
    z = layout.terrain_height(x, y)
    if z < 0.75:
        return False
    if r < layout.PLATEAU_R + 1.0:
        return False
    if layout.slope_at(x, y, 0.4) > 0.55:
        return False
    if _near_path(x, y, path_samples, 1.4):
        return False
    if math.hypot(x - layout.LIGHTHOUSE_X,
                  y - layout.LIGHTHOUSE_Y) < 4.2:
        return False
    return True


def build_foliage(mats):
    util.reset_collection(config.C_FOLIAGE)
    path_samples = _path_samples()

    # --- grass clumps ------------------------------------------------------
    rng = util.sub_rng("island_grass")
    spots = util.poisson_disc(config.GRASS_CLUMPS, 15.0, 31.5, 0.85, rng,
                              accept=lambda x, y, r: _grass_ok(
                                  x, y, r, path_samples))
    gv, gf, gu = [], [], []
    for x, y in spots:
        z = layout.terrain_height(x, y) + 0.01
        base_yaw = rng.uniform(0, TAU)
        for k in range(3):
            _add_card(gv, gf, gu, x, y, z,
                      base_yaw + k * TAU / 3 + rng.uniform(-0.35, 0.35),
                      rng.uniform(0.30, 0.58), rng.uniform(0.45, 0.95),
                      rng.uniform(0.05, 0.32), segments=3,
                      bend=rng.uniform(-0.12, 0.12))
    grass = _make_object("FOLIAGE_Grass", gv, gf, gu, mats["grass_card"])

    # --- shrubs -----------------------------------------------------------
    rng = util.sub_rng("island_bushes")
    spots = util.poisson_disc(config.FERN_CLUMPS, 15.5, 30.5, 2.0, rng,
                              accept=lambda x, y, r: _bush_ok(
                                  x, y, r, path_samples))
    bv, bf, bu = [], [], []
    for x, y in spots:
        z = layout.terrain_height(x, y) + 0.02
        base_yaw = rng.uniform(0, TAU)
        scale = rng.uniform(0.75, 1.5)
        for k in range(6):
            _add_card(bv, bf, bu, x, y, z,
                      base_yaw + TAU * k / 6 + rng.uniform(-0.3, 0.3),
                      rng.uniform(0.62, 1.05) * scale,
                      rng.uniform(0.75, 1.25) * scale,
                      rng.uniform(0.18, 0.65) * scale, segments=3,
                      bend=rng.uniform(-0.16, 0.16))

    # A few ferns hugging the palm trunks.
    for x, y, z, _ang, _rad in layout.palm_sites():
        for k in range(4):
            a = rng.uniform(0, TAU)
            off = rng.uniform(0.7, 1.3)
            px, py = x + math.cos(a) * off, y + math.sin(a) * off
            pz = layout.terrain_height(px, py) + 0.02
            scale = rng.uniform(0.55, 0.9)
            for j in range(4):
                _add_card(bv, bf, bu, px, py, pz,
                          a + j * TAU / 4 + rng.uniform(-0.2, 0.2),
                          rng.uniform(0.55, 0.85) * scale,
                          rng.uniform(0.6, 1.0) * scale,
                          rng.uniform(0.2, 0.5) * scale, segments=3,
                          bend=rng.uniform(-0.1, 0.1))
    bushes = _make_object("FOLIAGE_Bushes", bv, bf, bu, mats["bush_leaf"])

    print(f"[foliage] {len(spots)} shrub clumps, grass leaves "
          f"{sum(len(o.data.polygons) for o in (grass, bushes))} quads")
    return {"grass": grass, "bushes": bushes}
