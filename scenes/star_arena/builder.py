"""Phase orchestration for the star arena."""
from __future__ import annotations

from arena_kit import util

from . import (camera, environment, lighting, materials, plaza, platform,
               structures)


def build(phases, reset=False, force_textures=False, materials_fn=None,
          get_materials_fn=None):
    if reset:
        util.reset_scene()

    if "materials" in phases:
        mats = (materials_fn or materials.build_materials)(
            force_textures=force_textures)
    else:
        mats = (get_materials_fn or materials.get_materials)()

    data = {}
    if "camera" in phases:
        data["camera"] = camera.build_camera()
    if "terrain" in phases:
        data["terrain"] = platform.build_platform(mats)
    if "arena" in phases:
        data["arena"] = plaza.build_plaza(mats)
    if "arch" in phases:
        data["arch"] = structures.build_structures(mats)
    if "trees" in phases or "foliage" in phases:
        print("[builder] star arena has no vegetation")
    if "props" in phases:
        data["props"] = environment.build_environment(mats)
    if "lighting" in phases:
        data["lighting"] = lighting.build_lighting(mats)
    return data


def set_mist_enabled(enabled: bool):
    lighting.set_mist_enabled(enabled)
