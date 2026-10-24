"""Flat "cel" material library: posterised base colour, no PBR maps.

The importers/generators only require the 16 kit material names, so this module
recreates them with a flat Principled setup.  A Freestyle lineset and a
Posterize compositor node give the Cycles preview the same graphic look as the
MToon shader used in Godot.
"""
from __future__ import annotations

import bpy

from arena_kit import config
from arena_kit.materials import make_emissive

from . import textures

MAT_NAMES = (
    "stone", "stone_warm", "stone_dark", "underlay", "ground",
    "bark", "wood", "moss", "leaf", "litter", "fern", "grass",
    "rune", "lantern", "mushroom", "firefly",
)


def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def _set(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def _new_mat(name):
    mat = bpy.data.materials.get(name)
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_fake_user = True
    return mat


def _flat_pbr(name, base_path=None, flat_color=None, alpha=False,
              backface=True):
    mat = _new_mat(name)
    nt = mat.node_tree
    bsdf = _principled(mat)
    _set(bsdf, "Metallic", 0.0)
    _set(bsdf, "Roughness", 0.95)
    _set(bsdf, "Specular IOR Level", 0.0)
    _set(bsdf, "Sheen Weight", 0.0)

    img = None
    if base_path is not None:
        img = nt.nodes.new("ShaderNodeTexImage")
        img.label = "BaseColor"
        image = bpy.data.images.load(str(base_path), check_existing=True)
        image.colorspace_settings.name = "sRGB"
        img.image = image
        nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        color = flat_color or (0.3, 0.3, 0.3)
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)

    mat.blend_method = "OPAQUE"

    if alpha:
        # Hard constraint: alpha must reach the Principled socket through a
        # GREATER_THAN node so glTF exports MASK instead of BLEND.
        gt = nt.nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.5
        nt.links.new(img.outputs["Alpha"], gt.inputs[0])
        nt.links.new(gt.outputs["Value"], bsdf.inputs["Alpha"])
        mat.blend_method = "CLIP"
        mat.alpha_threshold = 0.5
        mat.use_backface_culling = False
    else:
        mat.use_backface_culling = backface
    return mat


def _setup_compositor():
    scene = bpy.context.scene
    old = bpy.data.node_groups.get("CEL_Posterise")
    if old is not None:
        bpy.data.node_groups.remove(old)
    ng = bpy.data.node_groups.new("CEL_Posterise", "CompositorNodeTree")
    ng.interface.new_socket(name="Image", in_out="OUTPUT",
                            socket_type="NodeSocketColor")
    out = ng.nodes.new("NodeGroupOutput")
    rl = ng.nodes.new("CompositorNodeRLayers")
    to_srgb = ng.nodes.new("CompositorNodeConvertColorSpace")
    to_srgb.from_color_space = "scene_linear"
    to_srgb.to_color_space = "sRGB"
    post = ng.nodes.new("CompositorNodePosterize")
    post.inputs["Steps"].default_value = 7.0
    to_linear = ng.nodes.new("CompositorNodeConvertColorSpace")
    to_linear.from_color_space = "sRGB"
    to_linear.to_color_space = "scene_linear"
    # Posterising scene-linear values drives everything below 1/14 to black;
    # convert to display space first, then back.
    ng.links.new(rl.outputs["Image"], to_srgb.inputs[0])
    ng.links.new(to_srgb.outputs[0], post.inputs["Image"])
    ng.links.new(post.outputs["Image"], to_linear.inputs[0])
    ng.links.new(to_linear.outputs[0], out.inputs[0])
    scene.compositing_node_group = ng
    scene.render.use_compositing = True

    scene.view_settings.view_transform = "Standard"
    try:
        scene.view_settings.look = "None"
    except TypeError:
        pass


def _setup_freestyle():
    """Freestyle is intentionally unused.

    It is evaluated during glTF export as well as rendering and OOMs on this
    mesh budget (>4 GB), so outlines are built as inverted-hull geometry by
    ``scenes/cel_forest_arena/ink.py`` instead.
    """
    scene = bpy.context.scene
    scene.render.use_freestyle = False
    bpy.context.view_layer.use_freestyle = False


def setup_render_style():
    _setup_compositor()
    _setup_freestyle()
    print("[style] cel preview: Standard view + posterize(7) + hull ink")


def build_materials(force_textures: bool = False) -> dict:
    paths = textures.ensure_textures(force=force_textures)
    p = lambda key: paths[key]

    mats = {
        "stone": _flat_pbr("stone", p("stone_base_toon")),
        "stone_warm": _flat_pbr("stone_warm", p("stone_warm_base_toon")),
        "stone_dark": _flat_pbr("stone_dark", p("stone_dark_base_toon")),
        "underlay": _flat_pbr("underlay",
                              flat_color=config.PALETTE["shadow"]),
        "ground": _flat_pbr("ground", p("ground_base_toon")),
        "bark": _flat_pbr("bark", p("bark_base_toon")),
        "wood": _flat_pbr("wood", p("wood_base_toon")),
        "moss": _flat_pbr("moss", p("moss_base_toon")),
        "leaf": _flat_pbr("leaf", p("leaf_cluster_toon"), alpha=True),
        "litter": _flat_pbr("litter", p("leaf_litter_toon"), alpha=True),
        "fern": _flat_pbr("fern", p("fern_toon"), alpha=True),
        "grass": _flat_pbr("grass", p("grass_toon"), alpha=True),
    }

    mats["rune"] = make_emissive("rune", config.PALETTE["rune"],
                                 config.RUNE_EMISSION,
                                 base_color=(0.03, 0.10, 0.12))
    mats["lantern"] = make_emissive("lantern", config.PALETTE["lantern"],
                                    config.LANTERN_EMISSION,
                                    base_color=(0.12, 0.07, 0.02))
    mats["mushroom"] = make_emissive("mushroom", config.PALETTE["mushroom"],
                                     config.MUSHROOM_EMISSION,
                                     base_color=(0.10, 0.04, 0.07))
    mats["firefly"] = make_emissive("firefly", config.PALETTE["lantern"],
                                    config.FIREFLY_EMISSION,
                                    base_color=(0.12, 0.08, 0.02))
    for key in ("rune", "lantern", "mushroom", "firefly"):
        mats[key].blend_method = "OPAQUE"

    setup_render_style()
    print(f"[materials] cel library: {len(mats)} materials, "
          f"4 alpha-masked cards")
    return mats


def get_materials() -> dict:
    existing = {name: bpy.data.materials.get(name) for name in MAT_NAMES}
    if all(m is not None for m in existing.values()):
        return existing
    return build_materials()
