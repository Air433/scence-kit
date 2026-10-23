"""Grass tufts, moss on the stonework and vines spilling off the ruins.

Alpha cards keep their root at UV.y = 0; the island Godot project's wind shader
can bend them by vertex height.  Everything is baked into one mesh per material.
"""
from __future__ import annotations

import math

from arena_kit import config, util

from . import geometry as geo
from . import layout, plaza, ruins

TAU = math.pi * 2.0


class _Batch:
    def __init__(self):
        self.verts = []
        self.faces = []
        self.uvs = []

    def extend(self, verts, faces, uvs):
        off = len(self.verts)
        self.verts.extend(verts)
        self.faces.extend(tuple(i + off for i in f) for f in faces)
        self.uvs.extend(uvs)

    def card(self, x, y, z, yaw, width, height, lean=0.0, segments=2,
             tilt=0.0):
        geo.card(self.verts, self.faces, self.uvs, x, y, z, yaw, width,
                 height, lean=lean, segments=segments, tilt=tilt)

    def patch(self, rng, x, y, z, size, yaw=None, stretch=1.0):
        yaw = rng.uniform(0.0, TAU) if yaw is None else yaw
        dx, dy = math.cos(yaw), math.sin(yaw)
        sx, sy = -dy, dx
        w = size * 0.5
        l = size * 0.5 * stretch
        verts, uvs = [], []
        for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            px = x + sx * u * w + dx * v * l
            py = y + sy * u * w + dy * v * l
            pz = z + rng.uniform(-0.012, 0.012)
            verts.append((px, py, pz))
            uvs.append(((u + 1.0) * 0.5, (v + 1.0) * 0.5))
        self.extend(verts, [(0, 1, 2, 3)], uvs)

    def build(self, name, mat, collection):
        if not self.faces:
            return None
        obj = util.mesh_object(name, self.verts, self.faces, collection, mat)
        uvl = obj.data.uv_layers.new(name="UVMap")
        for loop in obj.data.loops:
            uvl.data[loop.index].uv = self.uvs[loop.vertex_index]
        util.link_object(obj, config.C_EXPORT)
        return obj


def _tuft(batch, rng, x, y, z, scale=1.0, cards=3):
    yaw0 = rng.uniform(0.0, TAU)
    for k in range(cards):
        batch.card(x, y, z,
                   yaw0 + TAU * k / cards + rng.uniform(-0.18, 0.18),
                   rng.uniform(0.36, 0.66) * scale,
                   rng.uniform(0.46, 1.02) * scale,
                   lean=rng.uniform(-0.10, 0.18),
                   segments=2, tilt=rng.uniform(0.0, 0.07))


def _bush(batch, rng, x, y, z, scale=1.0):
    yaw0 = rng.uniform(0.0, TAU)
    for k in range(6):
        batch.card(x, y, z,
                   yaw0 + TAU * k / 6.0 + rng.uniform(-0.25, 0.25),
                   rng.uniform(0.55, 1.0) * scale,
                   rng.uniform(0.65, 1.30) * scale,
                   lean=rng.uniform(0.12, 0.50) * scale,
                   segments=3, tilt=rng.uniform(0.0, 0.16))


def _columns():
    out = []
    for a, kind, height in ruins.column_layout():
        out.append((ruins.R_COL * math.cos(a), ruins.R_COL * math.sin(a),
                    kind, height))
    return out


def _braziers():
    return [(plaza.BRAZIER_R * math.cos(TAU * (i + 0.5) / 4.0),
             plaza.BRAZIER_R * math.sin(TAU * (i + 0.5) / 4.0))
            for i in range(4)]


def _floor_ok(x, y):
    r = math.hypot(x, y)
    if r < 6.25 or r > 12.30:
        return False
    for bx, by in _braziers():
        if (x - bx) ** 2 + (y - by) ** 2 < 1.25 * 1.25:
            return False
    return not layout.in_gate_corridor(x, y)


def _terrace_ok(x, y, r, columns):
    if layout.in_gate_corridor(x, y, 0.2):
        return False
    if r > 19.80:
        return False
    for cx, cy, _kind, _h in columns:
        if (x - cx) ** 2 + (y - cy) ** 2 < 1.15 * 1.15:
            return False
    return True


def _rim_ok(x, y, r):
    a = math.atan2(y, x)
    if r > layout.edge_radius(a) - 0.55:
        return False
    if layout.in_gate_corridor(x, y, 0.2):
        return False
    return True


