"""Monumental gate, glowing portal, crown spires and the overhead halo."""
from __future__ import annotations

import math

from arena_kit import config, util

from . import geometry as geo

TAU = math.pi * 2.0
HALF_W = 5.68
FRONT_Y = 17.15
BACK_Y = 19.55
OPEN_HALF = 2.60
SPRING = 8.40
APEX = SPRING + OPEN_HALF
BASE_Z = 0.30
ENT_Z0 = 11.05
ENT_Z1 = 12.00
ATTIC_Z1 = 14.00
HALO_Y = 18.65
HALO_Z = 21.20
HALO_R = 6.10


def _bar_xz(cx, cy, cz, angle, r0, r1, width, depth):
    ca, sa = math.cos(angle), math.sin(angle)
    verts = []
    for yy in (-depth * 0.5, depth * 0.5):
        for rr, zz in ((r0, -width * 0.5), (r1, -width * 0.5),
                       (r1, width * 0.5), (r0, width * 0.5)):
            verts.append((cx + rr * ca - zz * sa, cy + yy,
                          cz + rr * sa + zz * ca))
    faces = [(0, 1, 2, 3), (7, 6, 5, 4),
             (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return verts, faces


def _arch_plate(width, z_base, z_spring, y, segs=32):
    half = width * 0.5
    verts = [(-half, y, z_base), (half, y, z_base), (half, y, z_spring)]
    for i in range(segs + 1):
        a = math.pi * i / segs
        verts.append((half * math.cos(a), y, z_spring + half * math.sin(a)))
    verts.append((-half, y, z_spring))
    return verts, [tuple(range(len(verts)))]


def _column(marble, gold, cx, cy, z0, z1, r):
    marble.append(geo.box(cx, cy, z0, z0 + 0.22, r * 2.4, r * 2.4))
    gold.append(geo.box(cx, cy, z0 + 0.18, z0 + 0.25,
                        r * 2.5, r * 2.5))
    gold.append(geo.prism(cx, cy, z0 + 0.25, z0 + 0.36,
                          r * 1.25, r * 1.05, 20))
    marble.append(geo.prism(cx, cy, z0 + 0.36, z1 - 0.62,
                            r, r * 0.86, 20))
    gold.append(geo.prism(cx, cy, z1 - 0.62, z1 - 0.55, r * 0.9, r * 0.92, 20))
    gold.append(geo.prism(cx, cy, z1 - 0.55, z1 - 0.30, r * 0.92, r * 1.28, 20))
    gold.append(geo.box(cx, cy, z1 - 0.30, z1 - 0.22,
                        r * 2.8, r * 2.8))
    marble.append(geo.box(cx, cy, z1 - 0.22, z1, r * 2.9, r * 2.9))


def _stairs(marble, gold):
    for k, (yc, z1) in enumerate(((15.55, 0.10), (16.15, 0.20),
                                  (16.75, 0.30))):
        marble.append(geo.box(0.0, yc, 0.0, z1, 10.80, 0.62))
        gold.append(geo.box(0.0, yc - 0.32, z1 - 0.035, z1 - 0.010,
                            10.64, 0.06))


def _gate_shell(marble, gold):
    marble.append(geo.box(0.0, (FRONT_Y - 0.30 + BACK_Y + 0.15) * 0.5,
                          BASE_Z, 0.68, HALF_W * 2.0 + 0.18, 3.05))
    gold.append(geo.box(0.0, (FRONT_Y - 0.36 + BACK_Y + 0.21) * 0.5,
                        0.66, 0.74, HALF_W * 2.0 + 0.32, 3.17))

    for sx in (-1.0, 1.0):
        x0 = sx * OPEN_HALF
        x1 = sx * HALF_W
        cx = (x0 + x1) * 0.5
        marble.append(geo.box(cx, (FRONT_Y + BACK_Y) * 0.5, 0.74, ENT_Z0,
                              abs(x1 - x0), BACK_Y - FRONT_Y))

    # Spandrels: fill the rectangular corners outside the round portal.
    steps = 18
    for k in range(steps):
        z0 = SPRING + OPEN_HALF * k / steps
        z1 = SPRING + OPEN_HALF * (k + 1) / steps
        zm = (z0 + z1) * 0.5
        inner = math.sqrt(max(0.0, OPEN_HALF ** 2 - (zm - SPRING) ** 2))
        fill = OPEN_HALF - inner
        if fill < 0.02:
            continue
        for sx in (-1.0, 1.0):
            cx = sx * (inner + fill * 0.5)
            marble.append(geo.box(cx, (FRONT_Y + BACK_Y) * 0.5, z0, z1,
                                  fill, BACK_Y - FRONT_Y))
    marble.append(geo.box(0.0, (FRONT_Y + BACK_Y) * 0.5, APEX, ENT_Z0,
                          OPEN_HALF * 2.0, BACK_Y - FRONT_Y))

    # Entablature and attic.
    marble.append(geo.box(0.0, (FRONT_Y - 0.30 + BACK_Y + 0.10) * 0.5,
                          ENT_Z0, ENT_Z1, HALF_W * 2.0 + 0.36, 3.10))
    gold.append(geo.box(0.0, (FRONT_Y - 0.36 + BACK_Y + 0.16) * 0.5,
                        ENT_Z0 - 0.06, ENT_Z0 + 0.02,
                        HALF_W * 2.0 + 0.50, 3.22))
    gold.append(geo.box(0.0, (FRONT_Y - 0.36 + BACK_Y + 0.16) * 0.5,
                        ENT_Z1 - 0.02, ENT_Z1 + 0.07,
                        HALF_W * 2.0 + 0.50, 3.22))

    marble.append(geo.box(0.0, 18.30, ENT_Z1, ATTIC_Z1, 9.40, 2.20))
    gold.append(geo.box(0.0, 18.30, ATTIC_Z1 - 0.02, ATTIC_Z1 + 0.08,
                        9.62, 2.30))
    marble.append(geo.box(0.0, 18.20, ATTIC_Z1, ATTIC_Z1 + 0.85, 7.20, 1.80))
    gold.append(geo.box(0.0, 18.20, ATTIC_Z1 + 0.85, ATTIC_Z1 + 0.92,
                        7.34, 1.90))

    # Paired columns on the facade.
    for sx in (-1.0, 1.0):
        for x in (3.02, 4.55):
            _column(marble, gold, sx * x, 17.00, 0.74, ENT_Z0, 0.31)


def _ornament(gold):
    for i in range(20):
        x = -5.30 + 10.60 * i / 19.0
        gold.append(geo.box(x, 16.62, 11.86, 11.96, 0.16, 0.09))
    for i in range(16):
        x = -4.55 + 9.10 * i / 15.0
        gold.append(geo.box(x, 17.21, 13.90, 14.00, 0.14, 0.08))
    for sx in (-1.0, 1.0):
        for x in (3.02, 4.55):
            for z in (3.35, 6.35, 9.35):
                r = 0.32 - 0.00465 * (z - 1.10)
                gold.append(geo.cylinder(sx * x, 17.00, z, z + 0.07, r, 20))


def _portal(gold, glow, portal, dark):
    y = FRONT_Y + 0.07
    glow.append(_arch_plate(OPEN_HALF * 2.0 - 0.06, 0.80, SPRING, y + 0.04))
    portal.append(_arch_plate(OPEN_HALF * 2.0 - 0.30, 0.88, SPRING, y))
    dark.append(_arch_plate(OPEN_HALF * 2.0 + 0.14, 0.76, SPRING, y + 0.08))

    gold.append(geo.arch_tube(FRONT_Y - 0.20, SPRING, OPEN_HALF + 0.22,
                              0.15, 36, 8))
    gold.append(geo.arch_tube(FRONT_Y - 0.16, SPRING, OPEN_HALF + 0.50,
                              0.06, 36, 6))
    for sx in (-1.0, 1.0):
        gold.append(geo.box(sx * (OPEN_HALF + 0.22), FRONT_Y - 0.20,
                            0.80, SPRING, 0.24, 0.18))
        gold.append(geo.box(sx * (OPEN_HALF + 0.50), FRONT_Y - 0.16,
                            0.80, SPRING, 0.12, 0.10))
    gold.append(geo.diamond(0.0, FRONT_Y - 0.18, APEX + 0.16, 0.22, 0.50, 4))

    # Glowing rosette on the attic.
    cy, cz = FRONT_Y - 0.07, 13.00
    gold.append(geo.torus_xz(cy, cz, 1.34, 0.07, 96, 6))
    gold.append(geo.torus_xz(cy, cz, 1.02, 0.10, 72, 6))
    gold.append(geo.torus_xz(cy, cz, 0.50, 0.045, 48, 6))
    for i in range(16):
        a = TAU * i / 16.0
        glow.append(geo.diamond(math.cos(a) * 1.02, cy,
                                cz + math.sin(a) * 1.02, 0.075, 0.22, 4))
        gold.append(_bar_xz(0.0, cy + 0.01, cz, a, 0.58, 1.28, 0.05, 0.07))
        gold.append(_bar_xz(0.0, cy + 0.01, cz, a + TAU / 32.0,
                            1.02, 1.30, 0.022, 0.05))
    glow.append(geo.diamond(0.0, cy, cz, 0.26, 0.66, 8))


def _crown(marble, gold, glow):
    for sx in (-1.0, 1.0):
        x = sx * 5.28
        marble.append(geo.box(x, 18.05, ENT_Z1, 12.55, 0.68, 0.68))
        marble.append(geo.spire(x, 18.05, 12.55, 15.55, 0.27, 0.10, 4))
        gold.append(geo.box(x, 18.05, 12.55, 12.64, 0.75, 0.75))
        gold.append(geo.box(x, 18.05, 14.10, 14.18, 0.38, 0.38))
        gold.append(geo.spire(x, 18.05, 15.55, 16.20, 0.12, 0.02, 4))
        glow.append(geo.diamond(x, 18.05, 16.38, 0.10, 0.30, 6))

    marble.append(geo.box(0.0, 18.10, ATTIC_Z1 + 0.85, 15.00, 3.10, 1.30))
    gold.append(geo.box(0.0, 18.10, 15.00, 15.08, 3.26, 1.40))
    gold.append(geo.spire(0.0, 18.10, 15.08, 16.55, 0.22, 0.03, 4))
    glow.append(geo.diamond(0.0, 18.10, 16.72, 0.13, 0.38, 6))


def _halo(gold, glow, halo_gold):
    halo_gold.append(geo.torus_xz(HALO_Y, HALO_Z, HALO_R, 0.19, 192, 8))
    halo_gold.append(geo.torus_xz(HALO_Y, HALO_Z, HALO_R - 0.38, 0.05, 160, 6))
    glow.append(geo.torus_xz(HALO_Y, HALO_Z, HALO_R - 0.60, 0.07, 160, 6))
    glow.append(geo.torus_xz(HALO_Y, HALO_Z, HALO_R + 0.09, 0.045, 192, 6))
    for i in range(24):
        a = TAU * i / 24.0
        gold.append(_bar_xz(0.0, HALO_Y, HALO_Z, a,
                            HALO_R - 0.10, HALO_R + 0.10, 0.34, 0.24))
        if i % 2 == 0:
            glow.append(geo.diamond(math.cos(a) * (HALO_R + 0.26), HALO_Y,
                                    HALO_Z + math.sin(a) * (HALO_R + 0.26),
                                    0.05, 0.14, 4))
    for i in range(12):
        a = TAU * i / 12.0
        glow.append(geo.diamond(math.cos(a) * (HALO_R - 0.72), HALO_Y,
                                HALO_Z + math.sin(a) * (HALO_R - 0.72),
                                0.09, 0.24, 4))

    # Floating crystal and inner orbit at the heart of the halo.
    halo_gold.append(geo.torus_xz(HALO_Y, HALO_Z, 2.10, 0.055, 96, 6))
    halo_gold.append(geo.torus_xz(HALO_Y, HALO_Z, 3.72, 0.030, 96, 5))
    for i in range(8):
        a = TAU * i / 8.0 + TAU / 16.0
        gold.append(_bar_xz(0.0, HALO_Y, HALO_Z, a, 2.18, 3.72, 0.05, 0.10))
        glow.append(geo.diamond(math.cos(a) * 3.72, HALO_Y,
                                HALO_Z + math.sin(a) * 3.72, 0.06, 0.18, 4))
    glow.append(geo.diamond(0.0, HALO_Y, HALO_Z, 1.05, 3.05, 10))


def build_gate(mats):
    marble, gold, glow, portal, dark, halo_gold = [], [], [], [], [], []
    _stairs(marble, gold)
    _gate_shell(marble, gold)
    _ornament(gold)
    _portal(gold, glow, portal, dark)
    _crown(marble, gold, glow)
    _halo(gold, glow, halo_gold)

    gate = geo.merged_mesh("GATE_Marble", marble, mats["marble"], config.C_ARCH)
    util.cube_uv(gate, 2.0)
    util.shade_smooth_by_angle(gate, 30.0)

    gold_obj = geo.merged_mesh("GATE_Gold", gold, mats["gold"], config.C_ARCH)
    util.shade_smooth_by_angle(gold_obj, 35.0)

    halo_obj = geo.merged_mesh("GATE_HaloGold", halo_gold, mats["gold_glow"],
                               config.C_ARCH)
    util.shade_smooth_by_angle(halo_obj, 35.0)

    geo.merged_mesh("GATE_Dark", dark, mats["stone_dark"], config.C_ARCH)
    portal_obj = geo.merged_mesh("GATE_Portal", portal, mats["portal"],
                                 config.C_ARCH)
    if portal_obj is not None:
        mesh = portal_obj.data
        uv = mesh.uv_layers.new(name="UVMap")
        z0 = 0.88
        z1 = APEX
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                co = mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv = ((co.x + OPEN_HALF) / (OPEN_HALF * 2.0),
                                  (co.z - z0) / (z1 - z0))
    geo.merged_mesh("GATE_PortalGlow", glow, mats["glow"], config.C_ARCH)

    print("[gate] portal, eaves, crown spires and overhead halo")
    return {"portal_z": APEX, "halo_z": HALO_Z}
