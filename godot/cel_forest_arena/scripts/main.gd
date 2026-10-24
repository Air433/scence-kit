extends Node3D

const PROFILE := preload("res://cel_forest_arena/scripts/scene_profile.gd")
const MTOON_SHADER: Shader = preload("res://cel_forest_arena/shaders/mtoon.gdshader")
const OUTLINE_SHADER: Shader = preload("res://cel_forest_arena/shaders/mtoon_outline.gdshader")
const SKY_SHADER: Shader = preload("res://cel_forest_arena/shaders/cel_sky.gdshader")

@onready var rig: Camera3D = $Camera

var env: Environment
var sky_mat: ShaderMaterial
var sun: DirectionalLight3D
var fill: DirectionalLight3D
var arena: Node3D

var hud: CanvasLayer
var hint_label: Label
var capture_mode := false
var capture_path := ""
var capture_left := -1
var cam_preset: String = PROFILE.DEFAULT_CAM
var nofog := false


func _ready() -> void:
    var args := ArenaCapture.parse_args()
    capture_path = String(args["shot"])
    capture_mode = capture_path != ""
    capture_left = int(args["frames"])
    if String(args["cam"]) != "":
        cam_preset = String(args["cam"])
    nofog = bool(args["nofog"])

    _build_environment()
    rig.call("configure", PROFILE.CAMERA)
    _load_arena()
    _apply_cam_preset(cam_preset)
    _build_ui()

    if capture_mode:
        rig.set("auto_orbit", false)
        hud.visible = false
        DisplayServer.window_set_size(Vector2i(1600, 900))
        if capture_left < 0:
            capture_left = PROFILE.DEFAULT_FRAMES
    print("[godot] cel forest ready, capture=", capture_mode)


func _process(_delta: float) -> void:
    if capture_mode and capture_left > 0:
        capture_left -= 1
        if capture_left == 0:
            _take_shot()


func _unhandled_input(event: InputEvent) -> void:
    if capture_mode:
        return
    if event is InputEventKey and event.pressed and not event.echo:
        match (event as InputEventKey).physical_keycode:
            KEY_1:
                _apply_cam_preset("hero")
            KEY_2:
                _apply_cam_preset("altar")
            KEY_3:
                _apply_cam_preset("wide")
            KEY_4:
                _apply_cam_preset("top")
            KEY_C:
                rig.set("auto_orbit", not bool(rig.get("auto_orbit")))
            KEY_H:
                hint_label.visible = not hint_label.visible


func _apply_cam_preset(preset: String) -> void:
    var presets: Dictionary = PROFILE.CAMERA_PRESETS
    var view: Dictionary = presets.get(preset, presets[PROFILE.DEFAULT_CAM])
    rig.set("auto_orbit", false)
    rig.call("set_view", view["target"], view["yaw"], view["pitch"],
             view["distance"])


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
    sky_mat.set_shader_parameter("horizon_color", PROFILE.SKY["horizon"])
    sky_mat.set_shader_parameter("mid_color", PROFILE.SKY["mid"])
    sky_mat.set_shader_parameter("zenith_color", PROFILE.SKY["zenith"])
    sky_mat.set_shader_parameter("warm_color", PROFILE.SKY["warm"])
    sky_mat.set_shader_parameter("sun_color", PROFILE.SKY["sun_color"])
    sky_mat.set_shader_parameter("sun_dir", PROFILE.SKY["sun_dir"])
    sky_mat.set_shader_parameter("band_strength", float(PROFILE.SKY["band_strength"]))
    sky.sky_material = sky_mat
    sky.radiance_size = Sky.RADIANCE_SIZE_256
    sky.process_mode = Sky.PROCESS_MODE_INCREMENTAL
    env.sky = sky

    var cfg: Dictionary = PROFILE.ENV
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = cfg["ambient_color"]
    env.ambient_light_energy = float(cfg["ambient_energy"])
    env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
    env.tonemap_mode = Environment.TONE_MAPPER_ACES
    env.tonemap_exposure = float(cfg["exposure"])
    env.tonemap_white = 6.0

    env.glow_enabled = true
    env.glow_normalized = true
    env.glow_intensity = float(cfg["glow_intensity"])
    env.glow_bloom = float(cfg["glow_bloom"])
    env.glow_hdr_threshold = float(cfg["glow_threshold"])
    env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN

    env.ssao_enabled = true
    env.ssao_radius = 1.6
    env.ssao_intensity = 0.9
    env.ssao_power = 1.4

    env.fog_enabled = not nofog
    env.fog_light_color = cfg["fog_color"]
    env.fog_density = 0.0 if nofog else float(cfg["fog_density"])
    env.fog_sky_affect = 0.25
    env.fog_aerial_perspective = 0.2
    env.fog_height = float(cfg["fog_height"])
    env.fog_height_density = 0.0 if nofog else float(cfg["fog_height_density"])

    env.volumetric_fog_enabled = not nofog
    env.volumetric_fog_density = 0.0 if nofog else float(cfg["volumetric_density"])
    env.volumetric_fog_albedo = cfg["fog_color"]
    env.volumetric_fog_length = 90.0
    env.volumetric_fog_anisotropy = 0.5
    env.volumetric_fog_sky_affect = 0.1

    env.adjustment_enabled = true
    env.adjustment_brightness = 1.0
    env.adjustment_contrast = float(cfg["contrast"])
    env.adjustment_saturation = float(cfg["saturation"])

    we.environment = env
    add_child(we)


# ---------------------------------------------------------------------------
# Arena import + MToon overrides
# ---------------------------------------------------------------------------