def _grass_floor(grass, rng, count):
    pts = util.poisson_disc(count, 6.3, 12.28, 0.72, rng,
                            accept=lambda x, y, r: _floor_ok(x, y))
    for x, y in pts:
        _tuft(grass, rng, x, y, 0.004, scale=rng.uniform(0.65, 1.0))
    return len(pts)


def _grass_terrace(grass, rng, count, columns):
    pts = util.poisson_disc(
        count, layout.STEP2_R + 0.15, 19.80, 0.82, rng,
        accept=lambda x, y, r: _terrace_ok(x, y, r, columns))
    for x, y in pts:
        _tuft(grass, rng, x, y, layout.TERRACE_Z + 0.004,
              scale=rng.uniform(0.9, 1.35))
    return len(pts)


def _grass_rim(grass, rng, count):
    pts = util.poisson_disc(count, 20.75, 24.30, 0.64, rng,
                            accept=lambda x, y, r: _rim_ok(x, y, r))
    for x, y in pts:
        _tuft(grass, rng, x, y, layout.LIP_Z + 0.004,
              scale=rng.uniform(1.0, 1.5))
    return len(pts)


def _grass_islets(grass, rng, count_by_islet):
    made = 0
    for islet, want in zip(layout.ISLETS, count_by_islet):
        offsets = layout.islet_ruin_offsets(islet["ruin"])
        pts = []
        tries = 0
        while len(pts) < want and tries < 4000:
            tries += 1
            a = rng.uniform(0.0, TAU)
            rr = islet["r"] * math.sqrt(rng.uniform(0.02, 0.80))
            x = islet["x"] + rr * math.cos(a)
            y = islet["y"] + rr * math.sin(a)
            if any((x - (islet["x"] + ox)) ** 2
                   + (y - (islet["y"] + oy)) ** 2 < 0.85 ** 2
                   for ox, oy in offsets):
                continue
            if all((x - px) ** 2 + (y - py) ** 2 > 0.36 ** 2
                   for px, py in pts):
                pts.append((x, y))
        for x, y in pts:
            _tuft(grass, rng, x, y, layout.islet_cap_z(islet, x, y) + 0.01,
                  scale=rng.uniform(0.75, 1.15))
        made += len(pts)
    return made


def _shrub_landmarks(rng):
    cols = [c for c in _columns() if c[2] == "broken"]
    out = []
    for x, y, _k, _h in cols[:4]:
        a = rng.uniform(0.0, TAU)
        out.append((x + 1.15 * math.cos(a), y + 1.15 * math.sin(a)))
    for sx in (-1.0, 1.0):
        out.append((sx * 5.55, 16.35))
        out.append((sx * 6.15, 18.05))
    for x, y in ((-11.4, 11.6), (13.9, 8.9), (-19.0, -2.4)):
        a = rng.uniform(0.0, TAU)
        out.append((x + 1.45 * math.cos(a), y + 1.45 * math.sin(a)))
    for x, y in ((9.0, 14.6), (-9.4, 15.2)):
        out.append((x, y))

    keep = []
    cols = _columns()
    for x, y in out:
        r = math.hypot(x, y)
        if 13.9 > r or r > 23.0 or 19.9 < r < 20.7:
            continue
        if any((x - cx) ** 2 + (y - cy) ** 2 < 1.2 ** 2
               for cx, cy, _k, _h in cols):
            continue
        keep.append((x, y))
    return keep


def _shrubs(bush, rng):
    columns = _columns()
    made = 0
    pts = util.poisson_disc(
        30, layout.STEP2_R + 0.4, 19.75, 1.9, rng,
        accept=lambda x, y, r: _terrace_ok(x, y, r, columns))
    for x, y in pts:
        _bush(bush, rng, x, y, layout.TERRACE_Z + 0.01,
              scale=rng.uniform(0.95, 1.5))
    made += len(pts)

    rim_pts = util.poisson_disc(8, 20.85, 23.0, 2.3, rng,
                                accept=lambda x, y, r: _rim_ok(x, y, r))
    for x, y in rim_pts:
        _bush(bush, rng, x, y, layout.LIP_Z + 0.01,
              scale=rng.uniform(0.8, 1.25))
    made += len(rim_pts)

    for x, y in _shrub_landmarks(rng):
        _bush(bush, rng, x, y, layout.TERRACE_Z + 0.01,
              scale=rng.uniform(0.9, 1.3))
        made += 1

    for islet in layout.ISLETS:
        if islet["ruin"] is None:
            count = 2
        else:
            count = 5
        placed = 0
        tries = 0
        while placed < count and tries < 1500:
            tries += 1
            a = rng.uniform(0.0, TAU)
            rr = islet["r"] * math.sqrt(rng.uniform(0.25, 0.78))
            x = islet["x"] + rr * math.cos(a)
            y = islet["y"] + rr * math.sin(a)
            _bush(bush, rng, x, y, layout.islet_cap_z(islet, x, y) + 0.01,
                  scale=rng.uniform(0.7, 1.05))
            placed += 1
        made += placed
    print(f"[foliage] {made} shrub clumps")
    return made


