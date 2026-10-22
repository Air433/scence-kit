"""Cycles-only ocean, foam and cloud dressing.

None of this is exported: the Godot project renders real-time water and sky.
The Blender previews use the same shoreline harmonics so the hero renders and
the runtime agree on where the beach is.
"""
from __future__ import annotations

import math

import bpy
from mathutils import Vector

from arena_kit import config, util
from arena_kit.materials import make_emissive

from . import layout
from .geo import uv_sphere

TAU = math.pi * 2.0
PREVIEW = "EF_PREVIEW"


def _wave_height(x, y):
    z = 0.0
    for amp, length, dx, dy, phase in (
        (0.30, 46.0, 0.30, 0.95, 0.0),
        (0.20, 27.0, -0.55, 0.84, 1.9),
        (0.12, 17.0, 0.86, 0.51, 4.2),
        (0.07, 9.5, -0.31, -0.95, 2.6),
    ):
        k = TAU / length
        z += amp * math.sin(k * (x * dx + y * dy) + phase)
    return z


def _ocean(mats):
    size = 1100.0
    res = 170
    half = size * 0.5
    step = size / res
    verts = []
    for j in range(res + 1):
        y = -half + j * step
        for i in range(res + 1):
            x = -half + i * step
            verts.append((x, y, _wave_height(x, y)))
    faces = []
    for j in range(res):
        for i in range(res):
            a = j * (res + 1) + i
            faces.append((a, a + 1, a + res + 2, a + res + 1))
    obj = util.mesh_object("PREVIEW_Ocean", verts, faces, PREVIEW,
                           mats["ocean_preview"], smooth=True)
    uvl = obj.data.uv_layers.new(name="UVMap")
    for loop in obj.data.loops:
        co = obj.data.vertices[loop.vertex_index].co
        uvl.data[loop.index].uv = (co.x / 23.0, co.y / 23.0)
    return obj


def _waterline(angle):
    lo, hi = 12.0, 48.0
    ca, sa = math.cos(angle), math.sin(angle)
    for _ in range(26):
        mid = (lo + hi) * 0.5
        if layout.terrain_height(ca * mid, sa * mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return lo


def _foam(mats):
    n = 300
    verts, faces, uvs = [], [], []
    for i in range(n + 1):
        a = TAU * i / n
        r = _waterline(a)
        ripple = 0.10 * math.sin(a * 23.0) + 0.06 * math.sin(a * 41.0 + 1.7)
        for off in (-1.45, 0.55):
            z = 0.06 + ripple + (0.035 if off > 0 else 0.0)
            verts.append((math.cos(a) * (r + off), math.sin(a) * (r + off), z))
            uvs.append((i / n * 9.0, 0.0 if off < 0 else 1.0))
    for i in range(n):
        a = i * 2
        faces.append((a, a + 2, a + 3, a + 1))
    obj = util.mesh_object("PREVIEW_Foam", verts, faces, PREVIEW,
                           mats["foam_preview"])
    uvl = obj.data.uv_layers.new(name="UVMap")
    for loop in obj.data.loops:
        uvl.data[loop.index].uv = uvs[loop.vertex_index]
    return obj


def _clouds(mats):
    specs = [
        (-150.0, 240.0, 48.0, 78.0, 26.0),
        (-95.0, 300.0, 70.0, 110.0, 34.0),
        (-30.0, 260.0, 58.0, 96.0, 30.0),
        (30.0, 330.0, 86.0, 140.0, 38.0),
        (95.0, 275.0, 64.0, 90.0, 28.0),
        (150.0, 340.0, 52.0, 120.0, 30.0),
        (-10.0, 390.0, 96.0, 180.0, 40.0),
        (120.0, 410.0, 40.0, 150.0, 26.0),
    ]
    # Camera position from scene.py; cards rotate to face it.
    cam_x, cam_y = 1.5, -47.0
    cell_uv = [(0.0, 0.0), (0.5, 0.0), (0.0, 0.5), (0.5, 0.5)]
    verts, faces, uvs = [], [], []
    for idx, (cx, cy, cz, w, h) in enumerate(specs):
        nx, ny = cam_x - cx, cam_y - cy
        length = max(math.hypot(nx, ny), 1e-4)
        dirx, diry = ny / length, -nx / length
        hw = w * 0.5
        off = len(verts)
        verts.extend([
            (cx - dirx * hw, cy - diry * hw, cz - h * 0.5),
            (cx + dirx * hw, cy + diry * hw, cz - h * 0.5),
            (cx + dirx * hw, cy + diry * hw, cz + h * 0.5),
            (cx - dirx * hw, cy - diry * hw, cz + h * 0.5),
        ])
        cu, cv = cell_uv[idx % 4]
        u0, u1 = cu, cu + 0.5
        if idx % 2 == 1:
            u0, u1 = u1, u0
        v0, v1 = cv, cv + 0.5
        uvs.extend([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
        faces.append((off, off + 1, off + 2, off + 3))
    obj = util.mesh_object("PREVIEW_Clouds", verts, faces, PREVIEW,
                           mats["cloud_preview"])
    uvl = obj.data.uv_layers.new(name="UVMap")
    for loop in obj.data.loops:
        uvl.data[loop.index].uv = uvs[loop.vertex_index]
    return obj


def _sun():
    mat = make_emissive("sun_preview", (1.0, 0.52, 0.18), 26.0,
                        base_color=(0.0, 0.0, 0.0))
    d = Vector(config.SUN_POS) - Vector(config.SUN_TARGET)
    d.normalize()
    pos = Vector((0.0, 0.0, 4.0)) + d * 520.0
    v, f = uv_sphere(pos.x, pos.y, pos.z, 11.0, sides=24, rings=12)
    obj = util.mesh_object("PREVIEW_Sun", v, f, PREVIEW, mat, smooth=True)
    return obj


def build_preview(mats):
    util.reset_collection(PREVIEW)
    coll = util.coll(PREVIEW)
    coll.hide_render = False
    coll.hide_viewport = False
    ocean = _ocean(mats)
    foam = _foam(mats)
    clouds = _clouds(mats)
    sun = _sun()
    print("[preview] ocean + foam + clouds + sun billboards (not exported)")
    return {"ocean": ocean, "foam": foam, "clouds": clouds, "sun": sun}
