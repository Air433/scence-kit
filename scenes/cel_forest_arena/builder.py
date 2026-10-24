"""Scene builder for the cel forest arena.

The kit's build order is reused verbatim; the only extra step is rebuilding
the preview-only ink shells after any geometry phase.  ``set_mist_enabled`` is
required by ``build.py`` when it renders.
"""
from __future__ import annotations

import json

import bpy

from arena_kit import (config, util, terrain, arena, architecture,
                       trees, foliage, props, lighting, camera)
from arena_kit import materials as kit_materials

from . import ink


def _collect_tree_data():
    out = []
    coll = bpy.data.collections.get(config.C_TREES)
    if coll is None:
        return out
    for obj in coll.all_objects:
        if obj.type == "MESH" and obj.name.startswith("TREE_Hero_") \
                and obj.name.endswith("_Bark"):
            out.append({
                "name": obj.name,
                "x": obj.location.x, "y": obj.location.y, "z": obj.location.z,
                "height": float(obj.get("tree_height", 28.0)),
                "radius": float(obj.get("tree_radius", 1.0)),
                "index": int(obj.get("tree_index", 0)),
            })
    out.sort(key=lambda t: t["index"])
    return out


def _collect_lanterns():
    obj = bpy.data.objects.get("PROP_LanternOrbs")
    if obj is None or "lantern_json" not in obj:
        return []
    return [tuple(p) for p in json.loads(obj["lantern_json"])]


def set_mist_enabled(enabled: bool):
    lighting.set_mist_enabled(enabled)


def build(phases, reset, force_textures=False, materials_fn=None,
          get_materials_fn=None):
    materials_fn = materials_fn or kit_materials.build_materials
    get_materials_fn = get_materials_fn or kit_materials.get_materials
    if reset:
        util.reset_scene()
    if "materials" in phases:
        mats = materials_fn(force_textures=force_textures)
    else:
        mats = get_materials_fn()
    data = {}

    if "camera" in phases:
        data["camera"] = camera.build_camera()
    if "terrain" in phases:
        data["terrain"] = terrain.build_terrain(mats)
    if "arena" in phases:
        data["arena"] = arena.build_arena(mats)
    if "arch" in phases:
        data["arch"] = architecture.build_architecture(mats)
    if "trees" in phases:
        data["trees"] = trees.build_trees(mats)
    if "foliage" in phases:
        data["foliage"] = foliage.build_foliage(mats)
    if "props" in phases:
        tree_data = data.get("trees") or _collect_tree_data()
        data["props"] = props.build_props(mats, tree_data)
    if "lighting" in phases:
        lanterns = []
        if "props" in data:
            lanterns = data["props"]["lanterns"]
        else:
            lanterns = _collect_lanterns()
        data["lighting"] = lighting.build_lighting(mats, lanterns)

    if any(p in phases for p in ("arena", "arch", "trees", "props")):
        ink.rebuild()
    return data