def _vines(leaf, rng):
    count = 0
    # Over the broken rim.
    for i in range(22):
        a = TAU * i / 22.0
        d = abs(((a - math.pi * 0.5 + math.pi) % TAU) - math.pi)
        if d < math.radians(26.0):
            continue
        r = layout.edge_radius(a) - 0.14
        x, y = r * math.cos(a), r * math.sin(a)
        leaf.card(x, y, layout.LIP_Z + 0.01, a,
                  rng.uniform(0.40, 0.72), -rng.uniform(1.8, 3.8),
                  lean=rng.uniform(-0.18, 0.18), segments=4)
        count += 1
    for i in range(8):
        a = math.radians(rng.uniform(235.0, 355.0))
        r = layout.edge_radius(a) - 0.14
        leaf.card(r * math.cos(a), r * math.sin(a), layout.LIP_Z + 0.01,
                  a, rng.uniform(0.36, 0.64), -rng.uniform(1.6, 3.4),
                  lean=rng.uniform(-0.2, 0.2), segments=4)
        count += 1

    # Hanging from the architraves, inside the colonnade.
    for a0, a1, frac in ruins.architrave_spans():
        span = (a1 - a0) * frac
        for k in range(6):
            a = a0 + span * (0.16 + 0.14 * k) + rng.uniform(-0.02, 0.02)
            r = ruins.R_COL - 0.58
            leaf.card(r * math.cos(a), r * math.sin(a), 7.78, a,
                      rng.uniform(0.28, 0.50), -rng.uniform(1.4, 2.8),
                      lean=rng.uniform(-0.1, 0.1), segments=3)
            count += 1

    # Gate face, lintel and the snapped east section.
    for x, z in ((-4.15, 11.20), (-3.55, 11.22), (-2.95, 11.18),
                 (-0.95, 11.20), (0.15, 11.24), (2.35, 8.66),
                 (3.05, 8.70), (3.75, 8.62), (2.10, 9.70), (4.25, 9.72)):
        leaf.card(x, ruins.GATE_FRONT - 0.06, z, math.pi * 0.5,
                  rng.uniform(0.28, 0.52), -rng.uniform(1.2, 2.8),
                  lean=rng.uniform(-0.12, 0.12), segments=4)
        count += 1
    for x, z in ((-3.15, 10.6), (-2.7, 6.25), (2.75, 8.05)):
        leaf.card(x, ruins.GATE_FRONT - 0.06, z, math.pi * 0.5,
                  rng.uniform(0.26, 0.46), -rng.uniform(1.1, 2.2),
                  lean=rng.uniform(-0.1, 0.1), segments=3)
        count += 1

    # Over the edges of the companion rocks.
    for islet in layout.ISLETS:
        for k in range(3):
            a = rng.uniform(0.0, TAU)
            x = islet["x"] + islet["r"] * 0.94 * math.cos(a)
            y = islet["y"] + islet["r"] * 0.94 * math.sin(a)
            z = layout.islet_cap_z(islet, x, y) - 0.02
            leaf.card(x, y, z, a, rng.uniform(0.28, 0.55),
                      -rng.uniform(1.2, 2.6), lean=rng.uniform(-0.2, 0.2),
                      segments=3)
            count += 1
    return count


