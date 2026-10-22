"""Small mesh primitives and a multi-material mesh accumulator."""
from __future__ import annotations

import math

import bpy

from arena_kit import config, util

TAU = math.pi * 2.0


class MeshBuilder:
    def __init__(self):
        self.verts = []
        self.faces = []
        self.mats = []
        self.mat_index = []
        self.smooth = []

    def add(self, verts, faces, mat, smooth=False):
        if mat is not None and mat not in self.mats:
            self.mats.append(mat)
        mi = self.mats.index(mat) if mat is not None else 0
        off = len(self.verts)
        self.verts.extend(tuple(v) for v in verts)
        for f in faces:
            self.faces.append(tuple(i + off for i in f))
            self.mat_index.append(mi)
            self.smooth.append(smooth)

    def build(self, name, collection, uv="planar", uv_scale=6.5,
              shade_angle=None):
        obj = util.mesh_object(name, self.verts, self.faces, collection,
                               self.mats[0] if self.mats else None)
        obj.data.materials.clear()
        for mat in self.mats:
            obj.data.materials.append(mat)
        for poly, mi, sm in zip(obj.data.polygons, self.mat_index, self.smooth):
            poly.material_index = mi
            poly.use_smooth = sm
        if uv == "planar":
            uvl = obj.data.uv_layers.new(name="UVMap")
            for loop in obj.data.loops:
                co = obj.data.vertices[loop.vertex_index].co
                uvl.data[loop.index].uv = (co.x / uv_scale, co.y / uv_scale)
        elif uv == "smart":
            util.smart_uv(obj, 60.0, 0.003)
        elif uv == "cube":
            util.cube_uv(obj, uv_scale)
        if shade_angle is not None:
            util.shade_smooth_by_angle(obj, shade_angle)
        util.link_object(obj, config.C_EXPORT)
        return obj


def box(cx, cy, z0, z1, sx, sy, angle=0.0):
    hx, hy = sx * 0.5, sy * 0.5
    ca, sa = math.cos(angle), math.sin(angle)
    pts = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    verts = []
    for x, y in pts:
        verts.append((cx + x * ca - y * sa, cy + x * sa + y * ca, z0))
    for x, y in pts:
        verts.append((cx + x * ca - y * sa, cy + x * sa + y * ca, z1))
    faces = [
        (0, 1, 2, 3), (7, 6, 5, 4),
        (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0),
    ]
    return verts, faces


def cylinder(radius, z0, z1, sides=32, radius_top=None):
    rt = radius if radius_top is None else radius_top
    verts = []
    for z, r in ((z0, radius), (z1, rt)):
        for s in range(sides):
            a = TAU * s / sides
            verts.append((r * math.cos(a), r * math.sin(a), z))
    faces = []
    for s in range(sides):
        n = (s + 1) % sides
        faces.append((s, n, sides + n, sides + s))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(range(sides, 2 * sides)))
    return verts, faces


def cylinder_at(cx, cy, z0, z1, r0, r1, sides=24):
    verts = []
    for z, r in ((z0, r0), (z1, r1)):
        for s in range(sides):
            a = TAU * s / sides
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    faces = []
    for s in range(sides):
        n = (s + 1) % sides
        faces.append((s, n, sides + n, sides + s))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(range(sides, 2 * sides)))
    return verts, faces


def disc(cx, cy, z, radius, sides=48):
    verts = [(cx, cy, z)]
    for s in range(sides):
        a = TAU * s / sides
        verts.append((cx + radius * math.cos(a), cy + radius * math.sin(a), z))
    faces = []
    for s in range(sides):
        faces.append((0, 1 + s, 1 + (s + 1) % sides))
    return verts, faces


def annular_sector(r_in, r_out, z0, z1, a0, a1, segs=12, cx=0.0, cy=0.0):
    verts = []
    faces = []
    rings = [(r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)]
    for r, z in rings:
        for s in range(segs + 1):
            a = a0 + (a1 - a0) * s / segs
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    n = segs + 1
    for s in range(segs):
        faces.append((s, s + 1, n + s + 1, n + s))
        faces.append((n + s, n + s + 1, 2 * n + s + 1, 2 * n + s))
        faces.append((2 * n + s, 2 * n + s + 1, 3 * n + s + 1, 3 * n + s))
        faces.append((3 * n + s, 3 * n + s + 1, s + 1, s))
    faces.append((1, 2, 3, 0))
    faces.append((3 * n + segs, 2 * n + segs, n + segs, segs))
    return verts, faces


def cone(cx, cy, z0, z1, radius, sides=24):
    verts = []
    for s in range(sides):
        a = TAU * s / sides
        verts.append((cx + radius * math.cos(a), cy + radius * math.sin(a), z0))
    verts.append((cx, cy, z1))
    faces = []
    for s in range(sides):
        faces.append((s, (s + 1) % sides, sides))
    faces.append(tuple(reversed(range(sides))))
    return verts, faces


def tapered_ring(cx, cy, z0, z1, r0, r1, sides=16, thickness=0.06):
    verts = []
    faces = []
    for r, z in ((r0, z0), (r1, z1)):
        for s in range(sides):
            a = TAU * s / sides
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    for s in range(sides):
        n = (s + 1) % sides
        faces.append((s, n, sides + n, sides + s))
    return verts, faces


def uv_sphere(cx, cy, cz, radius, sides=10, rings=6, scale=(1.0, 1.0, 1.0)):
    verts = []
    faces = []
    for j in range(1, rings):
        v = j / rings
        phi = math.pi * v
        for s in range(sides):
            a = TAU * s / sides
            verts.append((
                cx + radius * math.sin(phi) * math.cos(a) * scale[0],
                cy + radius * math.sin(phi) * math.sin(a) * scale[1],
                cz + radius * math.cos(phi) * scale[2],
            ))
    top = len(verts)
    verts.append((cx, cy, cz + radius * scale[2]))
    bot = len(verts)
    verts.append((cx, cy, cz - radius * scale[2]))
    for j in range(rings - 2):
        for s in range(sides):
            a = j * sides + s
            b = j * sides + (s + 1) % sides
            c = (j + 1) * sides + (s + 1) % sides
            d = (j + 1) * sides + s
            faces.append((a, b, c, d))
    for s in range(sides):
        faces.append((top, (s + 1) % sides, s))
        base = (rings - 2) * sides
        faces.append((bot, base + s, base + (s + 1) % sides))
    return verts, faces


def catenary(p0, p1, sag, segments=16):
    verts = []
    for i in range(segments + 1):
        t = i / segments
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        z = p0[2] + (p1[2] - p0[2]) * t - sag * math.sin(math.pi * t)
        verts.append((x, y, z))
    return verts


def create_mesh_object(name, verts, faces, collection, mat, smooth=True,
                       uv="planar", uv_scale=6.5):
    b = MeshBuilder()
    b.add(verts, faces, mat, smooth=smooth)
    return b.build(name, collection, uv=uv, uv_scale=uv_scale)


def apply_bevel(obj, width=0.02, segments=2, angle=35.0):
    util.bevel(obj, width, segments=segments, angle_deg=angle)
    util.apply_modifiers(obj)
