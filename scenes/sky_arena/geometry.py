"""Procedural mesh helpers for the floating sky ruins."""
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


# ---------------------------------------------------------------------------
# Blocks and rings
# ---------------------------------------------------------------------------

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


def ring_slab(r_in, r_out, z0, z1, segs=96, cx=0.0, cy=0.0, phase=0.0):
    verts, faces = [], []
    for r, z in ((r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)):
        for s in range(segs):
            a = TAU * s / segs + phase
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    for i in range(4):
        j = (i + 1) % 4
        for s in range(segs):
            t = (s + 1) % segs
            faces.append((i * segs + s, i * segs + t,
                          j * segs + t, j * segs + s))
    return verts, faces


def deck_ring(r_in, radius_fn, z_top, z_bottom, segs=192, phase=0.0):
    """Ring whose outer edge follows ``radius_fn(angle)`` (jagged rim)."""
    verts, faces = [], []
    for s in range(segs):
        a = TAU * s / segs + phase
        r_out = radius_fn(a)
        ca, sa = math.cos(a), math.sin(a)
        verts.extend([
            (r_out * ca, r_out * sa, z_top),
            (r_out * ca, r_out * sa, z_bottom),
            (r_in * ca, r_in * sa, z_bottom),
            (r_in * ca, r_in * sa, z_top),
        ])
    for s in range(segs):
        t = (s + 1) % segs
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((s * 4 + k, s * 4 + k2, t * 4 + k2, t * 4 + k))
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


# ---------------------------------------------------------------------------
# Round ornaments
# ---------------------------------------------------------------------------

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
    pts = [(R * math.cos(math.pi * i / segs), cy,
            cz + R * math.sin(math.pi * i / segs))
           for i in range(segs + 1)]
    return util.make_tube(pts, [tube] * len(pts), sides=sides, caps=True)


def arch_band(cx, cy, a_mid, radius, spring, band_w, depth, segs=32):
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
            (px - n[0] * depth * 0.5, py - n[1] * depth * 0.5,
             z - band_w * 0.5),
            (px + n[0] * depth * 0.5, py + n[1] * depth * 0.5,
             z - band_w * 0.5),
            (px + n[0] * depth * 0.5, py + n[1] * depth * 0.5,
             z + band_w * 0.5),
            (px - n[0] * depth * 0.5, py - n[1] * depth * 0.5,
             z + band_w * 0.5),
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


def spire(cx, cy, z0, z1, base_r, tip_r, sides=4, phase=math.pi * 0.25):
    return prism(cx, cy, z0, z1, base_r, tip_r, sides, phase)


# ---------------------------------------------------------------------------
# Ruins
# ---------------------------------------------------------------------------

def broken_column(cx, cy, z0, z1, r0, r1, segs, rng, jag=0.75,
                  phase=0.0):
    """Tapered shaft with a chipped, uneven break at the top."""
    verts, faces = [], []
    for s in range(segs):
        a = TAU * s / segs + phase
        verts.append((cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0))
    top_z = []
    for s in range(segs):
        a = TAU * s / segs + phase
        z = z1 - rng.uniform(0.0, jag) - 0.18 * (0.5 + 0.5 * math.sin(3 * a))
        top_z.append(z)
        verts.append((cx + r1 * math.cos(a), cy + r1 * math.sin(a), z))
    for s in range(segs):
        t = (s + 1) % segs
        faces.append((s, t, segs + t, segs + s))
    faces.append(tuple(reversed(range(segs))))
    center = (cx, cy, sum(top_z) / segs - 0.10)
    ci = len(verts)
    verts.append(center)
    for s in range(segs):
        t = (s + 1) % segs
        faces.append((ci, segs + s, segs + t))
    return verts, faces


def lying_drum(cx, cy, cz, radius, length, angle, sides=18):
    """Column drum lying on its side, axis in the XY plane."""
    ax, ay = math.cos(angle), math.sin(angle)
    sx, sy = -ay, ax
    verts, faces = [], []
    for end in (-length * 0.5, length * 0.5):
        bx, by = cx + ax * end, cy + ay * end
        for s in range(sides):
            a = TAU * s / sides
            verts.append((bx + sx * radius * math.cos(a),
                          by + sy * radius * math.cos(a),
                          cz + radius * math.sin(a)))
    for s in range(sides):
        t = (s + 1) % sides
        faces.append((s, t, sides + t, sides + s))
    faces.append(tuple(reversed(range(sides))))
    faces.append(tuple(range(sides, 2 * sides)))
    return verts, faces


def uv_sphere(radius, lon_segs=128, lat_segs=64):
    """Inward-view sky sphere with equirectangular UVs (row 0 = zenith)."""
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


def rock_shell(radius_fn, z_top, z_tip, rng, rings=9, segs=72):
    """Tapering rock mass under the deck, with strata jitter."""
    verts, faces = [], []
    for k in range(rings):
        t = k / (rings - 1)
        z = z_top + (z_tip - z_top) * (t ** 0.92)
        scale = (1.0 - t) ** 0.62
        for s in range(segs):
            a = TAU * s / segs
            base = radius_fn(a)
            wobble = (1.0 + 0.055 * math.sin(5.0 * a + k * 1.7)
                      + 0.035 * math.sin(11.0 * a - k * 2.3))
            r = base * scale * wobble
            zz = z + (0.30 * math.sin(3.0 * a + k * 0.9)
                      + rng.uniform(-0.18, 0.18)) * (1.0 - t) * 0.55
            verts.append((r * math.cos(a), r * math.sin(a), zz))
    for k in range(rings - 1):
        a0 = k * segs
        b0 = (k + 1) * segs
        for s in range(segs):
            t = (s + 1) % segs
            faces.append((a0 + s, a0 + t, b0 + t, b0 + s))
    tip = len(verts)
    verts.append((0.0, 0.0, z_tip))
    last = (rings - 1) * segs
    for s in range(segs):
        t = (s + 1) % segs
        faces.append((tip, last + t, last + s))
    return verts, faces


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

def card(verts, faces, uvs, cx, cy, z, yaw, width, height, lean=0.0,
         segments=2, tilt=0.0):
    dx, dy = math.cos(yaw), math.sin(yaw)
    sx, sy = -dy, dx
    off = len(verts)
    for i in range(segments + 1):
        t = i / segments
        w = width * 0.5 * (1.0 - 0.22 * t)
        px = cx + dx * lean * t * t
        py = cy + dy * lean * t * t
        pz = z + height * t - tilt * t * t
        verts.append((px - sx * w, py - sy * w, pz))
        verts.append((px + sx * w, py + sy * w, pz))
        uvs.append((0.0, t))
        uvs.append((1.0, t))
    for i in range(segments):
        a = off + i * 2
        faces.append((a, a + 2, a + 3, a + 1))
