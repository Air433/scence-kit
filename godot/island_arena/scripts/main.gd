extends Node3D

const PROFILE := preload("res://island_arena/scripts/scene_profile.gd")
const SKY_SHADER: Shader = preload("res://island_arena/shaders/sky.gdshader")
const OCEAN_SHADER: Shader = preload("res://island_arena/shaders/ocean.gdshader")
const WIND_SHADER: Shader = preload("res://island_arena/shaders/wind.gdshader")
const TERRAIN_SHADER: Shader = preload("res://island_arena/shaders/terrain.gdshader")
const VIGNETTE_SHADER: Shader = preload("res://island_arena/shaders/vignette.gdshader")

const ALL_LAYERS := 0xFFFFF
const LAYER_SEABED := 1 << 1
const LAYER_WATER := 1 << 2
const LAYER_FX := 1 << 3

@onready var rig: Camera3D = $Camera

var moods: Dictionary = {}
var state: Dictionary = {}
var from_state: Dictionary = {}
var to_state: Dictionary = {}
var mood: String = PROFILE.DEFAULT_MOOD
var blend := 1.0
var blend_speed: float = PROFILE.BLEND_SPEED

var env: Environment
var sky_mat: ShaderMaterial
var sun: DirectionalLight3D
var fill: DirectionalLight3D
var lightning: DirectionalLight3D
var ocean_mat: ShaderMaterial
var ocean: MeshInstance3D
var wind_mats: Array[ShaderMaterial] = []
var refl_vp: SubViewport
var refl_cam: Camera3D
var refl_env: Environment

var torch_lights: Array[OmniLight3D] = []
var lighthouse_light: OmniLight3D
var compass_light: OmniLight3D
var string_light: OmniLight3D
var beam: SpotLight3D
var beam_pivot: Node3D

var rain: GPUParticles3D
var flash := 0.0
var flash_timer := 7.0

var hud: CanvasLayer
var weather_label: Label
var hint_label: Label
var flash_rect: ColorRect
var vignette_mat: ShaderMaterial

var elapsed := 0.0
var auto_timer: float = PROFILE.AUTO_WEATHER_START
var auto_weather := true
var capture_mode := false
var capture_path := ""
var capture_left := -1
var cam_preset: String = PROFILE.DEFAULT_CAM
var nofog := false


func _ready() -> void:
    moods = PROFILE.WEATHER.presets()
    var args := ArenaCapture.parse_args()
    var want: String = PROFILE.DEFAULT_MOOD
    if String(args["mood"]) != "":
        want = String(args["mood"])
    if bool(args["random"]):
        want = String(moods.keys().pick_random())
    if String(args["cam"]) != "":
        cam_preset = String(args["cam"])
    capture_path = String(args["shot"])
    capture_mode = capture_path != ""
    capture_left = int(args["frames"])
    nofog = bool(args["nofog"])

    if not moods.has(want):
        want = PROFILE.DEFAULT_MOOD
    mood = want
    from_state = moods[mood].duplicate(true)
    to_state = moods[mood].duplicate(true)
    state = from_state.duplicate(true)

    _build_environment()
    rig.call("configure", PROFILE.CAMERA)
    _load_island()
    _build_ocean()
    _build_weather_fx()
    _build_ui()

    _apply_cam_preset(cam_preset)

    if capture_mode:
        auto_weather = false
        rig.set("auto_orbit", false)
        hud.visible = false
        DisplayServer.window_set_size(Vector2i(1600, 900))
        if capture_left < 0:
            capture_left = PROFILE.DEFAULT_FRAMES
    _apply_state(state)


