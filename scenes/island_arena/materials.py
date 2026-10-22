"""Island material library.  All exported materials are image + Principled."""
from __future__ import annotations

import bpy

from arena_kit import config
from arena_kit.materials import make_emissive, make_pbr

from . import island_textures

MAT_NAMES = (
    "sand", "wet_sand", "seabed", "grass", "rock", "stone", "plaster",
    "paint_red", "wood", "palm_bark", "palm_frond", "grass_card",
    "bush_leaf", "metal", "compass", "flame", "bulb", "lighthouse_glass",
    "window", "cloud_preview", "ocean_preview", "foam_preview",
)


def _new(name):
    mat = bpy.data.materials.get(name)
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_fake_user = True
    return mat


def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def _tex(mat, path, colorspace="sRGB", label="Tex"):
    nt = mat.node_tree
    node = nt.nodes.new("ShaderNodeTexImage")
    node.label = label
    img = bpy.data.images.load(str(path), check_existing=True)
    img.colorspace_settings.name = colorspace
    node.image = img
    return node


def make_metal(name, color, metallic=0.85, roughness=0.32):
    mat = _new(name)
    bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def make_compass():
    mat = _new("compass")
    bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = (*config.hex_rgb("#8a6a32"), 1.0)
    bsdf.inputs["Metallic"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.28
    bsdf.inputs["Emission Color"].default_value = (*config.PALETTE["rune"], 1.0)
    bsdf.inputs["Emission Strength"].default_value = config.RUNE_EMISSION
    return mat


def make_cloud_preview(path):
    mat = _new("cloud_preview")
    nt = mat.node_tree
    bsdf = _principled(mat)
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Emission Strength"].default_value = 0.18
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.72, 0.52, 1.0)
    tex = _tex(mat, path, "sRGB", "Cloud")
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    mat.blend_method = "BLEND"
    mat.use_backface_culling = False
    mat.show_transparent_back = False
    return mat


def make_ocean_preview(path_norm):
    mat = _new("ocean_preview")
    nt = mat.node_tree
    bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = (*config.hex_rgb("#123a46"), 1.0)
    bsdf.inputs["Roughness"].default_value = 0.055
    bsdf.inputs["IOR"].default_value = 1.333
    bsdf.inputs["Metallic"].default_value = 0.0
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.55
        bsdf.inputs["Coat Roughness"].default_value = 0.02
    ntex = _tex(mat, path_norm, "Non-Color", "WaterNormal")
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = 0.55
    nt.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def make_foam_preview(path):
    mat = _new("foam_preview")
    nt = mat.node_tree
    bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = (0.88, 0.92, 0.95, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55
    tex = _tex(mat, path, "sRGB", "Foam")
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.18
    nt.links.new(tex.outputs["Alpha"], gt.inputs[0])
    nt.links.new(gt.outputs["Value"], bsdf.inputs["Alpha"])
    mat.blend_method = "BLEND"
    mat.use_backface_culling = False
    return mat


def build_materials(force_textures: bool = False):
    p = island_textures.ensure_textures(force=force_textures)
    get = lambda k: p.get(k)

    mats = {}
    mats["sand"] = make_pbr("sand", {
        "base": get("sand_base"), "rough": get("sand_rough"),
        "normal": get("sand_normal")})
    mats["wet_sand"] = make_pbr("wet_sand", {
        "base": get("wet_sand_base"), "normal": get("sand_normal")},
        roughness=0.34)
    mats["seabed"] = make_pbr("seabed", {
        "base": get("seabed_base"), "normal": get("sand_normal")},
        roughness=0.9)
    mats["grass"] = make_pbr("grass", {
        "base": get("grass_base"), "rough": get("grass_rough"),
        "normal": get("grass_normal")})
    mats["rock"] = make_pbr("rock", {
        "base": get("rock_base"), "rough": get("rock_rough"),
        "normal": get("rock_normal")})
    mats["stone"] = make_pbr("stone", {
        "base": get("stone_base"), "rough": get("stone_rough"),
        "normal": get("stone_normal")})
    mats["plaster"] = make_pbr("plaster", {
        "base": get("plaster_base"), "normal": get("plaster_normal")},
        roughness=0.72)
    mats["paint_red"] = make_pbr("paint_red", {}, flat_color=config.hex_rgb("#a83a2c"),
                                 roughness=0.55)
    mats["wood"] = make_pbr("wood", {
        "base": get("wood_base"), "normal": get("wood_normal")}, roughness=0.78)
    mats["palm_bark"] = make_pbr("palm_bark", {
        "base": get("palm_bark_base"), "rough": get("palm_bark_rough"),
        "normal": get("palm_bark_normal")})
    mats["palm_frond"] = make_pbr("palm_frond", {"base": get("palm_frond")},
                                  alpha=True, roughness=0.58)
    mats["grass_card"] = make_pbr("grass_card", {"base": get("grass_card")},
                                  alpha=True, roughness=0.8)
    mats["bush_leaf"] = make_pbr("bush_leaf", {"base": get("bush_leaf")},
                                 alpha=True, roughness=0.62)

    mats["metal"] = make_metal("metal", config.hex_rgb("#3a3330"), 0.82, 0.36)
    mats["compass"] = make_compass()
    mats["flame"] = make_emissive("flame", config.hex_rgb("#ff9a3a"), 7.0,
                                  base_color=(0.18, 0.05, 0.01))
    mats["bulb"] = make_emissive("bulb", config.hex_rgb("#ffc26a"),
                                 config.LANTERN_EMISSION,
                                 base_color=(0.2, 0.12, 0.05))
    mats["lighthouse_glass"] = make_emissive(
        "lighthouse_glass", config.hex_rgb("#ffd9a0"), 3.0,
        base_color=(0.16, 0.12, 0.07))
    mats["window"] = make_emissive("window", config.hex_rgb("#ffb35f"), 2.4,
                                   base_color=(0.12, 0.08, 0.04))

    mats["cloud_preview"] = make_cloud_preview(get("cloud"))
    mats["ocean_preview"] = make_ocean_preview(get("water_normal"))
    mats["foam_preview"] = make_foam_preview(get("foam"))

    print(f"[materials] island library: {len(mats)} materials")
    return mats


def get_materials():
    existing = {name: bpy.data.materials.get(name) for name in MAT_NAMES}
    if all(m is not None for m in existing.values()):
        return existing
    return build_materials()
