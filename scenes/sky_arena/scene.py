"""天空竞技场 / Sky arena.

A ruined sanctuary floating above a sea of clouds: a weathered ivory-stone
platform with a broken colonnade, a half-collapsed sky gate and a central
rune dais holding a suspended crystal.  The kit's landscape/forest phases are
replaced by scene-local modules in ``builder.py``.
"""

SCENE = {
    "name": "sky_arena",
    "title": "天空竞技场",
    "seed": 20261023,
    "glb_name": "sky_arena.glb",

    # ---------------------------------------------------------------- world
    # Radii drive the platform modules directly; the kit bowl is unused.
    "world": {
        "inner_r": 12.6,             # paved fighting floor
        "tier_count": 0,
        "tier_tread": 0.0,
        "tier_rise": 0.0,
        "colonnade_r": 16.7,         # broken column ring
        "rune_r": 4.05,              # central dais rune
        "floor_z": 0.0,
        "terrain_base_z": -18.0,     # rock tip below the floating deck
    },

    # No trees: vegetation is grass, moss and vines handled by foliage.py.
    "trees": {
        "hero_count": 0,
        "bg_count": 0,
        "hero_angles": [],
        "hero_radii": [],
    },

    "counts": {
        "ferns": 60,                 # bush clumps on the rim
        "grass": 780,                # grass tufts
        "mushrooms": 0,
        "boulders": 34,              # rubble chunks
        "fireflies": 0,
    },

    # Elevated 3/4 view from beyond the southern rim: reads as a sky island,
    # keeps the gate, the dais and the cloud sea in one frame.
    "camera": {
        "loc": (24.0, -37.0, 10.5),
        "target": (0.0, 1.6, 3.6),
        "lens": 22.0,
    },

    "palette": {
        "stone":       "#d7c6a4",   # sunlit ivory limestone
        "stone_dark":  "#6a5f4c",   # weathered recess
        "stone_warm":  "#c8a670",   # warm sandstone trim
        "moss":        "#4f6b34",
        "moss_bright": "#87a84a",
        "ground":      "#657f3f",   # grass on the islets
        "bark":        "#6b5140",
        "leaf":        "#4b7a2f",
        "leaf_light":  "#8fbe54",
        "rune":        "#6cf2da",   # celadon rune light
        "lantern":     "#ffc47c",   # brazier amber
        "mushroom":    "#ffe6b0",
        "wood":        "#8a6a45",
        "shadow":      "#38352b",
    },

    # Warm afternoon sky: golden horizon, celadon mid sky, deep azure zenith.
    # Preview only; the exported sky is a painted dome.
    "sky_stops": [
        (0.00, "#a8c6c9"),
        (0.38, "#d8ecee"),
        (0.48, "#ffe9c9"),
        (0.53, "#a5d6ec"),
        (0.70, "#62a9d8"),
        (1.00, "#1f5f9e"),
    ],

    "lighting": {
        "sun_energy": 4.8,
        "sun_temperature": 4400,
        "sun_angle_deg": 2.4,
        "sun_pos": (-40.0, -24.0, 26.0),
        "sun_target": (0.0, 0.0, 3.5),
        "fill_energy": 380.0,
        "fill_color": "#cfe9f4",
        "fill_size": (30.0, 18.0),
        "fill_pos": (17.0, -26.0, 15.0),
        "fill_target": (0.0, 2.0, 3.5),
        "bounce_energy": 500.0,
        "bounce_color": "#ffd9a4",
        "bounce_size": (26.0, 16.0),
        "bounce_pos": (-6.0, 26.0, 17.0),
        "bounce_target": (0.0, 3.0, 8.0),
        "exposure": 0.0,
        "world_strength": 0.55,
        "mist_density": 0.0022,      # faint aerial haze, preview only
        "mist_height": 26.0,
        "mist_color": (0.82, 0.90, 0.93),
        "mist_anisotropy": 0.35,
        "lantern_energy": 55.0,
        "lantern_energy_far": 35.0,
        "lantern_temperature": 2800,
        "rune_light_energy": 60.0,
    },

    "materials": {
        "rune_emission": 2.2,
        "lantern_emission": 3.2,
        "mushroom_emission": 2.0,
        "firefly_emission": 2.5,
    },
}
