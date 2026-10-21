"""Forest terrain with a flattened arena hollow."""
from __future__ import annotations

import math

from mathutils import Vector, noise

from . import config, util


def _fbm(x: float, y: float, octaves: int = 4, scale: float = 0.05) -> float:
    total = 0.0
    amp = 1.0
    norm = 0.0
    f = scale
    for i in range(octaves):
        total += amp * noise.noise(Vector((x * f, y * f, 0.137 * i + 0.31)))
        norm += amp
        amp *= 0.5
        f *= 2.0
    return total / max(norm, 1e-9)


def _smoothstep(a: float, b: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - a) / (b - a + 1e-9)))
    return t * t * (3.0 - 2.0 * t)


def height_at(x: float, y: float) -> float:
    r = math.hypot(x, y)
    # Gentle bowl that closes the composition; absolutely flat under the arena.
    bowl = 1.05 * _smoothstep(13.0, 30.0, r)
    broad = _fbm(x, y, 4, 0.045)
    fine = _fbm(x, y, 3, 0.13)
    detail = 0.62 * broad + 0.22 * fine
    flat = _smoothstep(12.2, 19.0, r)
    return config.TERRAIN_BASE_Z + bowl + detail * flat


def build_terrain(mats):
    util.reset_collection(config.C_TERRAIN)
    res = config.TERRAIN_RES
    size = config.TERRAIN_SIZE
    half = size * 0.5
    step = size / res

    verts = []
    faces = []
    for j in range(res + 1):
        y = -half + j * step
        for i in range(res + 1):
            x = -half + i * step
            verts.append((x, y, height_at(x, y)))
    for j in range(res):
        for i in range(res):
            a = j * (res + 1) + i
            b = a + 1
            c = a + res + 2
            d = a + res + 1
            faces.append((a, b, c, d))

    obj = util.mesh_object("TERRAIN_Ground", verts, faces, config.C_TERRAIN,
                           mats["ground"], smooth=True)
    mesh = obj.data
    uv = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        co = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (co.x / 4.0 + 0.5, co.y / 4.0 + 0.5)

    # A slightly darker ring of leaf litter around the arena apron.
    util.link_object(obj, config.C_EXPORT)
    print(f"[terrain] {len(verts)} verts / {len(faces)} quads")
    return obj
