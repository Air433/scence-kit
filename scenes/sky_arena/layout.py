"""Shared measurements for the floating sky sanctuary."""
from __future__ import annotations

import math

from arena_kit import config

ARENA_R = 12.6
STEP1_R = 13.3
STEP2_R = 14.0
TERRACE_IN = 13.9
TERRACE_OUT = 20.6
TERRACE_Z = 0.34
LIP_Z = 0.30
GATE_Y = 19.9
GATE_HALF_W = 4.4

# Companion rocks.  The first entries sit in the hero frame; the far ones give
# the cloud sea a sense of scale.  ``z`` is the top of the grassy cap.
ISLETS = [
    {"x": -36.0, "y": -4.0, "z": 3.0, "r": 4.6, "depth": 7.2,
     "ruin": "column"},
    {"x": 26.0, "y": 26.0, "z": 0.5, "r": 4.0, "depth": 6.4,
     "ruin": "arch"},
    {"x": -24.0, "y": -20.0, "z": -2.0, "r": 2.8, "depth": 4.6,
     "ruin": None},
    {"x": 38.0, "y": 8.0, "z": -6.0, "r": 2.2, "depth": 3.4,
     "ruin": None},
    {"x": 10.0, "y": 60.0, "z": -1.5, "r": 3.2, "depth": 4.6,
     "ruin": None},
]

# Tops sit near the horizon so they are not swallowed by the main island.
FAR_ISLETS = [
    (-95.0, 12.0, 4.0, 8.0, 14.0),
    (-72.0, 55.0, 1.0, 6.0, 11.0),
    (32.0, 100.0, 2.0, 7.5, 13.0),
    (-120.0, 80.0, 2.0, 7.5, 12.0),
    (38.0, 112.0, 2.0, 6.0, 10.0),
    (95.0, 30.0, -2.0, 8.0, 13.0),
]


def islet_cap_z(islet: dict, x: float, y: float) -> float:
    dx, dy = x - islet["x"], y - islet["y"]
    t = min(1.0, math.hypot(dx, dy) / islet["r"])
    return (islet["z"] + 0.15 * (1.0 - t * t)
            + 0.025 * math.sin(5.0 * math.atan2(dy, dx) + 1.0))


def islet_ruin_offsets(kind) -> list:
    if kind == "column":
        return [(-0.4, 0.2)]
    if kind == "arch":
        return [(-1.7, 0.0), (1.3, 0.0)]
    return []


def edge_radius(a: float) -> float:
    """Irregular, broken rim (min ~21.6 m, max ~24.8 m)."""
    return (23.2
            + 0.85 * math.sin(3.0 * a + 0.7)
            + 0.48 * math.sin(7.0 * a + 2.1)
            + 0.25 * math.sin(11.0 * a + 3.7))


def colonnade_r() -> float:
    return config.COLONNADE_R


def in_gate_corridor(x: float, y: float, pad: float = 0.0) -> bool:
    return y > 14.0 and abs(x) < GATE_HALF_W + 0.8 + pad


def on_terrace(x: float, y: float) -> bool:
    r = math.hypot(x, y)
    return TERRACE_IN < r < TERRACE_OUT


def terrace_z(x: float, y: float) -> float:
    r = math.hypot(x, y)
    if r < ARENA_R:
        return 0.0
    if r < STEP1_R:
        return 0.17
    if r < STEP2_R:
        return TERRACE_Z
    return TERRACE_Z
