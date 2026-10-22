"""Island heightfield, split into above-water land and seabed.

Faces share the grid vertices; material variation is a per-polygon index.
The split lets the Godot planar-reflection camera exclude the seabed without
excluding the island itself.
"""
from __future__ import annotations

import bpy
from mathutils import Vector, noise

from arena_kit import config, util

from . import layout


def _patch_noise(x, y):
    return noise.noise(Vector((x * 0.55 + 12.3, y * 0.55 - 4.7, 0.71)))


def _finish(name, verts, faces, face_mats, mats, uv_scale, smooth_angle):
    obj = util.mesh_object(name, verts, faces, config.C_TERRAIN)
    for mat in mats:
        obj.data.materials.append(mat)
    for poly, mi in zip(obj.data.polygons, face_mats):
        poly.material_index = mi
    mesh = obj.data
    uvl = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        co = mesh.vertices[loop.vertex_index].co
        uvl.data[loop.index].uv = (co.x / uv_scale, co.y / uv_scale)
    util.link_object(obj, config.C_EXPORT)
    util.shade_smooth_by_angle(obj, smooth_angle)
    return obj


def build_terrain(mats):
    util.reset_collection(config.C_TERRAIN)
    res = config.TERRAIN_RES
    size = config.TERRAIN_SIZE
    half = size * 0.5
    step = size / res

    verts = []
    for j in range(res + 1):
        y = -half + j * step
        for i in range(res + 1):
            x = -half + i * step
            verts.append((x, y, layout.terrain_height(x, y)))

    land_mats = ("sand", "wet_sand", "grass", "rock")
    index = {k: i for i, k in enumerate(land_mats)}
    land_faces, land_ids = [], []
    sea_faces = []
    counts = {"sand": 0, "wet": 0, "grass": 0, "rock": 0, "seabed": 0}

    for j in range(res):
        for i in range(res):
            a = j * (res + 1) + i
            face = (a, a + 1, a + res + 2, a + res + 1)
            x = -half + (i + 0.5) * step
            y = -half + (j + 0.5) * step
            h = layout.terrain_height(x, y)

            if h < -0.55:
                sea_faces.append(face)
                counts["seabed"] += 1
                continue

            slope = layout.slope_at(x, y, e=max(step * 0.6, 0.35))
            n = _patch_noise(x, y)
            rocky = slope > 0.62 or (
                layout.lighthouse_hill(x, y) > 2.0
                and layout.slope_at(x, y, 0.9) > 0.30)
            if rocky:
                key = "rock"
                counts["rock"] += 1
            elif h < 1.10:
                key = "wet_sand"
                counts["wet"] += 1
            elif h > 1.9 and slope < 0.5 and n > -0.22:
                key = "grass"
                counts["grass"] += 1
            elif h > 2.6 and slope < 0.72:
                key = "grass"
                counts["grass"] += 1
            else:
                key = "sand"
                counts["sand"] += 1
            land_faces.append(face)
            land_ids.append(index[key])

    island = _finish("TERRAIN_Island", verts, land_faces, land_ids,
                     [mats[k] for k in land_mats], 7.0, 38.0)
    seabed = _finish("TERRAIN_Seabed", verts, sea_faces,
                     [0] * len(sea_faces), [mats["seabed"]], 9.0, 50.0)
    print(f"[terrain] {len(verts)} verts; faces {counts}")
    return {"island": island, "seabed": seabed}
