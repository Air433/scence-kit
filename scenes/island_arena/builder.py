"""Phase orchestration for the tropical island scene."""
from __future__ import annotations

import json

import bpy

from arena_kit import config, util

from . import (
    arena, camera, features, foliage, lighting, materials, palms, preview,
    terrain,
)


def _collect_torches():
    obj = bpy.data.objects.get("ARENA_Structure")
    if obj is None or "torch_lights" not in obj:
        return []
    return [tuple(p) for p in json.loads(obj["torch_lights"])]


def _collect_lighthouse():
    obj = bpy.data.objects.get("LIGHTHOUSE_BeamOrigin")
    if obj is None:
        return {}
    return {"light_pos": tuple(obj.location)}


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
        data["terrain"] = terrain.build_terrain(mats)
    if "arena" in phases:
        data["arena"] = arena.build_arena(mats)
    if "arch" in phases:
        data["arch"] = features.build_features(mats)
    if "trees" in phases:
        data["trees"] = palms.build_palms(mats)
    if "foliage" in phases:
        data["foliage"] = foliage.build_foliage(mats)
    if "props" in phases:
        data["props"] = preview.build_preview(mats)
    if "lighting" in phases:
        torches = (data.get("arena") or {}).get("torches") or _collect_torches()
        lighthouse = (data.get("arch") or {}).get("lighthouse") \
            or _collect_lighthouse()
        data["lighting"] = lighting.build_lighting(mats, torches, lighthouse)
    return data


def set_mist_enabled(enabled: bool):
    lighting.set_mist_enabled(enabled)