func _process(delta: float) -> void:
    elapsed += delta

    if blend < 1.0:
        blend = minf(1.0, blend + delta * blend_speed)
        state = _mix_state(from_state, to_state, smoothstep(0.0, 1.0, blend))

    if auto_weather and blend >= 1.0:
        auto_timer -= delta
        if auto_timer <= 0.0:
            _transition_to(_random_mood())
            auto_timer = randf_range(PROFILE.AUTO_WEATHER_MIN, PROFILE.AUTO_WEATHER_MAX)

    _apply_state(state)
    _update_reflection()

    if rain != null:
        rain.global_position = rig.global_position + Vector3(0.0, 26.0, 0.0)

    if beam_pivot != null:
        beam_pivot.rotate_y(delta * lerp(0.18, 0.5, float(state.night)))

    if flash > 0.001:
        flash = maxf(0.0, flash - delta * 4.6)
    if weather_label != null:
        var clock_h := fmod(float(state.clock) + elapsed * 0.006, 24.0)
        var hh := int(clock_h)
        var mm := int((clock_h - float(hh)) * 60.0)
        weather_label.text = "%s   %s:%s" % [String(state.label), str(hh).pad_zeros(2), str(mm).pad_zeros(2)]
    if flash_rect != null:
        flash_rect.color.a = flash * 0.16

    if capture_mode and capture_left > 0:
        capture_left -= 1
        if capture_left == 0:
            _take_shot()


func _apply_cam_preset(preset: String) -> void:
    var presets: Dictionary = PROFILE.CAMERA_PRESETS
    var view: Dictionary = presets.get(preset, presets[PROFILE.DEFAULT_CAM])
    rig.call("set_view", view["target"], view["yaw"], view["pitch"], view["distance"])


func _unhandled_input(event: InputEvent) -> void:
    if capture_mode:
        return
    if event is InputEventKey and event.pressed and not event.echo:
        match (event as InputEventKey).physical_keycode:
            KEY_1:
                _transition_to("sunny")
            KEY_2:
                _transition_to("storm")
            KEY_3:
                _transition_to("night")
            KEY_R:
                _transition_to(_random_mood())
            KEY_C:
                rig.set("auto_orbit", not bool(rig.get("auto_orbit")))
            KEY_H:
                hint_label.visible = not hint_label.visible


# ---------------------------------------------------------------------------
# Weather state
# ---------------------------------------------------------------------------

func _mix_state(a: Dictionary, b: Dictionary, t: float) -> Dictionary:
    var out := {}
    for key in b.keys():
        var vb = b[key]
        var va = a.get(key, vb)
        if vb is float:
            out[key] = lerp(float(va), float(vb), t)
        elif vb is Color:
            out[key] = (va as Color).lerp(vb as Color, t)
        elif vb is Vector3:
            out[key] = (va as Vector3).lerp(vb as Vector3, t)
        else:
            out[key] = vb
    return out


func _transition_to(name: String) -> void:
    if not moods.has(name) or name == mood:
        return
    from_state = state.duplicate(true)
    to_state = moods[name].duplicate(true)
    mood = name
    blend = 0.0


func _random_mood() -> String:
    var keys: Array = moods.keys()
    keys.erase(mood)
    return String(keys.pick_random())


