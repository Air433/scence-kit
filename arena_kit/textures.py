"""Offline procedural PBR texture generation (numpy, no network needed)."""
from __future__ import annotations

import math
from pathlib import Path

import bpy
import numpy as np

from . import config

TAU = math.pi * 2.0


# ---------------------------------------------------------------------------
# Small math helpers
# ---------------------------------------------------------------------------

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a + 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def mix(a, b, t):
    t = t[..., None] if (np.ndim(t) == 2 and np.ndim(a) == 3) else t
    return a * (1.0 - t) + b * t


def lin(hex_color: str):
    return np.array(config.hex_rgb(hex_color), dtype=np.float32)


# ---------------------------------------------------------------------------
# Tileable noise
# ---------------------------------------------------------------------------

def periodic_value_noise(size: int, freq: int, rng: np.random.Generator):
    freq = max(1, int(freq))
    grid = rng.random((freq, freq)).astype(np.float32)
    xs = np.linspace(0.0, freq, size, endpoint=False, dtype=np.float32)
    ys = np.linspace(0.0, freq, size, endpoint=False, dtype=np.float32)
    x0 = np.floor(xs).astype(np.int64) % freq
    y0 = np.floor(ys).astype(np.int64) % freq
    x1 = (x0 + 1) % freq
    y1 = (y0 + 1) % freq
    fx = xs - np.floor(xs)
    fy = ys - np.floor(ys)
    sx = fx * fx * (3.0 - 2.0 * fx)
    sy = fy * fy * (3.0 - 2.0 * fy)
    X0 = x0[None, :]
    X1 = x1[None, :]
    SX = sx[None, :]
    Y0 = y0[:, None]
    Y1 = y1[:, None]
    SY = sy[:, None]
    top = grid[Y0, X0] * (1.0 - SX) + grid[Y0, X1] * SX
    bot = grid[Y1, X0] * (1.0 - SX) + grid[Y1, X1] * SX
    return top * (1.0 - SY) + bot * SY


def periodic_aniso_noise(size: int, fx: int, fy: int, rng: np.random.Generator):
    fx = max(1, int(fx))
    fy = max(1, int(fy))
    grid = rng.random((fy, fx)).astype(np.float32)
    xs = np.linspace(0.0, fx, size, endpoint=False, dtype=np.float32)
    ys = np.linspace(0.0, fy, size, endpoint=False, dtype=np.float32)
    x0 = np.floor(xs).astype(np.int64) % fx
    y0 = np.floor(ys).astype(np.int64) % fy
    x1 = (x0 + 1) % fx
    y1 = (y0 + 1) % fy
    fxr = xs - np.floor(xs)
    fyr = ys - np.floor(ys)
    sx = (fxr * fxr * (3.0 - 2.0 * fxr))[None, :]
    sy = (fyr * fyr * (3.0 - 2.0 * fyr))[:, None]
    X0, X1 = x0[None, :], x1[None, :]
    Y0, Y1 = y0[:, None], y1[:, None]
    top = grid[Y0, X0] * (1.0 - sx) + grid[Y0, X1] * sx
    bot = grid[Y1, X0] * (1.0 - sx) + grid[Y1, X1] * sx
    return top * (1.0 - sy) + bot * sy


def fbm(size: int, base_freq: int, octaves: int, rng: np.random.Generator,
        gain: float = 0.5, lacunarity: float = 2.0):
    total = np.zeros((size, size), dtype=np.float32)
    amp = 1.0
    norm = 0.0
    f = base_freq
    for _ in range(octaves):
        total += amp * periodic_value_noise(size, int(round(f)), rng)
        norm += amp
        amp *= gain
        f *= lacunarity
    return total / max(norm, 1e-9)


