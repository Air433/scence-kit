extends RefCounted

# Scene-level data for the cel forest runtime.  Keep logic out of this file:
# another cel arena only needs a new GLB, a new MTOON table and new camera
# presets.

const GLB_PATH := "res://assets/cel_forest_arena.glb"
const DEFAULT_CAM := "hero"
const DEFAULT_FRAMES := 90
const FOV := 46.0
const MIN_DISTANCE := 5.0
const MAX_DISTANCE := 30.0

const CAMERA_PRESETS := {
    "hero": {
        "target": Vector3(0.0, 2.9, -1.5),
        "yaw": 17.9, "pitch": -1.4, "distance": 11.7,
    },
    "altar": {
        "target": Vector3(0.0, 3.0, -4.0),
        "yaw": 12.0, "pitch": 2.0, "distance": 15.0,
    },
    "wide": {
        "target": Vector3(0.0, 2.4, 0.0),
        "yaw": 26.0, "pitch": 3.0, "distance": 20.0,
    },
    "top": {
        "target": Vector3(0.0, 0.8, 0.0),
        "yaw": 0.0, "pitch": 72.0, "distance": 28.0,
    },
}

# Material key -> cel parameters.  Values mirror the VRMC_materials_mtoon
# block written by scenes/cel_forest_arena/post_export.py.
const MTOON := {
    "stone": {
        "shade": Color("#80907b"), "rim": Color("#a8d8b8"),
        "outline": 0.020,
    },
    "stone_warm": {
        "shade": Color("#9c8f69"), "rim": Color("#e8d9ae"),
        "outline": 0.020,
    },
    "stone_dark": {
        "shade": Color("#3a473d"), "rim": Color("#8fb49a"),
        "outline": 0.020,
    },
    "underlay": {
        "shade": Color("#1c2a22"), "rim": Color("#4f6b57"),
        "outline": 0.012,
    },
    "ground": {
        "shade": Color("#405e2b"), "rim": Color("#9ecf7a"),
        "outline": 0.012,
    },
    "bark": {
        "shade": Color("#69523b"), "rim": Color("#b39a6b"),
        "outline": 0.032,
    },
    "wood": {
        "shade": Color("#695038"), "rim": Color("#c2a982"),
        "outline": 0.020,
    },
    "moss": {
        "shade": Color("#3a6b2e"), "rim": Color("#a5d16a"),
        "outline": 0.014,
    },
    "leaf": {
        "shade": Color("#26754a"), "rim": Color("#9bd44f"),
        "outline": 0.0, "alpha": true,
    },
    "litter": {
        "shade": Color("#2f5a3a"), "rim": Color("#9bd44f"),
        "outline": 0.0, "alpha": true,
    },
    "fern": {
        "shade": Color("#26754a"), "rim": Color("#9bd44f"),
        "outline": 0.0, "alpha": true,
    },
    "grass": {
        "shade": Color("#2c6b3d"), "rim": Color("#a6d95a"),
        "outline": 0.0, "alpha": true,
    },
    "rune": {
        "shade": Color("#55e6ff"), "rim": Color.BLACK,
        "outline": 0.0, "emissive": true,
        "emission": Color("#55e6ff"), "energy": 1.5,
    },
    "lantern": {
        "shade": Color("#ffd166"), "rim": Color.BLACK,
        "outline": 0.0, "emissive": true,
        "emission": Color("#ffd166"), "energy": 4.0,
    },
    "mushroom": {
        "shade": Color("#ff8fb1"), "rim": Color.BLACK,
        "outline": 0.0, "emissive": true,
        "emission": Color("#ff8fb1"), "energy": 2.4,
    },
    "firefly": {
        "shade": Color("#ffd166"), "rim": Color.BLACK,
        "outline": 0.0, "emissive": true,
        "emission": Color("#ffd166"), "energy": 4.0,
    },
}

const OUTLINE_COLOR := Color("#0b1a12")
const OUTLINE_SCALE := 2.5

const SKY := {
    "horizon": Color("#9fd8e2"),
    "mid": Color("#56b3dd"),
    "zenith": Color("#2f7fd0"),
    "warm": Color("#dcb173"),
    "sun_color": Color("#ffe2a6"),
    "sun_dir": Vector3(-0.68, 0.58, 0.53),
    "band_strength": 0.55,
}

const ENV := {
    "ambient_color": Color("#cfe5dd"),
    "ambient_energy": 0.36,
    "exposure": 1.02,
    "glow_intensity": 0.55,
    "glow_bloom": 0.02,
    "glow_threshold": 0.90,
    "fog_color": Color("#9fc8bd"),
    "fog_density": 0.0035,
    "fog_height": 3.0,
    "fog_height_density": 0.004,
    "volumetric_density": 0.006,
    "saturation": 1.12,
    "contrast": 1.06,
}

const SUN := {
    "energy": 1.45,
    "color": Color("#fff1d8"),
    "shadow_distance": 70.0,
    "bias": 0.03,
    "normal_bias": 1.2,
}

const FILL := {
    "energy": 0.45,
    "color": Color("#b9dce8"),
    "pos": Vector3(14.0, 12.0, 14.0),
    "target": Vector3(0.0, 2.0, 0.0),
}

const LANTERN_RANGE := 9.0
const RUNE_RANGE := 8.0

const HUD := {
    "title": "赛璐璐森林竞技场",
    "subtitle": "CEL FOREST ARENA  ·  MTOON 1.0",
    "hint": "拖动旋转 · 滚轮缩放 ·  1 主视觉   2 祭坛   3 全景   4 俯视   C 自动环绕",
    "shot_name": "cel_forest_shot.png",
}