func _apply_state(s: Dictionary) -> void:
    var drift := sin(elapsed * 0.010) * 0.09 + sin(elapsed * 0.0031) * 0.05
    var sun_dir: Vector3 = (s.sun_dir as Vector3).normalized().rotated(Vector3.UP, drift)

    # Sun / moon direction. -Z of the light points along the travel direction.
    if sun != null:
        sun.light_color = s.sun_color
        sun.light_energy = float(s.sun_energy) + flash * 5.0 * float(s.storm)
        var target := -sun_dir * 100.0
        sun.look_at(target, Vector3.UP)

    if sky_mat != null:
        sky_mat.set_shader_parameter("zenith_color", s.sky_zenith)
        sky_mat.set_shader_parameter("horizon_color", s.sky_horizon)
        sky_mat.set_shader_parameter("horizon_cool", s.horizon_cool)
        sky_mat.set_shader_parameter("ground_color", s.sky_ground)
        sky_mat.set_shader_parameter("cloud_lit", s.cloud_lit)
        sky_mat.set_shader_parameter("cloud_shadow", s.cloud_shadow)
        sky_mat.set_shader_parameter("sun_color", s.sun_color)
        sky_mat.set_shader_parameter("sun_dir", sun_dir)
        sky_mat.set_shader_parameter("moon_dir", s.moon_dir)
        sky_mat.set_shader_parameter("cloud_cover", s.cloud_cover)
        sky_mat.set_shader_parameter("cloud_speed", 0.35 + float(s.wind))
        sky_mat.set_shader_parameter("night", s.night)
        sky_mat.set_shader_parameter("storm", s.storm)
        sky_mat.set_shader_parameter("flash", flash)

    if env != null:
        env.tonemap_exposure = float(s.exposure)
        env.ambient_light_color = s.ambient_color
        env.ambient_light_energy = float(s.ambient_energy)
        env.glow_intensity = float(s.glow)
        env.fog_light_color = s.fog_color
        env.fog_density = 0.0 if nofog else float(s.fog_density) * 0.28
        env.volumetric_fog_density = 0.0 if nofog else float(s.fog_volume) * 0.14
    if refl_env != null:
        refl_env.tonemap_exposure = float(s.exposure) * 1.15
        refl_env.fog_light_color = s.fog_color
        refl_env.fog_density = float(s.fog_density) * 0.18
        refl_env.ambient_light_color = s.ambient_color
        refl_env.ambient_light_energy = float(s.ambient_energy)

    if ocean_mat != null:
        ocean_mat.set_shader_parameter("deep_color", s.water_deep)
        ocean_mat.set_shader_parameter("shallow_color", s.water_shallow)
        ocean_mat.set_shader_parameter("sky_color", s.water_sky)
        ocean_mat.set_shader_parameter("sun_color", s.sun_color)
        ocean_mat.set_shader_parameter("horizon_warm", s.sky_horizon)
        ocean_mat.set_shader_parameter("horizon_cool", s.horizon_cool)
        ocean_mat.set_shader_parameter("sun_dir", sun_dir)
        ocean_mat.set_shader_parameter("wave_scale", s.wave_scale)
        ocean_mat.set_shader_parameter("foam_amount", s.foam)
        ocean_mat.set_shader_parameter("reflection_amount", s.reflection)
        ocean_mat.set_shader_parameter("wind", s.wind)
        ocean_mat.set_shader_parameter("night", s.night)
        ocean_mat.set_shader_parameter("storm", s.storm)
        ocean_mat.set_shader_parameter("rain", s.rain)
        ocean_mat.set_shader_parameter("light_level", s.light_level)
        ocean_mat.set_shader_parameter("flash", flash)

    for m in wind_mats:
        m.set_shader_parameter("wind", s.wind)
        m.set_shader_parameter("wind_dir", Vector3(0.78, 0.0, 0.55))

    if vignette_mat != null:
        vignette_mat.set_shader_parameter("strength", s.vignette)

    for i in torch_lights.size():
        var flick := 1.0 + sin(elapsed * 17.3 + i * 1.7) * 0.12 + sin(elapsed * 29.1 + i * 2.3) * 0.06
        torch_lights[i].light_energy = (2.4 + float(s.night) * 6.2) * flick
    if lighthouse_light != null:
        lighthouse_light.light_energy = 2.2 + float(s.night) * 7.0
    if compass_light != null:
        compass_light.light_energy = 0.35 + float(s.night) * 1.7
    if string_light != null:
        string_light.light_energy = 0.5 + float(s.night) * 2.2
    if beam != null:
        beam.visible = float(s.night) > 0.2
        beam.light_energy = 0.1 + float(s.night) * 9.0
        beam.light_volumetric_fog_energy = 0.05 + float(s.night) * 3.2

    if fill != null:
        fill.light_color = s.fill_color
        fill.light_energy = float(s.fill_energy) + flash * 0.8 * float(s.storm)

    if lightning != null:
        lightning.light_energy = flash * 8.0 * float(s.storm)

    if rain != null:
        rain.amount_ratio = clampf(float(s.rain), 0.0, 1.0)
        rain.emitting = float(s.rain) > 0.04
        rain.visible = float(s.rain) > 0.02
        if rain.visible:
            rain.global_position = rig.global_position + Vector3(0.0, 26.0, 0.0)

    if float(s.storm) > 0.5 and flash_timer > 0.0 and not capture_mode:
        flash_timer -= get_process_delta_time()
        if flash_timer <= 0.0:
            _strike_lightning()
            flash_timer = randf_range(5.5, 13.0)
    elif float(s.storm) <= 0.5:
        flash_timer = randf_range(4.0, 8.0)


