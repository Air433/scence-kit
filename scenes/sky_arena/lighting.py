"""Afternoon sun over the cloud sea, rune practicals and preview mist."""
from __future__ import annotations

import math

import bpy

from arena_kit import config, util

from . import plaza


def set_mist_enabled(enabled: bool):
    world = bpy.data.worlds.get("SKY_World")
    if world is None or world.node_tree is None:
        return
    node = world.node_tree.nodes.get("MistDensity")
    if node is not None:
        node.inputs[1].default_value = config.MIST_DENSITY if enabled else 0.0


def _build_world():
    old = bpy.data.worlds.get("SKY_World")
    if old is not None:
        bpy.data.worlds.remove(old)
    world = bpy.data.worlds.new("SKY_World")
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
    me = mels.new(0.34)
    me.color = (0.52, 0.52, 0.52, 1.0)
    me = mels.new(0.68)
    me.color = (0.14, 0.14, 0.14, 1.0)
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


def _point(name, location, energy, color, radius=0.35, shadow=False,
           kelvin=None):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = energy
    data.shadow_soft_size = radius
    data.use_shadow = shadow
    if kelvin is None:
        data.use_temperature = False
        data.color = color
    else:
        data.use_temperature = True
        data.temperature = kelvin
    return _light_object(name, data, location, (location[0], location[1], 0.0),
                         export=True)


def _compositor_glow():
    """Subtle bloom on runes and brazier flames (render only, not exported)."""
    old = bpy.data.node_groups.get("SKY_Compositor")
    if old is not None:
        bpy.data.node_groups.remove(old)
    ng = bpy.data.node_groups.new("SKY_Compositor", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT",
                            socket_type="NodeSocketColor")
    rl = ng.nodes.new("CompositorNodeRLayers")
    glare = ng.nodes.new("CompositorNodeGlare")
    out = ng.nodes.new("NodeGroupOutput")
    glare.inputs["Type"].default_value = "Fog Glow"
    glare.inputs["Quality"].default_value = "High"
    glare.inputs["Threshold"].default_value = 1.0
    glare.inputs["Smoothness"].default_value = 0.25
    glare.inputs["Size"].default_value = 0.62
    glare.inputs["Strength"].default_value = 0.32
    glare.inputs["Saturation"].default_value = 1.1
    ng.links.new(rl.outputs["Image"], glare.inputs["Image"])
    ng.links.new(glare.outputs["Image"], out.inputs["Image"])
    bpy.context.scene.compositing_node_group = ng


def build_lighting(mats=None, braziers=None, gate_light=None):
    util.reset_collection(config.C_LIGHTS)
    _build_world()
    _compositor_glow()
    sun = _sun()

    _area("LIGHT_Fill", config.FILL_ENERGY, config.FILL_COLOR,
          config.FILL_SIZE, config.FILL_POS, config.FILL_TARGET)
    _area("LIGHT_Bounce", config.BOUNCE_ENERGY, config.BOUNCE_COLOR,
          config.BOUNCE_SIZE, config.BOUNCE_POS, config.BOUNCE_TARGET)
    _area("LIGHT_Sky", 800.0, "#e9f3fb", (70.0, 70.0),
          (0.0, -4.0, 42.0), (0.0, 0.0, 0.0))
    _area("LIGHT_CloudBounce", 700.0, "#ffd9b0", (40.0, 40.0),
          (0.0, 0.0, -14.0), (0.0, 0.0, 2.0))

    practicals = []
    braziers = braziers or plaza.brazier_positions()
    for i, (x, y, z) in enumerate(braziers):
        practicals.append(_point(
            f"LIGHT_Brazier_{i:02d}", (x, y, z + 0.28),
            config.LANTERN_ENERGY, None, radius=0.38,
            shadow=(i in (1, 3)), kelvin=config.LANTERN_TEMPERATURE))

    rune = config.PALETTE["rune"]
    practicals.append(_point("LIGHT_DaisRune", (0.0, 0.0, 1.15),
                             config.RUNE_LIGHT_ENERGY, rune,
                             radius=0.55, shadow=True))
    practicals.append(_point("LIGHT_Heart", (0.0, 0.0, 3.05), 26.0, rune,
                             radius=0.38))
    gx, gy, gz = gate_light or (0.0, 18.3, 11.7)
    practicals.append(_point("LIGHT_GateRune", (gx, gy, gz), 30.0, rune,
                             radius=0.5))

    scene = bpy.context.scene
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
    scene.view_settings.exposure = config.EXPOSURE
    print(f"[lighting] sun + sky fill + mist + {len(practicals)} practicals")
    return {"sun": sun, "practicals": practicals}
