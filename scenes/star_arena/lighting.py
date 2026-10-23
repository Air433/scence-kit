"""Warm palace lighting and exported practical lights."""
from __future__ import annotations

import math

import bpy

from arena_kit import config, util


def set_mist_enabled(enabled: bool):
    return None


def _build_world():
    old = bpy.data.worlds.get("STAR_World")
    if old is not None:
        bpy.data.worlds.remove(old)
    world = bpy.data.worlds.new("STAR_World")
    world.use_nodes = True
    bpy.context.scene.world = world

    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    ramp = nt.nodes.new("ShaderNodeValToRGB")

    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = 0.0
    mr.inputs["To Max"].default_value = 1.0
    bg.inputs["Strength"].default_value = config.WORLD_STRENGTH
    ramp.color_ramp.interpolation = "EASE"

    stops = config.SKY_STOPS
    els = ramp.color_ramp.elements
    els[0].position = stops[0][0]
    els[0].color = (*config.hex_rgb(stops[0][1]), 1.0)
    for pos, hexc in stops[1:]:
        e = els.new(pos)
        e.color = (*config.hex_rgb(hexc), 1.0)

    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return world


def _light_object(name, data, location, target, export=False):
    obj = bpy.data.objects.new(name, data)
    util.link_object(obj, config.C_LIGHTS)
    if export:
        util.link_object(obj, config.C_EXPORT)
    obj.location = location
    util.look_at(obj, target)
    return obj


def _sun():
    data = bpy.data.lights.new("LIGHT_Sun", "SUN")
    data.energy = config.SUN_ENERGY
    data.angle = math.radians(config.SUN_ANGLE_DEG)
    data.use_temperature = True
    data.temperature = config.SUN_TEMPERATURE
    return _light_object("LIGHT_Sun", data, config.SUN_POS, config.SUN_TARGET,
                         export=True)


def _area(name, energy, color, size, pos, target):
    data = bpy.data.lights.new(name, "AREA")
    data.shape = "RECTANGLE"
    data.size = size[0]
    data.size_y = size[1]
    data.energy = energy
    data.color = config.hex_rgb(color)
    return _light_object(name, data, pos, target)


def _point(name, location, energy, color, radius=0.4, shadow=False):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = energy
    data.color = color
    data.shadow_soft_size = radius
    data.use_temperature = False
    data.use_shadow = shadow
    return _light_object(name, data, location, (0.0, 0.0, 0.0), export=True)


def build_lighting(mats=None):
    util.reset_collection(config.C_LIGHTS)
    _build_world()
    sun = _sun()

    _area("LIGHT_Fill", config.FILL_ENERGY, config.FILL_COLOR, config.FILL_SIZE,
          config.FILL_POS, config.FILL_TARGET)
    _area("LIGHT_Rim", config.BOUNCE_ENERGY, config.BOUNCE_COLOR,
          config.BOUNCE_SIZE, config.BOUNCE_POS, config.BOUNCE_TARGET)
    # Soft cool skylight: keeps the ivory marble white against the gold.
    _area("LIGHT_Sky", 2200.0, "#f8fbff", (60.0, 60.0),
          (0.0, 0.0, 38.0), (0.0, 0.0, 0.0))

    practicals = []
    practicals.append(_point("LIGHT_Portal", (0.0, 18.6, 6.2), 30.0,
                             config.hex_rgb("#ffd9a0"), radius=0.9))
    practicals.append(_point("LIGHT_Halo", (0.0, 18.4, 19.4), 75.0,
                             config.hex_rgb("#ffe9c8"), radius=1.4))
    practicals.append(_point("LIGHT_Plaza", (0.0, 0.0, 1.4), 14.0,
                             config.hex_rgb("#ffd9a0"), radius=0.7))

    sconce_angles = (54.0, 126.0, 234.0, 306.0)
    for i, ang in enumerate(sconce_angles):
        a = math.radians(ang)
        practicals.append(_point(
            f"LIGHT_Sconce_{i:02d}",
            (19.15 * math.cos(a), 19.15 * math.sin(a), 4.55),
            10.0, config.hex_rgb("#ffc98a"), radius=0.22))

    for i, ang in enumerate((45.0, 135.0, 225.0, 315.0)):
        a = math.radians(ang)
        practicals.append(_point(
            f"LIGHT_Brazier_{i:02d}",
            (11.55 * math.cos(a), 11.55 * math.sin(a), 2.15),
            18.0, config.hex_rgb("#ff9d5c"), radius=0.35))

    scene = bpy.context.scene
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
    scene.view_settings.exposure = config.EXPOSURE
    print(f"[lighting] palace rig: sun + fill + rim + {len(practicals)} point lights")
    return {"sun": sun, "practicals": practicals}
