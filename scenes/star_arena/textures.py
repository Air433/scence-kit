"""Procedural textures for the star arena: ivory marble and a warm sky dome."""
from __future__ import annotations

import math

import numpy as np

from arena_kit import config
from arena_kit.textures import (fbm, gray_rgb, lin, mix, normal_from_height,
                                periodic_value_noise, save_image, smoothstep)

TAU = math.pi * 2.0


def make_marble(seed=311, size=1024, prefix="marble", tint=(1.0, 1.0, 1.0)):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    u = xx / size
    v = yy / size

    cloud = fbm(size, 3, 6, rng)
    warp = fbm(size, 5, 4, rng)
    fine = periodic_value_noise(size, 140, rng)

    t = np.asarray(tint, dtype=np.float32)
    ivory = lin("#fffdf9") * t
    cream = lin("#f7f2e8") * t
    warm = lin("#ece3d4") * t
    vein_col = lin("#a89f90") * t
    gold_fleck = lin("#c9a35a") * t

    val = np.clip(0.25 + 0.90 * cloud, 0.0, 1.0)
    col = mix(np.broadcast_to(ivory, (size, size, 3)),
              np.broadcast_to(cream, (size, size, 3)), val)
    col = mix(col, np.broadcast_to(warm, col.shape),
              (0.10 * smoothstep(0.55, 0.90, warp))[..., None])

    # Three warped vein systems: broad grey rivers plus fine hairlines.
    vein = np.zeros((size, size), dtype=np.float32)
    for freq, amp, warp_amt, width in (
            (1.7, 0.62, 1.9, 0.028), (4.1, 0.28, 2.4, 0.018),
            (8.3, 0.12, 1.2, 0.010)):
        phase = (u * TAU * freq + (warp - 0.5) * TAU * warp_amt
                 + (fine - 0.5) * TAU * 0.55 + v * TAU * 0.75)
        line = 1.0 - smoothstep(0.0, width, np.abs(np.sin(phase)))
        vein = np.maximum(vein, line * amp)
    vein = np.clip(vein * (0.70 + 0.50 * fine), 0.0, 1.0)
    col = mix(col, np.broadcast_to(vein_col, col.shape), (0.46 * vein)[..., None])
    col *= (0.965 + 0.070 * fine[..., None])

    # Sparse warm flecks, like inclusions in polished stone.
    fleck = rng.random((size, size)).astype(np.float32)
    fleck = smoothstep(0.9994, 0.9999, fleck)
    col += gold_fleck[None, None, :] * (0.55 * fleck[..., None])
    col = np.clip(col, 0.0, 1.0)

    height = 0.10 * vein + 0.05 * fine
    rough = np.clip(0.15 + 0.09 * fine + 0.16 * vein + 0.05 * (1.0 - cloud),
                    0.10, 0.45)

    save_image(f"{prefix}_base", col, colorspace="sRGB")
    save_image(f"{prefix}_rough", gray_rgb(rough), colorspace="Non-Color")
    save_image(f"{prefix}_normal", normal_from_height(height, 0.9),
               colorspace="Non-Color")


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


def _stamp_dot(rgb, cx, cy, sigma, color, intensity):
    h, w, _ = rgb.shape
    ext = max(2, int(sigma * 3.0))
    x0, x1 = cx - ext, cx + ext + 1
    y0, y1 = max(0, cy - ext), min(h, cy + ext + 1)
    xx = np.arange(x0, x1) % w
    yy = np.arange(y0, y1)
    dx = xx[None, :] - cx
    dy = yy[:, None] - cy
    g = np.exp(-(dx * dx + dy * dy) / (2.0 * sigma * sigma)) * intensity
    g = g.astype(np.float32)
    rgb[y0:y1][:, xx] += g[..., None] * np.asarray(color, dtype=np.float32)


def _stamp_spike(rgb, cx, cy, length, color, intensity):
    h, w, _ = rgb.shape
    x0, x1 = int(cx - length), int(cx + length + 1)
    y0, y1 = max(0, int(cy - length)), min(h, int(cy + length + 1))
    xx = np.arange(x0, x1) % w
    yy = np.arange(y0, y1)
    dx = np.abs(xx[None, :] - cx)
    dy = np.abs(yy[:, None] - cy)
    fall = np.exp(-dx / max(1.0, length * 0.35)) * np.exp(-(dy * dy) / 3.0)
    fall += np.exp(-dy / max(1.0, length * 0.35)) * np.exp(-(dx * dx) / 3.0)
    fall *= intensity
    g = fall.astype(np.float32)
    rgb[y0:y1][:, xx] += g[..., None] * np.asarray(color, dtype=np.float32)


