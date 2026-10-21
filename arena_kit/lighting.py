"""Morning-gold lighting, magical point lights and preview mist."""
from __future__ import annotations

import math

import bpy

from . import config, util

def set_mist_enabled(enabled: bool):
    """Toggle the world-volume mist (preview only; never exported)."""
    world = bpy.data.worlds.get("EF_MorningWorld")
    if world is None or world.node_tree is None:
        return
    node = world.node_tree.nodes.get("MistDensity")
    if node is not None:
        node.inputs[1].default_value = config.MIST_DENSITY if enabled else 0.0


def _build_world():
    world = bpy.data.worlds.get("EF_MorningWorld")
    if world is not None:
        bpy.data.worlds.remove(world)
    world = bpy.data.worlds.new("EF_MorningWorld")
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

    # Ground-hugging morning mist. A world volume has no bounding box, which
    # sidesteps Cycles dropping very large object volumes; world shading is
    # never exported, so this stays a preview/hero-render effect.
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = config.MIST_HEIGHT
    mist_ramp = nt.nodes.new("ShaderNodeValToRGB")
    mist_ramp.color_ramp.interpolation = "EASE"
    mels = mist_ramp.color_ramp.elements
    mels[0].position = 0.0
    mels[0].color = (1.0, 1.0, 1.0, 1.0)
    me = mels.new(0.30)
    me.color = (0.55, 0.55, 0.55, 1.0)
    me = mels.new(0.62)
    me.color = (0.16, 0.16, 0.16, 1.0)
    mels[-1].position = 1.0
    mels[-1].color = (0.0, 0.0, 0.0, 1.0)
    mult = nt.nodes.new("ShaderNodeMath")
    mult.name = "MistDensity"
    mult.operation = "MULTIPLY"
    mult.inputs[1].default_value = config.MIST_DENSITY
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*config.MIST_COLOR, 1.0)
    vol.inputs["Anisotropy"].default_value = config.MIST_ANISOTROPY
    nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], mist_ramp.inputs["Fac"])
    nt.links.new(mist_ramp.outputs["Color"], mult.inputs[0])
    nt.links.new(mult.outputs["Value"], vol.inputs["Density"])
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    return world


def _light_object(name, light_data, location, target, collection, export):
    obj = bpy.data.objects.new(name, light_data)
    util.link_object(obj, collection)
    if export:
        util.link_object(obj, config.C_EXPORT)
    obj.location = location
    util.look_at(obj, target)
    return obj


def _build_sun():
    data = bpy.data.lights.new("LIGHT_Sun", type="SUN")
    data.energy = config.SUN_ENERGY
    data.angle = math.radians(config.SUN_ANGLE_DEG)
    data.use_temperature = True
    data.temperature = config.SUN_TEMPERATURE
    return _light_object("LIGHT_Sun", data, config.SUN_POS, config.SUN_TARGET,
                         config.C_LIGHTS, True)


def _build_fill():
    data = bpy.data.lights.new("LIGHT_Fill", type="AREA")
    data.shape = "RECTANGLE"
    data.size = config.FILL_SIZE[0]
    data.size_y = config.FILL_SIZE[1]
    data.energy = config.FILL_ENERGY
    data.color = config.hex_rgb(config.FILL_COLOR)
    return _light_object("LIGHT_Fill", data, config.FILL_POS, config.FILL_TARGET,
                         config.C_LIGHTS, False)


def _build_bounce():
    """Warm bounce just behind the camera to lift the near flagstones."""
    data = bpy.data.lights.new("LIGHT_Bounce", type="AREA")
    data.shape = "RECTANGLE"
    data.size = config.BOUNCE_SIZE[0]
    data.size_y = config.BOUNCE_SIZE[1]
    data.energy = config.BOUNCE_ENERGY
    data.color = config.hex_rgb(config.BOUNCE_COLOR)
    return _light_object("LIGHT_Bounce", data, config.BOUNCE_POS,
                         config.BOUNCE_TARGET, config.C_LIGHTS, False)


def _build_point(name, location, energy, kelvin, radius=0.28, shadow=False):
    data = bpy.data.lights.new(name, type="POINT")
    data.energy = energy
    data.shadow_soft_size = radius
    data.use_temperature = True
    data.temperature = kelvin
    data.use_shadow = shadow
    obj = bpy.data.objects.new(name, data)
    util.link_object(obj, config.C_LIGHTS)
    util.link_object(obj, config.C_EXPORT)
    obj.location = location
    return obj


def build_lighting(mats, lanterns):
    util.reset_collection(config.C_LIGHTS)
    _build_world()
    sun = _build_sun()
    _build_fill()
    _build_bounce()

    # warm practicals at a subset of the lanterns (most visible first)
    warm = []
    for i, (x, y, z) in enumerate(lanterns[:8]):
        energy = config.LANTERN_ENERGY if i < 6 else config.LANTERN_ENERGY_FAR
        warm.append(_build_point(f"LIGHT_Lantern_{i:02d}", (x, y, z + 0.02),
                                 energy, config.LANTERN_TEMPERATURE,
                                 shadow=(i in (1, 4))))

    rune = _build_point("LIGHT_Rune", (0.0, 0.0, 0.55),
                        config.RUNE_LIGHT_ENERGY, 6500, radius=0.5, shadow=True)
    rune.data.use_temperature = False
    rune.data.color = config.PALETTE["rune"]

    scene = bpy.context.scene
    scene.view_settings.exposure = config.EXPOSURE
    print(f"[lighting] sun + fill + mist + {len(warm) + 1} point lights")
    return {"sun": sun, "warm": warm, "rune": rune}
