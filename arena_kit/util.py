"""Shared helpers: RNG, collections, mesh generation, UVs, scatter."""
from __future__ import annotations

import math
import random
import zlib

import bmesh
import bpy
from mathutils import Quaternion, Vector

from . import config


# ---------------------------------------------------------------------------
# Deterministic randomness
# ---------------------------------------------------------------------------

def relocate_images() -> int:
    """Repair texture paths after a scene/checkpoint directory move.

    Blender stores absolute image paths in the .blend.  If a checkpoint was
    saved before textures moved (e.g. from ``textures/`` to
    ``textures/<scene>/``), every image becomes a missing-file stub and the
    glTF exporter silently drops it.  Re-point any missing image at a file of
    the same name in the active scene's texture directory.
    """
    from pathlib import Path
    fixed = 0
    for img in bpy.data.images:
        if img.source != "FILE" or not img.filepath:
            continue
        current = Path(bpy.path.abspath(img.filepath))
        if current.exists():
            continue
        candidate = config.TEXTURE_DIR / current.name
        if candidate.exists():
            img.filepath = str(candidate)
            img.reload()
            fixed += 1
    if fixed:
        print(f"[images] relocated {fixed} textures -> {config.TEXTURE_DIR}")
    return fixed


def sub_rng(name: str) -> random.Random:
    seed = zlib.crc32(f"{config.SEED}:{name}".encode("utf-8"))
    return random.Random(seed)


def hash01(name: str, i: int) -> float:
    h = zlib.crc32(f"{config.SEED}:{name}:{i}".encode("utf-8"))
    return (h & 0xFFFFFFFF) / 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Scene / collection management
# ---------------------------------------------------------------------------

def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    ensure_master_collections()


def ensure_master_collections() -> None:
    master = bpy.data.collections.get(config.C_MASTER)
    if master is None:
        master = bpy.data.collections.new(config.C_MASTER)
        bpy.context.scene.collection.children.link(master)
    for name in (
        config.C_TERRAIN, config.C_ARENA, config.C_ARCH, config.C_TREES,
        config.C_CANOPY, config.C_FOLIAGE, config.C_PROPS, config.C_LIGHTS,
        config.C_CAMERA, config.C_EXPORT, config.C_SCRATCH,
    ):
        if bpy.data.collections.get(name) is None:
            child = bpy.data.collections.new(name)
            master.children.link(child)
    # scratch is hidden in viewport/render
    scratch = bpy.data.collections.get(config.C_SCRATCH)
    if scratch:
        scratch.hide_render = True
        scratch.hide_viewport = True


def coll(name: str):
    ensure_master_collections()
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.data.collections[config.C_MASTER].children.link(c)
    return c


def link_object(obj, collection_name: str):
    c = coll(collection_name)
    if obj.name not in c.objects:
        c.objects.link(obj)
    return obj


def reset_collection(name: str) -> None:
    c = bpy.data.collections.get(name)
    if c is None:
        return
    for obj in list(c.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for child in list(c.children):
        bpy.data.collections.remove(child)
    bpy.data.orphans_purge(do_recursive=True)


def purge_orphans() -> None:
    bpy.data.orphans_purge(do_recursive=True)


# ---------------------------------------------------------------------------
# Object creation
# ---------------------------------------------------------------------------

def mesh_object(name: str, verts, faces, collection_name: str, mat=None,
                smooth: bool = False):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    mesh.validate(verbose=False)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    coll(collection_name).objects.link(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    return obj


def bmesh_object(name: str, bm: bmesh.types.BMesh, collection_name: str,
                 mat=None, smooth: bool = False):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(name, mesh)
    coll(collection_name).objects.link(obj)
    if mat is not None:
        obj.data.materials.append(mat)
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    return obj


def set_active(obj) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def bevel(obj, width: float, segments: int = 2, angle_deg: float = 30.0,
          clamp: bool = True) -> None:
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angle_deg)
    mod.use_clamp_overlap = clamp
    mod.miter_outer = "MITER_ARC"


def apply_modifiers(obj) -> None:
    if not obj.modifiers:
        return
    set_active(obj)
    for mod in list(obj.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError:
            obj.modifiers.remove(mod)


def apply_transform(obj, location=False, rotation=False, scale=True) -> None:
    set_active(obj)
    bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)


def smart_uv(obj, angle_deg: float = 66.0, margin: float = 0.004) -> None:
    set_active(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(angle_deg),
        island_margin=margin,
        correct_aspect=True,
        scale_to_bounds=False,
    )
    bpy.ops.object.mode_set(mode="OBJECT")


def cube_uv(obj, size: float = 2.0) -> None:
    set_active(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=size, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def cylindrical_uv(obj, repeat: float = 1.6) -> None:
    """Analytic cylindrical UV for trunks / logs."""
    mesh = obj.data
    uv = mesh.uv_layers.get("UVMap") or mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            ang = math.atan2(co.y, co.x)
            uv.data[li].uv = (ang / math.tau + 0.5, co.z / repeat)


def shade_smooth_by_angle(obj, angle_deg: float = 30.0) -> None:
    set_active(obj)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg))
    except Exception:
        pass


