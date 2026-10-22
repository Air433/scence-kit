"""Island layout: analytic terrain, shoreline and landmark placement.

Kept free of bpy so the same numbers can be mirrored by the Godot water
shader (shoreline foam uses the same analytic radius).
"""
from __future__ import annotations

import math

from mathutils import Vector, noise

from arena_kit import config

SEA_LEVEL = 0.0
ARENA_Z = config.ARENA_FLOOR_Z
OUTER_R = config.INNER_R + config.TIER_COUNT * config.TIER_TREAD
PLATEAU_R = OUTER_R + 2.2

LIGHTHOUSE_X = 20.5
LIGHTHOUSE_Y = 21.5
LIGHTHOUSE_BASE_Z = 6.6
LIGHTHOUSE_HEIGHT = 17.6

# Shoreline harmonics must match ``shaders/ocean.gdshader``.
SHORE_BASE = 33.0
SHORE_A = (3.0, 1.4, 0.7)
SHORE_PHASE = (0.8, 2.2, 0.1)
SHORE_FREQ = (3.0, 7.0, 11.0)


def smoothstep(a: float, b: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - a) / (b - a + 1e-9)))
    return t * t * (3.0 - 2.0 * t)


def _fbm(x: float, y: float, octaves: int = 4, scale: float = 0.05) -> float:
    total = 0.0
    amp = 1.0
    norm = 0.0
    f = scale
    for i in range(octaves):
        total += amp * noise.noise(Vector((x * f, y * f, 0.173 * i + 0.41)))
        norm += amp
        amp *= 0.5
        f *= 2.0
    return total / max(norm, 1e-9)


def shore_radius(angle: float) -> float:
    r = SHORE_BASE
    for amp, phase, freq in zip(SHORE_A, SHORE_PHASE, SHORE_FREQ):
        r += amp * math.sin(freq * angle + phase)
    return r


def lighthouse_hill(x: float, y: float) -> float:
    dx = x - LIGHTHOUSE_X
    dy = y - LIGHTHOUSE_Y
    return 7.4 * math.exp(-(dx * dx + dy * dy) / (2.0 * 8.5 * 8.5))


def terrain_height(x: float, y: float) -> float:
    r = math.hypot(x, y)
    a = math.atan2(y, x)
    d = r / max(shore_radius(a), 1e-3)

    h = ARENA_Z
    h -= 4.9 * smoothstep(0.68, 0.965, d)
    h -= 1.4 * smoothstep(0.94, 1.045, d)
    if d > 1.045:
        h -= 17.0 * (d - 1.045) ** 0.92

    dune = 0.52 * _fbm(x, y, 4, 0.078) + 0.16 * _fbm(x, y, 3, 0.235)
    # Dunes belong to the beach band; the ground inside the arena ring stays
    # level so the flagstones sit flush with the terrain.
    dune *= smoothstep(0.62, 0.78, d) * (1.0 - smoothstep(0.86, 0.975, d))
    h += dune

    h += lighthouse_hill(x, y) * (1.0 - smoothstep(1.00, 1.06, d))

    # Flat apron under the arena; blend back into dunes outside the tiers.
    flat = 1.0 - smoothstep(PLATEAU_R, PLATEAU_R + 4.5, r)
    h = h * (1.0 - flat) + (ARENA_Z - 0.02) * flat

    # Level headland pad for the lighthouse and keeper's cottage.
    dl = math.hypot(x - LIGHTHOUSE_X, y - LIGHTHOUSE_Y)
    pad = 1.0 - smoothstep(7.0, 12.0, dl)
    h = h * (1.0 - pad) + LIGHTHOUSE_BASE_Z * pad
    return h


def slope_at(x: float, y: float, e: float = 0.35) -> float:
    dx = terrain_height(x + e, y) - terrain_height(x - e, y)
    dy = terrain_height(x, y + e) - terrain_height(x, y - e)
    return math.hypot(dx, dy) / (2.0 * e)


def is_underwater(x: float, y: float, margin: float = 0.0) -> bool:
    return terrain_height(x, y) < SEA_LEVEL - margin


def palm_sites():
    """(x, y, z, angle_deg, radius) for every hero palm in the scene."""
    out = []
    for ang_deg, radius in zip(config.HERO_TREE_ANGLES, config.HERO_TREE_RADII):
        a = math.radians(ang_deg)
        x, y = math.cos(a) * radius, math.sin(a) * radius
        z = terrain_height(x, y)
        if z < 0.45:
            # Pull shoreline palms inland instead of drowning them.
            for shrink in (0.9, 0.8, 0.7, 0.6):
                x, y = math.cos(a) * radius * shrink, math.sin(a) * radius * shrink
                z = terrain_height(x, y)
                if z >= 0.45:
                    break
        out.append((x, y, z, ang_deg, math.hypot(x, y)))
    return out


def path_points():
    """Stepping-stone path from the south arena stair to the lighthouse."""
    pts = []
    n = 46
    for i in range(n):
        t = i / (n - 1)
        # Start south of the arena, sweep east around the tiers, climb the
        # headland.  Hand-tuned control points keep it out of the palms.
        p0 = (0.0, -18.5)
        p1 = (8.0, -18.0)
        p2 = (16.0, -8.0)
        p3 = (18.5, 6.0)
        p4 = (20.5, 15.5)
        u = 1.0 - t
        x = (u ** 4) * p0[0] + 4 * (u ** 3) * t * p1[0] + \
            6 * (u ** 2) * (t ** 2) * p2[0] + 4 * u * (t ** 3) * p3[0] + \
            (t ** 4) * p4[0]
        y = (u ** 4) * p0[1] + 4 * (u ** 3) * t * p1[1] + \
            6 * (u ** 2) * (t ** 2) * p2[1] + 4 * u * (t ** 3) * p3[1] + \
            (t ** 4) * p4[1]
        if i % 2 == 0:
            pts.append((x, y))
    return pts
