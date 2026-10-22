"""Build an arena scene from ``scenes/<name>/scene.py`` and export a Godot-ready GLB.

Headless usage:
  blender -b --factory-startup -P build.py -- --scene <name> --phase all --render quick
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bpy

from arena_kit import (config, util, terrain, arena, architecture,
                       trees, foliage, props, lighting, camera, export, scene)
from arena_kit import materials as kit_materials

BUILD_ORDER = ["materials", "camera", "terrain", "arena", "arch", "trees",
               "foliage", "props", "lighting"]


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser(
        description="Build one arena scene from scenes/<name>/scene.py")
    p.add_argument("--scene", default=os.environ.get("EF_SCENE", "elven_arena"),
                   help="scene name under scenes/ (default: elven_arena)")
    p.add_argument("--list-scenes", action="store_true",
                   help="print available scene names and exit")
    p.add_argument("--phase", default="all",
                   choices=["all"] + BUILD_ORDER + ["export", "render"])
    p.add_argument("--seed", type=int, default=None,
                   help="override the seed defined by the scene")
    p.add_argument("--render", default="quick",
                   choices=["none", "quick", "mid", "hero", "both"])
    p.add_argument("--samples", type=int, default=0,
                   help="override sample count for the hero render")
    p.add_argument("--resume", action="store_true",
                   help="load the checkpoint and rebuild only the requested phase")
    p.add_argument("--force-textures", action="store_true")
    p.add_argument("--export", action="store_true",
                   help="also export when building a single phase")
    p.add_argument("--no-save", action="store_true")
    return p.parse_args(argv)


def checkpoint_path():
    return config.CHECKPOINT_DIR / config.GLB_NAME.replace(".glb", ".blend")


def materials_builder(scene_name):
    """Scenes may ship ``materials.py`` to replace the default library."""
    mod = scene.optional_module(scene_name, "materials")
    if mod is not None and hasattr(mod, "build_materials"):
        print(f"[scene] using scenes/{scene_name}/materials.py")
        return mod.build_materials
    return kit_materials.build_materials


def materials_getter(scene_name):
    mod = scene.optional_module(scene_name, "materials")
    if mod is not None and hasattr(mod, "get_materials"):
        return mod.get_materials
    return kit_materials.get_materials


def scene_builder(scene_name):
    """Scenes may ship ``builder.py`` when the kit's arena shape is wrong.

    The module exposes ``build(phases, ...)`` with the same contract as the
    kit build below, plus an optional ``set_mist_enabled(bool)`` hook.
    """
    mod = scene.optional_module(scene_name, "builder")
    if mod is not None and hasattr(mod, "build"):
        return mod
    return None


def load_checkpoint():
    path = checkpoint_path()
    if not path.exists():
        raise SystemExit(f"checkpoint missing: {path}")
    bpy.ops.wm.open_mainfile(filepath=str(path))
    util.relocate_images()
    print(f"[load] {path}", flush=True)


def collect_tree_data():
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


def collect_lanterns():
    obj = bpy.data.objects.get("PROP_LanternOrbs")
    if obj is None or "lantern_json" not in obj:
        return []
    return [tuple(p) for p in json.loads(obj["lantern_json"])]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def setup_render(res, samples, mist):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.02
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 3
    scene.cycles.transmission_bounces = 2
    scene.cycles.transparent_max_bounces = 24
    scene.cycles.sample_clamp_indirect = 8.0
    scene.cycles.volume_step_rate = 3.0
    scene.cycles.volume_max_steps = 256
    scene.render.use_persistent_data = True
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False

    builder = scene_builder(config.SCENE_NAME)
    if builder is not None and hasattr(builder, "set_mist_enabled"):
        builder.set_mist_enabled(mist)
    else:
        lighting.set_mist_enabled(mist)


def render_to(path, res, samples, mist):
    setup_render(res, samples, mist)
    scene = bpy.context.scene
    scene.render.filepath = str(path)
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"[render] {path} ({time.time() - t0:.1f}s)", flush=True)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build(phases, reset, force_textures=False, materials_fn=None,
          get_materials_fn=None, builder=None):
    if builder is not None:
        return builder.build(
            phases, reset=reset, force_textures=force_textures,
            materials_fn=materials_fn, get_materials_fn=get_materials_fn)
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
        tree_data = data.get("trees") or collect_tree_data()
        data["props"] = props.build_props(mats, tree_data)
    if "lighting" in phases:
        lanterns = []
        if "props" in data:
            lanterns = data["props"]["lanterns"]
        else:
            lanterns = collect_lanterns()
        data["lighting"] = lighting.build_lighting(mats, lanterns)
    return data


def main():
    args = parse_args()

    if args.list_scenes:
        print("\n".join(scene.list_scenes()))
        return

    scene.load(args.scene)
    if args.seed is not None:
        config.SEED = args.seed
    t_start = time.time()

    mats_build = materials_builder(args.scene)
    mats_get = materials_getter(args.scene)
    builder = scene_builder(args.scene)
    if builder is not None:
        print(f"[scene] using scenes/{args.scene}/builder.py", flush=True)

    if args.phase in ("export", "render"):
        load_checkpoint()
    elif args.resume and checkpoint_path().exists():
        load_checkpoint()
        phases = BUILD_ORDER if args.phase == "all" else [args.phase]
        print(f"[build] resume seed={config.SEED} phases={phases}", flush=True)
        build(phases, reset=False, force_textures=args.force_textures,
              materials_fn=mats_build, get_materials_fn=mats_get,
              builder=builder)
    else:
        if args.phase == "all":
            phases = BUILD_ORDER
        else:
            phases = BUILD_ORDER[:BUILD_ORDER.index(args.phase) + 1]
        print(f"[build] seed={config.SEED} phases={phases}", flush=True)
        build(phases, reset=True, force_textures=args.force_textures,
              materials_fn=mats_build, get_materials_fn=mats_get,
              builder=builder)

    if args.phase != "render":
        full = args.phase == "all"
        if full and not args.no_save:
            export.save_blend()
        if full or args.phase == "export" or args.export:
            glb = export.export_glb()
            export.validate_glb(glb)

    if args.render in ("quick", "both"):
        render_to(config.RENDER_DIR / "preview_main.png", (960, 540), 24, False)
    if args.render == "mid":
        render_to(config.RENDER_DIR / "preview_mid.png", (1200, 675), 40, True)
    if args.render in ("hero", "both"):
        samples = args.samples or 72
        render_to(config.RENDER_DIR / "hero.png", (1600, 900), samples, True)

    print(f"[done] {time.time() - t_start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
