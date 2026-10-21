"""glTF export and GLB structural validation."""
from __future__ import annotations

import json
import struct

import bpy

from . import config, util


def _find_layer_collection(layer_coll, name):
    if layer_coll.name == name:
        return layer_coll
    for child in layer_coll.children:
        found = _find_layer_collection(child, name)
        if found is not None:
            return found
    return None


def _prepare():
    util.relocate_images()
    export_coll = bpy.data.collections.get(config.C_EXPORT)
    if export_coll is None:
        raise RuntimeError("EF_EXPORT collection is missing")
    for obj in list(export_coll.all_objects):
        if obj.type == "MESH" and obj.modifiers:
            util.apply_modifiers(obj)

    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    lc = _find_layer_collection(bpy.context.view_layer.layer_collection,
                                config.C_EXPORT)
    if lc is None:
        raise RuntimeError("EF_EXPORT layer collection is missing")
    bpy.context.view_layer.active_layer_collection = lc

    meshes = [o for o in export_coll.all_objects if o.type == "MESH"]
    tris = 0
    for o in meshes:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
    print(f"[export] {len(meshes)} meshes, {tris} triangles, "
          f"{len(bpy.data.materials)} materials")
    return tris


def export_glb(path=None):
    path = path or (config.OUTPUT_DIR / config.GLB_NAME)
    _prepare()
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_active_collection=True,
        use_active_collection_with_nested=True,
        export_apply=True,
        export_yup=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_keep_originals=False,
        export_cameras=True,
        export_lights=True,
        export_extras=True,
        export_animations=False,
        export_gn_mesh=False,
        export_vertex_color="ACTIVE",
        export_all_vertex_colors=True,
        export_active_vertex_color_when_no_material=True,
        export_draco_mesh_compression_enable=False,
        export_meshopt_compression_enable=False,
        export_use_gltfpack=False,
        # Godot treats light intensity as unitless energy, so the physical
        # SPEC units (lux/candela) come in ~700x too hot. COMPAT writes the
        # Blender values directly, which lands in Godot's expected range.
        export_import_convert_lighting_mode="COMPAT",
    )
    print(f"[export] wrote {path}")
    return path


def validate_glb(path):
    data = open(path, "rb").read()
    magic, version, total = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        raise RuntimeError("Not a GLB file")
    chunk_len, chunk_type = struct.unpack_from("<II", data, 12)
    if chunk_type != 0x4E4F534A:
        raise RuntimeError("First chunk is not JSON")
    doc = json.loads(data[20:20 + chunk_len].decode("utf-8"))

    accessors = doc.get("accessors", [])
    tris = 0
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            if prim.get("mode", 4) != 4:
                continue
            idx = prim.get("indices")
            if idx is not None:
                tris += accessors[idx]["count"] // 3
            else:
                tris += accessors[prim["attributes"]["POSITION"]]["count"] // 3

    ext_used = doc.get("extensionsUsed", [])
    ext_req = doc.get("extensionsRequired", [])
    bad = [e for e in ext_req if "draco" in e.lower() or "meshopt" in e.lower()]

    mats = doc.get("materials", [])
    alpha = {}
    for m in mats:
        mode = m.get("alphaMode", "OPAQUE")
        alpha[mode] = alpha.get(mode, 0) + 1
    double = sum(1 for m in mats if m.get("doubleSided"))

    lights = 0
    for node in doc.get("nodes", []):
        if "KHR_lights_punctual" in node.get("extensions", {}):
            lights += 1
    cameras = len(doc.get("cameras", []))
    images = doc.get("images", [])

    print("---- GLB VALIDATION ----")
    print(f"file            : {path}")
    print(f"size            : {len(data) / (1024 * 1024):.2f} MB")
    print(f"glTF version    : {version}, generator {doc.get('asset', {}).get('generator', '?')}")
    print(f"nodes/meshes    : {len(doc.get('nodes', []))} / {len(doc.get('meshes', []))}")
    print(f"triangles       : {tris}")
    print(f"materials       : {len(mats)}  alpha {alpha}  double-sided {double}")
    print(f"images          : {len(images)}")
    print(f"lights/cameras  : {lights} / {cameras}")
    print(f"extensionsUsed  : {ext_used}")
    print(f"extensionsReq   : {ext_req}")
    if bad:
        print(f"!! unsupported compression: {bad}")
    print("------------------------")
    return {
        "size_mb": len(data) / (1024 * 1024),
        "triangles": tris,
        "materials": len(mats),
        "alpha": alpha,
        "images": len(images),
        "lights": lights,
        "cameras": cameras,
        "extensions": ext_used,
        "bad_compression": bad,
    }


def save_blend(path=None):
    path = path or (config.CHECKPOINT_DIR / "forest_arena_elven.blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    print(f"[blend] saved {path}")
    return path
