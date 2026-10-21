"""Runtime configuration shared by every scene.

A *scene* lives in ``scenes/<name>/scene.py`` and overrides the values below
through ``arena_kit.scene.load()``.  The defaults in this file describe the
elven arena, so importing the kit without a scene still builds something
sane; in practice ``build.py`` always applies a scene first.

Every generator reads ``config.*`` at call time, never at import time, which
is what makes the single-module override approach work.
"""
from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Identity (overridden by the scene spec)
# ---------------------------------------------------------------------------
SCENE_NAME = "elven_arena"
SCENE_TITLE = "精灵森林竞技场"
SEED = 20261019
GLB_NAME = "forest_arena_elven.glb"

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output" / SCENE_NAME
RENDER_DIR = ROOT / "renders" / SCENE_NAME
TEXTURE_DIR = ROOT / "textures" / SCENE_NAME
CHECKPOINT_DIR = ROOT / "checkpoints" / SCENE_NAME

for _d in (OUTPUT_DIR, RENDER_DIR, TEXTURE_DIR, CHECKPOINT_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def use_scene(name: str) -> None:
    """Point every output path at ``output/<name>/`` etc."""
    global SCENE_NAME
    SCENE_NAME = name
    for attr, base in (("OUTPUT_DIR", "output"), ("RENDER_DIR", "renders"),
                       ("TEXTURE_DIR", "textures"),
                       ("CHECKPOINT_DIR", "checkpoints")):
        path = ROOT / base / name
        path.mkdir(parents=True, exist_ok=True)
        globals()[attr] = path


# ---------------------------------------------------------------------------
# World dimensions (metres)
# ---------------------------------------------------------------------------
TERRAIN_SIZE = 64.0
TERRAIN_RES = 160
INNER_R = 9.0
TIER_COUNT = 3
TIER_TREAD = 0.9
TIER_RISE = 0.22
OUTER_R = INNER_R + TIER_COUNT * TIER_TREAD          # 11.7
COLONNADE_R = 12.4
RUNE_R = 3.2
ARENA_FLOOR_Z = 0.0
TERRAIN_BASE_Z = -0.18

HERO_TREE_COUNT = 7
BG_TREE_COUNT = 30

# Shared hero-tree layout: (azimuth degrees, radial distance metres).
HERO_TREE_ANGLES = [30, 58, 100, 125, 165, 220, 330]
HERO_TREE_RADII = [17.0, 13.5, 21.0, 12.5, 16.5, 18.0, 14.5]

FERN_CLUMPS = 760
GRASS_CLUMPS = 1800
MUSHROOM_CLUSTERS = 34
BOULDER_COUNT = 58
FIREFLY_COUNT = 130

# Camera / hero framing
CAMERA_LOC = (3.6, -9.6, 2.62)
CAMERA_TARGET = (0.0, 1.5, 2.90)
CAMERA_LENS = 24.0

# ---------------------------------------------------------------------------
# Lighting rig (Blender preview + exported punctual lights)
# ---------------------------------------------------------------------------
SUN_ENERGY = 7.5
SUN_TEMPERATURE = 4200
SUN_ANGLE_DEG = 3.0
SUN_POS = (-32.0, -19.0, 12.5)
SUN_TARGET = (0.0, 0.0, 2.2)

# Preview-only soft lights (never exported to glTF).
FILL_ENERGY = 850.0
FILL_COLOR = "#b9d2dc"
FILL_SIZE = (16.0, 11.0)
FILL_POS = (9.0, -15.0, 10.0)
FILL_TARGET = (0.0, 1.5, 2.0)

BOUNCE_ENERGY = 1300.0
BOUNCE_COLOR = "#ffc98c"
BOUNCE_SIZE = (16.0, 9.0)
BOUNCE_POS = (-5.0, -16.0, 8.0)
BOUNCE_TARGET = (0.0, 1.0, 1.5)

EXPOSURE = 1.0
WORLD_STRENGTH = 1.35

# World-volume morning mist (Cycles preview only; never exported).
MIST_DENSITY = 0.023
MIST_HEIGHT = 9.5
MIST_COLOR = (0.78, 0.82, 0.80)
MIST_ANISOTROPY = 0.55

# Sky gradient: (position, hex). 0 = nadir, 1 = zenith.
SKY_STOPS = [
    (0.00, "#0d1512"),
    (0.42, "#232c22"),
    (0.49, "#8a7857"),
    (0.53, "#a8906c"),
    (0.60, "#4a615f"),
    (0.78, "#2d4a52"),
    (1.00, "#16303c"),
]

# Exported practicals.
LANTERN_ENERGY = 95.0
LANTERN_ENERGY_FAR = 65.0
LANTERN_TEMPERATURE = 2700
RUNE_LIGHT_ENERGY = 38.0

# ---------------------------------------------------------------------------
# Emissive material strengths (exported via KHR_materials_emissive_strength)
# ---------------------------------------------------------------------------
RUNE_EMISSION = 1.05
LANTERN_EMISSION = 3.4
MUSHROOM_EMISSION = 1.8
FIREFLY_EMISSION = 3.5

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def _s2l(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgb(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    return tuple(_s2l(int(value[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


PALETTE = {
    "stone":        hex_rgb("#8a8b82"),
    "stone_dark":   hex_rgb("#565a52"),
    "stone_warm":   hex_rgb("#9a9384"),
    "moss":         hex_rgb("#4f6b31"),
    "moss_bright":  hex_rgb("#6f8d3d"),
    "ground":       hex_rgb("#3b3524"),
    "bark":         hex_rgb("#4a3a2b"),
    "leaf":         hex_rgb("#3f6b2a"),
    "leaf_light":   hex_rgb("#6f9440"),
    "rune":         hex_rgb("#46f0c8"),
    "lantern":      hex_rgb("#ffb45c"),
    "mushroom":     hex_rgb("#7fe6b0"),
    "wood":         hex_rgb("#5a4430"),
    "shadow":       hex_rgb("#1b2117"),
}

# ---------------------------------------------------------------------------
# Collection names (kept stable so old checkpoints still resume)
# ---------------------------------------------------------------------------
C_MASTER = "ELVEN_ARENA"
C_TERRAIN = "EF_TERRAIN"
C_ARENA = "EF_ARENA"
C_ARCH = "EF_ARCH"
C_TREES = "EF_TREES"
C_CANOPY = "EF_CANOPY"
C_FOLIAGE = "EF_FOLIAGE"
C_PROPS = "EF_PROPS"
C_LIGHTS = "EF_LIGHTS"
C_CAMERA = "EF_CAMERA"
C_EXPORT = "EF_EXPORT"
C_SCRATCH = "_SCRATCH"

PHASE_ORDER = [
    "terrain",
    "arena",
    "arch",
    "trees",
    "foliage",
    "props",
    "materials",
    "lighting",
    "export",
]