func _load_arena() -> void:
    var packed := load(PROFILE.GLB_PATH) as PackedScene
    if packed == null:
        push_error("%s could not be loaded" % PROFILE.GLB_PATH)
        return
    arena = packed.instantiate() as Node3D
    arena.name = "Arena"
    add_child(arena)

    for node in arena.find_children("*", "Camera3D", true, false):
        node.queue_free()

    _setup_lights(arena)

    var overrides := {}
    var seen := {}
    for node in arena.find_children("*", "MeshInstance3D", true, false):
        var mi := node as MeshInstance3D
        var mesh := mi.mesh
        if mesh == null:
            continue
        for s in range(mesh.get_surface_count()):
            var mat := mesh.surface_get_material(s)
            if mat == null:
                continue
            var key := _material_key(mat)
            seen[key] = true
            if not PROFILE.MTOON.has(key):
                continue
            if not overrides.has(key):
                overrides[key] = _make_override(key, mat)
            mi.set_surface_override_material(s, overrides[key])
    print("[godot] materials: ", seen.keys())

    rig.current = true


func _material_key(mat: Material) -> String:
    var name := mat.resource_name.to_lower().strip_edges()
    if PROFILE.MTOON.has(name):
        return name
    var keys := PROFILE.MTOON.keys()
    keys.sort_custom(func(a, b): return String(a).length() > String(b).length())
    for key in keys:
        if name.begins_with(String(key)):
            return String(key)
    return name


func _make_override(key: String, mat: Material) -> ShaderMaterial:
    var data: Dictionary = PROFILE.MTOON[key]
    var sm := ShaderMaterial.new()
    sm.shader = MTOON_SHADER
    sm.set_shader_parameter("alpha_cut", 0.5 if data.get("alpha", false) else 0.0)
    sm.set_shader_parameter("albedo_boost", 1.0)
    sm.set_shader_parameter("shade_color", data["shade"])
    sm.set_shader_parameter("rim_color", data["rim"])
    sm.set_shader_parameter("rim_mix", 0.35)
    sm.set_shader_parameter("shading_toony", 0.92)
    sm.set_shader_parameter("shading_shift", -0.02)

    if data.get("emissive", false):
        var glow: Color = data["emission"]
        sm.set_shader_parameter("use_albedo_tex", 0.0)
        sm.set_shader_parameter("albedo_tint",
                Color(glow.r * 0.35, glow.g * 0.35, glow.b * 0.35, 1.0))
        sm.set_shader_parameter("emission_color", glow)
        sm.set_shader_parameter("emission_energy", float(data["energy"]))
    elif mat is BaseMaterial3D:
        var std := mat as BaseMaterial3D
        var has_tex := std.albedo_texture != null
        sm.set_shader_parameter("use_albedo_tex", 1.0 if has_tex else 0.0)
        if has_tex:
            sm.set_shader_parameter("albedo_tex", std.albedo_texture)
        sm.set_shader_parameter("albedo_tint", std.albedo_color)

    var width := float(data.get("outline", 0.0))
    if width > 0.0:
        var om := ShaderMaterial.new()
        om.shader = OUTLINE_SHADER
        om.set_shader_parameter("outline_width", width * float(PROFILE.OUTLINE_SCALE))
        om.set_shader_parameter("outline_color", PROFILE.OUTLINE_COLOR)
        sm.next_pass = om
    return sm


func _setup_lights(root: Node) -> void:
    for node in root.find_children("*", "DirectionalLight3D", true, false):
        var lamp := node as DirectionalLight3D
        if lamp.name.begins_with("LIGHT_Sun"):
            sun = lamp
    if sun == null:
        sun = DirectionalLight3D.new()
        sun.name = "LIGHT_SunRuntime"
        add_child(sun)
        sun.rotation_degrees = Vector3(-38.0, -36.0, 0.0)
    sun.light_color = PROFILE.SUN["color"]
    sun.light_energy = float(PROFILE.SUN["energy"])
    sun.shadow_enabled = true
    sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
    sun.directional_shadow_max_distance = float(PROFILE.SUN["shadow_distance"])
    sun.shadow_bias = float(PROFILE.SUN["bias"])
    sun.shadow_normal_bias = float(PROFILE.SUN["normal_bias"])
    sun.shadow_blur = 1.0
    sun.light_angular_distance = 1.6
    sun.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY

    fill = DirectionalLight3D.new()
    fill.name = "LIGHT_FillRuntime"
    fill.light_color = PROFILE.FILL["color"]
    fill.light_energy = float(PROFILE.FILL["energy"])
    fill.shadow_enabled = false
    fill.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
    add_child(fill)
    fill.look_at_from_position(PROFILE.FILL["pos"], PROFILE.FILL["target"],
                               Vector3.UP)

    for node in root.find_children("*", "OmniLight3D", true, false):
        var lamp := node as OmniLight3D
        lamp.shadow_enabled = false
        lamp.omni_attenuation = 1.2
        lamp.light_volumetric_fog_energy = 0.35
        if lamp.name.begins_with("LIGHT_Lantern"):
            lamp.omni_range = float(PROFILE.LANTERN_RANGE)
        elif lamp.name.begins_with("LIGHT_Rune"):
            lamp.omni_range = float(PROFILE.RUNE_RANGE)
            lamp.light_volumetric_fog_energy = 0.55


# ---------------------------------------------------------------------------
# UI / capture
# ---------------------------------------------------------------------------

func _build_ui() -> void:
    var ui := ArenaHud.build(self, PROFILE.HUD)
    hud = ui["hud"]
    hint_label = ui["hint"]


func _take_shot() -> void:
    var path := capture_path
    if path == "":
        path = "user://" + String(PROFILE.HUD["shot_name"])
    ArenaCapture.take_shot(self, path)
