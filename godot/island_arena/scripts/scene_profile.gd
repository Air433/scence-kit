extends RefCounted

# Scene-level data for the real-time runtime. Keep this file free of logic:
# adding another arena to the shared godot/ project should mostly mean copying
# island_arena, then replacing the GLB, this table and scripts/weather.gd.

const WEATHER := preload("res://island_arena/scripts/weather.gd")

const GLB_PATH := "res://island_arena/assets/island_arena.glb"
const DEFAULT_MOOD := "sunny"
const DEFAULT_CAM := "hero"
const DEFAULT_FRAMES := 100
const BLEND_SPEED := 0.24
const AUTO_WEATHER_START := 82.0
const AUTO_WEATHER_MIN := 62.0
const AUTO_WEATHER_MAX := 96.0

const CAMERA := {
    "fov": 38.0,
    "near": 0.2,
    "far": 30000.0,
    "pitch_min": -4.0,
    "pitch_max": 34.0,
    "min_distance": 16.0,
    "max_distance": 130.0,
    "auto_orbit_delay": 5.0,
    "auto_orbit_speed": 0.45,
}

const NODES := {
    "camera": "CAM_Hero",
    "sun": "LIGHT_Sun",
    "beam": "LIGHT_LighthouseBeam",
    "seabed": "TERRAIN_Seabed",
    "terrain": "TERRAIN_Island",
    "compass": "LIGHT_Compass",
    "string": "LIGHT_String",
    "torch_prefix": "LIGHT_Torch_",
    "lighthouse": "LIGHT_Lighthouse",
    "beam_origin": "LIGHTHOUSE_BeamOrigin",
    "arena": "ARENA_Structure",
}

# GLB material names used by the continuous terrain shader.
const TERRAIN_MATERIALS := {
    "sand": "sand",
    "wet": "wet_sand",
    "grass": "grass",
    "rock": "rock",
}

const MATERIAL_SEABED := "seabed"
# Reflection camera sees the island from below; these emissive/glass surfaces
# keep back-face culling so the mirrored view is not overexposed.
const CULL_BACK_MATERIALS := ["flame", "bulb", "window", "lighthouse_glass", "compass"]

const WIND_SWAY := {
    "palm_frond": 0.62,
    "grass_card": 0.24,
    "bush_leaf": 0.17,
}
const WIND_FLUTTER := {
    "palm_frond": 1.35,
    "grass_card": 1.0,
    "bush_leaf": 0.6,
}
const WIND_BRIGHTNESS := {
    "grass_card": 1.30,
    "bush_leaf": 1.12,
    "palm_frond": 1.08,
}

const CAMERA_PRESETS := {
    "hero": {
        "target": Vector3(0.0, 4.5, -2.0),
        "yaw": 2.0, "pitch": 7.5, "distance": 62.0,
    },
    "shore": {
        "target": Vector3(0.0, 2.0, 0.0),
        "yaw": 4.0, "pitch": 7.0, "distance": 70.0,
    },
    "top": {
        "target": Vector3(0.0, 0.0, 0.0),
        "yaw": 0.0, "pitch": 82.0, "distance": 120.0,
    },
    "low": {
        "target": Vector3(0.0, 6.0, -6.0),
        "yaw": 2.0, "pitch": 2.0, "distance": 58.0,
    },
    "east": {
        "target": Vector3(0.0, 4.0, 0.0),
        "yaw": 100.0, "pitch": 6.0, "distance": 60.0,
    },
}

const TORCH_RANGE := 18.0
const STRING_RANGE := 22.0
const LIGHTHOUSE_RANGE := 36.0

const BEAM := {
    "fallback_pos": Vector3(20.5, 22.72, -21.5),
    "rotation_deg": Vector3(-4.0, 0.0, 0.0),
    "color": Color(1.0, 0.86, 0.62),
    "energy": 1.2,
    "range": 190.0,
    "angle": 8.0,
    "angle_attenuation": 0.55,
    "attenuation": 0.9,
    "fog_energy": 0.5,
}

const FILL_POS := Vector3(14.0, 24.0, 55.0)
const FILL_TARGET := Vector3(0.0, 4.0, 0.0)

# Must match scenes/island_arena/layout.py's SHORE_* constants.
# wave = (amplitude, frequency, phase).
const SHORE := {
    "base": 33.0,
    "wave_1": Vector3(3.0, 3.0, 0.8),
    "wave_2": Vector3(1.4, 7.0, 2.2),
    "wave_3": Vector3(0.7, 11.0, 0.1),
}

const HUD := {
    "title": "热带海岛竞技场",
    "subtitle": "ISLAND ARENA  ·  REAL-TIME",
    "weather_placeholder": "晴天",
    "hint": "拖动旋转 · 滚轮缩放 ·  1 晴天   2 暴雨   3 夜晚   R 随机天气   C 自动环绕",
    "shot_name": "island_arena_shot.png",
    "title_color": Color(1.0, 0.96, 0.90),
    "subtitle_color": Color(1.0, 0.88, 0.72, 0.85),
    "hint_color": Color(1.0, 0.95, 0.88, 0.72),
    "outline_color": Color(0.03, 0.03, 0.04, 0.7),
}
