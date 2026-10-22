"""Sunset world, sun/fill rig and exported practicals.

The GLB carries the sun, torches, compass and lighthouse lights.  Godot
drives energy/range/colour at runtime; this module only needs to look right
in Cycles (and be plausible as an import default).
"""
from __future__ import annotations

import math

import bpy

from arena_kit import config, util

from . import layout

WORLD_NAME = "EF_IslandWorld"


def set_mist_enabled(enabled: bool):
    world = bpy.data.worlds.get(WORLD_NAME)
    if world is None or world.node_tree is None:
        return
    node = world.node_tree.nodes.get("MistDensity")
    if node is not None:
        node.inputs[1].default_value = config.MIST_DENSITY if enabled else 0.0


def _build_world():
    old = bpy.data.worlds.get(WORLD_NAME)
    if old is not None:
        bpy.data.worlds.remove(old)
    world = bpy.data.worlds.new(WORLD_NAME)
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

    # Warm sea haze: a world volume has no bounds, so Cycles never culls it.
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    vsep = nt.nodes.new("ShaderNodeSeparateXYZ")
    vmr = nt.nodes.new("ShaderNodeMapRange")
    vmr.inputs["From Min"].default_value = 0.0
    vmr.inputs["From Max"].default_value = config.MIST_HEIGHT
    mist_ramp = nt.nodes.new("ShaderNodeValToRGB")
    mist_ramp.color_ramp.interpolation = "EASE"
    mels = mist_ramp.color_ramp.elements
    mels[0].position = 0.0
    mels[0].color = (1.0, 1.0, 1.0, 1.0)
    me = mels.new(0.24)
    me.color = (0.72, 0.72, 0.72, 1.0)
    me = mels.new(0.58)
    me.color = (0.22, 0.22, 0.22, 1.0)
    mels[-1].position = 1.0
    mels[-1].color = (0.0, 0.0, 0.0, 1.0)
    mult = nt.nodes.new("ShaderNodeMath")
    mult.name = "MistDensity"
    mult.operation = "MULTIPLY"
    mult.inputs[1].default_value = config.MIST_DENSITY
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*config.MIST_COLOR, 1.0)
    vol.inputs["Anisotropy"].default_value = config.MIST_ANISOTROPY
    nt.links.new(geo.outputs["Position"], vsep.inputs["Vector"])
    nt.links.new(vsep.outputs["Z"], vmr.inputs["Value"])
    nt.links.new(vmr.outputs["Result"], mist_ramp.inputs["Fac"])
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


def _build_sun():
    data = bpy.data.lights.new("LIGHT_Sun", type="SUN")
    data.energy = config.SUN_ENERGY
    data.angle = math.radians(config.SUN_ANGLE_DEG)
    data.use_temperature = True
    data.temperature = config.SUN_TEMPERATURE
    return _light_object("LIGHT_Sun", data, config.SUN_POS,
                         config.SUN_TARGET, export=True)


def _area(name, pos, target, energy, color, size):
    data = bpy.data.lights.new(name, type="AREA")
    data.shape = "RECTANGLE"
    data.size, data.size_y = size
    data.energy = energy
    data.color = config.hex_rgb(color)
    return _light_object(name, data, pos, target, export=False)


def _point(name, pos, energy, kelvin, radius=0.3, shadow=False, color=None):
    data = bpy.data.lights.new(name, type="POINT")
    data.energy = energy
    data.shadow_soft_size = radius
    if color is not None:
        data.use_temperature = False
        data.color = color
    else:
        data.use_temperature = True
        data.temperature = kelvin
    data.use_shadow = shadow
    obj = _light_object(name, data, pos, (0, 0, 0), export=True)
    return obj


def _build_lighthouse_light(lighthouse):
    pos = lighthouse.get("light_pos") or (
        layout.LIGHTHOUSE_X, layout.LIGHTHOUSE_Y,
        layout.LIGHTHOUSE_BASE_Z + 15.5)
    _point("LIGHT_Lighthouse", pos, 180.0, 2300, radius=0.7,
           shadow=False)
    beam = bpy.data.lights.new("LIGHT_LighthouseBeam", type="SPOT")
    beam.energy = 1800.0
    beam.spot_size = math.radians(19.0)
    beam.spot_blend = 0.35
    beam.color = config.hex_rgb("#ffd39a")
    beam.use_shadow = False
    beam.shadow_soft_size = 0.4
    target = (layout.LIGHTHOUSE_X - 26.0, layout.LIGHTHOUSE_Y - 30.0, 2.5)
    _light_object("LIGHT_LighthouseBeam", beam, pos, target, export=True)


def _setup_compositor():
    scene = bpy.context.scene
    try:
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()
        rl = tree.nodes.new("CompositorNodeRLayers")
        glare = tree.nodes.new("CompositorNodeGlare")
        glare.glare_type = "FOG_GLOW"
        try:
            glare.quality = "HIGH"
        except Exception:
            pass
        glare.threshold = 1.05
        glare.size = 7
        comp = tree.nodes.new("CompositorNodeComposite")
        tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
        tree.links.new(glare.outputs["Image"], comp.inputs["Image"])
    except Exception as exc:
        print(f"[lighting] compositor skipped: {exc}")


def build_lighting(mats, torches, lighthouse):
    util.reset_collection(config.C_LIGHTS)
    _build_world()
    sun = _build_sun()
    _area("LIGHT_Fill", config.FILL_POS, config.FILL_TARGET,
          config.FILL_ENERGY, config.FILL_COLOR, config.FILL_SIZE)
    _area("LIGHT_Bounce", config.BOUNCE_POS, config.BOUNCE_TARGET,
          config.BOUNCE_ENERGY, config.BOUNCE_COLOR, config.BOUNCE_SIZE)

    for i, (x, y, z) in enumerate(torches[:8]):
        _point(f"LIGHT_Torch_{i:02d}", (x, y, z), config.LANTERN_ENERGY,
               config.LANTERN_TEMPERATURE, radius=0.24,
               shadow=(i in (2, 6)))

    zs = layout.terrain_height(0.0, -16.0)
    _point("LIGHT_String", (0.0, -16.0, zs + 4.1), 24.0, 2600, radius=0.3)

    _point("LIGHT_Compass", (0.0, 0.0, layout.ARENA_Z + 0.8),
           config.RUNE_LIGHT_ENERGY, 6500, radius=0.55, shadow=False,
           color=config.PALETTE["rune"])

    _build_lighthouse_light(lighthouse)
    _setup_compositor()

    scene = bpy.context.scene
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = config.EXPOSURE

    print(f"[lighting] sunset sun + fill + {len(torches)} torches + "
          f"lighthouse beam")
    return {"sun": sun}
