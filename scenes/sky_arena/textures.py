"""Procedural textures for the sky arena (numpy only, no network)."""
from __future__ import annotations

import math

import numpy as np

from arena_kit import config
from arena_kit.textures import (fbm, gray_rgb, normal_from_height,
                                periodic_value_noise, save_image, smoothstep,
                                stamp_ellipse, stamp_leaf, worley)

TAU = math.pi * 2.0


def _srgb(hex_color: str):
    h = hex_color.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)],
                    dtype=np.float32)


def _stamp_scalar(channel, cx, cy, rx, ry, angle, value, edge=0.10):
    """Soft ellipse into a single-channel map (stamp_ellipse is RGB-only)."""
    h, w = channel.shape
    ext = max(rx, ry) * (1.0 + edge) + 2
    x0 = max(0, int(cx - ext))
    x1 = min(w, int(cx + ext) + 1)
    y0 = max(0, int(cy - ext))
    y1 = min(h, int(cy + ext) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    ys, xs = np.mgrid[y0:y1, x0:x1]
    ca, sa = math.cos(angle), math.sin(angle)
    dx, dy = xs - cx, ys - cy
    xr = dx * ca + dy * sa
    yr = -dx * sa + dy * ca
    d = np.sqrt((xr / max(rx, 1e-6)) ** 2 + (yr / max(ry, 1e-6)) ** 2)
    alpha = 1.0 - smoothstep(1.0 - edge, 1.0, d)
    sub = channel[y0:y1, x0:x1]
    channel[y0:y1, x0:x1] = sub * (1.0 - alpha) + value * alpha


# ---------------------------------------------------------------------------
# Stone
# ---------------------------------------------------------------------------

def make_limestone(seed=401, size=1024, prefix="limestone",
                   tint=(1.0, 1.0, 1.0)):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    v = yy / size

    cloud = fbm(size, 3, 6, rng)
    warp = fbm(size, 5, 4, rng)
    fine = periodic_value_noise(size, 150, rng)
    pit, _ = worley(size, 34, rng)

    t = np.asarray(tint, dtype=np.float32)
    ivory = _srgb("#eadcc0") * t
    cream = _srgb("#d8c5a2") * t
    warm = _srgb("#c1a476") * t
    grey = _srgb("#948468") * t
    moss = _srgb("#6a7c45") * t

    val = np.clip(0.10 + 1.05 * cloud, 0.0, 1.0)
    col = cream[None, None, :] * (1.0 - val[..., None]) \
        + ivory[None, None, :] * val[..., None]
    strata = 0.5 + 0.5 * np.sin(v * TAU * 3.0 + (warp - 0.5) * 6.0
                                + (fine - 0.5) * 2.0)
    col = col * (1.0 - 0.16 * strata[..., None]) \
        + warm[None, None, :] * (0.16 * strata[..., None])
    grey_mix = 0.16 * smoothstep(0.50, 0.80, warp)
    col = col * (1.0 - grey_mix[..., None]) \
        + grey[None, None, :] * grey_mix[..., None]

    # Shallow weather pits and a hint of moss in the damp hollows.
    pits = 1.0 - smoothstep(0.0, 0.055, pit)
    col *= (1.0 - 0.22 * pits[..., None])
    damp = smoothstep(0.60, 0.86, cloud) * smoothstep(0.45, 0.15, pit)
    col = col * (1.0 - 0.24 * damp[..., None]) + moss[None, None, :] * (0.24 * damp[..., None])
    col *= (0.955 + 0.075 * fine[..., None])

    # Sparse hairline cracks.
    crack = np.zeros((size, size), dtype=np.float32)
    for _ in range(26):
        x = rng.uniform(0, size)
        y = rng.uniform(0, size)
        ang = rng.uniform(0, TAU)
        for _step in range(rng.integers(10, 28)):
            x += math.cos(ang) * rng.uniform(3.0, 7.0)
            y += math.sin(ang) * rng.uniform(3.0, 7.0)
            ang += rng.uniform(-0.55, 0.55)
            _stamp_scalar(crack, x % size, y % size, 2.2, 0.8, ang, 1.0,
                          edge=0.6)
    crack = np.clip(crack, 0.0, 1.0) * 0.5
    col *= (1.0 - 0.42 * crack[..., None])

    height = 0.22 * pits + 0.06 * fine + 0.14 * crack
    rough = np.clip(0.62 + 0.18 * fine + 0.10 * (1.0 - cloud)
                    + 0.10 * pits, 0.45, 0.94)

    save_image(f"{prefix}_base", np.clip(col, 0.0, 1.0), colorspace="sRGB")
    save_image(f"{prefix}_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image(f"{prefix}_normal", normal_from_height(height, 1.1),
               colorspace="Non-Color")


def make_paving(seed=411, size=1024, tiles=4):
    """Large worn flagstones with grout, chips and hairline cracks."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)

    cloud = fbm(size, 4, 5, rng)
    fine = periodic_value_noise(size, 220, rng)
    col = np.empty((size, size, 3), dtype=np.float32)
    height = np.zeros((size, size), dtype=np.float32)

    step = size // tiles
    stone_a = _srgb("#cfbd9b")
    stone_b = _srgb("#b8a37e")
    grout = _srgb("#6a604c")
    grout_moss = _srgb("#616b46")

    for ty in range(tiles):
        for tx in range(tiles):
            x0, x1 = tx * step, (tx + 1) * step
            y0, y1 = ty * step, (ty + 1) * step
            mixv = rng.uniform(0.0, 1.0)
            tint = stone_a * (1.0 - mixv) + stone_b * mixv
            tile_noise = rng.uniform(0.90, 1.04)
            col[y0:y1, x0:x1] = tint[None, None, :] * tile_noise

            # Bevel: 4 px grout channel then a soft lit edge.
            local_x = np.arange(step, dtype=np.float32)[None, :]
            local_y = np.arange(step, dtype=np.float32)[:, None]
            edge = np.minimum(np.minimum(local_x, step - 1 - local_x),
                              np.minimum(local_y, step - 1 - local_y))
            bevel = smoothstep(0.0, 16.0, edge)
            height[y0:y1, x0:x1] = 0.25 + 0.55 * bevel

            # Chipped corners.
            for _ in range(rng.integers(0, 3)):
                cx = x0 + rng.choice([rng.uniform(0, 16), rng.uniform(step - 16, step)])
                cy = y0 + rng.choice([rng.uniform(0, 16), rng.uniform(step - 16, step)])
                stamp_ellipse(col, np.ones_like(height), cx, cy,
                              rng.uniform(3.0, 10.0), rng.uniform(3.0, 8.0),
                              rng.uniform(0, TAU), grout * 0.9, edge=0.5)
                _stamp_scalar(height, cx, cy,
                              rng.uniform(3.0, 10.0), rng.uniform(3.0, 8.0),
                              rng.uniform(0, TAU), 0.0, edge=0.5)

            # Hairline cracks inside the slab.
            for _ in range(rng.integers(0, 3)):
                cx = x0 + rng.uniform(20, step - 20)
                cy = y0 + rng.uniform(20, step - 20)
                ang = rng.uniform(0, TAU)
                for _seg in range(rng.integers(4, 12)):
                    nx = cx + math.cos(ang) * rng.uniform(4.0, 9.0)
                    ny = cy + math.sin(ang) * rng.uniform(4.0, 9.0)
                    if not (x0 + 8 < nx < x1 - 8 and y0 + 8 < ny < y1 - 8):
                        break
                    stamp_ellipse(col, np.ones_like(height), nx, ny,
                                  3.2, 1.1, ang, grout * 0.75, edge=0.4)
                    _stamp_scalar(height, nx, ny, 3.2, 1.1, ang, 0.0,
                                  edge=0.5)
                    cx, cy = nx, ny
                    ang += rng.uniform(-0.6, 0.6)

    # Grout channels on the grid lines, with moss creeping into damp joints.
    gx = np.abs(((xx + step * 0.5) % step) - step * 0.5)
    gy = np.abs(((yy + step * 0.5) % step) - step * 0.5)
    line = 1.0 - smoothstep(2.0, 8.0, np.minimum(gx, gy))
    col = col * (1.0 - 0.68 * line[..., None]) + grout[None, None, :] * (0.68 * line[..., None])
    joint_moss = line * smoothstep(0.58, 0.86, cloud) * 0.45
    col = col * (1.0 - joint_moss[..., None]) + grout_moss[None, None, :] * joint_moss[..., None]
    height = height * (1.0 - line) + 0.05 * line

    col *= (0.90 + 0.16 * cloud[..., None])
    col *= (0.97 + 0.05 * fine[..., None])
    rough = np.clip(0.64 + 0.14 * fine + 0.10 * line + 0.08 * (1.0 - cloud),
                    0.5, 0.96)

    save_image("paving_base", np.clip(col, 0.0, 1.0), colorspace="sRGB")
    save_image("paving_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image("paving_normal", normal_from_height(height, 2.6),
               colorspace="Non-Color")


def make_rock(seed=421, size=1024):
    """Layered grey-brown rock for the floating hull and islets."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    v = yy / size

    cloud = fbm(size, 3, 5, rng)
    fine = periodic_value_noise(size, 170, rng)
    f1, f2 = worley(size, 26, rng)

    col = np.empty((size, size, 3), dtype=np.float32)
    dark = _srgb("#4f493b")
    mid = _srgb("#796c54")
    light = _srgb("#a08d6c")
    moss = _srgb("#5f7440")

    val = np.clip(0.15 + 0.95 * cloud, 0.0, 1.0)
    col[:] = dark[None, None, :] * (1.0 - val[..., None]) \
        + mid[None, None, :] * val[..., None]

    strata = 0.5 + 0.5 * np.sin(v * TAU * 7.5
                                + (cloud - 0.5) * 7.0
                                + (fine - 0.5) * 2.5)
    col = col * (1.0 - 0.24 * strata[..., None]) \
        + light[None, None, :] * (0.24 * strata[..., None])

    crack = 1.0 - smoothstep(0.0, 0.07, f2 - f1)
    col *= (1.0 - 0.62 * crack[..., None])
    damp = smoothstep(0.62, 0.88, cloud)
    col = col * (1.0 - 0.28 * damp[..., None]) + moss[None, None, :] * (0.28 * damp[..., None])
    col *= (0.92 + 0.14 * fine[..., None])

    height = 0.55 * crack + 0.25 * (1.0 - f1) + 0.12 * fine
    rough = np.clip(0.80 + 0.12 * fine + 0.05 * crack, 0.72, 0.98)

    save_image("rock_base", np.clip(col, 0.0, 1.0), colorspace="sRGB")
    save_image("rock_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image("rock_normal", normal_from_height(height, 2.2),
               colorspace="Non-Color")


# ---------------------------------------------------------------------------
# Foliage cards (alpha)
# ---------------------------------------------------------------------------

def make_grass_card(seed=431, size=512):
    rng = np.random.default_rng(seed)
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    alpha = np.zeros((size, size), dtype=np.float32)

    dark = _srgb("#3d6a2b")
    mid = _srgb("#5f9838")
    bright = _srgb("#9ccb57")
    tip = _srgb("#d2e78c")

    bases = [(int(size * f), int(size * 0.98)) for f in
             (0.18, 0.34, 0.50, 0.66, 0.82)]
    for bi, (bx, by) in enumerate(bases):
        count = 11 if bi in (2,) else 9
        for i in range(count):
            ang = -math.pi * 0.5 + rng.uniform(-0.95, 0.95)
            length = rng.uniform(0.36, 0.72) * size
            width = rng.uniform(0.034, 0.062) * size
            bx2 = bx + rng.uniform(-26, 26)
            stamp_leaf(rgb, alpha, bx2, by, length, width, ang, dark,
                       midrib=None)
            stamp_leaf(rgb, alpha, bx2 + math.cos(ang) * length * 0.12,
                       by + math.sin(ang) * length * 0.12,
                       length * 0.82, width * 0.55, ang, mid, midrib=bright)
            # Bright sunlit tip.
            tx = bx2 + math.cos(ang) * length * 0.38
            ty = by + math.sin(ang) * length * 0.38
            stamp_ellipse(rgb, alpha, tx, ty, width * 0.35, width * 0.9,
                          ang, tip, edge=0.5)

    # A few floating seed heads.
    for _ in range(7):
        x = rng.uniform(0.12, 0.88) * size
        y = rng.uniform(0.08, 0.35) * size
        stamp_ellipse(rgb, alpha, x, y, 3.0, 9.0,
                      rng.uniform(0, TAU), bright, edge=0.5)

    # Warm wildflower specks so the ground cover reads as a meadow.
    flower = _srgb("#f4d98f")
    flower_core = _srgb("#fff2c8")
    for _ in range(22):
        x = rng.uniform(0.10, 0.90) * size
        y = rng.uniform(0.10, 0.62) * size
        rr = rng.uniform(7.0, 13.0)
        stamp_ellipse(rgb, alpha, x, y, rr, rr * 0.72,
                      rng.uniform(0, TAU), flower, edge=0.5)
        stamp_ellipse(rgb, alpha, x, y, rr * 0.30, rr * 0.30, 0.0,
                      flower_core, edge=0.4)

    save_image("grass_card", np.clip(rgb, 0.0, 1.0), alpha=alpha,
               colorspace="sRGB")


def make_leaf_card(seed=441, size=512):
    """A hanging vine sprig used on architraves, gate and rim."""
    rng = np.random.default_rng(seed)
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    alpha = np.zeros((size, size), dtype=np.float32)

    deep = _srgb("#2e5c28")
    mid = _srgb("#519036")
    light = _srgb("#8fc653")
    gold = _srgb("#d0cf76")

    stem = _srgb("#5c5232")
    stamp_ellipse(rgb, alpha, size * 0.5, size * 0.5, 3.5, size * 0.44,
                  0.0, stem, edge=0.4)
    for i in range(13):
        t = 0.05 + i * 0.073
        cy = size * (0.5 + (t - 0.5) * 0.9)
        side = -1.0 if i % 2 == 0 else 1.0
        length = rng.uniform(0.18, 0.30) * size
        width = rng.uniform(0.08, 0.13) * size
        ang = side * rng.uniform(0.55, 1.15) + math.pi * 0.5
        cx = size * 0.5 + side * rng.uniform(8, 30)
        stamp_leaf(rgb, alpha, cx, cy, length, width, ang, deep)
        stamp_leaf(rgb, alpha, cx + math.cos(ang) * 8,
                   cy + math.sin(ang) * 8, length * 0.78, width * 0.72,
                   ang, mid, midrib=light)
        stamp_ellipse(rgb, alpha,
                      cx + math.cos(ang) * length * 0.30,
                      cy + math.sin(ang) * length * 0.30,
                      width * 0.24, width * 0.38, ang, light, edge=0.5)

    for _ in range(6):
        x = size * 0.5 + rng.uniform(-40, 40)
        y = rng.uniform(0.15, 0.85) * size
        stamp_ellipse(rgb, alpha, x, y, 3.0, 3.0, 0.0, gold, edge=0.4)

    save_image("leaf_card", np.clip(rgb, 0.0, 1.0), alpha=alpha,
               colorspace="sRGB")


def make_moss_card(seed=451, size=512):
    rng = np.random.default_rng(seed)
    rgb = np.zeros((size, size, 3), dtype=np.float32)
    alpha = np.zeros((size, size), dtype=np.float32)

    deep = _srgb("#3e5b28")
    mid = _srgb("#5f8438")
    light = _srgb("#8fb04f")
    pale = _srgb("#b3c977")

    for _ in range(90):
        a = rng.uniform(0, TAU)
        rad = rng.uniform(0, size * 0.30)
        cx = size * 0.5 + math.cos(a) * rad
        cy = size * 0.5 + math.sin(a) * rad * 0.8
        r = rng.uniform(0.05, 0.16) * size
        stamp_ellipse(rgb, alpha, cx, cy, r * rng.uniform(0.7, 1.4), r,
                      rng.uniform(0, TAU), deep, edge=0.55)
        stamp_ellipse(rgb, alpha, cx + rng.uniform(-8, 8),
                      cy + rng.uniform(-8, 8),
                      r * 0.72, r * 0.55, rng.uniform(0, TAU), mid,
                      edge=0.55)
    for _ in range(70):
        a = rng.uniform(0, TAU)
        rad = rng.uniform(0, size * 0.30)
        cx = size * 0.5 + math.cos(a) * rad
        cy = size * 0.5 + math.sin(a) * rad * 0.8
        stamp_ellipse(rgb, alpha, cx, cy, rng.uniform(1.5, 4.5),
                      rng.uniform(1.5, 4.5), 0.0,
                      light if rng.random() < 0.7 else pale, edge=0.5)

    save_image("moss_card", np.clip(rgb, 0.0, 1.0), alpha=alpha,
               colorspace="sRGB")


# ---------------------------------------------------------------------------
# Sky dome
# ---------------------------------------------------------------------------

def _fft_clouds(h, w, sigma, seed):
    rng = np.random.default_rng(seed)
    white = rng.standard_normal((h, w)).astype(np.float32)
    fy = np.fft.fftfreq(h).astype(np.float32)[:, None]
    fx = np.fft.rfftfreq(w).astype(np.float32)[None, :]
    filt = np.exp(-2.0 * (math.pi ** 2) * (sigma ** 2) * (fx * fx + fy * fy))
    field = np.fft.irfft2(np.fft.rfft2(white) * filt, s=(h, w)).astype(np.float32)
    field -= field.mean()
    field /= field.std() + 1e-6
    return np.clip(field * 0.30 + 0.50, 0.0, 1.0)


def _wrapped_add(target, cx, cy, rx, ry, weight):
    h, w = target.shape
    ext_x = int(rx * 2.6)
    ext_y = int(ry * 2.6)
    y0, y1 = max(0, cy - ext_y), min(h, cy + ext_y + 1)
    if y0 >= y1:
        return
    xs = np.arange(cx - ext_x, cx + ext_x + 1) % w
    ys = np.arange(y0, y1)
    dx = (np.arange(cx - ext_x, cx + ext_x + 1) - cx)[None, :] / max(rx, 1e-3)
    dy = (ys - cy)[:, None] / max(ry, 1e-3)
    blob = np.exp(-(dx * dx + dy * dy) * 1.25).astype(np.float32)
    target[y0:y1, xs] = np.maximum(target[y0:y1, xs], blob * weight)


def _stamp_cumulus(mask, cu, cv, size_px, seed, strength=1.0):
    h, w = mask.shape
    rng = np.random.default_rng(seed)
    cx, cy = int(cu * w), int(cv * h)
    for i in range(16):
        ox = rng.normal(0.0, size_px * 0.55)
        oy = rng.normal(0.0, size_px * 0.22)
        rx = size_px * rng.uniform(0.40, 0.95)
        ry = rx * rng.uniform(0.55, 0.82)
        _wrapped_add(mask, int(cx + ox), int(cy + oy), rx, ry,
                     strength * rng.uniform(0.55, 1.0))


def make_sky(seed=461, width=4096, height=2048):
    rng = np.random.default_rng(seed)
    vy = np.linspace(0.0, 1.0, height, dtype=np.float32)
    vy2 = vy[:, None]
    vy3 = vy[:, None, None]
    ux = np.linspace(0.0, 1.0, width, dtype=np.float32)

    stops_v = np.array([0.00, 0.12, 0.26, 0.38, 0.455, 0.500, 0.535,
                        0.60, 0.72, 1.00], dtype=np.float32)
    stops_c = np.array([_srgb(h) for h in (
        "#2a6cb2", "#3a83c0", "#57a3d4", "#8cc8e4", "#d7e9e8",
        "#ffedc8", "#c7e0e2", "#a9c9d2", "#8fa9b7", "#6f8d9e")],
        dtype=np.float32)
    col = np.empty((height, width, 3), dtype=np.float32)
    for ch in range(3):
        col[..., ch] = np.interp(vy, stops_v, stops_c[:, ch])[:, None]

    cloud_a = _fft_clouds(height, width, 30.0, seed + 1)
    cloud_b = _fft_clouds(height, width, 11.0, seed + 2)
    cloud_c = _fft_clouds(height, width, 4.5, seed + 3)
    cloud_d = _fft_clouds(height, width, 20.0, seed + 4)

    # --- cumulus band above the horizon -----------------------------------
    mixed = 0.55 * cloud_a + 0.30 * cloud_b + 0.15 * cloud_c
    puffy = smoothstep(0.555, 0.615, mixed)
    loft = 0.45 + 0.55 * smoothstep(0.12, 0.40, vy2)
    amount = puffy * loft
    shade = smoothstep(0.38, 0.70, cloud_b)
    cloud_col = (np.array([0.71, 0.79, 0.87], dtype=np.float32)[None, None, :]
                 * (1.0 - shade[..., None])
                 + np.array([1.0, 0.97, 0.905], dtype=np.float32)[None, None, :]
                 * shade[..., None])
    above = 1.0 - smoothstep(0.494, 0.512, vy2)
    a_cloud = np.clip(amount * 0.86 * above, 0.0, 1.0)
    col = col * (1.0 - a_cloud[..., None]) + cloud_col * a_cloud[..., None]

    # --- high cirrus ------------------------------------------------------
    cirrus = smoothstep(0.58, 0.80, cloud_d) * 0.18
    cirrus = cirrus * smoothstep(0.06, 0.16, vy2) \
        * (1.0 - smoothstep(0.36, 0.46, vy2))
    col = col * (1.0 - cirrus[..., None]) \
        + np.array([0.98, 0.99, 1.0], dtype=np.float32)[None, None, :] \
        * cirrus[..., None]

    # --- cloud sea below the horizon --------------------------------------
    billow = 0.62 * cloud_d + 0.24 * cloud_b + 0.14 * cloud_c
    sea_shade = smoothstep(0.44, 0.72, np.roll(billow, 9, axis=0))
    sea_col = (np.array([0.50, 0.62, 0.72], dtype=np.float32)[None, None, :]
               * (1.0 - sea_shade[..., None])
               + np.array([0.99, 0.965, 0.905], dtype=np.float32)[None, None, :]
               * sea_shade[..., None])
    depth = smoothstep(0.70, 1.0, vy2)
    sea_col = sea_col * (1.0 - 0.30 * depth[..., None])
    # Fade the cloud tops into the horizon glow instead of a hard seam.
    horizon_glow = np.exp(-((vy2 - 0.505) / 0.055) ** 2)
    sea_col = sea_col * (1.0 - 0.55 * horizon_glow[..., None]) \
        + np.array([1.0, 0.93, 0.80], dtype=np.float32)[None, None, :] \
        * (0.55 * horizon_glow[..., None])
    a_sea = smoothstep(0.504, 0.600, vy2) * 0.95
    col = col * (1.0 - a_sea[..., None]) + sea_col * a_sea[..., None]

    # --- hand-placed cumulus in the hero view -----------------------------
    mask = np.zeros((height, width), dtype=np.float32)
    _stamp_cumulus(mask, 0.205, 0.450, height * 0.085, seed + 11, 0.85)
    _stamp_cumulus(mask, 0.285, 0.425, height * 0.060, seed + 12, 0.70)
    _stamp_cumulus(mask, 0.372, 0.462, height * 0.048, seed + 13, 0.55)
    _stamp_cumulus(mask, 0.105, 0.400, height * 0.075, seed + 14, 0.75)
    _stamp_cumulus(mask, 0.475, 0.440, height * 0.068, seed + 15, 0.60)
    mask = smoothstep(0.08, 0.48, mask) * 0.9
    shade2 = np.clip(np.roll(mask, 12, axis=0) * 0.9, 0.0, 1.0)
    top_col = np.array([1.0, 0.985, 0.94], dtype=np.float32)[None, None, :]
    bot_col = np.array([0.68, 0.76, 0.84], dtype=np.float32)[None, None, :]
    puff_col = bot_col * (1.0 - shade2[..., None]) + top_col * shade2[..., None]
    col = col * (1.0 - mask[..., None]) + puff_col * mask[..., None]

    # --- horizon haze -----------------------------------------------------
    haze = (np.exp(-((vy2 - 0.500) / 0.032) ** 2) * 0.45)
    col = col * (1.0 - haze[..., None]) \
        + np.array([1.0, 0.93, 0.80], dtype=np.float32)[None, None, :] \
        * haze[..., None]

    # --- sun disc and glow (matches SUN_POS: azimuth 211, elevation 26) ---
    du = np.abs(ux - 0.5861)
    du = np.minimum(du, 1.0 - du)
    dv = np.abs(vy - 0.3556)
    deg = np.sqrt((du[None, :] * 360.0) ** 2
                  + (dv[:, None] * 180.0) ** 2) / 90.0
    disc = np.exp(-(deg / 0.010) ** 2)[..., None] * 1.8
    glow = (np.exp(-(deg / 0.10) ** 2) * 0.35
            + np.exp(-(deg / 0.34) ** 2) * 0.15)[..., None]
    sun_col = np.array([1.0, 0.94, 0.80], dtype=np.float32)[None, None, :]
    col = col + sun_col * (disc + glow)

    save_image("sky", np.clip(col, 0.0, 1.0), colorspace="sRGB")


def ensure_textures(force=False):
    expected = [
        "paving_base", "paving_rough", "paving_normal",
        "limestone_base", "limestone_rough", "limestone_normal",
        "rock_base", "rock_rough", "rock_normal",
        "grass_card", "leaf_card", "moss_card", "sky",
    ]
    if not force and all((config.TEXTURE_DIR / f"{name}.png").exists()
                         for name in expected):
        return {name: config.TEXTURE_DIR / f"{name}.png" for name in expected}

    print("[textures] generating sky arena textures ...")
    make_paving()
    make_limestone()
    make_rock()
    make_grass_card()
    make_leaf_card()
    make_moss_card()
    make_sky()
    print("[textures] done")
    return {name: config.TEXTURE_DIR / f"{name}.png" for name in expected}