def _stamp_galaxy(rgb, cu, cv, radius, angle, seed, arms=2,
                  core_color=(1.0, 0.92, 0.78), arm_color=(0.62, 0.74, 1.0)):
    h, w, _ = rgb.shape
    cx, cy = cu * w, cv * h
    ext = int(radius * 1.9)
    x0, x1 = max(0, int(cx - ext)), min(w, int(cx + ext))
    y0, y1 = max(0, int(cy - ext)), min(h, int(cy + ext))
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx = (xs - cx) / radius
    dy = (ys - cy) / radius
    ca, sa = math.cos(angle), math.sin(angle)
    xr = dx * ca + dy * sa
    yr = -dx * sa + dy * ca
    r = np.sqrt(xr * xr + yr * yr) + 1e-5
    theta = np.arctan2(yr, xr)
    phase = arms * (theta - 2.05 * np.log(r + 0.055))
    arm = 0.5 + 0.5 * np.cos(phase)
    arm = arm * arm
    disk = np.exp(-3.1 * r)
    spiral = np.exp(-1.9 * r) * arm
    core = np.exp(-(r / 0.16) ** 2)
    halo = np.exp(-1.25 * r) * 0.20
    edge = 1.0 - smoothstep(0.95, 1.55, r)
    val = (0.90 * spiral + 0.16 * disk + 0.55 * core + 0.14 * halo) * edge
    col = (np.asarray(arm_color, np.float32)[None, None, :] * (1.05 * val[..., None])
           + np.asarray(core_color, np.float32)[None, None, :] * (0.50 * core[..., None]))
    dust = (0.5 + 0.5 * np.cos(phase + math.pi)) ** 2 * np.exp(-2.0 * r) * edge
    rgb[y0:y1, x0:x1] *= (1.0 - 0.42 * dust[..., None])
    rgb[y0:y1, x0:x1] += col.astype(np.float32)

    rng = np.random.default_rng(seed)
    for _ in range(900):
        rr = rng.random() ** 0.65 * 0.85
        th = rng.uniform(0, TAU)
        armness = 0.5 + 0.5 * math.cos(arms * (th - 2.05 * math.log(rr + 0.055)))
        if rng.random() > armness ** 2 * 0.95 + 0.05:
            continue
        lx, ly = rr * math.cos(th), rr * math.sin(th)
        px = lx * ca - ly * sa + cx
        py = lx * sa + ly * ca + cy
        b = rng.uniform(0.15, 0.75)
        _stamp_dot(rgb, int(px) % w, int(py), rng.uniform(0.8, 1.8),
                   arm_color, b)


def _stamp_planet(rgb, cu, cv, radius):
    h, w, _ = rgb.shape
    cx, cy = cu * w, cv * h
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = (xs - cx) / radius
    dy = (ys - cy) / radius
    r = np.sqrt(dx * dx + dy * dy)

    ang = -0.38
    ca, sa = math.cos(ang), math.sin(ang)
    rx = dx * ca + dy * sa
    ry = -dx * sa + dy * ca
    ell = np.sqrt((rx / 1.9) ** 2 + (ry / 0.52) ** 2)
    band_dist = np.abs(ell - 1.0)
    ring_alpha = ((1.0 - smoothstep(0.030, 0.060, band_dist))
                  * smoothstep(1.02, 1.08, r)
                  * (1.0 - smoothstep(1.85, 2.15, r)))
    ring_col = np.array([0.82, 0.66, 0.44], np.float32)
    rgb[:] = rgb * (1.0 - 0.55 * ring_alpha[..., None]) \
        + ring_col[None, None, :] * (0.62 * ring_alpha[..., None])

    z = np.sqrt(np.clip(1.0 - r * r, 0.0, 1.0))
    lat = np.arcsin(np.clip(dy, -1.0, 1.0))
    bands = 0.5 + 0.5 * np.sin(lat * 15.0 + 0.9 * np.sin(lat * 5.0))
    base = np.array([0.14, 0.09, 0.06], np.float32)
    band_col = np.array([0.58, 0.40, 0.26], np.float32)
    col = base[None, None, :] + (band_col - base)[None, None, :] * bands[..., None]
    light = np.clip(-0.52 * dx - 0.36 * dy + 0.78 * z, 0.0, 1.0)
    shade = (0.20 + 0.80 * light) * (0.35 + 0.65 * z)
    col *= shade[..., None]
    rim = smoothstep(0.91, 1.0, r) * (1.0 - smoothstep(1.0, 1.012, r))
    col += np.array([1.0, 0.80, 0.55], np.float32)[None, None, :] * (
        (0.22 + 0.45 * light) * rim)[..., None]
    alpha = (1.0 - smoothstep(0.985, 1.012, r))[..., None]
    rgb[:] = rgb * (1.0 - alpha) + col * alpha


