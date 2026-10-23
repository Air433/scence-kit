"""Phase orchestration for the floating sky sanctuary."""
from __future__ import annotations

from arena_kit import util

from . import (camera, environment, foliage, lighting, materials, plaza,
               platform, ruins)


def _collect_braziers():
    return plaza.brazier_positions()


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
        data["arch"] = ruins.build_ruins(mats)
    if "trees" in phases:
        print("[builder] sky arena has no trees")
    if "foliage" in phases:
        data["foliage"] = foliage.build_foliage(mats)
    if "props" in phases:
        data["props"] = environment.build_environment(mats)
    if "lighting" in phases:
        braziers = (data.get("arena") or {}).get("braziers") \
            or _collect_braziers()
        gate_light = (data.get("arch") or {}).get("gate_light") \
            or (0.0, 18.3, 11.7)
        data["lighting"] = lighting.build_lighting(mats, braziers, gate_light)
    return data


def set_mist_enabled(enabled: bool):
    lighting.set_mist_enabled(enabled)