def worley(size: int, cells: int, rng: np.random.Generator):
    pts = rng.random((cells, cells, 2)).astype(np.float32)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    xs = xs / size * cells
    ys = ys / size * cells
    f1 = np.full((size, size), 9.0, dtype=np.float32)
    f2 = np.full((size, size), 9.0, dtype=np.float32)
    for cy in range(cells):
        for cx in range(cells):
            px = cx + pts[cy, cx, 0]
            py = cy + pts[cy, cx, 1]
            dx = np.abs(xs - px)
            dx = np.minimum(dx, cells - dx)
            dy = np.abs(ys - py)
            dy = np.minimum(dy, cells - dy)
            d = np.sqrt(dx * dx + dy * dy)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            f1 = np.where(closer, d, f1)
    return f1, f2


def normal_from_height(height, strength: float = 2.0):
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5
    nx = -dx * strength
    ny = dy * strength
    nz = np.ones_like(height)
    length = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
    return np.stack((nx / length, ny / length, nz / length), axis=-1) * 0.5 + 0.5


def gray_rgb(gray):
    return np.repeat(gray[..., None], 3, axis=-1)


# ---------------------------------------------------------------------------
# Image save
# ---------------------------------------------------------------------------

def save_image(name: str, rgb, alpha=None, colorspace: str = "SRGB"):
    if rgb.ndim == 2:
        rgb = gray_rgb(rgb)
    h, w, _ = rgb.shape
    arr = np.ones((h, w, 4), dtype=np.float32)
    arr[..., :3] = np.clip(rgb, 0.0, 1.0)
    if alpha is not None:
        arr[..., 3] = np.clip(alpha, 0.0, 1.0)
    arr = arr[::-1].copy()
    img = bpy.data.images.new(name, width=w, height=h, alpha=True, float_buffer=False)
    img.colorspace_settings.name = colorspace
    img.pixels.foreach_set(arr.ravel())
    path = config.TEXTURE_DIR / f"{name}.png"
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return path


# ---------------------------------------------------------------------------
# Painting helpers for foliage atlases
# ---------------------------------------------------------------------------

def _over(dst_rgb, dst_a, color, alpha):
    out_a = alpha + dst_a * (1.0 - alpha)
    safe = np.maximum(out_a, 1e-6)
    out_rgb = (color * alpha[..., None] + dst_rgb * dst_a[..., None] * (1.0 - alpha[..., None])) / safe[..., None]
    return out_rgb, out_a


