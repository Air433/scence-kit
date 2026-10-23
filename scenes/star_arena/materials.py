"""Ivory marble, champagne gold and warm light for the star arena."""
from __future__ import annotations

import bpy

from arena_kit import config
from arena_kit.materials import make_emissive, make_pbr

from . import textures

MAT_NAMES = (
    "marble", "marble_warm", "gold", "gold_deep", "gold_glow", "stone_dark",
    "glow", "sconce", "portal", "starfield", "shadow",
)


def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def _flat(name, color, metallic=0.0, roughness=0.5):
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


def _marble(name, base, rough, normal):
    mat = make_pbr(name, {"base": base, "rough": rough, "normal": normal},
                   roughness=0.22)
    bsdf = _principled(mat)
    bsdf.inputs["Metallic"].default_value = 0.0
    nmap = next((n for n in mat.node_tree.nodes
                 if n.type == "NORMAL_MAP"), None)
    if nmap is not None:
        nmap.inputs["Strength"].default_value = 0.35
    return mat


def _portal(path):
    mat = bpy.data.materials.get("portal")
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new("portal")
    mat.use_nodes = True
    mat.use_fake_user = True
    nt = mat.node_tree
    bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = (0.02, 0.012, 0.004, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 1.0

    node = nt.nodes.new("ShaderNodeTexImage")
    node.label = "PortalNebula"
    img = bpy.data.images.load(str(path), check_existing=True)
    img.colorspace_settings.name = "sRGB"
    node.image = img
    nt.links.new(node.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = config.MUSHROOM_EMISSION
    mat.use_backface_culling = False
    return mat


def _starfield(path):
    mat = bpy.data.materials.get("starfield")
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new("starfield")
    mat.use_nodes = True
    mat.use_fake_user = True
    nt = mat.node_tree
    bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 1.0

    node = nt.nodes.new("ShaderNodeTexImage")
    node.label = "Starfield"
    img = bpy.data.images.load(str(path), check_existing=True)
    img.colorspace_settings.name = "sRGB"
    node.image = img
    nt.links.new(node.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.20
    mat.use_backface_culling = False
    return mat


def build_materials(force_textures: bool = False):
    paths = textures.ensure_textures(force=force_textures)
    p = lambda key: paths.get(key)

    mats = {}
    mats["marble"] = _marble("marble", p("marble_base"), p("marble_rough"),
                             p("marble_normal"))
    mats["marble_warm"] = _marble("marble_warm", p("marble_warm_base"),
                                  p("marble_warm_rough"),
                                  p("marble_warm_normal"))
    mats["gold"] = _flat("gold", config.hex_rgb("#e2b45f"),
                         metallic=1.0, roughness=0.20)
    mats["gold_deep"] = _flat("gold_deep", config.hex_rgb("#a97c33"),
                              metallic=1.0, roughness=0.32)
    mats["gold_glow"] = _flat("gold_glow", config.hex_rgb("#e2b45f"),
                              metallic=1.0, roughness=0.18)
    gbsdf = _principled(mats["gold_glow"])
    gbsdf.inputs["Emission Color"].default_value = (
        *config.hex_rgb("#ffcf7a"), 1.0)
    gbsdf.inputs["Emission Strength"].default_value = 0.9
    mats["stone_dark"] = _flat("stone_dark", config.PALETTE["stone_dark"],
                               metallic=0.0, roughness=0.58)
    mats["shadow"] = _flat("shadow", config.PALETTE["shadow"],
                           metallic=0.0, roughness=0.92)

    mats["glow"] = make_emissive("glow", config.PALETTE["rune"],
                                 config.RUNE_EMISSION,
                                 base_color=(0.05, 0.035, 0.015))
    mats["sconce"] = make_emissive("sconce", config.PALETTE["lantern"],
                                   config.LANTERN_EMISSION,
                                   base_color=(0.05, 0.025, 0.008))
    mats["portal"] = _portal(p("portal"))
    mats["starfield"] = _starfield(p("starfield"))

    print(f"[materials] marble library: {len(mats)} materials")
    return mats


def get_materials():
    existing = {name: bpy.data.materials.get(name) for name in MAT_NAMES}
    if all(m is not None for m in existing.values()):
        return existing
    return build_materials()