func _strike_lightning() -> void:
    flash = 1.0
    if lightning != null:
        lightning.rotation = Vector3(
            deg_to_rad(randf_range(-38.0, -16.0)),
            deg_to_rad(randf_range(0.0, 360.0)),
            0.0
        )


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

func _build_environment() -> void:
    var we := WorldEnvironment.new()
    we.name = "World"
    env = Environment.new()
    env.background_mode = Environment.BG_SKY

    var sky := Sky.new()
    sky_mat = ShaderMaterial.new()
    sky_mat.shader = SKY_SHADER
    sky.sky_material = sky_mat
    sky.radiance_size = Sky.RADIANCE_SIZE_256
    sky.process_mode = Sky.PROCESS_MODE_INCREMENTAL
    env.sky = sky

    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color("#7fa3bf")
    env.ambient_light_energy = 1.45
    env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
    env.tonemap_mode = Environment.TONE_MAPPER_ACES
    env.tonemap_exposure = 1.05
    env.tonemap_white = 6.0

    env.glow_enabled = true
    env.glow_normalized = true
    env.glow_intensity = 0.85
    env.glow_bloom = 0.03
    env.glow_hdr_threshold = 1.0
    env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN

    env.ssao_enabled = true
    env.ssao_radius = 1.5
    env.ssao_intensity = 1.0
    env.ssao_power = 1.2
    env.ssil_enabled = false
    env.sdfgi_enabled = false

    env.fog_enabled = true
    env.fog_light_color = Color("#bfae9d")
    env.fog_density = 0.0024
    env.fog_sky_affect = 0.05
    env.fog_aerial_perspective = 0.30
    env.fog_height = 4.0
    env.fog_height_density = 0.003

    env.volumetric_fog_enabled = true
    env.volumetric_fog_density = 0.006
    env.volumetric_fog_albedo = Color(0.95, 0.93, 0.90)
    env.volumetric_fog_length = 240.0
    env.volumetric_fog_anisotropy = 0.55
    env.volumetric_fog_sky_affect = 0.08

    env.adjustment_enabled = true
    env.adjustment_brightness = 1.02
    env.adjustment_contrast = 1.05
    env.adjustment_saturation = 1.06

    we.environment = env
    add_child(we)

    sun = DirectionalLight3D.new()
    sun.name = "LIGHT_SunRuntime"
    sun.shadow_enabled = true
    sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
    sun.directional_shadow_max_distance = 280.0
    sun.shadow_bias = 0.035
    sun.shadow_normal_bias = 1.4
    sun.shadow_blur = 1.2
    sun.light_angular_distance = 0.65
    sun.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
    add_child(sun)

    # Cool front fill: lifts the shaded south cliffs without flattening the sun.
    fill = DirectionalLight3D.new()
    fill.name = "LIGHT_FillRuntime"
    fill.light_color = Color("#93b6c9")
    fill.light_energy = 0.9
    fill.shadow_enabled = false
    fill.light_specular = 0.25
    fill.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
    add_child(fill)
    fill.look_at_from_position(PROFILE.FILL_POS, PROFILE.FILL_TARGET, Vector3.UP)

    lightning = DirectionalLight3D.new()
    lightning.name = "LIGHT_Lightning"
    lightning.light_color = Color(0.78, 0.86, 1.0)
    lightning.light_energy = 0.0
    lightning.shadow_enabled = false
    lightning.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
    add_child(lightning)


# ---------------------------------------------------------------------------
# Island (static GLB)
# ---------------------------------------------------------------------------