def _moss(moss, rng):
    count = 0
    for x, y, kind, height in _columns():
        if kind == "missing":
            moss.patch(rng, x, y, layout.TERRACE_Z + 0.466,
                       rng.uniform(0.5, 0.8))
        elif kind == "tall":
            moss.patch(rng, x, y, layout.TERRACE_Z + height + 0.006,
                       rng.uniform(0.36, 0.62))
        else:
            jag = min(0.85, 0.28 + 0.10 * height)
            moss.patch(rng, x, y,
                       layout.TERRACE_Z + height - jag * 0.5 + 0.01,
                       rng.uniform(0.34, 0.58))
        count += 1

    for _i, a0, a1, _mid, top in ruins.parapet_specs():
        a = a0 + (a1 - a0) * rng.uniform(0.25, 0.75)
        moss.patch(rng, 20.28 * math.cos(a), 20.28 * math.sin(a),
                   top + 0.105, rng.uniform(0.34, 0.58), yaw=a,
                   stretch=1.5)
        count += 1

    for a0, a1, frac in ruins.architrave_spans():
        span = (a1 - a0) * frac
        for k in range(4):
            a = a0 + span * (0.12 + 0.26 * k)
            moss.patch(rng, ruins.R_COL * math.cos(a),
                       ruins.R_COL * math.sin(a), 9.055,
                       rng.uniform(0.4, 0.7), yaw=a, stretch=1.6)
            count += 1

    for x in (-4.0, -3.2, -2.1, -1.1, 0.0, 0.4):
        moss.patch(rng, x, ruins.GATE_CY, 12.805,
                   rng.uniform(0.35, 0.65), stretch=1.4)
        count += 1
    for x in (1.2, 2.4, 3.5):
        moss.patch(rng, x, ruins.GATE_CY, 9.795,
                   rng.uniform(0.3, 0.55), stretch=1.3)
        count += 1
    for x in (-3.15, 3.15):
        moss.patch(rng, x, ruins.GATE_CY, ruins.GATE_TOP_L + 0.345
                   if x < 0 else ruins.GATE_TOP_R + 0.37,
                   rng.uniform(0.4, 0.65))
        count += 1

    for x, y, sx, sy, h in ((-11.4, 11.6, 0.9, 0.55, 0.55),
                            (13.9, 8.9, 1.2, 0.48, 0.48),
                            (-19.0, -2.4, 2.5, 0.42, 0.42)):
        moss.patch(rng, x, y, layout.TERRACE_Z + h + 0.006,
                   max(sx, sy) * 0.8)
        count += 1

    for i in range(26):
        a = rng.uniform(0.0, TAU)
        r = layout.edge_radius(a) - rng.uniform(0.5, 1.0)
        moss.patch(rng, r * math.cos(a), r * math.sin(a),
                   layout.LIP_Z + 0.006, rng.uniform(0.4, 0.85))
        count += 1

    for islet in layout.ISLETS:
        for _k in range(3):
            a = rng.uniform(0.0, TAU)
            rr = islet["r"] * rng.uniform(0.3, 0.8)
            x = islet["x"] + rr * math.cos(a)
            y = islet["y"] + rr * math.sin(a)
            moss.patch(rng, x, y, layout.islet_cap_z(islet, x, y) + 0.02,
                       rng.uniform(0.35, 0.65))
            count += 1
    print(f"[foliage] {count} moss patches")
    return count


def build_foliage(mats):
    util.reset_collection(config.C_FOLIAGE)
    grass, leaf, moss, vine = _Batch(), _Batch(), _Batch(), _Batch()
    rng = util.sub_rng("sky_grass")
    columns = _columns()

    n_floor = _grass_floor(grass, rng, 100)
    n_terrace = _grass_terrace(grass, rng, 320, columns)
    n_rim = _grass_rim(grass, rng, 440)
    n_islet = _grass_islets(grass, rng, (30, 18, 24, 12, 10))
    print(f"[foliage] {n_floor + n_terrace + n_rim + n_islet} grass tufts "
          f"({n_rim} rim / {n_terrace} terrace / {n_floor} floor / "
          f"{n_islet} islets)")

    _shrubs(leaf, rng)
    n_vines = _vines(vine, rng)
    n_moss = _moss(moss, rng)

    grass_obj = grass.build("FOLIAGE_Grass", mats["grass"], config.C_FOLIAGE)
    leaf_obj = leaf.build("FOLIAGE_Leaf", mats["leaf"], config.C_FOLIAGE)
    moss_obj = moss.build("FOLIAGE_Moss", mats["moss"], config.C_FOLIAGE)
    vine_obj = vine.build("FOLIAGE_Vines", mats["grass"], config.C_FOLIAGE)
    quads = sum(len(o.data.polygons)
                for o in (grass_obj, leaf_obj, moss_obj, vine_obj))
    print(f"[foliage] {n_vines} hanging vines, {n_moss} moss patches, "
          f"{quads} quads total")
    return {"grass": grass_obj, "leaf": leaf_obj, "moss": moss_obj,
            "vine": vine_obj}
