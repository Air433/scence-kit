"""Two-storey ivory arcade with gold arches, wall panels and roof spires."""
from __future__ import annotations

import math

from arena_kit import config, util

from . import geometry as geo

TAU = math.pi * 2.0
R_COL = 18.4
BAYS = 20
BAY_ANG = TAU / BAYS
GATE_HALF = math.radians(18.0)       # opening between columns at 72 / 108 deg
GATE_A0 = math.pi * 0.5 - GATE_HALF
GATE_A1 = math.pi * 0.5 + GATE_HALF

LOWER_SPRING = 4.95
LOWER_ARCH_R = 2.72
LOWER_ENT_Z0 = 7.62
LOWER_ENT_Z1 = 8.42
UPPER_SPRING = 10.55
UPPER_ARCH_R = 2.35
UPPER_ENT_Z0 = 12.88
UPPER_ENT_Z1 = 13.66
WALL_IN = 20.0
WALL_OUT = 20.7


def _arc_tube(radius, z, tube, a0, a1, steps=96, sides=6):
    pts = [(radius * math.cos(a0 + (a1 - a0) * i / steps),
            radius * math.sin(a0 + (a1 - a0) * i / steps), z)
           for i in range(steps + 1)]
    return util.make_tube(pts, [tube] * len(pts), sides=sides, caps=True)


def _gate_open(a):
    d = abs(((a - math.pi * 0.5 + math.pi) % TAU) - math.pi)
    return d < GATE_HALF - 1e-5


def _column_angles():
    for i in range(BAYS):
        a = BAY_ANG * i
        if abs(((a - math.pi * 0.5 + math.pi) % TAU) - math.pi) < math.radians(1.0):
            continue
        yield a


def _lower_column(a, marble, gold):
    x, y = R_COL * math.cos(a), R_COL * math.sin(a)
    marble.append(geo.box(x, y, 0.30, 0.60, 0.96, 0.96, a))
    gold.append(geo.box(x, y, 0.56, 0.64, 1.02, 1.02, a))
    gold.append(geo.prism(x, y, 0.64, 0.74, 0.47, 0.40, 20))
    marble.append(geo.prism(x, y, 0.74, 4.48, 0.36, 0.31, 20))
    gold.append(geo.prism(x, y, 4.48, 4.57, 0.33, 0.34, 20))
    gold.append(geo.prism(x, y, 4.57, 4.86, 0.33, 0.47, 20))
    gold.append(geo.box(x, y, 4.86, 4.94, 1.00, 1.00, a))
    marble.append(geo.box(x, y, 4.94, 5.08, 1.04, 1.04, a))
    for s in range(8):
        aa = TAU * s / 8.0 + a
        gold.append(geo.diamond(x + 0.40 * math.cos(aa),
                                y + 0.40 * math.sin(aa),
                                4.72, 0.055, 0.22, 4))


def _upper_column(a, marble, gold):
    x, y = R_COL * math.cos(a), R_COL * math.sin(a)
    marble.append(geo.box(x, y, LOWER_ENT_Z1, LOWER_ENT_Z1 + 0.24,
                          0.60, 0.60, a))
    gold.append(geo.box(x, y, LOWER_ENT_Z1 + 0.24, LOWER_ENT_Z1 + 0.29,
                        0.64, 0.64, a))
    marble.append(geo.prism(x, y, 8.71, 10.20, 0.22, 0.185, 16))
    gold.append(geo.prism(x, y, 10.20, 10.27, 0.20, 0.21, 16))
    gold.append(geo.prism(x, y, 10.27, 10.48, 0.21, 0.29, 16))
    marble.append(geo.box(x, y, 10.48, 10.60, 0.60, 0.60, a))