func _load_island() -> void:
    var packed := load(PROFILE.GLB_PATH) as PackedScene
    if packed == null:
        push_error("%s could not be loaded" % PROFILE.GLB_PATH)
        return
    var island := packed.instantiate()
    island.name = "Island"
    add_child(island)

    for node in island.find_children(PROFILE.NODES["camera"], "Camera3D", true, false):
        node.queue_free()
    for node in island.find_children(PROFILE.NODES["sun"], "Light3D", true, false):
        node.queue_free()
    for node in island.find_children(PROFILE.NODES["beam"], "Light3D", true, false):
        node.queue_free()

    var overrides := {}
    var seen := {}
    for node in island.find_children("*", "MeshInstance3D", true, false):
        var mi := node as MeshInstance3D
        var seabed := mi.name == PROFILE.NODES["seabed"]
        if seabed:
            mi.layers = LAYER_SEABED
            mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
        if mi.name == PROFILE.NODES["terrain"]:
            var terrain_mat := _make_terrain_material(mi.mesh)
            if terrain_mat != null:
                mi.material_override = terrain_mat
                continue
        var mesh := mi.mesh
        if mesh == null:
            continue
        var has_wind := false
        for s in range(mesh.get_surface_count()):
            var mat := mesh.surface_get_material(s)
            if mat == null:
                continue
            var key := _material_key(mat)
            seen[key] = true
            if PROFILE.WIND_SWAY.has(key):
                has_wind = true
            if not overrides.has(key):
                overrides[key] = _make_override(key, mat)
            var ov: Material = overrides[key]
            if ov != null:
                mi.set_surface_override_material(s, ov)
        if has_wind:
            mi.extra_cull_margin = 2.0
    print("[godot] materials: ", seen.keys())

    _grab_light(island, PROFILE.NODES["compass"])
    _grab_light(island, PROFILE.NODES["string"])
    var torch_pattern: String = PROFILE.NODES["torch_prefix"] + "*"
    for node in island.find_children(torch_pattern, "OmniLight3D", true, false):
        var lamp := node as OmniLight3D
        lamp.omni_range = PROFILE.TORCH_RANGE
        lamp.shadow_enabled = false
        torch_lights.append(lamp)
    if torch_lights.is_empty():
        _fallback_torches(island)

    var lh := island.find_child(PROFILE.NODES["lighthouse"], true, false)
    if lh is OmniLight3D:
        lighthouse_light = lh as OmniLight3D
        lighthouse_light.omni_range = PROFILE.LIGHTHOUSE_RANGE
        lighthouse_light.shadow_enabled = false
        lighthouse_light.light_volumetric_fog_energy = 1.2

    _build_lighthouse_beam(island)

    rig.current = true
    rig.cull_mask = ALL_LAYERS


func _grab_light(island: Node, light_name: String) -> void:
    var node := island.find_child(light_name, true, false)
    if node is OmniLight3D:
        var lamp := node as OmniLight3D
        lamp.shadow_enabled = false
        if light_name == PROFILE.NODES["compass"]:
            compass_light = lamp
        elif light_name == PROFILE.NODES["string"]:
            string_light = lamp
            string_light.omni_range = PROFILE.STRING_RANGE


func _fallback_torches(island: Node) -> void:
    var arena := island.find_child(PROFILE.NODES["arena"], true, false)
    if arena == null or not arena.has_meta("torch_lights"):
        return
    var raw := str(arena.get_meta("torch_lights"))
    var arr = JSON.parse_string(raw)
    if not (arr is Array):
        return
    for item in arr:
        if not (item is Array) or (item as Array).size() < 3:
            continue
        var p := Vector3(float(item[0]), float(item[2]), -float(item[1]))
        var lamp := OmniLight3D.new()
        lamp.light_color = Color(1.0, 0.62, 0.28)
        lamp.omni_range = PROFILE.TORCH_RANGE
        lamp.position = p
        add_child(lamp)
        torch_lights.append(lamp)