def make_portal(seed=321, width=512, height=1024):
    """Warm spiral nebula for the gate portal (UV mapped to the arch)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    dx = (xx - width * 0.5) / height
    dy = (yy - height * 0.46) / height
    r = np.sqrt(dx * dx + dy * dy) + 1e-5
    theta = np.arctan2(dy, dx)

    cloud = _fft_clouds(height, width, 26.0, seed + 1)
    fine = _fft_clouds(height, width, 8.0, seed + 2)

    arms = 3.0
    phase = arms * (theta + 2.1 * np.log(r + 0.045)) - 1.2
    swirl = (0.5 + 0.5 * np.cos(phase)) ** 2.4
    swirl *= (0.55 + 0.45 * cloud)

    core = np.exp(-(r / 0.105) ** 2)
    halo = np.exp(-(r / 0.36) ** 2)
    rim = 1.0 - smoothstep(0.38, 0.56, r)
    light = (0.95 * swirl * np.exp(-1.9 * r) + 1.15 * core
             + 0.30 * halo * (0.55 + 0.45 * cloud)) * rim

    ivory = np.array([1.00, 0.95, 0.82], np.float32)
    gold = np.array([1.00, 0.70, 0.29], np.float32)
    amber = np.array([0.72, 0.29, 0.07], np.float32)
    violet = np.array([0.30, 0.34, 0.72], np.float32)

    rgb = amber[None, None, :] * (0.55 * halo * (0.55 + 0.45 * fine))[..., None]
    rgb += gold[None, None, :] * (1.05 * swirl * np.exp(-1.6 * r))[..., None]
    rgb += violet[None, None, :] * (
        0.55 * swirl * smoothstep(0.18, 0.48, r) * (0.4 + 0.6 * fine)
    )[..., None]
    rgb += ivory[None, None, :] * (1.30 * core + 0.16 * halo)[..., None]

    # Light spilling onto the threshold at the bottom of the arch.
    spill = np.exp(-((yy / height - 0.97) / 0.075) ** 2) * 0.55
    rgb += ivory[None, None, :] * (spill * (0.6 + 0.4 * cloud))[..., None]

    for _ in range(180):
        rr = rng.random() ** 0.7 * 0.46
        th = rng.uniform(0, TAU)
        px = int((width * 0.5 + rr * math.cos(th) * height) % width)
        py = int(height * 0.46 + rr * math.sin(th) * height)
        b = rng.uniform(0.10, 0.55)
        _stamp_dot(rgb, px, py, rng.uniform(0.6, 1.6), (1.0, 0.86, 0.58), b)

    save_image("portal", np.clip(rgb, 0.0, 1.0), colorspace="sRGB")


def _star_color(rng):
    t = rng.random()
    if t < 0.20:
        return (0.70, 0.82, 1.00)
    if t < 0.58:
        return (0.96, 0.95, 0.98)
    if t < 0.86:
        return (1.00, 0.91, 0.76)
    return (1.00, 0.74, 0.56)


def make_starfield(seed=302, width=4096, height=2048):
    rng = np.random.default_rng(seed)
    u = np.linspace(0.0, 1.0, width, endpoint=False, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, height, endpoint=False, dtype=np.float32)[:, None]

    deep = np.array([0.003, 0.003, 0.007], np.float32)
    warm = np.array([0.010, 0.006, 0.008], np.float32)
    rgb = np.empty((height, width, 3), np.float32)
    rgb[:] = deep[None, None, :]
    rgb += warm[None, None, :] * (0.55 + 0.45 * np.cos(v * math.pi))[..., None]

    large = _fft_clouds(height, width, 90.0, seed + 1)
    medium = _fft_clouds(height, width, 34.0, seed + 2)
    fine = _fft_clouds(height, width, 11.0, seed + 3)

    nebula = smoothstep(0.48, 0.88, large) * (0.25 + 0.75 * smoothstep(0.20, 0.85, medium))
    amber = np.array([0.052, 0.024, 0.012], np.float32)
    rose = np.array([0.042, 0.014, 0.040], np.float32)
    rgb += amber[None, None, :] * (0.80 * nebula * (0.55 + 0.45 * fine))[..., None]
    rgb += rose[None, None, :] * (0.55 * nebula * (1.0 - 0.55 * fine))[..., None]

    # Milky way: a soft warm band crossing the upper sky.
    band_center = 0.315 + 0.055 * np.sin(u * TAU * 1.3 + 0.7)
    band = np.exp(-((v - band_center) / 0.105) ** 2)
    dust = smoothstep(0.62, 0.90, medium) * band
    rgb += np.array([0.026, 0.038, 0.058], np.float32)[None, None, :] * (
        band * (0.55 + 0.45 * fine))[..., None]
    rgb *= (1.0 - 0.30 * dust[..., None])
    rgb *= (0.84 + 0.28 * nebula[..., None])

    # The hero galaxy sits upper-left of the gate (u=0.315 -> 113 deg, v=0.285
    # -> +39 deg elevation); a cooler companion and the ringed planet fill the
    # upper-right sky.
    _stamp_galaxy(rgb, 0.315, 0.285, 165.0, 0.55, seed + 10,
                  arms=2, core_color=(1.00, 0.93, 0.80),
                  arm_color=(0.64, 0.76, 1.00))
    _stamp_galaxy(rgb, 0.255, 0.235, 58.0, -0.75, seed + 11,
                  arms=2, core_color=(1.00, 0.88, 0.72),
                  arm_color=(0.92, 0.62, 0.38))
    for i in range(6):
        gu = 0.345 + 0.028 * math.cos(i * 2.1)
        gv = 0.225 + 0.020 * math.sin(i * 2.6)
        _stamp_galaxy(rgb, gu, gv, 13.0 + 8.0 * (i % 3), i * 0.9, seed + 20 + i,
                      arms=2, core_color=(1.0, 0.9, 0.8),
                      arm_color=(0.55, 0.62, 0.88))

    _stamp_planet(rgb, 0.155, 0.315, 70.0)

    for _ in range(14000):
        su = rng.random()
        if rng.random() < 0.34:
            sv = float(band_center[0, int(su * width)]) + rng.normal(0.0, 0.050)
        else:
            sv = rng.random()
        sv = min(0.985, max(0.015, sv))
        color = _star_color(rng)
        b = 0.08 + 0.92 * rng.random() ** 8.5
        sigma = 0.55 + 1.8 * rng.random() ** 3.2
        _stamp_dot(rgb, int(su * width), int(sv * height), sigma, color, b)
        if b > 0.62:
            _stamp_dot(rgb, int(su * width), int(sv * height), sigma * 2.8,
                       color, 0.10 + 0.12 * (b - 0.62))

    for _ in range(40):
        su = rng.uniform(0.02, 0.98)
        sv = rng.uniform(0.05, 0.95)
        color = _star_color(rng)
        _stamp_spike(rgb, int(su * width), int(sv * height),
                     rng.uniform(6.0, 16.0), color, rng.uniform(0.50, 0.95))
        _stamp_dot(rgb, int(su * width), int(sv * height), 1.1, color, 1.0)

    save_image("starfield", np.clip(rgb, 0.0, 1.0), colorspace="sRGB")


def ensure_textures(force=False):
    expected = [
        "marble_base", "marble_rough", "marble_normal",
        "marble_warm_base", "marble_warm_rough", "marble_warm_normal",
        "portal", "starfield",
    ]
    if not force and all((config.TEXTURE_DIR / f"{name}.png").exists()
                         for name in expected):
        return {name: config.TEXTURE_DIR / f"{name}.png" for name in expected}

    print("[textures] generating star arena textures ...")
    make_marble()
    make_marble(seed=312, prefix="marble_warm", tint=(1.0, 0.97, 0.92))
    make_portal()
    make_starfield()
    print("[textures] done")
    return {name: config.TEXTURE_DIR / f"{name}.png" for name in expected}