def _arches(marble, gold, glow):
    for i in range(BAYS):
        a = BAY_ANG * (i + 0.5)
        if _gate_open(a):
            continue
        cx, cy = R_COL * math.cos(a), R_COL * math.sin(a)
        marble.append(geo.arch_band(cx, cy, a, LOWER_ARCH_R, LOWER_SPRING,
                                    0.36, 0.36, 30))
        marble.append(geo.arch_band(cx, cy, a, UPPER_ARCH_R, UPPER_SPRING,
                                    0.27, 0.27, 26))

        n = (math.cos(a), math.sin(a))
        t = (-math.sin(a), math.cos(a))
        pts = []
        for k in range(25):
            th = math.pi * k / 24.0
            s = (LOWER_ARCH_R - 0.17) * math.cos(th)
            z = LOWER_SPRING + (LOWER_ARCH_R - 0.17) * math.sin(th)
            pts.append((cx + t[0] * s + n[0] * 0.03,
                        cy + t[1] * s + n[1] * 0.03, z))
        gold.append(util.make_tube(pts, [0.06] * len(pts), sides=6, caps=True))
        gold.append(geo.diamond(cx + n[0] * 0.05, cy + n[1] * 0.05,
                                LOWER_SPRING + LOWER_ARCH_R + 0.14,
                                0.20, 0.44, 4))

        pts = []
        for k in range(23):
            th = math.pi * k / 22.0
            s = (UPPER_ARCH_R - 0.13) * math.cos(th)
            z = UPPER_SPRING + (UPPER_ARCH_R - 0.13) * math.sin(th)
            pts.append((cx + t[0] * s + n[0] * 0.02,
                        cy + t[1] * s + n[1] * 0.02, z))
        gold.append(util.make_tube(pts, [0.032] * len(pts), sides=6, caps=True))


def _entablature(marble, gold):
    a0, a1 = GATE_A1, GATE_A0 + TAU
    marble.append(geo.arc_slab(17.95, 19.15, LOWER_ENT_Z0, LOWER_ENT_Z1,
                               a0, a1, 120))
    gold.append(geo.arc_slab(17.90, 19.20, LOWER_ENT_Z0 - 0.05,
                             LOWER_ENT_Z0 + 0.02, a0, a1, 120))
    gold.append(geo.arc_slab(17.90, 19.20, LOWER_ENT_Z1 - 0.02,
                             LOWER_ENT_Z1 + 0.05, a0, a1, 120))

    marble.append(geo.arc_slab(18.0, 19.25, UPPER_ENT_Z0, UPPER_ENT_Z1,
                               a0, a1, 120))
    gold.append(geo.arc_slab(17.95, 19.30, UPPER_ENT_Z0 - 0.04,
                             UPPER_ENT_Z0 + 0.02, a0, a1, 120))
    gold.append(geo.arc_slab(17.95, 19.30, UPPER_ENT_Z1 - 0.02,
                             UPPER_ENT_Z1 + 0.06, a0, a1, 120))


def _balustrade(marble, gold):
    a0, a1 = GATE_A1, GATE_A0 + TAU
    posts = 40
    for i in range(posts):
        a = TAU * i / posts
        if _gate_open(a):
            continue
        x, y = 18.68 * math.cos(a), 18.68 * math.sin(a)
        marble.append(geo.box(x, y, UPPER_ENT_Z1, UPPER_ENT_Z1 + 0.62,
                              0.16, 0.16, a))
        gold.append(geo.box(x, y, UPPER_ENT_Z1 + 0.62, UPPER_ENT_Z1 + 0.69,
                            0.20, 0.20, a))
    for i in range(posts):
        a = TAU * (i + 0.5) / posts
        if _gate_open(a):
            continue
        for k in range(3):
            aa = a + TAU / posts * (k - 1) / 4.0
            x, y = 18.68 * math.cos(aa), 18.68 * math.sin(aa)
            gold.append(geo.cylinder(x, y, UPPER_ENT_Z1 + 0.06,
                                     UPPER_ENT_Z1 + 0.60, 0.022, 6))
    gold.append(_arc_tube(18.68, UPPER_ENT_Z1 + 0.72, 0.05, a0, a1, 120))
    gold.append(_arc_tube(18.68, UPPER_ENT_Z1 + 0.04, 0.03, a0, a1, 120))


