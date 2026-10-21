"""TEMPLATE — copy this directory to scenes/<your_scene>/ and edit.

    cp -r scenes/_template scenes/red_desert
    # then rename and edit scenes/red_desert/scene.py
    blender -b -P build.py -- --scene red_desert --phase all --render quick

Every key below is optional except ``name``.  Omitted keys keep the kit
defaults (which are tuned for the elven arena), so start with ``name``,
``seed`` and ``palette`` and only add sections you actually want to change.

See GUIDE.md for the full authoring workflow and the glTF/Godot constraints.
"""

SCENE = {
    "name": "my_arena",              # must match the directory name
    "title": "我的竞技场",             # shown by build.py in the log
    "seed": 20261020,                # drives every deterministic RNG
    "glb_name": "my_arena.glb",      # written to output/<name>/

    # ---------------------------------------------------------------- world
    # All distances in metres; arena centre is the world origin.
    "world": {
        "terrain_size": 64.0,        # square terrain side
        "terrain_res": 160,          # vertices per side
        "inner_r": 9.0,              # flat arena floor radius
        "tier_count": 3,             # concentric spectator steps
        "tier_tread": 0.9,           # step depth
        "tier_rise": 0.22,           # step height
        "colonnade_r": 12.4,         # pillar ring radius
        "rune_r": 3.2,               # central rune ring radius (0 = no rune)
        "floor_z": 0.0,
        "terrain_base_z": -0.18,
    },

    # ---------------------------------------------------------------- trees
    # hero_count must equal len(hero_angles) == len(hero_radii).
    "trees": {
        "hero_count": 7,
        "bg_count": 30,              # simplified distant trees
        "hero_angles": [30, 58, 100, 125, 165, 220, 330],
        "hero_radii": [17.0, 13.5, 21.0, 12.5, 16.5, 18.0, 14.5],
    },

    # --------------------------------------------------------------- counts
    # Upper bounds; placement rejects collisions and the camera wedge.
    "counts": {
        "ferns": 760,
        "grass": 1800,
        "mushrooms": 34,
        "boulders": 58,
        "fireflies": 130,
    },

    # --------------------------------------------------------------- camera
    # Used for every render; also exported as CAM_Hero.
    "camera": {
        "loc": (3.6, -9.6, 2.62),
        "target": (0.0, 1.5, 2.90),
        "lens": 24.0,
    },

    # -------------------------------------------------------------- palette
    # Hex colours are converted to linear RGB automatically.
    # Keys are fixed: stone, stone_dark, stone_warm, moss, moss_bright,
    # ground, bark, leaf, leaf_light, rune, lantern, mushroom, wood, shadow.
    "palette": {
        "stone": "#8a8b82",
        "rune": "#46f0c8",
    },

    # --------------------------------------------------------- sky gradient
    # (position 0..1 bottom-to-top, hex). Preview only; not exported.
    # "sky_stops": [(0.0, "#0d1512"), (1.0, "#16303c")],

    # ------------------------------------------------------------- lighting
    # sun_* are exported as KHR_lights_punctual; fill/bounce/world/mist are
    # Cycles-preview only and never reach the GLB.
    "lighting": {
        "sun_energy": 7.5,           # Blender only; glTF sun exports as 1.0
        "sun_temperature": 4200,
        "sun_angle_deg": 3.0,
        "sun_pos": (-32.0, -19.0, 12.5),
        "sun_target": (0.0, 0.0, 2.2),
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
        "mist_density": 0.023,       # 0 disables the preview mist
        "mist_height": 9.5,
        "mist_color": (0.78, 0.82, 0.80),
        "mist_anisotropy": 0.55,
        "lantern_energy": 95.0,
        "lantern_energy_far": 65.0,
        "lantern_temperature": 2700,
        "rune_light_energy": 38.0,
    },

    # ------------------------------------------------------------ materials
    # Emissive strengths > 1 export via KHR_materials_emissive_strength.
    "materials": {
        "rune_emission": 1.05,
        "lantern_emission": 3.4,
        "mushroom_emission": 1.8,
        "firefly_emission": 3.5,
    },
}
