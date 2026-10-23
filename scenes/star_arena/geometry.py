"""Procedural mesh helpers shared by the star-arena modules."""
from __future__ import annotations

import math

import bmesh

from arena_kit import config, util

TAU = math.pi * 2.0


def mesh(name, verts, faces, mat, collection, smooth=False):
    bm = bmesh.new()
    bmv = [bm.verts.new(tuple(v)) for v in verts]
    bm.verts.ensure_lookup_table()
    for face in faces:
        try:
            bm.faces.new([bmv[i] for i in face])
        except ValueError:
            pass
    if not bm.faces:
        bm.free()
        return None
    obj = util.bmesh_object(name, bm, collection, mat, smooth=smooth)
    util.link_object(obj, config.C_EXPORT)
    return obj


def merge(parts):
    verts, faces = [], []
    for v, f in parts:
        if not v:
            continue
        off = len(verts)
        verts.extend(v)
        faces.extend(tuple(i + off for i in face) for face in f)
    return verts, faces


def merged_mesh(name, parts, mat, collection, smooth=False):
    v, f = merge(parts)
    return mesh(name, v, f, mat, collection, smooth)


def box(cx, cy, z0, z1, sx, sy, angle=0.0):
    hx, hy = sx * 0.5, sy * 0.5
    ca, sa = math.cos(angle), math.sin(angle)
    verts = []
    for z in (z0, z1):
        for x, y in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
            verts.append((cx + x * ca - y * sa, cy + x * sa + y * ca, z))
    faces = [(0, 1, 2, 3), (7, 6, 5, 4),
             (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return verts, faces


def box_bounds(x0, x1, y0, y1, z0, z1):
    return box((x0 + x1) * 0.5, (y0 + y1) * 0.5, z0, z1,
               abs(x1 - x0), abs(y1 - y0))


def prism(cx, cy, z0, z1, r0, r1, sides=8, phase=0.0):
    verts, faces = [], []
    for z, r in ((z0, r0), (z1, r1)):
        for s in range(sides):
            a = TAU * s / sides + phase
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    for s in range(sides):
        t = (s + 1) % sides
        faces.append((s, t, sides + t, sides + s))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(range(sides, 2 * sides)))
    return verts, faces


def cylinder(cx, cy, z0, z1, r, segs=24, r_top=None):
    return prism(cx, cy, z0, z1, r, r if r_top is None else r_top, segs)


def ring_slab(r_in, r_out, z0, z1, segs=96, cx=0.0, cy=0.0):
    verts, faces = [], []
    for r, z in ((r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)):
        for s in range(segs):
            a = TAU * s / segs
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    for i in range(4):
        j = (i + 1) % 4
        for s in range(segs):
            t = (s + 1) % segs
            faces.append((i * segs + s, i * segs + t,
                          j * segs + t, j * segs + s))
    return verts, faces


def arc_slab(r_in, r_out, z0, z1, a0, a1, segs=48, cx=0.0, cy=0.0):
    verts, faces = [], []
    for i in range(segs + 1):
        a = a0 + (a1 - a0) * i / segs
        ca, sa = math.cos(a), math.sin(a)
        verts.extend([
            (cx + r_out * ca, cy + r_out * sa, z0),
            (cx + r_out * ca, cy + r_out * sa, z1),
            (cx + r_in * ca, cy + r_in * sa, z1),
            (cx + r_in * ca, cy + r_in * sa, z0),
        ])
    for i in range(segs):
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((i * 4 + k, i * 4 + k2,
                          (i + 1) * 4 + k2, (i + 1) * 4 + k))
    faces.append((0, 1, 2, 3))
    last = segs * 4
    faces.append((last, last + 3, last + 2, last + 1))
    return verts, faces


def torus_z(R, r, z, maj=96, minr=8, cx=0.0, cy=0.0):
    verts, faces = [], []
    for i in range(maj):
        a = TAU * i / maj
        ca, sa = math.cos(a), math.sin(a)
        for j in range(minr):
            b = TAU * j / minr
            rad = R + r * math.cos(b)
            verts.append((cx + rad * ca, cy + rad * sa, z + r * math.sin(b)))
    for i in range(maj):
        ni = (i + 1) % maj
        for j in range(minr):
            nj = (j + 1) % minr
            faces.append((i * minr + j, ni * minr + j,
                          ni * minr + nj, i * minr + nj))
    return verts, faces


def torus_xz(cy, cz, R, r, maj=128, minr=8):
    """Ring lying in the XZ plane (axis +Y)."""
    verts, faces = [], []
    for i in range(maj):
        a = TAU * i / maj
        ca, sa = math.cos(a), math.sin(a)
        for j in range(minr):
            b = TAU * j / minr
            rad = R + r * math.cos(b)
            verts.append((rad * ca, cy + r * math.sin(b), cz + rad * sa))
    for i in range(maj):
        ni = (i + 1) % maj
        for j in range(minr):
            nj = (j + 1) % minr
            faces.append((i * minr + j, ni * minr + j,
                          ni * minr + nj, i * minr + nj))
    return verts, faces


def torus_facing(cx, cy, cz, facing, R, r, maj=32, minr=6):
    """Ring standing in a vertical plane, axis pointing along ``facing``."""
    n = (math.cos(facing), math.sin(facing))
    t = (-math.sin(facing), math.cos(facing))
    verts, faces = [], []
    for i in range(maj):
        a = TAU * i / maj
        radial = R * math.cos(a)
        vertical = R * math.sin(a)
        for j in range(minr):
            b = TAU * j / minr
            off = r * math.cos(b)
            verts.append((cx + t[0] * radial + n[0] * off,
                          cy + t[1] * radial + n[1] * off,
                          cz + vertical + r * math.sin(b)))
    for i in range(maj):
        ni = (i + 1) % maj
        for j in range(minr):
            nj = (j + 1) % minr
            faces.append((i * minr + j, ni * minr + j,
                          ni * minr + nj, i * minr + nj))
    return verts, faces


def ring_tube(radius, z, tube, sides=6, steps=96, cx=0.0, cy=0.0):
    pts = [(cx + radius * math.cos(TAU * i / steps),
            cy + radius * math.sin(TAU * i / steps), z)
           for i in range(steps)]
    pts.append(pts[0])
    return util.make_tube(pts, [tube] * len(pts), sides=sides, caps=False)


def arch_tube(cy, cz, R, tube, segs=32, sides=6):
    """Round half-arch in the XZ plane, opening downwards."""
    pts = [(R * math.cos(math.pi * i / segs), cy,
            cz + R * math.sin(math.pi * i / segs))
           for i in range(segs + 1)]
    return util.make_tube(pts, [tube] * len(pts), sides=sides, caps=True)


def arch_band(cx, cy, a_mid, radius, spring, band_w, depth, segs=32):
    """Flat arch ring in the plane tangent to the circle at ``a_mid``."""
    n = (math.cos(a_mid), math.sin(a_mid))
    t = (-math.sin(a_mid), math.cos(a_mid))
    rings = []
    for i in range(segs + 1):
        th = math.pi * i / segs
        s = radius * math.cos(th)
        z = spring + radius * math.sin(th)
        px = cx + t[0] * s
        py = cy + t[1] * s
        rings.append([
            (px - n[0] * depth * 0.5, py - n[1] * depth * 0.5, z - band_w * 0.5),
            (px + n[0] * depth * 0.5, py + n[1] * depth * 0.5, z - band_w * 0.5),
            (px + n[0] * depth * 0.5, py + n[1] * depth * 0.5, z + band_w * 0.5),
            (px - n[0] * depth * 0.5, py - n[1] * depth * 0.5, z + band_w * 0.5),
        ])
    return util.loft_rings(rings, caps=True)


def diamond(cx, cy, cz, radius, height, sides=6):
    verts = [(cx, cy, cz + height * 0.5), (cx, cy, cz - height * 0.5)]
    for s in range(sides):
        a = TAU * s / sides
        verts.append((cx + radius * math.cos(a),
                      cy + radius * math.sin(a), cz))
    faces = []
    for s in range(sides):
        t = (s + 1) % sides
        faces.append((0, 2 + s, 2 + t))
        faces.append((1, 2 + t, 2 + s))
    return verts, faces


def cone_shell(cx, cy, z0, z1, r0, r1, segs=40):
    verts = []
    for z, r in ((z0, r0), (z1, r1)):
        for s in range(segs):
            a = TAU * s / segs
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    faces = []
    for s in range(segs):
        t = (s + 1) % segs
        faces.append((s, t, segs + t, segs + s))
    return verts, faces


def spire(cx, cy, z0, z1, base_r, tip_r, sides=4, phase=math.pi * 0.25):
    return prism(cx, cy, z0, z1, base_r, tip_r, sides, phase)


def square_ring_path(radius, z, steps=64):
    return [(radius * math.cos(TAU * i / steps),
             radius * math.sin(TAU * i / steps), z)
            for i in range(steps + 1)]
