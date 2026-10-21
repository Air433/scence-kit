"""Material library built on image textures only (glTF-safe)."""
from __future__ import annotations

import bpy

from . import config, textures

MAT_NAMES = (
    "stone", "stone_warm", "stone_dark", "underlay", "ground",
    "bark", "wood", "moss", "leaf", "litter", "fern", "grass",
    "rune", "lantern", "mushroom", "firefly",
)


def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def _tex_node(mat, path, colorspace="sRGB", label="Tex"):
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.label = label
    img = bpy.data.images.load(str(path), check_existing=True)
    img.colorspace_settings.name = colorspace
    node.image = img
    return node


def _new_mat(name):
    mat = bpy.data.materials.get(name)
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    # Materials are created before any geometry exists; without a fake user a
    # phase's orphan purge would delete every one of them mid-build.
    mat.use_fake_user = True
    return mat


def make_pbr(name: str, paths: dict, flat_color=None, roughness: float = 0.8,
             alpha: bool = False, backface: bool = True):
    mat = _new_mat(name)
    nt = mat.node_tree
    bsdf = _principled(mat)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = roughness

    if paths.get("base") and flat_color is None:
        base = _tex_node(mat, paths["base"], "sRGB", "BaseColor")
        nt.links.new(base.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        c = flat_color or (0.3, 0.3, 0.3)
        bsdf.inputs["Base Color"].default_value = (*c, 1.0)

    if paths.get("rough"):
        rough = _tex_node(mat, paths["rough"], "Non-Color", "Roughness")
        nt.links.new(rough.outputs["Color"], bsdf.inputs["Roughness"])

    if paths.get("normal"):
        ntex = _tex_node(mat, paths["normal"], "Non-Color", "Normal")
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = 1.0
        nt.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    if alpha:
        img_node = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and n.label == "BaseColor"), None)
        if img_node is not None:
            gt = nt.nodes.new("ShaderNodeMath")
            gt.operation = "GREATER_THAN"
            gt.inputs[1].default_value = 0.5
            nt.links.new(img_node.outputs["Alpha"], gt.inputs[0])
            nt.links.new(gt.outputs["Value"], bsdf.inputs["Alpha"])
        mat.blend_method = "CLIP"
        mat.alpha_threshold = 0.5
        mat.use_backface_culling = False
    else:
        mat.use_backface_culling = backface

    return mat


def make_emissive(name: str, color, strength: float, base_color=None):
    mat = _new_mat(name)
    mat.use_nodes = True
    bsdf = _principled(mat)
    base = base_color or (0.02, 0.03, 0.02)
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.45
    bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
    bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def build_materials(force_textures: bool = False) -> dict:
    paths = textures.ensure_textures(force=force_textures)
    p = lambda key: paths.get(key)

    mats = {}
    mats["stone"] = make_pbr("stone", {
        "base": p("stone_base"), "rough": p("stone_rough"), "normal": p("stone_normal"),
    })
    mats["stone_warm"] = make_pbr("stone_warm", {
        "base": p("stone_warm_base"), "rough": p("stone_warm_rough"),
        "normal": p("stone_warm_normal"),
    })
    mats["stone_dark"] = make_pbr("stone_dark", {
        "base": p("stone_dark_base"), "rough": p("stone_dark_rough"),
        "normal": p("stone_dark_normal"),
    })
    mats["underlay"] = make_pbr("underlay", {}, flat_color=config.PALETTE["shadow"], roughness=0.95)
    mats["ground"] = make_pbr("ground", {
        "base": p("ground_base"), "rough": p("ground_rough"), "normal": p("ground_normal"),
    })
    mats["bark"] = make_pbr("bark", {
        "base": p("bark_base"), "rough": p("bark_rough"), "normal": p("bark_normal"),
    })
    mats["wood"] = make_pbr("wood", {
        "base": p("wood_base"), "normal": p("wood_normal"),
    })
    mats["moss"] = make_pbr("moss", {
        "base": p("moss_base"), "normal": p("moss_normal"),
    })
    mats["leaf"] = make_pbr("leaf", {"base": p("leaf_cluster")}, alpha=True)
    mats["litter"] = make_pbr("litter", {"base": p("leaf_litter")}, alpha=True)
    mats["fern"] = make_pbr("fern", {"base": p("fern")}, alpha=True)
    mats["grass"] = make_pbr("grass", {"base": p("grass")}, alpha=True)

    mats["rune"] = make_emissive("rune", config.PALETTE["rune"],
                                 config.RUNE_EMISSION)
    mats["lantern"] = make_emissive("lantern", config.PALETTE["lantern"],
                                    config.LANTERN_EMISSION)
    mats["mushroom"] = make_emissive("mushroom", config.PALETTE["mushroom"],
                                     config.MUSHROOM_EMISSION)
    mats["firefly"] = make_emissive("firefly", config.PALETTE["lantern"],
                                    config.FIREFLY_EMISSION)

    print(f"[materials] built {len(mats)} materials")
    return mats


def get_materials() -> dict:
    existing = {name: bpy.data.materials.get(name) for name in MAT_NAMES}
    if all(m is not None for m in existing.values()):
        return existing
    return build_materials()
