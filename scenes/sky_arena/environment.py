"""Baked sky panorama and the companion rocks floating in the cloud sea."""
from __future__ import annotations

import math

from arena_kit import config, util

from . import geometry as geo
from . import layout

TAU = math.pi * 2.0
DOME_R = 240.0


def _sky_dome(mats):
    verts, faces, uvs = geo.uv_sphere(DOME_R, 128, 64)
    sky = util.mesh_object("SKY_Dome", verts, faces, config.C_PROPS,
                           mats["sky"], smooth=True)
    mesh = sky.data
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = uvs[mesh.loops[li].vertex_index]
    sky.visible_shadow = False
    # Backdrop only: the world gradient supplies the ambient light so the
    # painted clouds do not act as a second sun in Cycles.  Glossy stays on
    # so gold inlays pick up the sky in reflections.
    sky.visible_diffuse = False
    sky.visible_glossy = True
    sky.visible_transmission = False
    sky.visible_volume_scatter = False
    util.link_object(sky, config.C_EXPORT)
    return sky


def _rock(islet, rng, rings=6, segs=40):
    phase = rng.uniform(0.0, TAU)
    base = islet["r"]

    def radius(a):
        return base * (1.0
                       + 0.12 * math.sin(3.0 * a + phase)
                       + 0.055 * math.sin(7.0 * a + 1.7 * phase))

    verts, faces = geo.rock_shell(radius, islet["z"] + 0.02,
                                  islet["z"] - islet["depth"], rng,
                                  rings=rings, segs=segs)
    ox, oy = islet["x"], islet["y"]
    return [(v[0] + ox, v[1] + oy, v[2]) for v in verts], faces


def _cap(islet, rings=5, segs=40):
    cx, cy, base = islet["x"], islet["y"], islet["r"]
    verts = [(cx, cy, layout.islet_cap_z(islet, cx, cy) + 0.01)]
    for k in range(1, rings + 1):
        t = (k / rings) ** 0.86
        for s in range(segs):
            a = TAU * s / segs
            wob = 1.0 + 0.045 * math.sin(5.0 * a + 1.3)
            x = cx + base * 0.975 * t * wob * math.cos(a)
            y = cy + base * 0.975 * t * wob * math.sin(a)
            verts.append((x, y, layout.islet_cap_z(islet, x, y) + 0.01))
    faces = []
    for s in range(segs):
        faces.append((0, 1 + s, 1 + (s + 1) % segs))
    for k in range(rings - 1):
        a0 = 1 + k * segs
        b0 = a0 + segs
        for s in range(segs):
            t = (s + 1) % segs
            faces.append((a0 + s, b0 + s, b0 + t, a0 + t))
    return verts, faces


def _islet_ruin(islet, stone, gold):
    ox_list = layout.islet_ruin_offsets(islet["ruin"])
    if not ox_list:
        return
    cz = islet["z"] + 0.06
    if islet["ruin"] == "column":
        ox, oy = ox_list[0]
        x, y = islet["x"] + ox, islet["y"] + oy
        stone.append(geo.box(x, y, cz, cz + 0.30, 1.25, 1.25, 0.4))
        stone.append(geo.prism(x, y, cz + 0.30, cz + 0.42, 0.52, 0.46, 16))
        stone.append(geo.broken_column(
            x, y, cz + 0.42, cz + 3.65, 0.40, 0.35, 16,
            util.sub_rng("sky_islet_column"), jag=0.55))
        gold.append(geo.torus_z(0.44, 0.026, cz + 0.43, 32, 5, x, y))
        stone.append(geo.lying_drum(islet["x"] + 1.9, islet["y"] - 1.5,
                                    cz + 0.38, 0.38, 1.9, -0.5))
    else:
        for i, (ox, oy) in enumerate(ox_list):
            x, y = islet["x"] + ox, islet["y"] + oy
            top = cz + (3.10 if i == 0 else 1.55)
            stone.append(geo.box(x, y, cz, cz + 0.26, 1.05, 1.05, 0.2))
            stone.append(geo.broken_column(
                x, y, cz + 0.26, top, 0.36, 0.33, 14,
                util.sub_rng(f"sky_islet_arch_{i}"), jag=0.6))
        stone.append(geo.box(islet["x"] + 0.15, islet["y"], cz + 2.85,
                             cz + 3.30, 2.55, 0.85, 0.03))
        gold.append(geo.box(islet["x"] + 0.15, islet["y"], cz + 3.30,
                            cz + 3.36, 2.62, 0.90, 0.03))


def build_environment(mats):
    util.reset_collection(config.C_PROPS)
    _sky_dome(mats)

    rng = util.sub_rng("sky_islets")
    rock, cap, stone, gold = [], [], [], []
    islets = list(layout.ISLETS)
    for x, y, z, r, depth in layout.FAR_ISLETS:
        islets.append({"x": x, "y": y, "z": z, "r": r, "depth": depth,
                       "ruin": None})

    for i, islet in enumerate(islets):
        near = islet["ruin"] is not None or i < len(layout.ISLETS)
        rock.append(_rock(islet, rng, rings=7 if near else 5,
                          segs=44 if near else 26))
        cap.append(_cap(islet, rings=5 if near else 4,
                        segs=44 if near else 26))
        if islet["ruin"] is not None:
            _islet_ruin(islet, stone, gold)

        # A soil lip hides the seam between grass and bare rock.
        if near:
            cap.append(geo.prism(islet["x"], islet["y"],
                                 islet["z"] - 0.52, islet["z"] + 0.045,
                                 islet["r"] * 1.035, islet["r"] * 0.98, 32))

    rock_obj = geo.merged_mesh("PROPS_IsletRock", rock, mats["rock"],
                               config.C_PROPS)
    util.cube_uv(rock_obj, 7.0)
    util.shade_smooth_by_angle(rock_obj, 38.0)
    cap_obj = geo.merged_mesh("PROPS_IsletGrass", cap, mats["ground"],
                              config.C_PROPS)
    if stone:
        stone_obj = geo.merged_mesh("PROPS_IsletRuins", stone,
                                    mats["limestone"], config.C_PROPS)
        util.cube_uv(stone_obj, 2.0)
        util.shade_smooth_by_angle(stone_obj, 30.0)
    if gold:
        gold_obj = geo.merged_mesh("PROPS_IsletTrim", gold, mats["gold"],
                                   config.C_PROPS)
        util.shade_smooth_by_angle(gold_obj, 32.0)

    print(f"[environment] sky dome r={DOME_R:.0f} m, "
          f"{len(layout.ISLETS)} near + {len(layout.FAR_ISLETS)} far islets")
    return {"sky": "SKY_Dome", "islets": len(islets)}