def stamp_ellipse(rgb, a, cx, cy, rx, ry, angle, color, edge=0.10):
    h, w = a.shape
    ext = max(rx, ry) * (1.0 + edge) + 2
    x0 = max(0, int(cx - ext))
    x1 = min(w, int(cx + ext) + 1)
    y0 = max(0, int(cy - ext))
    y1 = min(h, int(cy + ext) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    ys, xs = np.mgrid[y0:y1, x0:x1]
    ca, sa = math.cos(angle), math.sin(angle)
    dx = xs - cx
    dy = ys - cy
    xr = dx * ca + dy * sa
    yr = -dx * sa + dy * ca
    d = np.sqrt((xr / max(rx, 1e-6)) ** 2 + (yr / max(ry, 1e-6)) ** 2)
    alpha = 1.0 - smoothstep(1.0 - edge, 1.0, d)
    if alpha.max() <= 1e-4:
        return
    sub_rgb, sub_a = _over(rgb[y0:y1, x0:x1], a[y0:y1, x0:x1],
                           np.asarray(color, dtype=np.float32), alpha.astype(np.float32))
    rgb[y0:y1, x0:x1] = sub_rgb
    a[y0:y1, x0:x1] = sub_a


def stamp_leaf(rgb, a, cx, cy, length, width, angle, color, midrib=None):
    stamp_ellipse(rgb, a, cx, cy, length * 0.5, width * 0.5, angle, color, edge=0.12)
    if midrib is not None:
        steps = 6
        ca, sa = math.cos(angle), math.sin(angle)
        for i in range(steps):
            t0 = -0.45 + 0.9 * i / steps
            t1 = -0.45 + 0.9 * (i + 1) / steps
            x0 = cx + ca * length * t0
            y0 = cy + sa * length * t0
            x1 = cx + ca * length * t1
            y1 = cy + sa * length * t1
            stamp_ellipse(rgb, a, (x0 + x1) * 0.5, (y0 + y1) * 0.5,
                          length * 0.055, max(1.2, width * 0.055), angle, midrib,
                          edge=0.25)


def stamp_blade(rgb, a, pts, widths, color):
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        seg_len = math.hypot(x1 - x0, y1 - y0)
        angle = math.atan2(y1 - y0, x1 - x0) + math.pi * 0.5
        w0 = widths[i]
        w1 = widths[i + 1]
        steps = max(1, int(seg_len / max(1.0, min(w0, w1) * 0.9)))
        for s in range(steps):
            t = (s + 0.5) / steps
            cx = x0 + (x1 - x0) * t
            cy = y0 + (y1 - y0) * t
            w = w0 + (w1 - w0) * t
            stamp_ellipse(rgb, a, cx, cy, w * 0.5, seg_len / steps * 0.65, angle,
                          color, edge=0.25)


# ---------------------------------------------------------------------------
# Individual textures
# ---------------------------------------------------------------------------

def make_stone(seed=11, size=1024, prefix="stone", tint=(1.0, 1.0, 1.0)):
    rng = np.random.default_rng(seed)
    base = fbm(size, 3, 6, rng)
    grain = fbm(size, 28, 3, rng)
    f1, f2 = worley(size, 8, rng)
    edge = smoothstep(0.0, 0.065, f2 - f1)
    crack = 1.0 - edge
    moss_n = fbm(size, 3, 5, rng)
    fine = periodic_value_noise(size, 96, rng)

    t = np.array(tint, dtype=np.float32)
    stone_a = lin("#4a4c45") * t
    stone_b = lin("#8a8b82") * t
    stone_c = lin("#a39c8c") * t
    moss = lin("#46692c")
    moss_light = lin("#729641")

    v = np.clip(0.15 + 0.95 * base, 0.0, 1.0)
    col = stone_a[None, None, :] * (1.0 - v[..., None]) + stone_b[None, None, :] * v[..., None]
    bright = smoothstep(0.55, 0.85, base) * 0.55
    col = mix(col, np.broadcast_to(stone_c, col.shape), bright)
    col *= (1.0 - 0.70 * crack[..., None])
    col *= (0.84 + 0.30 * grain[..., None])
    col *= (0.96 + 0.08 * fine[..., None])

    moss_mask = smoothstep(0.50, 0.78, moss_n) * (0.35 + 0.65 * smoothstep(0.0, 0.5, crack))
    moss_col = mix(np.broadcast_to(moss, col.shape), np.broadcast_to(moss_light, col.shape),
                   smoothstep(0.4, 0.8, grain))
    col = mix(col, moss_col, (0.75 * moss_mask)[..., None])

    height = 0.45 * base + 0.25 * grain + 0.15 * fine - 0.45 * crack + 0.30 * moss_mask
    rough = 0.68 + 0.18 * grain + 0.16 * crack - 0.12 * moss_mask
    rough = np.clip(rough, 0.35, 0.98)

    save_image(f"{prefix}_base", col, colorspace="sRGB")
    save_image(f"{prefix}_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image(f"{prefix}_normal", normal_from_height(height, 2.4), colorspace="Non-Color")


def make_stone_warm(seed=12, size=1024):
    make_stone(seed=seed, size=size, prefix="stone_warm", tint=(1.10, 1.02, 0.88))


def make_stone_dark(seed=13, size=1024):
    make_stone(seed=seed, size=size, prefix="stone_dark", tint=(0.58, 0.62, 0.55))


def make_ground(seed=21, size=1024):
    rng = np.random.default_rng(seed)
    base = fbm(size, 3, 6, rng)
    fine = fbm(size, 40, 3, rng)
    moss_n = fbm(size, 5, 4, rng)

    soil = lin("#33291c")
    soil_light = lin("#5a4a30")
    green = lin("#415c27")
    dead_leaf = lin("#8a6a35")
    dark = lin("#1e1a12")

    v = np.clip(0.15 + 0.9 * base, 0.0, 1.0)
    col = soil[None, None, :] * (1.0 - v[..., None]) + soil_light[None, None, :] * v[..., None]
    col = mix(col, np.broadcast_to(green, col.shape), (0.65 * smoothstep(0.5, 0.8, moss_n))[..., None])
    col *= (0.72 + 0.5 * fine[..., None])

    # leaf litter specks
    rgb = col.copy()
    alpha = np.ones((size, size), dtype=np.float32)
    for _ in range(900):
        cx = rng.uniform(0, size)
        cy = rng.uniform(0, size)
        rx = rng.uniform(2.0, 8.0)
        ry = rx * rng.uniform(0.35, 0.8)
        ang = rng.uniform(0, TAU)
        c = dead_leaf if rng.random() < 0.55 else dark
        c = np.clip(c * rng.uniform(0.75, 1.25), 0, 1)
        stamp_ellipse(rgb, alpha, cx, cy, rx, ry, ang, c, edge=0.35)
    col = rgb

    height = 0.5 * base + 0.25 * fine
    rough = np.clip(0.82 + 0.14 * fine, 0.6, 1.0)

    save_image("ground_base", col, colorspace="sRGB")
    save_image("ground_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image("ground_normal", normal_from_height(height, 1.4), colorspace="Non-Color")


def make_bark(seed=31, size=1024):
    rng = np.random.default_rng(seed)
    ridged = (periodic_aniso_noise(size, 26, 3, rng) * 0.55
              + periodic_aniso_noise(size, 52, 6, rng) * 0.30
              + periodic_aniso_noise(size, 110, 12, rng) * 0.15)
    cracks = 1.0 - smoothstep(0.18, 0.34, ridged)
    fine = fbm(size, 30, 3, rng)
    moss_n = fbm(size, 4, 4, rng)

    bark_dark = lin("#2e2318")
    bark_mid = lin("#5c4934")
    bark_light = lin("#8a7356")
    moss = lin("#4b6b2f")

    v = np.clip(ridged * 1.15, 0.0, 1.0)
    col = bark_dark[None, None, :] * (1.0 - v[..., None]) + bark_mid[None, None, :] * v[..., None]
    col = mix(col, np.broadcast_to(bark_light, col.shape),
              (0.5 * smoothstep(0.62, 0.9, ridged))[..., None])
    col *= (1.0 - 0.55 * cracks[..., None]) * (0.82 + 0.36 * fine[..., None])
    col = mix(col, np.broadcast_to(moss, col.shape),
              (0.55 * smoothstep(0.52, 0.8, moss_n))[..., None])

    height = 0.75 * ridged + 0.25 * fine
    rough = np.clip(0.78 + 0.18 * fine - 0.08 * ridged, 0.55, 1.0)

    save_image("bark_base", col, colorspace="sRGB")
    save_image("bark_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image("bark_normal", normal_from_height(height, 3.2), colorspace="Non-Color")


def make_moss(seed=41, size=512):
    rng = np.random.default_rng(seed)
    base = fbm(size, 5, 5, rng)
    fine = fbm(size, 40, 3, rng)
    dark = lin("#2f421e")
    mid = lin("#54742f")
    light = lin("#7f9e46")
    v = np.clip(0.1 + base, 0, 1)
    col = dark[None, None, :] * (1 - v[..., None]) + mid[None, None, :] * v[..., None]
    col = mix(col, np.broadcast_to(light, col.shape),
              (0.5 * smoothstep(0.55, 0.85, fine))[..., None])
    height = 0.6 * base + 0.4 * fine
    save_image("moss_base", col, colorspace="sRGB")
    save_image("moss_normal", normal_from_height(height, 2.0), colorspace="Non-Color")


def make_leaf_cluster(seed=51, size=1024):
    rng = np.random.default_rng(seed)
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    alpha = np.zeros((size, size), dtype=np.float32)

    greens = [lin("#2c4a1e"), lin("#3d6b25"), lin("#4d7f2e"),
              lin("#5f9438"), lin("#74a745"), lin("#8bb954"),
              lin("#a3b957"), lin("#b8c06a")]
    cx0 = cy0 = size * 0.5
    radius = size * 0.46

    # thin twigs
    for _ in range(8):
        ang = rng.uniform(0, TAU)
        length = rng.uniform(radius * 0.5, radius * 0.95)
        pts = []
        for i in range(7):
            t = i / 6.0
            wob = math.sin(t * 5.0 + ang) * 10.0
            pts.append((cx0 + math.cos(ang) * length * t + wob,
                        cy0 + math.sin(ang) * length * t - wob * 0.5))
        stamp_blade(rgb, alpha, pts, [size * 0.008] * 7, lin("#4a3a26"))

    for _ in range(190):
        r = radius * (rng.random() ** 0.36)
        ang = rng.uniform(0, TAU)
        cx = cx0 + math.cos(ang) * r
        cy = cy0 + math.sin(ang) * r
        length = rng.uniform(size * 0.050, size * 0.145)
        width = length * rng.uniform(0.34, 0.60)
        leaf_ang = rng.uniform(0, TAU)
        color = greens[min(len(greens) - 1,
                           int(rng.random() ** 1.6 * len(greens)))]
        color = np.clip(color * rng.uniform(0.82, 1.18), 0, 1)
        midrib = np.clip(color * 0.52, 0, 1)
        stamp_leaf(rgb, alpha, cx, cy, length, width, leaf_ang, color, midrib)

    save_image("leaf_cluster", rgb, alpha=alpha, colorspace="sRGB")


def make_leaf_litter(seed=52, size=512):
    rng = np.random.default_rng(seed)
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    alpha = np.zeros((size, size), dtype=np.float32)

    browns = [lin("#4d3418"), lin("#5f4324"), lin("#73502b"),
              lin("#8a6434"), lin("#9c7a3e"), lin("#ad8c46"),
              lin("#6b5a28")]
    cx0 = cy0 = size * 0.5
    radius = size * 0.47
    for _ in range(160):
        r = radius * (rng.random() ** 0.42)
        ang = rng.uniform(0, TAU)
        cx = cx0 + math.cos(ang) * r
        cy = cy0 + math.sin(ang) * r
        length = rng.uniform(size * 0.06, size * 0.16)
        width = length * rng.uniform(0.36, 0.60)
        color = browns[rng.integers(0, len(browns))]
        color = np.clip(color * rng.uniform(0.80, 1.20), 0, 1)
        midrib = np.clip(color * 0.55, 0, 1)
        stamp_leaf(rgb, alpha, cx, cy, length, width,
                   rng.uniform(0, TAU), color, midrib)
    save_image("leaf_litter", rgb, alpha=alpha, colorspace="sRGB")


def make_fern(seed=61, size=1024):
    rng = np.random.default_rng(seed)
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    alpha = np.zeros((size, size), dtype=np.float32)

    stem = lin("#3c5a23")
    greens = [lin("#2f5420"), lin("#426f2b"), lin("#558436"), lin("#6a9a42")]
    base_x = size * 0.5
    base_y = size * 0.98

    for f in range(7):
        ang = -math.pi * 0.5 + rng.uniform(-0.85, 0.85)
        length = rng.uniform(size * 0.42, size * 0.78)
        bend = rng.uniform(-0.25, 0.25)
        pts = []
        for i in range(11):
            t = i / 10.0
            a = ang + bend * t
            pts.append((base_x + math.cos(a) * length * t,
                        base_y + math.sin(a) * length * t))
        stamp_blade(rgb, alpha, pts, [max(1.2, size * 0.006 * (1 - 0.6 * i / 10)) for i in range(11)],
                    stem)
        for i in range(1, 10):
            t = i / 10.0
            px, py = pts[i]
            leaf_len = size * 0.075 * (1.0 - 0.55 * t) * rng.uniform(0.8, 1.2)
            for side in (-1, 1):
                la = ang + side * math.pi * 0.52 + rng.uniform(-0.15, 0.15)
                lx = px + math.cos(la) * leaf_len * 0.55
                ly = py + math.sin(la) * leaf_len * 0.55
                color = greens[rng.integers(0, len(greens))]
                color = np.clip(color * rng.uniform(0.8, 1.15), 0, 1)
                stamp_leaf(rgb, alpha, lx, ly, leaf_len, leaf_len * 0.34, la, color)

    save_image("fern", rgb, alpha=alpha, colorspace="sRGB")


def make_grass(seed=71, size=1024):
    rng = np.random.default_rng(seed)
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    alpha = np.zeros((size, size), dtype=np.float32)
    greens = [lin("#3c5a22"), lin("#4d6f2c"), lin("#628a3a"),
              lin("#789a47"), lin("#8c9a4a")]

    for _ in range(26):
        base_x = size * rng.uniform(0.12, 0.88)
        base_y = size * 1.01
        length = size * rng.uniform(0.34, 0.9)
        bend = rng.uniform(-0.32, 0.32)
        pts = []
        widths = []
        for i in range(13):
            t = i / 12.0
            x = base_x + bend * size * t * t + math.sin(t * 5 + base_x) * size * 0.012
            y = base_y - length * t
            pts.append((x, y))
            widths.append(max(1.1, size * 0.010 * (1.0 - 0.85 * t)))
        color = greens[rng.integers(0, len(greens))]
        color = np.clip(color * rng.uniform(0.75, 1.2), 0, 1)
        stamp_blade(rgb, alpha, pts, widths, color)

    save_image("grass", rgb, alpha=alpha, colorspace="sRGB")


def make_wood(seed=81, size=512):
    rng = np.random.default_rng(seed)
    ridged = (periodic_aniso_noise(size, 18, 4, rng) * 0.6
              + periodic_aniso_noise(size, 44, 7, rng) * 0.4)
    fine = fbm(size, 30, 3, rng)
    dark = lin("#2b2118")
    mid = lin("#5a4632")
    light = lin("#8c7352")
    v = np.clip(ridged, 0, 1)
    col = dark[None, None, :] * (1 - v[..., None]) + mid[None, None, :] * v[..., None]
    col = mix(col, np.broadcast_to(light, col.shape),
              (0.45 * smoothstep(0.65, 0.9, ridged))[..., None])
    col *= (0.8 + 0.4 * fine[..., None])
    save_image("wood_base", col, colorspace="sRGB")
    save_image("wood_normal", normal_from_height(0.7 * ridged + 0.3 * fine, 2.0),
               colorspace="Non-Color")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def ensure_textures(force: bool = False):
    expected = [
        "stone_base", "stone_rough", "stone_normal",
        "stone_warm_base", "stone_warm_rough", "stone_warm_normal",
        "stone_dark_base", "stone_dark_rough", "stone_dark_normal",
        "ground_base", "ground_rough", "ground_normal",
        "bark_base", "bark_rough", "bark_normal",
        "moss_base", "moss_normal", "wood_base", "wood_normal",
        "leaf_cluster", "leaf_litter", "fern", "grass",
    ]
    if not force and all((config.TEXTURE_DIR / f"{n}.png").exists() for n in expected):
        return {n: config.TEXTURE_DIR / f"{n}.png" for n in expected}

    print("[textures] generating procedural PBR textures ...")
    make_stone()
    make_stone_warm()
    make_stone_dark()
    make_ground()
    make_bark()
    make_moss()
    make_wood()
    make_leaf_cluster()
    make_leaf_litter()
    make_fern()
    make_grass()
    print("[textures] done")
    return {n: config.TEXTURE_DIR / f"{n}.png" for n in expected}