func _build_lighthouse_beam(island: Node) -> void:
    var origin := island.find_child(PROFILE.NODES["beam_origin"], true, false) as Node3D
    var pos: Vector3 = PROFILE.BEAM["fallback_pos"]
    if origin != null:
        pos = origin.global_position

    beam_pivot = Node3D.new()
    beam_pivot.name = "LighthouseBeamPivot"
    add_child(beam_pivot)
    beam_pivot.global_position = pos

    beam = SpotLight3D.new()
    beam.name = "LIGHT_BeamRuntime"
    beam.rotation_degrees = PROFILE.BEAM["rotation_deg"]
    beam.light_color = PROFILE.BEAM["color"]
    beam.light_energy = PROFILE.BEAM["energy"]
    beam.spot_range = PROFILE.BEAM["range"]
    beam.spot_angle = PROFILE.BEAM["angle"]
    beam.spot_angle_attenuation = PROFILE.BEAM["angle_attenuation"]
    beam.spot_attenuation = PROFILE.BEAM["attenuation"]
    beam.light_volumetric_fog_energy = PROFILE.BEAM["fog_energy"]
    beam.shadow_enabled = false
    beam_pivot.add_child(beam)


func _material_key(mat: Material) -> String:
    var n := mat.resource_name.to_lower().strip_edges()
    if n == "" and mat is StandardMaterial3D:
        var tex := (mat as StandardMaterial3D).albedo_texture
        if tex != null:
            n = tex.resource_name.to_lower().strip_edges()
    for key in PROFILE.WIND_SWAY.keys():
        if n.contains(String(key)):
            return String(key)
    return n


func _make_terrain_material(mesh: Mesh) -> ShaderMaterial:
    if mesh == null:
        return null
    var layers: Dictionary = PROFILE.TERRAIN_MATERIALS
    var albedo := {}
    var normals := {}
    for s in range(mesh.get_surface_count()):
        var std := mesh.surface_get_material(s) as StandardMaterial3D
        if std == null:
            continue
        var key := _material_key(std)
        if std.albedo_texture != null:
            albedo[key] = std.albedo_texture
        if std.normal_texture != null:
            normals[key] = std.normal_texture
    for src in layers.values():
        if not albedo.has(src):
            return null
    var sm := ShaderMaterial.new()
    sm.shader = TERRAIN_SHADER
    sm.set_shader_parameter("albedo_sand", albedo[layers["sand"]])
    sm.set_shader_parameter("albedo_wet", albedo[layers["wet"]])
    sm.set_shader_parameter("albedo_grass", albedo[layers["grass"]])
    sm.set_shader_parameter("albedo_rock", albedo[layers["rock"]])
    sm.set_shader_parameter("normal_sand", normals.get(layers["sand"]))
    sm.set_shader_parameter("normal_grass", normals.get(layers["grass"]))
    sm.set_shader_parameter("normal_rock", normals.get(layers["rock"]))
    return sm


func _make_override(key: String, mat: Material) -> Material:
    if PROFILE.WIND_SWAY.has(key) and mat is StandardMaterial3D:
        var std := mat as StandardMaterial3D
        var sm := ShaderMaterial.new()
        sm.shader = WIND_SHADER
        sm.set_shader_parameter("albedo_tex", std.albedo_texture)
        sm.set_shader_parameter("tint", std.albedo_color)
        sm.set_shader_parameter("sway_amount", float(PROFILE.WIND_SWAY[key]))
        sm.set_shader_parameter("flutter", float(PROFILE.WIND_FLUTTER[key]))
        sm.set_shader_parameter("alpha_cut", 0.45)
        sm.set_shader_parameter("brightness", float(PROFILE.WIND_BRIGHTNESS.get(key, 1.0)))
        wind_mats.append(sm)
        return sm

    if key == PROFILE.MATERIAL_SEABED:
        return null

    if mat is StandardMaterial3D:
        var dup := (mat as StandardMaterial3D).duplicate() as StandardMaterial3D
        # The mirrored reflection camera looks at the island from below.
        dup.cull_mode = BaseMaterial3D.CULL_DISABLED
        if key in PROFILE.CULL_BACK_MATERIALS:
            dup.cull_mode = BaseMaterial3D.CULL_BACK
        return dup
    return null


