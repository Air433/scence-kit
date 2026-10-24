"""Post-export pass: tag every material with VRMC_materials_mtoon 1.0.

Blender's glTF exporter has no MToon path, so the extension is injected into
the GLB JSON after export.  ``VRMC_materials_mtoon`` is added to
``extensionsUsed`` only (never ``extensionsRequired``): Godot and other
importers that do not know MToon still load the base PBR material unchanged.

Run standalone with:
    python scenes/cel_forest_arena/post_export.py output/cel_forest_arena/cel_forest_arena.glb
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arena_kit import config
from arena_kit import scene as scene_kit

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
EXTENSION = "VRMC_materials_mtoon"

ALPHA_CARDS = {"leaf", "litter", "fern", "grass"}
EMISSIVE = {"rune", "lantern", "mushroom", "firefly"}
PALETTE_KEY = {
    "stone": "stone",
    "stone_warm": "stone_warm",
    "stone_dark": "stone_dark",
    "underlay": "shadow",
    "ground": "ground",
    "bark": "bark",
    "wood": "wood",
    "moss": "moss",
    "leaf": "leaf",
    "litter": "leaf",
    "fern": "leaf",
    "grass": "leaf",
}
OUTLINE_WIDTH = {
    "stone": 0.020,
    "stone_warm": 0.020,
    "stone_dark": 0.020,
    "underlay": 0.012,
    "ground": 0.012,
    "bark": 0.032,
    "wood": 0.020,
    "moss": 0.014,
}
RIM_COLOR = (0.42, 0.62, 0.48)
OUTLINE_COLOR = (0.015, 0.028, 0.020)


def _load_palette():
    if config.SCENE_NAME != "cel_forest_arena":
        scene_kit.load("cel_forest_arena")


def _round(values, digits=4):
    return [round(float(v), digits) for v in values]


def _material_color(name, mat):
    key = PALETTE_KEY.get(name)
    if key is not None and key in config.PALETTE:
        return config.PALETTE[key]
    factor = mat.get("pbrMetallicRoughness", {}).get("baseColorFactor",
                                                     [1.0, 1.0, 1.0, 1.0])
    return tuple(factor[:3])


def _mtoon(name, mat):
    color = _material_color(name, mat)
    emissive = name in EMISSIVE
    alpha = name in ALPHA_CARDS

    if emissive:
        shade = [max(c * 0.85, 0.02) for c in color]
        toony, gi, rim_mix = 1.0, 1.0, 0.0
        rim = (0.0, 0.0, 0.0)
    else:
        shade = [max(c * (0.70 if alpha else 0.55), 0.015) for c in color]
        toony, gi, rim_mix = 0.92, 0.85, 0.35
        rim = RIM_COLOR

    ext = {
        "specVersion": "1.0",
        "transparentWithZWrite": False,
        "renderQueueOffsetNumber": 0,
        "shadeColorFactor": _round(shade),
        "shadingShiftFactor": -0.02,
        "shadingToonyFactor": toony,
        "giEqualizationFactor": gi,
        "matcapFactor": [0.0, 0.0, 0.0],
        "parametricRimColorFactor": _round(rim),
        "parametricRimFresnelPowerFactor": 5.0,
        "parametricRimLiftFactor": 0.05,
        "rimLightingMixFactor": rim_mix,
        "outlineWidthMode": "none",
    }

    width = OUTLINE_WIDTH.get(name)
    if width is not None and not alpha and not emissive:
        ext["outlineWidthMode"] = "worldCoordinates"
        ext["outlineWidthFactor"] = width
        ext["outlineColorFactor"] = _round(OUTLINE_COLOR)
        ext["outlineLightingMixFactor"] = 0.0
    return ext


def _patch(doc):
    materials = doc.get("materials", [])
    for mat in materials:
        name = mat.get("name", "").split(".")[0]
        mat.setdefault("extensions", {})[EXTENSION] = _mtoon(name, mat)
    used = doc.setdefault("extensionsUsed", [])
    if EXTENSION not in used:
        used.append(EXTENSION)
    return len(materials)


def _read_chunks(path):
    data = path.read_bytes()
    magic, version, total = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC or version != 2:
        raise RuntimeError(f"not a glTF 2.0 GLB: {path}")
    if total != len(data):
        raise RuntimeError(f"GLB length mismatch: {total} != {len(data)}")
    chunks = []
    offset = 12
    while offset + 8 <= total:
        length, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        chunks.append([kind, data[offset:offset + length]])
        offset += length
    return chunks


def _write_chunks(path, chunks):
    payload = bytearray()
    for kind, data in chunks:
        pad = (4 - len(data) % 4) % 4
        filler = b" " * pad if kind == CHUNK_JSON else b"\x00" * pad
        payload += struct.pack("<II", len(data) + pad, kind) + data + filler
    header = struct.pack("<III", GLB_MAGIC, 2, 12 + len(payload))
    path.write_bytes(header + payload)


def process(glb_path):
    _load_palette()
    path = Path(glb_path)
    chunks = _read_chunks(path)
    index = next(i for i, (kind, _) in enumerate(chunks) if kind == CHUNK_JSON)
    doc = json.loads(chunks[index][1].decode("utf-8"))
    count = _patch(doc)
    chunks[index][1] = json.dumps(
        doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    _write_chunks(path, chunks)
    print(f"[mtoon] {count} materials tagged with {EXTENSION} (spec 1.0)")
    return path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(
            "usage: python scenes/cel_forest_arena/post_export.py <file.glb>")
    process(sys.argv[1])