def _wall(mats, gold, glow):
    wall = geo.mesh("ARCADE_Wall", *geo.ring_slab(WALL_IN, WALL_OUT, 0.30,
                                                 UPPER_ENT_Z1, 180),
                    mats["marble_warm"], config.C_ARCH)
    util.cube_uv(wall, 3.0)

    panels = []
    frames = []
    for i in range(BAYS):
        a = BAY_ANG * (i + 0.5)
        ca, sa = math.cos(a), math.sin(a)
        tx, ty = -sa, ca
        for z0, z1, half in ((1.55, 4.65, 1.12), (9.15, 10.55, 0.86)):
            px, py = (WALL_IN - 0.035) * ca, (WALL_IN - 0.035) * sa
            panels.append(geo.box(px, py, z0, z1, half * 2.0, 0.07,
                                  a + math.pi * 0.5))
            fx = (WALL_IN - 0.065) * ca
            fy = (WALL_IN - 0.065) * sa
            for dz, h in ((z0 - 0.04, 0.08), (z1 + 0.04, 0.08)):
                frames.append(geo.box(fx, fy, dz - h * 0.5, dz + h * 0.5,
                                      half * 2.0 + 0.18, 0.06,
                                      a + math.pi * 0.5))
            for s in (-1.0, 1.0):
                bx = fx + tx * s * (half + 0.05)
                by = fy + ty * s * (half + 0.05)
                frames.append(geo.box(bx, by, z0 - 0.06, z1 + 0.06,
                                      0.08, 0.06, a + math.pi * 0.5))

        # Rosettes set into the wall panels.
        rp = WALL_IN - 0.075
        for zc, rr, studs in ((3.10, 0.36, 8), (9.85, 0.27, 6)):
            gold.append(geo.torus_facing(rp * ca, rp * sa, zc, a, rr, 0.05,
                                         30, 6))
            gold.append(geo.torus_facing(rp * ca, rp * sa, zc, a, rr * 0.55,
                                         0.028, 20, 5))
            glow.append(geo.diamond(rp * ca, rp * sa, zc, 0.080, 0.24, 4))
            for k in range(studs):
                ang = TAU * k / studs
                off = rr + 0.07
                gold.append(geo.diamond(
                    rp * ca - sa * math.cos(ang) * off,
                    rp * sa + ca * math.cos(ang) * off,
                    zc + math.sin(ang) * off, 0.045, 0.12, 4))

        sx, sy = (WALL_IN - 0.50) * ca, (WALL_IN - 0.50) * sa
        gold.append(geo.torus_facing((WALL_IN - 0.10) * ca,
                                     (WALL_IN - 0.10) * sa, 4.82, a,
                                     0.24, 0.045, 24, 5))
        gold.append(geo.box(sx, sy, 4.28, 4.38, 0.46, 0.10, a + math.pi * 0.5))
        gold.append(geo.box(sx, sy, 4.38, 4.54, 0.12, 0.12, a))
        gold.append(geo.prism(sx, sy, 4.54, 4.64, 0.16, 0.10, 8))
        glow.append(geo.diamond(sx, sy, 4.82, 0.20, 0.52, 6))
        gold.append(geo.diamond(sx, sy, 5.16, 0.055, 0.16, 4))

    geo.merged_mesh("ARCADE_WallPanels", panels, mats["stone_dark"],
                    config.C_ARCH)
    geo.merged_mesh("ARCADE_PanelFrames", frames, mats["gold"], config.C_ARCH)
    geo.merged_mesh("ARCADE_Sconces", glow, mats["sconce"], config.C_ARCH)