# ---------------------------------------------------------------------------
# Ocean + planar reflection
# ---------------------------------------------------------------------------

func _build_ocean() -> void:
    ocean_mat = ShaderMaterial.new()
    ocean_mat.shader = OCEAN_SHADER
    ocean_mat.set_shader_parameter("water_normal", load("res://island_arena/assets/water_normal.png"))
    ocean_mat.set_shader_parameter("foam_tex", load("res://island_arena/assets/foam.png"))
    var shore: Dictionary = PROFILE.SHORE
    ocean_mat.set_shader_parameter("shore_base", shore["base"])
    ocean_mat.set_shader_parameter("shore_wave_1", shore["wave_1"])
    ocean_mat.set_shader_parameter("shore_wave_2", shore["wave_2"])
    ocean_mat.set_shader_parameter("shore_wave_3", shore["wave_3"])

    ocean = MeshInstance3D.new()
    ocean.name = "OCEAN_Surface"
    ocean.mesh = _make_ocean_mesh()
    ocean.material_override = ocean_mat
    ocean.layers = LAYER_WATER
    ocean.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    ocean.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
    add_child(ocean)
    print("[godot] ocean aabb=", ocean.get_aabb(), " surfaces=", ocean.mesh.get_surface_count())

    refl_vp = SubViewport.new()
    refl_vp.name = "ReflectionViewport"
    refl_vp.size = Vector2i(960, 540)
    refl_vp.msaa_3d = Viewport.MSAA_DISABLED
    refl_vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
    refl_vp.use_taa = false
    refl_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    refl_vp.world_3d = get_viewport().world_3d
    add_child(refl_vp)

    refl_env = env.duplicate()
    refl_env.glow_enabled = false
    refl_env.ssao_enabled = false
    refl_env.ssil_enabled = false
    refl_env.volumetric_fog_enabled = false
    refl_env.fog_density = env.fog_density * 0.7

    refl_cam = Camera3D.new()
    refl_cam.name = "ReflectionCamera"
    refl_cam.fov = rig.fov
    refl_cam.near = 0.2
    refl_cam.far = 9000.0
    refl_cam.cull_mask = ALL_LAYERS & ~(LAYER_SEABED | LAYER_WATER | LAYER_FX)
    refl_cam.environment = refl_env
    refl_vp.add_child(refl_cam)
    refl_cam.current = true

    ocean_mat.set_shader_parameter("reflection_tex", refl_vp.get_texture())


func _make_ocean_mesh() -> ArrayMesh:
    var segs := 256
    var rings := 168
    var r0 := 4.0
    var r1 := 24000.0
    var count := (rings + 1) * segs
    var verts := PackedVector3Array()
    var normals := PackedVector3Array()
    var indices := PackedInt32Array()
    verts.resize(count)
    normals.resize(count)
    var idx := 0
    for j in range(rings + 1):
        var r: float = r0 * pow(r1 / r0, float(j) / float(rings))
        for i in range(segs):
            var a := TAU * float(i) / float(segs)
            verts[idx] = Vector3(cos(a) * r, 0.0, sin(a) * r)
            normals[idx] = Vector3.UP
            idx += 1
    for j in range(rings):
        for i in range(segs):
            var a0 := j * segs + i
            var a1 := j * segs + (i + 1) % segs
            var b0 := (j + 1) * segs + i
            var b1 := (j + 1) * segs + (i + 1) % segs
            indices.append(a0)
            indices.append(b0)
            indices.append(b1)
            indices.append(a0)
            indices.append(b1)
            indices.append(a1)
    var arrays := []
    arrays.resize(Mesh.ARRAY_MAX)
    arrays[Mesh.ARRAY_VERTEX] = verts
    arrays[Mesh.ARRAY_NORMAL] = normals
    arrays[Mesh.ARRAY_INDEX] = indices
    var mesh := ArrayMesh.new()
    mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
    return mesh


