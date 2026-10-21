"""Scene registry: load a scene definition and apply it to ``config``.

A scene is a directory ``scenes/<name>/`` containing ``scene.py`` with a
module-level ``SCENE`` dict.  See ``scenes/_template/scene.py`` for the full
list of supported keys and ``GUIDE.md`` for the authoring workflow.
"""
from __future__ import annotations

import importlib
from pathlib import Path

from . import config

SCENES_DIR = config.ROOT / "scenes"

# spec section -> {spec key: config attribute}
WORLD_KEYS = {
    "terrain_size": "TERRAIN_SIZE",
    "terrain_res": "TERRAIN_RES",
    "inner_r": "INNER_R",
    "tier_count": "TIER_COUNT",
    "tier_tread": "TIER_TREAD",
    "tier_rise": "TIER_RISE",
    "colonnade_r": "COLONNADE_R",
    "rune_r": "RUNE_R",
    "floor_z": "ARENA_FLOOR_Z",
    "terrain_base_z": "TERRAIN_BASE_Z",
}
TREE_KEYS = {
    "hero_count": "HERO_TREE_COUNT",
    "bg_count": "BG_TREE_COUNT",
    "hero_angles": "HERO_TREE_ANGLES",
    "hero_radii": "HERO_TREE_RADII",
}
COUNT_KEYS = {
    "ferns": "FERN_CLUMPS",
    "grass": "GRASS_CLUMPS",
    "mushrooms": "MUSHROOM_CLUSTERS",
    "boulders": "BOULDER_COUNT",
    "fireflies": "FIREFLY_COUNT",
}
CAMERA_KEYS = {
    "loc": "CAMERA_LOC",
    "target": "CAMERA_TARGET",
    "lens": "CAMERA_LENS",
}
LIGHT_KEYS = {
    "sun_energy": "SUN_ENERGY",
    "sun_temperature": "SUN_TEMPERATURE",
    "sun_angle_deg": "SUN_ANGLE_DEG",
    "sun_pos": "SUN_POS",
    "sun_target": "SUN_TARGET",
    "fill_energy": "FILL_ENERGY",
    "fill_color": "FILL_COLOR",
    "fill_size": "FILL_SIZE",
    "fill_pos": "FILL_POS",
    "fill_target": "FILL_TARGET",
    "bounce_energy": "BOUNCE_ENERGY",
    "bounce_color": "BOUNCE_COLOR",
    "bounce_size": "BOUNCE_SIZE",
    "bounce_pos": "BOUNCE_POS",
    "bounce_target": "BOUNCE_TARGET",
    "exposure": "EXPOSURE",
    "world_strength": "WORLD_STRENGTH",
    "mist_density": "MIST_DENSITY",
    "mist_height": "MIST_HEIGHT",
    "mist_color": "MIST_COLOR",
    "mist_anisotropy": "MIST_ANISOTROPY",
    "lantern_energy": "LANTERN_ENERGY",
    "lantern_energy_far": "LANTERN_ENERGY_FAR",
    "lantern_temperature": "LANTERN_TEMPERATURE",
    "rune_light_energy": "RUNE_LIGHT_ENERGY",
}
MATERIAL_KEYS = {
    "rune_emission": "RUNE_EMISSION",
    "lantern_emission": "LANTERN_EMISSION",
    "mushroom_emission": "MUSHROOM_EMISSION",
    "firefly_emission": "FIREFLY_EMISSION",
}
TOP_KEYS = {"name", "title", "seed", "glb_name", "world", "trees", "counts",
            "camera", "palette", "lighting", "sky_stops", "materials", "notes"}
# Sky stop colours are hex strings and converted in lighting.py.
HEX_LIGHT_KEYS = {"fill_color", "bounce_color"}

# Colours stored as linear RGB tuples.
TUPLE_LIGHT_KEYS = {"sun_pos", "sun_target", "fill_size", "fill_pos",
                    "fill_target", "bounce_size", "bounce_pos",
                    "bounce_target", "mist_color"}


def list_scenes() -> list[str]:
    if not SCENES_DIR.exists():
        return []
    return sorted(p.name for p in SCENES_DIR.iterdir()
                  if not p.name.startswith("_") and (p / "scene.py").is_file())


def _apply_section(spec: dict, section: str, mapping: dict) -> None:
    values = spec.get(section) or {}
    if not isinstance(values, dict):
        raise TypeError(f"SCENE['{section}'] must be a dict")
    unknown = set(values) - set(mapping)
    if unknown:
        raise KeyError(
            f"unknown key(s) in SCENE['{section}']: {sorted(unknown)}; "
            f"valid keys: {sorted(mapping)}")
    for key, value in values.items():
        setattr(config, mapping[key], value)


def apply(spec: dict) -> None:
    """Write a scene spec into the process-wide config module."""
    unknown = set(spec) - TOP_KEYS
    if unknown:
        raise KeyError(f"unknown SCENE key(s): {sorted(unknown)}; "
                       f"valid keys: {sorted(TOP_KEYS)}")

    if "name" in spec:
        config.SCENE_NAME = spec["name"]
    if "title" in spec:
        config.SCENE_TITLE = spec["title"]
    if "seed" in spec:
        config.SEED = int(spec["seed"])
    if "glb_name" in spec:
        config.GLB_NAME = spec["glb_name"]

    _apply_section(spec, "world", WORLD_KEYS)
    _apply_section(spec, "trees", TREE_KEYS)
    _apply_section(spec, "counts", COUNT_KEYS)
    _apply_section(spec, "camera", CAMERA_KEYS)
    _apply_section(spec, "lighting", LIGHT_KEYS)
    _apply_section(spec, "materials", MATERIAL_KEYS)

    # Derived geometry.
    config.OUTER_R = config.INNER_R + config.TIER_COUNT * config.TIER_TREAD

    palette = spec.get("palette") or {}
    if palette:
        unknown = set(palette) - set(config.PALETTE)
        if unknown:
            raise KeyError(f"unknown palette key(s): {sorted(unknown)}; "
                           f"valid keys: {sorted(config.PALETTE)}")
        for key, value in palette.items():
            config.PALETTE[key] = config.hex_rgb(value)

    if "sky_stops" in spec:
        config.SKY_STOPS = [tuple(item) for item in spec["sky_stops"]]


def load(name: str):
    """Import ``scenes.<name>.scene``, apply it, and return the module."""
    if name not in list_scenes():
        raise SystemExit(
            f"unknown scene '{name}'. Available: {', '.join(list_scenes())}")
    module = importlib.import_module(f"scenes.{name}.scene")
    spec = getattr(module, "SCENE", None)
    if not isinstance(spec, dict):
        raise SystemExit(f"scenes/{name}/scene.py must define SCENE = {{...}}")

    config.use_scene(name)
    spec = dict(spec)
    spec.setdefault("name", name)
    apply(spec)
    print(f"[scene] {name} - {config.SCENE_TITLE} (seed {config.SEED})")
    return module


def optional_module(scene_name: str, sub: str):
    """Return ``scenes.<name>.<sub>`` if it exists, else None.

    Hooks let a scene replace the kit's default texture or material library
    without forking the whole project.
    """
    full = f"scenes.{scene_name}.{sub}"
    try:
        return importlib.import_module(full)
    except ModuleNotFoundError as exc:
        if exc.name != full:
            raise
        return None
