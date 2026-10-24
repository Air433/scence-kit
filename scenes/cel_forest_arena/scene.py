"""赛璐璐森林竞技场 / Cel-shaded forest arena.

Same layout as ``elven_arena``; the style shift lives in
``scenes/cel_forest_arena/materials.py`` (flat toon materials), ``textures.py``
(posterised albedo maps) and the post-export ``VRMC_materials_mtoon`` pass in
``scenes/cel_forest_arena/mtoon.py``.
"""

SCENE = {
    "name": "cel_forest_arena",
    "title": "赛璐璐森林竞技场",
    "seed": 20261024,
    "glb_name": "cel_forest_arena.glb",

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
        "bg_count": 28,
        "hero_angles": [30, 58, 100, 125, 165, 220, 330],
        "hero_radii": [17.0, 13.5, 21.0, 12.5, 16.5, 18.0, 14.5],
    },

    "counts": {
        "ferns": 600,
        "grass": 1500,
        "mushrooms": 30,
        "boulders": 46,
        "fireflies": 100,
    },

    "camera": {
        "loc": (3.6, -9.6, 2.62),
        "target": (0.0, 1.5, 2.90),
        "lens": 24.0,
    },

    # Bright, saturated cel palette: pale sage stone, emerald foliage and a
    # cyan rune so the posterised bands stay readable.
    "palette": {
        "stone":       "#a9b8a2",
        "stone_dark":  "#4e5f52",
        "stone_warm":  "#cdbb8a",
        "moss":        "#4e8f3e",
        "moss_bright": "#8bc34a",
        "ground":      "#567d3c",
        "bark":        "#8a6b4f",
        "leaf":        "#2e8b57",
        "leaf_light":  "#9bd44f",
        "rune":        "#55e6ff",
        "lantern":     "#ffd166",
        "mushroom":    "#ff8fb1",
        "wood":        "#8a6a4a",
        "shadow":      "#1c2a22",
    },

    # Crisp daylight sky: warm horizon band, saturated zenith.  The stops stay
    # below clipping under the preview exposure so the gradient keeps its bands.
    "sky_stops": [
        (0.00, "#12302b"),
        (0.40, "#376e60"),
        (0.47, "#dcb173"),
        (0.51, "#9fd8e2"),
        (0.58, "#56b3dd"),
        (0.70, "#2f7fd0"),
        (0.84, "#2860b4"),
        (1.00, "#1d4a9a"),
    ],

    "lighting": {
        "sun_energy": 7.0,
        "sun_temperature": 5600,
        "sun_angle_deg": 2.2,
        # High front-left sun: short graphic shadows across the stands.
        "sun_pos": (-26.0, -20.0, 22.0),
        "sun_target": (0.0, 0.0, 2.0),
        # Preview-only soft lights (not exported).  A strong neutral fill keeps
        # the shadow side of the canopy readable instead of pure black.
        "fill_energy": 2600.0,
        "fill_color": "#cfe7f2",
        "fill_size": (18.0, 12.0),
        "fill_pos": (10.0, -14.0, 11.0),
        "fill_target": (0.0, 1.5, 2.0),
        "bounce_energy": 800.0,
        "bounce_color": "#eef5e4",
        "bounce_size": (16.0, 9.0),
        "bounce_pos": (-5.0, -16.0, 8.0),
        "bounce_target": (0.0, 1.0, 1.5),
        "exposure": 1.15,
        "world_strength": 0.55,
        # Thin stacked fog bands read as a cel background layer.
        "mist_density": 0.002,
        "mist_height": 5.0,
        "mist_color": (0.70, 0.82, 0.80),
        "mist_anisotropy": 0.45,
        # Exported point lights.
        "lantern_energy": 95.0,
        "lantern_energy_far": 65.0,
        "lantern_temperature": 2700,
        "rune_light_energy": 38.0,
    },

    "materials": {
        "rune_emission": 2.0,
        "lantern_emission": 4.0,
        "mushroom_emission": 2.2,
        "firefly_emission": 4.0,
    },

    "notes": (
        "Cel style: posterised albedo textures, flat Principled materials, "
        "preview-only inverted-hull ink lines (ink.py) and a Posterize "
        "compositor pass for the Blender preview. The GLB is post-processed "
        "with VRMC_materials_mtoon by scenes/cel_forest_arena/post_export.py."
    ),
}
