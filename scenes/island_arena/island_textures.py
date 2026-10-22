"""Procedural textures for the tropical island (numpy, offline).

Everything exported to the GLB uses image textures only; the helper set in
``arena_kit.textures`` supplies tileable noise, stamping and PNG saving.
"""
from __future__ import annotations

import math

import numpy as np

from arena_kit import config
from arena_kit.textures import (
    TAU, fbm, gray_rgb, lin, mix, normal_from_height, periodic_aniso_noise,
    periodic_value_noise, save_image, smoothstep, stamp_blade, stamp_ellipse,
    stamp_leaf, worley,
)


def _uv(size):
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    return xs / size, ys / size


# ---------------------------------------------------------------------------
# Ground
# ---------------------------------------------------------------------------

def make_sand(seed=101, size=1024):
    rng = np.random.default_rng(seed)
    base = fbm(size, 4, 6, rng)
    grain = fbm(size, 96, 2, rng)
    ripple = periodic_aniso_noise(size, 22, 5, rng)
    shell_n = fbm(size, 12, 3, rng)

    pale = lin("#eadbbd")
    warm = lin("#d6c09a")
    dark = lin("#b49a74")
    shell = lin("#f7efdd")

    v = np.clip(0.15 + 0.95 * base, 0, 1)
    col = pale[None, None, :] * v[..., None] + warm[None, None, :] * (1 - v[..., None])
    col = mix(col, np.broadcast_to(dark, col.shape),
              (0.14 * smoothstep(0.5, 0.85, ripple))[..., None])
    col *= (0.94 + 0.16 * grain[..., None])
    col = mix(col, np.broadcast_to(shell, col.shape),
              (0.20 * smoothstep(0.76, 0.92, shell_n))[..., None])

    # Tiny coral / shell fragments.
    rgb = col.copy()
    alpha = np.ones((size, size), dtype=np.float32)
    for _ in range(240):
        cx, cy = rng.uniform(0, size), rng.uniform(0, size)
        rx = rng.uniform(1.2, 4.6)
        ry = rx * rng.uniform(0.35, 0.9)
        c = shell * rng.uniform(0.75, 1.15)
        if rng.random() < 0.15:
            c = lin("#b86f55") * rng.uniform(0.8, 1.1)
        stamp_ellipse(rgb, alpha, cx, cy, rx, ry, rng.uniform(0, TAU), c, edge=0.4)
    col = np.clip(rgb, 0, 1)

    height = 0.52 * base + 0.26 * ripple + 0.08 * grain
    rough = np.clip(0.76 + 0.20 * grain, 0.6, 1.0)
    save_image("sand_base", col)
    save_image("sand_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image("sand_normal", normal_from_height(height, 1.6), colorspace="Non-Color")

    # Wet sand: same grain, lower, cooler.  Reuses sand normal / roughness.
    wet = col * np.array([0.72, 0.65, 0.57], dtype=np.float32)
    wet = mix(wet, np.broadcast_to(lin("#8a7d67"), wet.shape),
              (0.28 * smoothstep(0.35, 0.75, base))[..., None])
    save_image("wet_sand_base", wet)

    seabed = col * np.array([0.62, 0.71, 0.64], dtype=np.float32)
    seabed = mix(seabed, np.broadcast_to(lin("#7d9b82"), seabed.shape),
                 (0.26 * smoothstep(0.42, 0.8, base))[..., None])
    save_image("seabed_base", seabed)


def make_grass(seed=111, size=1024):
    rng = np.random.default_rng(seed)
    base = fbm(size, 5, 6, rng)
    fine = fbm(size, 64, 3, rng)
    clump = fbm(size, 16, 4, rng)

    soil = lin("#7d6742")
    olive = lin("#8b944b")
    green = lin("#6f8f3f")
    dry = lin("#b3a066")

    col = mix(np.broadcast_to(soil, (size, size, 3)),
              np.broadcast_to(olive, (size, size, 3)),
              smoothstep(0.30, 0.72, base)[..., None])
    col = mix(col, np.broadcast_to(green, col.shape),
              (0.65 * smoothstep(0.42, 0.78, clump))[..., None])
    col = mix(col, np.broadcast_to(dry, col.shape),
              (0.35 * smoothstep(0.62, 0.9, fine))[..., None])
    col *= (0.90 + 0.26 * fine[..., None])

    height = 0.5 * base + 0.35 * clump + 0.1 * fine
    rough = np.clip(0.86 + 0.10 * fine, 0.7, 1.0)
    save_image("grass_base", col)
    save_image("grass_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image("grass_normal", normal_from_height(height, 1.4), colorspace="Non-Color")


def make_basalt(seed=121, size=1024):
    rng = np.random.default_rng(seed)
    base = fbm(size, 4, 6, rng)
    grain = fbm(size, 72, 3, rng)
    f1, f2 = worley(size, 7, rng)
    crack = 1.0 - smoothstep(0.0, 0.055, f2 - f1)
    lichen = fbm(size, 9, 4, rng)

    dark = lin("#5f594f")
    mid = lin("#958b7c")
    light = lin("#bcaf9a")
    moss = lin("#8a9563")

    v = np.clip(0.12 + 0.9 * base, 0, 1)
    col = dark[None, None, :] * (1 - v[..., None]) + mid[None, None, :] * v[..., None]
    col = mix(col, np.broadcast_to(light, col.shape),
              (0.40 * smoothstep(0.55, 0.9, grain))[..., None])
    col *= (1.0 - 0.48 * crack[..., None])
    col = mix(col, np.broadcast_to(moss, col.shape),
              (0.40 * smoothstep(0.62, 0.82, lichen))[..., None])
    col *= (0.90 + 0.22 * grain[..., None])

    height = 0.55 * base + 0.20 * grain - 0.5 * crack + 0.08 * lichen
    rough = np.clip(0.72 + 0.16 * grain + 0.10 * crack, 0.5, 1.0)
    save_image("rock_base", col)
    save_image("rock_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image("rock_normal", normal_from_height(height, 2.6), colorspace="Non-Color")


def make_sandstone(seed=131, size=1024):
    rng = np.random.default_rng(seed)
    base = fbm(size, 4, 6, rng)
    grain = fbm(size, 88, 3, rng)
    f1, f2 = worley(size, 5, rng)
    joints = 1.0 - smoothstep(0.0, 0.05, f2 - f1)
    strata = 0.5 + 0.5 * np.sin(TAU * (_uv(size)[1] * 26.0 + 0.3 * base))

    a = lin("#a58d6a")
    b = lin("#cdb587")
    c = lin("#e0c89c")
    shade = lin("#6e604b")

    v = np.clip(0.15 + 0.95 * base, 0, 1)
    col = a[None, None, :] * (1 - v[..., None]) + b[None, None, :] * v[..., None]
    col = mix(col, np.broadcast_to(c, col.shape),
              (0.45 * strata * smoothstep(0.4, 0.8, grain))[..., None])
    col *= (1.0 - 0.42 * joints[..., None])
    col *= (0.9 + 0.2 * grain[..., None])
    col = mix(col, np.broadcast_to(shade, col.shape),
              (0.22 * smoothstep(0.7, 0.92, base))[..., None])

    height = 0.42 * base + 0.18 * strata + 0.08 * grain - 0.30 * joints
    rough = np.clip(0.72 + 0.16 * grain + 0.08 * joints, 0.55, 0.98)
    save_image("stone_base", col)
    save_image("stone_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image("stone_normal", normal_from_height(height, 2.0), colorspace="Non-Color")


def make_plaster(seed=141, size=512):
    rng = np.random.default_rng(seed)
    base = fbm(size, 5, 5, rng)
    stain = fbm(size, 12, 4, rng)
    grain = fbm(size, 60, 2, rng)
    white = lin("#e7e2d4")
    warm = lin("#cfc7b4")
    col = mix(np.broadcast_to(white, (size, size, 3)),
              np.broadcast_to(warm, (size, size, 3)),
              smoothstep(0.35, 0.8, base)[..., None])
    col = mix(col, np.broadcast_to(lin("#a89d86"), col.shape),
              (0.22 * smoothstep(0.72, 0.95, stain))[..., None])
    col *= (0.93 + 0.13 * grain[..., None])
    height = 0.5 * base + 0.22 * grain
    save_image("plaster_base", col)
    save_image("plaster_normal", normal_from_height(height, 1.1),
               colorspace="Non-Color")


# ---------------------------------------------------------------------------
# Wood & palm
# ---------------------------------------------------------------------------

def make_wood(seed=151, size=1024):
    rng = np.random.default_rng(seed)
    grain = periodic_aniso_noise(size, 4, 28, rng)
    knots = fbm(size, 18, 3, rng)
    scratch = periodic_aniso_noise(size, 60, 3, rng)
    plank = np.abs(np.sin(TAU * (_uv(size)[0] * 5.0 + 0.08 * grain)))
    groove = smoothstep(0.02, 0.12, plank)

    dark = lin("#3b2a1c")
    mid = lin("#6b4c31")
    light = lin("#8d6a46")
    v = np.clip(0.2 + 0.85 * grain, 0, 1)
    col = dark[None, None, :] * (1 - v[..., None]) + mid[None, None, :] * v[..., None]
    col = mix(col, np.broadcast_to(light, col.shape),
              (0.30 * smoothstep(0.55, 0.9, knots))[..., None])
    col *= (0.55 + 0.55 * groove[..., None])
    col *= (0.88 + 0.2 * scratch[..., None])

    height = 0.55 * grain + 0.2 * knots - 0.3 * (1.0 - groove)
    save_image("wood_base", col)
    save_image("wood_normal", normal_from_height(height, 1.8), colorspace="Non-Color")


def make_palm_bark(seed=161, size=1024):
    rng = np.random.default_rng(seed)
    fiber = periodic_aniso_noise(size, 40, 6, rng)
    rings = 0.5 + 0.5 * np.sin(TAU * (_uv(size)[1] * 22.0 + 0.35 * fiber))
    ring_shadow = 1.0 - 0.55 * smoothstep(0.55, 0.95, rings)
    noise = fbm(size, 20, 4, rng)

    dark = lin("#5e4a37")
    mid = lin("#9c8468")
    light = lin("#c0a584")
    col = dark[None, None, :] * 0.5 + mid[None, None, :] * 0.5
    col = mix(col, np.broadcast_to(light, col.shape),
              (0.40 * smoothstep(0.4, 0.8, fiber))[..., None])
    col *= (0.72 + 0.40 * ring_shadow[..., None])
    col *= (0.90 + 0.22 * noise[..., None])

    height = 0.4 * fiber + 0.35 * ring_shadow + 0.08 * noise
    rough = np.clip(0.82 + 0.12 * fiber, 0.65, 1.0)
    save_image("palm_bark_base", col)
    save_image("palm_bark_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image("palm_bark_normal", normal_from_height(height, 2.0),
               colorspace="Non-Color")


def make_palm_frond(seed=171, size=1024):
    """Pinnate frond atlas.  UV.y=0 is the petiole, UV.y=1 the tip."""
    rng = np.random.default_rng(seed)
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    a = np.zeros((size, size), dtype=np.float32)

    cx = size * 0.5
    base_y = size * 0.985
    tip_y = size * 0.015
    rachis = lin("#9aab63")
    leaf_dark = lin("#3f6b2b")
    leaf_mid = lin("#628f39")
    leaf_light = lin("#9bbb58")
    dry = lin("#b09a58")

    # Rachis from bottom (base) to top (tip).
    for i in range(90):
        t = i / 89.0
        y = base_y + (tip_y - base_y) * t
        w = (1.0 - t) * 7.0 + 1.2
        stamp_ellipse(rgb, a, cx, y, w, (base_y - tip_y) / 120.0,
                      math.pi * 0.5, rachis, edge=0.35)

    # Leaflets: two staggered rows per side for a dense, feathered silhouette.
    pairs = 52
    for i in range(pairs):
        t = 0.035 + 0.93 * i / (pairs - 1)
        y = base_y + (tip_y - base_y) * t
        span = (1.0 - t) ** 0.5
        length = size * (0.075 + 0.30 * span) * rng.uniform(0.84, 1.1)
        ang = math.radians(rng.uniform(24, 40) + 20 * (1.0 - t))
        for side in (-1, 1):
            for layer in (0.0, 0.12):
                x0 = cx + side * (3.0 + layer * 20)
                y0 = y
                aa = ang + rng.uniform(-0.10, 0.10)
                x1 = x0 + side * math.cos(aa) * length * (1.0 - layer * 0.25)
                y1 = y0 - math.sin(aa) * length * (1.0 - layer * 0.25)
                midx = (x0 + x1) * 0.5
                midy = (y0 + y1) * 0.5
                seg_len = math.hypot(x1 - x0, y1 - y0)
                mx2 = (x0 + midx) * 0.5 + side * seg_len * 0.07
                my2 = (y0 + midy) * 0.5 + seg_len * 0.02
                c = leaf_mid * rng.uniform(0.85, 1.25)
                if rng.random() < 0.07:
                    c = dry * rng.uniform(0.85, 1.05)
                color = np.clip(mix(c, leaf_dark, rng.uniform(0.0, 0.35)), 0, 1).ravel()
                stamp_blade(rgb, a,
                            [(x0, y0), (mx2, my2), (x1, y1)],
                            [5.0 + 4.5 * (1 - t), 4.0 + 3.5 * (1 - t), 1.2],
                            color)
                if rng.random() < 0.45:
                    stamp_blade(rgb, a,
                                [(x0, y0), (midx, midy)],
                                [1.2, 0.8],
                                np.clip(mix(color, leaf_light, 0.55), 0, 1))

    # Sunlit centre line.
    for i in range(26):
        t = rng.uniform(0.05, 0.95)
        y = base_y + (tip_y - base_y) * t
        stamp_ellipse(rgb, a, cx + rng.uniform(-4, 4), y,
                      rng.uniform(1.5, 3.0), rng.uniform(9.0, 22.0),
                      math.pi * 0.5,
                      np.clip(mix(rachis, leaf_light, rng.uniform(0.3, 0.8)), 0, 1),
                      edge=0.45)

    alpha = np.clip(a, 0.0, 1.0)
    alpha[alpha < 0.16] = 0.0
    save_image("palm_frond", rgb, alpha=alpha)
    return alpha


def make_grass_card(seed=181, size=512):
    rng = np.random.default_rng(seed)
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    a = np.zeros((size, size), dtype=np.float32)
    base = size * 0.98
    greens = [lin("#8c9c57"), lin("#a4b165"), lin("#b9b573"), lin("#728b45")]
    for i in range(72):
        x0 = size * 0.5 + rng.uniform(-size * 0.33, size * 0.33)
        h = rng.uniform(size * 0.35, size * 0.94)
        lean = rng.uniform(-size * 0.22, size * 0.22)
        w = rng.uniform(3.0, 7.5)
        pts = [(x0, base)]
        widths = [w]
        for k in range(1, 5):
            t = k / 4.0
            pts.append((x0 + lean * t * t + math.sin(t * 5 + i) * 3,
                        base - h * t))
            widths.append(w * (1.0 - 0.8 * t) + 0.4)
        col = greens[rng.integers(0, len(greens))] * rng.uniform(0.8, 1.15)
        stamp_blade(rgb, a, pts, widths, np.clip(col, 0, 1))
    save_image("grass_card", rgb, alpha=np.clip(a, 0, 1))


def make_bush_leaf(seed=191, size=1024):
    rng = np.random.default_rng(seed)
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    a = np.zeros((size, size), dtype=np.float32)
    greens = [lin("#2e5c2c"), lin("#3f7134"), lin("#56833b"), lin("#6f9445")]
    cx, cy = size * 0.5, size * 0.72
    for i in range(120):
        ang = rng.uniform(-math.pi * 0.92, -math.pi * 0.08)
        dist = rng.uniform(0, size * 0.34) ** 0.8
        x = cx + math.cos(ang) * dist
        y = cy + math.sin(ang) * dist * 1.15
        length = rng.uniform(size * 0.10, size * 0.28)
        width = length * rng.uniform(0.28, 0.45)
        col = greens[rng.integers(0, len(greens))] * rng.uniform(0.75, 1.2)
        stamp_leaf(rgb, a, x, y, length, width, ang + rng.uniform(-0.5, 0.5),
                   np.clip(col, 0, 1), midrib=np.clip(col * 1.35, 0, 1))
    save_image("bush_leaf", rgb, alpha=np.clip(a, 0, 1))


# ---------------------------------------------------------------------------
# Water / FX
# ---------------------------------------------------------------------------

def make_water_normal(seed=201, size=1024):
    rng = np.random.default_rng(seed)
    xs, ys = _uv(size)
    height = np.zeros((size, size), dtype=np.float32)
    waves = [
        (2.0, 0.0, 0.9), (3.0, 0.7, 0.6), (5.0, 2.1, 0.4),
        (8.0, 4.2, 0.26), (13.0, 1.3, 0.16), (21.0, 3.7, 0.10),
    ]
    for freq, ang, amp in waves:
        ca, sa = math.cos(ang), math.sin(ang)
        height += amp * np.sin(TAU * freq * (xs * ca + ys * sa) + rng.uniform(0, TAU))
    height += 0.15 * fbm(size, 32, 3, rng)
    save_image("water_normal", normal_from_height(height, 2.2), colorspace="Non-Color")


def make_foam(seed=211, size=512):
    rng = np.random.default_rng(seed)
    n = fbm(size, 6, 6, rng)
    fine = periodic_value_noise(size, 48, rng)
    f1, f2 = worley(size, 14, rng)
    cells = 1.0 - smoothstep(0.0, 0.10, f2 - f1)
    alpha = smoothstep(0.42, 0.72, n + 0.22 * fine) * (0.75 + 0.25 * cells)
    alpha *= 1.0 - smoothstep(0.72, 0.95, f2)
    rgb = np.ones((size, size, 3), dtype=np.float32)
    save_image("foam", rgb, alpha=np.clip(alpha, 0, 1))


def make_cloud(seed=221, size=1024):
    """2x2 atlas of soft cumulus puffs with fully transparent borders.

    Eight billboards sample the four cells with mirrored UVs, which keeps the
    preview sky from reading as repeated rectangles.
    """
    rng = np.random.default_rng(seed)
    cell = size // 2
    atlas = np.zeros((size, size, 3), dtype=np.float32)
    alpha = np.zeros((size, size), dtype=np.float32)
    ys, xs = np.mgrid[0:cell, 0:cell].astype(np.float32) / cell
    top = lin("#ffe6c8")
    mid = lin("#d7d5d2")
    base = lin("#8e98aa")

    for ci in range(4):
        body = np.zeros((cell, cell), dtype=np.float32)
        for _ in range(int(rng.integers(5, 8))):
            cx = 0.5 + rng.uniform(-0.26, 0.26)
            cy = 0.52 + rng.uniform(-0.10, 0.12)
            rx = rng.uniform(0.11, 0.23)
            ry = rx * rng.uniform(0.58, 0.95)
            d = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2
            body = np.maximum(body, np.clip(1.0 - d, 0.0, 1.0) ** 0.55)

        n = fbm(cell, 9, 5, rng)
        detail = fbm(cell, 34, 4, rng)
        body *= 0.58 + 0.42 * n
        body = smoothstep(0.16, 0.52, body * 0.72 + detail * 0.40)

        # Zero at every cell edge so the billboard never shows a seam.
        edge = (smoothstep(0.02, 0.14, xs) * (1.0 - smoothstep(0.86, 0.98, xs))
                * smoothstep(0.02, 0.11, ys) * (1.0 - smoothstep(0.86, 0.99, ys)))
        cell_a = np.clip(body * edge * 1.6, 0.0, 1.0)

        shade = smoothstep(0.18, 0.92, ys)[..., None]
        rgb = top[None, None, :] * (1.0 - shade) + base[None, None, :] * shade
        rgb = mix(rgb, np.broadcast_to(mid, rgb.shape),
                  0.30 * (1.0 - shade))
        rgb *= (0.92 + 0.14 * detail[..., None])

        ox, oy = (ci % 2) * cell, (ci // 2) * cell
        atlas[oy:oy + cell, ox:ox + cell] = rgb
        alpha[oy:oy + cell, ox:ox + cell] = cell_a

    save_image("cloud", atlas, alpha=alpha)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_KEYS = [
    "sand_base", "sand_rough", "sand_normal", "wet_sand_base", "seabed_base",
    "grass_base", "grass_rough", "grass_normal",
    "rock_base", "rock_rough", "rock_normal",
    "stone_base", "stone_rough", "stone_normal",
    "plaster_base", "plaster_normal",
    "wood_base", "wood_normal",
    "palm_bark_base", "palm_bark_rough", "palm_bark_normal",
    "palm_frond", "grass_card", "bush_leaf",
    "water_normal", "foam", "cloud",
]


def texture_paths():
    return {k: config.TEXTURE_DIR / f"{k}.png" for k in _KEYS}


def ensure_textures(force: bool = False):
    paths = texture_paths()
    if not force and all(p.exists() for p in paths.values()):
        print(f"[textures] reusing {len(paths)} island textures")
        return paths
    print("[textures] generating island texture set...", flush=True)
    make_sand()
    make_grass()
    make_basalt()
    make_sandstone()
    make_plaster()
    make_wood()
    make_palm_bark()
    make_palm_frond()
    make_grass_card()
    make_bush_leaf()
    make_water_normal()
    make_foam()
    make_cloud()
    print(f"[textures] wrote {len(paths)} textures to {config.TEXTURE_DIR}")
    return texture_paths()
