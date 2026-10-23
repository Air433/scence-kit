"""星空竞技场 / Star arena.

A floating classical arena in deep space: an ivory-marble plaza enclosed by a
two-storey golden arcade, a monumental gate at the north chord, and a great
gold halo suspended above it.  The kit's bowl, forest and architecture phases
are replaced by scene-local modules in ``builder.py``.
"""

SCENE = {
    "name": "star_arena",
    "title": "星空竞技场",
    "seed": 20261023,
    "glb_name": "star_arena.glb",

    "world": {
        "inner_r": 12.0,
        "tier_count": 0,
        "tier_tread": 0.0,
        "tier_rise": 0.0,
        "colonnade_r": 18.4,
        "rune_r": 0.0,
        "floor_z": 0.0,
        "terrain_base_z": -0.45,
    },

    # No vegetation: the scene builder skips the tree / foliage phases.
    "trees": {
        "hero_count": 0,
        "bg_count": 0,
        "hero_angles": [],
        "hero_radii": [],
    },

    "counts": {
        "ferns": 0,
        "grass": 0,
        "mushrooms": 0,
        "boulders": 0,
        "fireflies": 0,
    },

    # Eye-level, slightly off-centre view from the south walkway.  The gate
    # sits at +Y, the halo rises to z ~ 26; 18 mm keeps both in frame.
    "camera": {
        "loc": (1.6, -15.2, 3.4),
        "target": (0.0, 0.6, 7.2),
        "lens": 18.0,
    },

    "palette": {
        "stone":       "#efe9dc",   # polished ivory marble
        "stone_dark":  "#c2b49a",   # warm stone recess
        "stone_warm":  "#d9b25f",   # champagne gold
        "moss":        "#6b5a3e",   # unused warm accent
        "moss_bright": "#ffe8b0",
        "ground":      "#100c09",
        "bark":        "#3a2c1c",   # deep bronze
        "leaf":        "#1a1410",
        "leaf_light":  "#5a4a35",
        "rune":        "#ffe6b8",   # warm-white inlay glow
        "lantern":     "#ffcf8f",   # sconce amber
        "mushroom":    "#fff1cf",   # portal light
        "wood":        "#8a6a3f",
        "shadow":      "#0a0806",
    },

    # Deep space behind the star-dome geometry; nearly black with a faint
    # warm haze so the dome's galaxies read as the light source.
    "sky_stops": [
        (0.00, "#050305"),
        (0.38, "#0b0709"),
        (0.50, "#1a100e"),
        (0.62, "#0c0810"),
        (1.00, "#030204"),
    ],

    "lighting": {
        "sun_energy": 4.5,
        "sun_temperature": 6500,
        "sun_angle_deg": 1.1,
        "sun_pos": (-34.0, -28.0, 40.0),
        "sun_target": (0.0, 0.0, 6.0),
        "fill_energy": 400.0,
        "fill_color": "#ffffff",
        "fill_size": (26.0, 16.0),
        "fill_pos": (20.0, -22.0, 14.0),
        "fill_target": (0.0, 3.0, 7.0),
        "bounce_energy": 250.0,
        "bounce_color": "#fff2e0",
        "bounce_size": (22.0, 14.0),
        "bounce_pos": (8.0, 28.0, 20.0),
        "bounce_target": (0.0, 7.0, 13.0),
        "exposure": 0.75,
        "world_strength": 0.12,
        "mist_density": 0.0,
        "mist_height": 1.0,
        "mist_color": (0.0, 0.0, 0.0),
        "mist_anisotropy": 0.0,
        "lantern_energy": 16.0,
        "lantern_energy_far": 10.0,
        "lantern_temperature": 2800,
        "rune_light_energy": 22.0,
    },

    "materials": {
        "rune_emission": 1.6,
        "lantern_emission": 1.8,
        "mushroom_emission": 2.0,
        "firefly_emission": 2.0,
    },
}