func _update_reflection() -> void:
    if refl_cam == null:
        return
    var pos := rig.global_position
    var rot := rig.rotation
    var basis := Basis.from_euler(Vector3(-rot.x, rot.y, -rot.z))
    refl_cam.global_transform = Transform3D(basis, Vector3(pos.x, -pos.y, pos.z))
    refl_cam.fov = rig.fov
    refl_cam.near = rig.near
    refl_cam.far = rig.far


# ---------------------------------------------------------------------------
# Rain, UI, capture
# ---------------------------------------------------------------------------

func _build_weather_fx() -> void:
    var pm := ParticleProcessMaterial.new()
    pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
    pm.emission_box_extents = Vector3(27.0, 2.0, 27.0)
    pm.direction = Vector3(0.0, -1.0, 0.0)
    pm.spread = 4.0
    pm.initial_velocity_min = 28.0
    pm.initial_velocity_max = 38.0
    pm.gravity = Vector3(0.0, -12.0, 0.0)
    pm.scale_min = 0.55
    pm.scale_max = 1.15
    pm.lifetime_randomness = 0.40

    var quad := QuadMesh.new()
    quad.size = Vector2(0.014, 0.85)
    var grad := Gradient.new()
    grad.set_color(0, Color(0.68, 0.77, 0.88, 0.0))
    grad.set_color(1, Color(0.68, 0.77, 0.88, 0.0))
    grad.add_point(0.30, Color(0.68, 0.77, 0.88, 0.24))
    grad.add_point(0.68, Color(0.68, 0.77, 0.88, 0.24))
    var grad_tex := GradientTexture2D.new()
    grad_tex.gradient = grad
    grad_tex.width = 4
    grad_tex.height = 64
    grad_tex.fill_from = Vector2(0.0, 0.0)
    grad_tex.fill_to = Vector2(0.0, 1.0)
    var rain_mat := StandardMaterial3D.new()
    rain_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    rain_mat.albedo_texture = grad_tex
    rain_mat.albedo_color = Color(1.0, 1.0, 1.0, 0.85)
    rain_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    rain_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
    rain_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
    rain_mat.disable_receive_shadows = true
    quad.material = rain_mat

    rain = GPUParticles3D.new()
    rain.name = "FX_Rain"
    rain.amount = 11000
    rain.lifetime = 1.35
    rain.preprocess = 0.8
    rain.local_coords = false
    rain.visibility_aabb = AABB(Vector3(-48.0, -36.0, -48.0), Vector3(96.0, 72.0, 96.0))
    rain.process_material = pm
    rain.draw_pass_1 = quad
    rain.layers = LAYER_FX
    rain.visible = false
    rain.emitting = false
    add_child(rain)

    var fx_layer := CanvasLayer.new()
    fx_layer.layer = 12
    add_child(fx_layer)
    flash_rect = ColorRect.new()
    flash_rect.color = Color(0.78, 0.86, 1.0, 0.0)
    flash_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
    flash_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    fx_layer.add_child(flash_rect)

    var vig_layer := CanvasLayer.new()
    vig_layer.layer = 13
    add_child(vig_layer)
    var vig := ColorRect.new()
    vig.mouse_filter = Control.MOUSE_FILTER_IGNORE
    vig.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    vignette_mat = ShaderMaterial.new()
    vignette_mat.shader = VIGNETTE_SHADER
    vig.material = vignette_mat
    vig_layer.add_child(vig)


func _build_ui() -> void:
    var ui := ArenaHud.build(self, PROFILE.HUD)
    hud = ui["hud"]
    hint_label = ui["hint"]
    var root: Control = ui["root"]

    weather_label = ArenaHud.label(PROFILE.HUD["weather_placeholder"], 20,
            Color(1.0, 0.94, 0.86, 0.95), ui["font"], ui["outline"])
    weather_label.set_anchors_preset(Control.PRESET_TOP_RIGHT)
    weather_label.position = Vector2(-420, 44)
    weather_label.size = Vector2(364, 40)
    weather_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
    root.add_child(weather_label)


func _take_shot() -> void:
    var path := capture_path
    if path == "":
        path = "user://" + String(PROFILE.HUD["shot_name"])
    ArenaCapture.take_shot(self, path, refl_vp)
