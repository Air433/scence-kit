"""Preview-only inverted-hull ink outlines.

Freestyle cannot be used here: Blender evaluates it during glTF export as well
as rendering, and it needs >4 GB on this mesh budget.  Instead each outline
target gets a slightly inflated copy with a back-face-only emission material.
The copies live in ``CEL_INK`` and are never linked to ``EF_EXPORT``.
"""
from __future__ import annotations

import bpy

from arena_kit import config

INK_COLLECTION = "CEL_INK"
INK_NAME = "CEL_Ink"

# collection -> outline width in metres (object local space).  The previews
# render with OIDN, which smears sub-pixel lines, so widths stay generous.
TARGETS = (
    (config.C_ARENA, 0.045),
    (config.C_ARCH, 0.055),
    (config.C_TREES, 0.100),
    (config.C_PROPS, 0.045),
)
SKIP_MATERIALS = {"rune", "lantern", "mushroom", "firefly"}


def _ink_material():
    mat = bpy.data.materials.get(INK_NAME)
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(INK_NAME)
    mat.use_nodes = True
    mat.use_fake_user = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    ink = nt.nodes.new("ShaderNodeEmission")
    ink.inputs["Color"].default_value = (0.012, 0.024, 0.016, 1.0)
    ink.inputs["Strength"].default_value = 1.0
    nt.links.new(geom.outputs["Backfacing"], mix.inputs["Fac"])
    nt.links.new(clear.outputs["BSDF"], mix.inputs[1])
    nt.links.new(ink.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def _ink_collection():
    master = bpy.data.collections.get(config.C_MASTER)
    coll = bpy.data.collections.get(INK_COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(INK_COLLECTION)
        master.children.link(coll)
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    return coll


def _skip(obj):
    for mat in obj.data.materials:
        if mat is None:
            continue
        if mat.name in SKIP_MATERIALS:
            return True
        if mat.blend_method in {"CLIP", "BLEND"}:
            return True
    return False


def _shell(obj, width, material, collection):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
    if not mesh.vertices:
        return
    mesh.name = f"INK_{obj.name}"
    normals = [v.normal.copy() for v in mesh.vertices]
    for vert, normal in zip(mesh.vertices, normals):
        vert.co += normal * width
    mesh.update()

    shell = bpy.data.objects.new(f"INK_{obj.name}", mesh)
    shell.matrix_world = obj.matrix_world.copy()
    shell.data.materials.clear()
    shell.data.materials.append(material)
    shell.visible_shadow = False
    shell.visible_diffuse = False
    shell.visible_glossy = False
    collection.objects.link(shell)


def rebuild():
    material = _ink_material()
    collection = _ink_collection()
    count = 0
    for collection_name, width in TARGETS:
        source = bpy.data.collections.get(collection_name)
        if source is None:
            continue
        for obj in list(source.objects):
            if obj.type != "MESH" or _skip(obj):
                continue
            _shell(obj, width, material, collection)
            count += 1
    print(f"[ink] {count} preview outline shells ({INK_COLLECTION})")
