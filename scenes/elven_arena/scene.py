"""精灵森林竞技场 / Elven forest arena.

This file is the *scene definition*: geometry scales, counts, palette and the
lighting rig.  The generators in ``arena_kit/`` read these values; nothing
below is code.  Copy this file when starting a new arena and change values.
"""

SCENE = {
    "name": "elven_arena",
    "title": "精灵森林竞技场",
    "seed": 20261019,
    "glb_name": "forest_arena_elven.glb",

    "world": {
        "terrain_size": 64.0,
        "terrain_res": 160,
        "inner_r": 9.0,
        "tier_count": 3,
        "tier_tread": 0.9,
        "tier_rise": 0.22,
        "colonnade_r": 12.4,
        "rune_r": 3.2,
        "floor_z": 0.0,
        "terrain_base_z": -0.18,
    },

    "trees": {
        "hero_count": 7,
        "bg_count": 30,
        # (azimuth degrees, radius metres) — keep radii > colonnade_r + 2
        "hero_angles": [30, 58, 100, 125, 165, 220, 330],
        "hero_radii": [17.0, 13.5, 21.0, 12.5, 16.5, 18.0, 14.5],
    },

    "counts": {
        "ferns": 760,
        "grass": 1800,
        "mushrooms": 34,
        "boulders": 58,
        "fireflies": 130,
    },

    "camera": {
        "loc": (3.6, -9.6, 2.62),
        "target": (0.0, 1.5, 2.90),
        "lens": 24.0,
    },

    "palette": {
        "stone":       "#8a8b82",
        "stone_dark":  "#565a52",
        "stone_warm":  "#9a9384",
        "moss":        "#4f6b31",
        "moss_bright": "#6f8d3d",
        "ground":      "#3b3524",
        "bark":        "#4a3a2b",
        "leaf":        "#3f6b2a",
        "leaf_light":  "#6f9440",
        "rune":        "#46f0c8",
        "lantern":     "#ffb45c",
        "mushroom":    "#7fe6b0",
        "wood":        "#5a4430",
        "shadow":      "#1b2117",
    },

    # Cycles preview sky gradient, low to high: (position, hex).
    "sky_stops": [
        (0.00, "#0d1512"),
        (0.42, "#232c22"),
        (0.49, "#8a7857"),
        (0.53, "#a8906c"),
        (0.60, "#4a615f"),
        (0.78, "#2d4a52"),
        (1.00, "#16303c"),
    ],

    "lighting": {
        "sun_energy": 7.5,
        "sun_temperature": 4200,
        "sun_angle_deg": 3.0,
        # Low front-left sun: long shadows toward the altar, warm rim on trunks.
        "sun_pos": (-32.0, -19.0, 12.5),
        "sun_target": (0.0, 0.0, 2.2),
        # Preview-only soft lights (not exported).
        "fill_energy": 850.0,
        "fill_color": "#b9d2dc",
        "fill_size": (16.0, 11.0),
        "fill_pos": (9.0, -15.0, 10.0),
        "fill_target": (0.0, 1.5, 2.0),
        "bounce_energy": 1300.0,
        "bounce_color": "#ffc98c",
        "bounce_size": (16.0, 9.0),
        "bounce_pos": (-5.0, -16.0, 8.0),
        "bounce_target": (0.0, 1.0, 1.5),
        "exposure": 1.0,
        "world_strength": 1.35,
        # Ground-hugging mist (preview only).
        "mist_density": 0.023,
        "mist_height": 9.5,
        "mist_color": (0.78, 0.82, 0.80),
        "mist_anisotropy": 0.55,
        # Exported point lights.
        "lantern_energy": 95.0,
        "lantern_energy_far": 65.0,
        "lantern_temperature": 2700,
        "rune_light_energy": 38.0,
    },

    "materials": {
        "rune_emission": 1.05,
        "lantern_emission": 3.4,
        "mushroom_emission": 1.8,
        "firefly_emission": 3.5,
    },
}
