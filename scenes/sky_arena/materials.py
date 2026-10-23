"""Weathered ivory limestone, celadon light and foliage cards."""
from __future__ import annotations

import bpy

from arena_kit import config
from arena_kit.materials import make_emissive, make_pbr

from . import textures

MAT_NAMES = (
    "paving", "limestone", "limestone_warm", "rock", "gold", "gold_deep",
    "stone_dark", "ground", "rune", "flame", "grass", "leaf", "moss", "sky",
)


def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def _set_normal_strength(mat, strength):
    nmap = next((n for n in mat.node_tree.nodes if n.type == "NORMAL_MAP"),
                None)
    if nmap is not None:
        nmap.inputs["Strength"].default_value = strength


def _flat(name, color, metallic=0.0, roughness=0.6):
    mat = bpy.data.materials.get(name)
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_fake_user = True
    bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def _sky(path):
    mat = bpy.data.materials.get("sky")
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new("sky")
    mat.use_nodes = True
    mat.use_fake_user = True
    nt = mat.node_tree
    bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 1.0

    node = nt.nodes.new("ShaderNodeTexImage")
    node.label = "SkyDome"
    img = bpy.data.images.load(str(path), check_existing=True)
    img.colorspace_settings.name = "sRGB"
    node.image = img
    nt.links.new(node.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    mat.use_backface_culling = False
    return mat


def build_materials(force_textures: bool = False):
    paths = textures.ensure_textures(force=force_textures)
    p = lambda key: paths.get(key)

    mats = {}
    mats["paving"] = make_pbr("paving", {
        "base": p("paving_base"), "rough": p("paving_rough"),
        "normal": p("paving_normal"),
    }, roughness=0.65)
    _set_normal_strength(mats["paving"], 0.75)

    mats["limestone"] = make_pbr("limestone", {
        "base": p("limestone_base"), "rough": p("limestone_rough"),
        "normal": p("limestone_normal"),
    }, roughness=0.66)
    _set_normal_strength(mats["limestone"], 0.85)

    mats["rock"] = make_pbr("rock", {
        "base": p("rock_base"), "rough": p("rock_rough"),
        "normal": p("rock_normal"),
    }, roughness=0.85)
    _set_normal_strength(mats["rock"], 1.15)

    mats["limestone_warm"] = _flat("limestone_warm",
                                   config.PALETTE["stone_warm"],
                                   roughness=0.58)
    mats["stone_dark"] = _flat("stone_dark",
                               config.PALETTE["stone_dark"], roughness=0.82)
    mats["ground"] = _flat("ground", config.PALETTE["ground"], roughness=0.9)
    mats["gold"] = _flat("gold", config.hex_rgb("#f2c964"),
                         metallic=0.88, roughness=0.26)
    gold_bsdf = _principled(mats["gold"])
    gold_bsdf.inputs["Emission Color"].default_value = (*config.hex_rgb("#d9a43c"), 1.0)
    gold_bsdf.inputs["Emission Strength"].default_value = 0.12
    mats["gold_deep"] = _flat("gold_deep", config.hex_rgb("#bd8a3a"),
                              metallic=0.85, roughness=0.36)
    deep_bsdf = _principled(mats["gold_deep"])
    deep_bsdf.inputs["Emission Color"].default_value = (*config.hex_rgb("#9a6d28"), 1.0)
    deep_bsdf.inputs["Emission Strength"].default_value = 0.06

    mats["rune"] = make_emissive("rune", config.PALETTE["rune"],
                                 config.RUNE_EMISSION,
                                 base_color=(0.02, 0.055, 0.045))
    mats["flame"] = make_emissive("flame", config.PALETTE["lantern"],
                                  config.LANTERN_EMISSION,
                                  base_color=(0.06, 0.03, 0.01))

    mats["grass"] = make_pbr("grass", {"base": p("grass_card")}, alpha=True)
    mats["leaf"] = make_pbr("leaf", {"base": p("leaf_card")}, alpha=True)
    mats["moss"] = make_pbr("moss", {"base": p("moss_card")}, alpha=True)
    mats["sky"] = _sky(p("sky"))

    print(f"[materials] sky-ruin library: {len(mats)} materials "
          f"(3 alpha-masked cards)")
    return mats


def get_materials():
    existing = {name: bpy.data.materials.get(name) for name in MAT_NAMES}
    if all(m is not None for m in existing.values()):
        return existing
    return build_materials()
