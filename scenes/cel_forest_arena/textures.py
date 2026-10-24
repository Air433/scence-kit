"""Cel-banded albedo maps for the toon look.

The kit's procedural maps use hard-coded earth tones, so the raw images stay
dark even when the scene palette changes.  Here each base map is smoothed and
remapped through a three-stop gradient built from the scene palette, with the
ramp *position* quantised into a few flat bands.  Quantising the final RGB
per channel would rotate warm golds toward magenta.
"""
from __future__ import annotations

import bpy
import numpy as np

from arena_kit import config
from arena_kit import textures as kit_textures
from arena_kit.textures import save_image

TOON_KEYS = {
    "stone_base": "stone_base_toon",
    "stone_warm_base": "stone_warm_base_toon",
    "stone_dark_base": "stone_dark_base_toon",
    "ground_base": "ground_base_toon",
    "bark_base": "bark_base_toon",
    "moss_base": "moss_base_toon",
    "wood_base": "wood_base_toon",
    "leaf_cluster": "leaf_cluster_toon",
    "leaf_litter": "leaf_litter_toon",
    "fern": "fern_toon",
    "grass": "grass_toon",
}

LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
CREAM = config.hex_rgb("#f4e9c6")

# Per-map flattening.  Large surfaces get coarse bands; foliage is almost a
# flat fill so its high-frequency leaf mask does not turn into speckle.
STYLE = {
    "stone_base": (5, 0.90, 1),
    "stone_warm_base": (5, 0.86, 1),
    "stone_dark_base": (5, 0.90, 1),
    "ground_base": (5, 0.90, 3),
    "bark_base": (5, 0.90, 2),
    "moss_base": (4, 0.92, 2),
    "wood_base": (5, 0.90, 1),
    "leaf_cluster": (4, 0.94, 2),
    "leaf_litter": (4, 0.94, 2),
    "fern": (4, 0.96, 1),
    "grass": (4, 0.96, 1),
}


def _mix(a, b, t):
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(3))


def _stops():
    p = config.PALETTE
    stone_light = _mix(p["stone"], CREAM, 0.45)
    bark_light = _mix(p["bark"], CREAM, 0.40)
    wood_light = _mix(p["wood"], CREAM, 0.40)
    return {
        "stone_base": ((0.0, p["stone_dark"]), (0.45, p["stone"]),
                       (1.0, stone_light)),
        "stone_warm_base": ((0.0, p["stone_dark"]), (0.50, p["stone_warm"]),
                            (1.0, CREAM)),
        "stone_dark_base": ((0.0, p["shadow"]), (0.55, p["stone_dark"]),
                            (1.0, p["stone"])),
        "ground_base": ((0.0, p["shadow"]), (0.50, p["ground"]),
                        (1.0, p["moss_bright"])),
        "bark_base": ((0.0, p["shadow"]), (0.35, p["bark"]),
                      (1.0, bark_light)),
        "moss_base": ((0.0, p["moss"]), (0.55, p["moss"]),
                      (1.0, p["moss_bright"])),
        "wood_base": ((0.0, p["bark"]), (0.50, p["wood"]),
                      (1.0, wood_light)),
        "leaf_cluster": ((0.0, p["leaf"]), (0.70, p["leaf"]),
                         (1.0, p["leaf_light"])),
        "leaf_litter": ((0.0, p["wood"]), (0.60, p["leaf"]),
                        (1.0, p["leaf_light"])),
        "fern": ((0.0, p["leaf"]), (0.65, p["leaf"]),
                 (1.0, p["leaf_light"])),
        "grass": ((0.0, p["moss"]), (0.60, p["leaf"]),
                  (1.0, p["leaf_light"])),
    }


def _load_rgba(path):
    img = bpy.data.images.load(str(path), check_existing=True)
    w, h = img.size
    flat = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(flat)
    arr = flat.reshape(h, w, 4)[::-1].copy()  # Blender rows are bottom-up
    return arr[..., :3], arr[..., 3]


def _ramp(lum, stops):
    out = np.empty((*lum.shape, 3), dtype=np.float32)
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        t = np.clip((lum - p0) / max(p1 - p0, 1e-6), 0.0, 1.0)
        band = (lum >= p0) & (lum <= p1)
        blend = (np.asarray(c0, dtype=np.float32)[None, None, :] * (1.0 - t[..., None])
                 + np.asarray(c1, dtype=np.float32)[None, None, :] * t[..., None])
        out[band] = blend[band]
    out[lum < stops[0][0]] = stops[0][1]
    out[lum > stops[-1][0]] = stops[-1][1]
    return out


def _box_blur(arr, radius):
    if radius <= 0:
        return arr
    k = 2 * radius + 1
    padded = np.pad(arr.astype(np.float32), radius, mode="edge")
    ii = np.zeros((padded.shape[0] + 1, padded.shape[1] + 1), dtype=np.float64)
    ii[1:, 1:] = padded.cumsum(0).cumsum(1)
    total = (ii[k:, k:] - ii[:-k, k:] - ii[k:, :-k] + ii[:-k, :-k])
    return (total / (k * k)).astype(np.float32)


def _smooth_luminance(lum, alpha, radius):
    """Blur luminance only, ignoring the transparent part of alpha cards."""
    if radius <= 0:
        return lum
    weight = (alpha > 0.5).astype(np.float32)
    if weight.min() > 0.5:
        return _box_blur(lum, radius)
    num = _box_blur(lum * weight, radius)
    den = _box_blur(weight, radius)
    return np.where(den > 1e-4, num / np.maximum(den, 1e-4), lum)


def _paletteise(rgb, alpha, stops, mix=0.78, bands=7, blur=0):
    lum = _smooth_luminance(rgb @ LUMA, alpha, blur)
    mask = alpha > 0.01
    if mask.any():
        lo, hi = np.percentile(lum[mask], (3.0, 97.0))
    else:
        lo, hi = 0.0, 1.0
    norm = np.clip((lum - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    # Quantise the ramp position, not the final RGB: rounding channels
    # independently turns warm golds into magenta.
    steps = max(int(bands) - 1, 1)
    norm = np.floor(norm * steps + 0.5) / steps
    rgb = _ramp(norm, stops) * mix + rgb * (1.0 - mix)
    return np.clip(rgb, 0.0, 1.0)


def ensure_textures(force: bool = False) -> dict:
    paths = kit_textures.ensure_textures(force=force)
    stops = _stops()
    out = {}
    for base_key, toon_key in TOON_KEYS.items():
        dst = config.TEXTURE_DIR / f"{toon_key}.png"
        out[toon_key] = dst
        if dst.exists() and not force:
            continue
        rgb, alpha = _load_rgba(paths[base_key])
        bands, mix, blur = STYLE[base_key]
        toon = _paletteise(rgb, alpha, stops[base_key], mix=mix,
                           bands=bands, blur=blur)
        save_image(toon_key, toon, alpha=alpha)
        print(f"[textures] cel {base_key} -> {toon_key}.png")

    print(f"[textures] cel set ready ({len(out)} maps)")
    return out