def join_objects(objs, name: str, collection_name: str):
    objs = [o for o in objs if o is not None and o.name in bpy.data.objects]
    if not objs:
        return None
    if len(objs) == 1:
        objs[0].name = name
        return objs[0]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    result = bpy.context.view_layer.objects.active
    result.name = name
    return result


def add_material(obj, mat) -> None:
    if mat is None:
        return
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def ensure_single_user(obj):
    if obj.data.users > 1:
        obj.data = obj.data.copy()
    return obj


# ---------------------------------------------------------------------------
# Geometry: tubes / lofts
# ---------------------------------------------------------------------------

def _parallel_frames(points):
    pts = [Vector(p) for p in points]
    n = len(pts)
    if n < 2:
        return []
    tangents = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        if t.length < 1e-9:
            t = Vector((0, 0, 1))
        tangents.append(t.normalized())

    up = Vector((0, 0, 1))
    if abs(tangents[0].dot(up)) > 0.92:
        up = Vector((0, 1, 0))
    normal = (up - tangents[0] * up.dot(tangents[0])).normalized()
    frames = []
    for i, t in enumerate(tangents):
        if i > 0:
            prev_t = tangents[i - 1]
            axis = prev_t.cross(t)
            if axis.length > 1e-8:
                angle = prev_t.angle(t)
                normal = Quaternion(axis.normalized(), angle) @ normal
        normal = (normal - t * normal.dot(t))
        if normal.length < 1e-8:
            normal = Vector((0, 0, 1)).cross(t)
        normal.normalize()
        binormal = t.cross(normal).normalized()
        frames.append((t, normal, binormal))
    return frames


def make_tube(points, radii, sides: int = 8, caps: bool = True,
              phase: float = 0.0):
    """Return (verts, faces) for a tube along a polyline."""
    pts = [Vector(p) for p in points]
    if len(pts) < 2:
        return [], []
    if isinstance(radii, (int, float)):
        radii = [float(radii)] * len(pts)
    frames = _parallel_frames(pts)
    verts = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        _, nrm, binrm = frames[i]
        for s in range(sides):
            a = 2.0 * math.pi * s / sides + phase
            verts.append(p + nrm * (r * math.cos(a)) + binrm * (r * math.sin(a)))
    faces = []
    for i in range(len(pts) - 1):
        for s in range(sides):
            a = i * sides + s
            b = i * sides + (s + 1) % sides
            c = (i + 1) * sides + (s + 1) % sides
            d = (i + 1) * sides + s
            faces.append((a, b, c, d))
    if caps:
        faces.append(tuple(reversed(range(sides))))
        faces.append(tuple(range((len(pts) - 1) * sides, len(pts) * sides)))
    return verts, faces


def loft_rings(rings, caps: bool = True):
    """rings: list of equal-length lists of 3D points."""
    if not rings:
        return [], []
    count = len(rings[0])
    verts = [tuple(p) for ring in rings for p in ring]
    faces = []
    for i in range(len(rings) - 1):
        for s in range(count):
            a = i * count + s
            b = i * count + (s + 1) % count
            c = (i + 1) * count + (s + 1) % count
            d = (i + 1) * count + s
            faces.append((a, b, c, d))
    if caps:
        faces.append(tuple(reversed(range(count))))
        faces.append(tuple(range((len(rings) - 1) * count, len(rings) * count)))
    return verts, faces


def circle_ring(center, normal, radius, sides: int, phase: float = 0.0):
    center = Vector(center)
    n = Vector(normal).normalized()
    helper = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((0, 1, 0))
    u = helper.cross(n).normalized()
    v = n.cross(u).normalized()
    return [
        center + u * (radius * math.cos(2 * math.pi * s / sides + phase))
        + v * (radius * math.sin(2 * math.pi * s / sides + phase))
        for s in range(sides)
    ]


# ---------------------------------------------------------------------------
# Scatter
# ---------------------------------------------------------------------------

def poisson_disc(count: int, r_min: float, r_max: float, min_dist: float,
                 rng: random.Random, accept=None, max_tries: int = 60000):
    pts = []
    d2 = min_dist * min_dist
    for _ in range(max_tries):
        r = math.sqrt(rng.uniform(r_min * r_min, r_max * r_max))
        a = rng.uniform(0.0, math.tau)
        p = (r * math.cos(a), r * math.sin(a))
        if accept is not None and not accept(p[0], p[1], r):
            continue
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 >= d2 for q in pts):
            pts.append(p)
            if len(pts) >= count:
                break
    return pts


def jitter(rng: random.Random, amount: float) -> float:
    return rng.uniform(-amount, amount)


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

def look_at(obj, target) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def set_vertex_colors(obj, color_func) -> None:
    """color_func(co) -> (r,g,b) in sRGB 0..1."""
    mesh = obj.data
    attr = mesh.color_attributes.get("Col")
    if attr is None:
        attr = mesh.color_attributes.new(name="Col", type="BYTE_COLOR", domain="POINT")
    for i, v in enumerate(mesh.vertices):
        r, g, b = color_func(v.co)
        attr.data[i].color_srgb = (r, g, b, 1.0)
    mesh.color_attributes.active_color = attr


def safe_name(text: str) -> str:
    return text.replace(" ", "_").replace(".", "_")