def _dentils(gold, glow):
    step = math.radians(1.8)
    count = int(TAU / step)
    for i in range(count):
        a = step * (i + 0.5)
        if _gate_open(a):
            continue
        ca, sa = math.cos(a), math.sin(a)
        for radius, z0, z1 in ((17.92, 7.50, 7.62), (17.97, 12.76, 12.88)):
            gold.append(geo.box(radius * ca, radius * sa, z0, z1,
                                0.18, 0.13, a))

    a0, a1 = GATE_A1, GATE_A0 + TAU
    for radius, z in ((17.91, 7.71), (17.91, 8.33),
                      (17.96, 12.95), (17.96, 13.57)):
        gold.append(_arc_tube(radius, z, 0.028, a0, a1, 110))

    # Frieze medallions on the lower entablature.
    for i in range(BAYS):
        a = BAY_ANG * (i + 0.5)
        if _gate_open(a):
            continue
        px, py = 17.93 * math.cos(a), 17.93 * math.sin(a)
        gold.append(geo.torus_facing(px, py, 8.02, a, 0.30, 0.05, 30, 6))
        gold.append(geo.torus_facing(px, py, 8.02, a, 0.17, 0.028, 20, 5))
        glow.append(geo.diamond(px, py, 8.02, 0.075, 0.20, 4))


def _spires(marble, gold, glow):
    # Small gold finials between the main pinnacles.
    for i in range(10):
        a = TAU * (i + 0.5) / 10.0
        x, y = 19.30 * math.cos(a), 19.30 * math.sin(a)
        gold.append(geo.cylinder(x, y, UPPER_ENT_Z1, UPPER_ENT_Z1 + 0.14,
                                 0.17, 8))
        gold.append(geo.prism(x, y, UPPER_ENT_Z1 + 0.14,
                              UPPER_ENT_Z1 + 0.40, 0.20, 0.055, 8))
        gold.append(geo.diamond(x, y, UPPER_ENT_Z1 + 0.52, 0.07, 0.20, 4))

    for i in range(5):
        a = TAU * i / 5.0
        x, y = 19.45 * math.cos(a), 19.45 * math.sin(a)
        marble.append(geo.box(x, y, UPPER_ENT_Z1, UPPER_ENT_Z1 + 0.52,
                              0.56, 0.56, a))
        marble.append(geo.spire(x, y, UPPER_ENT_Z1 + 0.52, 16.95,
                                0.30, 0.11, 4))
        gold.append(geo.box(x, y, UPPER_ENT_Z1 + 0.52,
                            UPPER_ENT_Z1 + 0.60, 0.62, 0.62, a))
        gold.append(geo.box(x, y, 15.55, 15.64, 0.42, 0.42, a))
        gold.append(geo.spire(x, y, 16.95, 17.60, 0.13, 0.02, 4))
        glow.append(geo.diamond(x, y, 17.78, 0.10, 0.30, 6))


def build_arcade(mats):
    marble, marble_warm, gold, glow = [], [], [], []
    for a in _column_angles():
        _lower_column(a, marble, gold)
        _upper_column(a, marble, gold)
    _arches(marble, gold, glow)
    _entablature(marble_warm, gold)
    _balustrade(marble, gold)
    _wall(mats, gold, glow)
    _dentils(gold, glow)
    _spires(marble, gold, glow)

    arc = geo.merged_mesh("ARCADE_Marble", marble, mats["marble"],
                          config.C_ARCH)
    util.cube_uv(arc, 2.0)
    util.shade_smooth_by_angle(arc, 30.0)

    wall = geo.merged_mesh("ARCADE_Entablature", marble_warm,
                           mats["marble_warm"], config.C_ARCH)
    util.cube_uv(wall, 3.0)

    gold_obj = geo.merged_mesh("ARCADE_Gold", gold, mats["gold"], config.C_ARCH)
    util.shade_smooth_by_angle(gold_obj, 35.0)
    geo.merged_mesh("ARCADE_Glow", glow, mats["sconce"], config.C_ARCH)
    print(f"[arcade] {BAYS}-bay two-storey colonnade, panels and spires")
    return {"bays": BAYS, "radius": R_COL}
