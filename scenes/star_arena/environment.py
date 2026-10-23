"""Exported star-dome surrounding the floating arena."""
from __future__ import annotations

import math

from arena_kit import config, util

TAU = math.pi * 2.0


def _uv_sphere(radius, lon_segs=128, lat_segs=64):
    verts = [(0.0, 0.0, radius)]
    uvs = [(0.5, 1.0)]
    for iy in range(1, lat_segs):
        v = iy / lat_segs
        lat = math.pi * 0.5 - v * math.pi
        cl, sl = math.cos(lat), math.sin(lat)
        for ix in range(lon_segs + 1):
            u = ix / lon_segs
            lon = u * TAU
            verts.append((radius * cl * math.cos(lon),
                          radius * cl * math.sin(lon),
                          radius * sl))
            uvs.append((u, 1.0 - v))
    bottom = len(verts)
    verts.append((0.0, 0.0, -radius))
    uvs.append((0.5, 0.0))

    faces = []
    ring0 = 1
    for ix in range(lon_segs):
        faces.append((0, ring0 + ix, ring0 + ix + 1))

    stride = lon_segs + 1
    for iy in range(lat_segs - 2):
        a0 = 1 + iy * stride
        b0 = a0 + stride
        for ix in range(lon_segs):
            faces.append((a0 + ix, a0 + ix + 1, b0 + ix + 1, b0 + ix))

    last = 1 + (lat_segs - 2) * stride
    for ix in range(lon_segs):
        faces.append((bottom, last + ix + 1, last + ix))
    return verts, faces, uvs


def build_environment(mats):
    util.reset_collection(config.C_PROPS)
    verts, faces, uvs = _uv_sphere(92.0, 128, 64)
    sky = util.mesh_object("SKY_Starfield", verts, faces, config.C_PROPS,
                           mats["starfield"], smooth=True)

    mesh = sky.data
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            uv.data[li].uv = uvs[vi]
    sky.visible_shadow = False
    util.link_object(sky, config.C_EXPORT)
    print("[environment] star dome r=92 m with baked galaxies")
    return {"sky": sky}
