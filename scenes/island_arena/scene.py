"""热带海岛竞技场 / Tropical island arena.

Static geometry is generated here and exported to ``island_arena.glb``.  The
real-time layer (Gerstner ocean, sky, weather, wind) lives in
``godot/island_arena`` inside the shared Godot project at ``godot/``.

Island-specific generators are wired through ``builder.py``; ``arena_kit``
keeps the shared utilities, texture helpers and exporter.
"""

SCENE = {
    "name": "island_arena",
    "title": "热带海岛竞技场",
    "seed": 20261022,
    "glb_name": "island_arena.glb",

    "world": {
        "terrain_size": 190.0,
        "terrain_res": 256,
        "inner_r": 8.4,
        "tier_count": 3,
        "tier_tread": 1.05,
        "tier_rise": 0.42,
        "colonnade_r": 15.0,
        "rune_r": 3.6,          # brass sun-compass inlay
        "floor_z": 4.35,
        "terrain_base_z": 0.0,
    },

    # Palms.  Count must match both arrays.  Angles avoid the south camera
    # wedge (-90 deg) and the north-east lighthouse headland (~45 deg).
    "trees": {
        "hero_count": 14,
        "bg_count": 6,
        "hero_angles": [-165, -138, -118, -62, -42, -18, 8, 32, 68, 100,
                        132, 158, 188, 215],
        "hero_radii": [24.0, 27.5, 22.5, 21.0, 26.0, 24.5, 27.0, 25.5,
                       26.5, 24.0, 27.0, 21.5, 25.0, 23.5],
    },

    "counts": {
        "ferns": 90,
        "grass": 520,
        "mushrooms": 0,
        "boulders": 90,
        "fireflies": 160,
    },

    # Hero framing: over the water south of the island, looking past the
    # arena toward the lighthouse and the setting sun.
    "camera": {
        "loc": (1.5, -47.0, 8.5),
        "target": (0.0, 6.0, 5.0),
        "lens": 30.0,
    },

    "palette": {
        "stone":       "#b8a37e",
        "stone_dark":  "#6d6252",
        "stone_warm":  "#d2bc91",
        "moss":        "#55703a",
        "moss_bright": "#87a04f",
        "ground":      "#8c7a52",
        "bark":        "#6a5540",
        "leaf":        "#3c742d",
        "leaf_light":  "#7fae4a",
        "rune":        "#ffcf7a",
        "lantern":     "#ffb45c",
        "mushroom":    "#7fe6b0",
        "wood":        "#5a422c",
        "shadow":      "#241f17",
    },

    # Sunset sky gradient for the Cycles preview, low to high.
    "sky_stops": [
        (0.00, "#1d3852"),
        (0.38, "#4c748c"),
        (0.455, "#b47f66"),
        (0.492, "#ffbe86"),
        (0.522, "#ef8f58"),
        (0.585, "#8d6272"),
        (0.72, "#4e5f7e"),
        (1.00, "#182c45"),
    ],

    "lighting": {
        "sun_energy": 5.4,
        "sun_temperature": 2950,
        "sun_angle_deg": 1.1,
        # Low west-north-west sun: rim light, long shadows and a sun path
        # across the water toward the camera.
        "sun_pos": (-50.0, 80.0, 23.0),
        "sun_target": (0.0, 4.0, 5.0),
        "fill_energy": 620.0,
        "fill_color": "#9fc4d8",
        "fill_size": (24.0, 14.0),
        "fill_pos": (6.0, -34.0, 12.0),
        "fill_target": (0.0, 2.0, 5.0),
        "bounce_energy": 1500.0,
        "bounce_color": "#ffb877",
        "bounce_size": (26.0, 10.0),
        "bounce_pos": (-8.0, -26.0, 3.0),
        "bounce_target": (0.0, 8.0, 5.0),
        "exposure": 1.10,
        "world_strength": 1.05,
        "mist_density": 0.0013,
        "mist_height": 42.0,
        "mist_color": (0.88, 0.76, 0.66),
        "mist_anisotropy": 0.55,
        "lantern_energy": 18.0,
        "lantern_energy_far": 11.0,
        "lantern_temperature": 2400,
        "rune_light_energy": 8.0,
    },

    "materials": {
        "rune_emission": 0.55,
        "lantern_emission": 5.0,
        "mushroom_emission": 0.0,
        "firefly_emission": 4.0,
    },
}
