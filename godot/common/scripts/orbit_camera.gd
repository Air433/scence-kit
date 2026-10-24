extends Camera3D

# Shared orbit camera.  Scene-specific framing comes from scene_profile.gd:
# configure() applies lens/clamp settings, set_view() applies a preset.

@export var target := Vector3.ZERO
@export var start_yaw := 0.0
@export var start_pitch := 0.0
@export var start_distance := 20.0
@export var min_distance := 1.0
@export var max_distance := 500.0
@export var pitch_min := -12.0
@export var pitch_max := 60.0
@export var auto_orbit := true
@export var auto_orbit_speed := 0.45
@export var auto_orbit_delay := 5.0
@export var drag_sensitivity := Vector2(0.16, 0.11)

var _yaw := 0.0
var _pitch := 0.0
var _distance := 0.0
var _yaw_goal := 0.0
var _pitch_goal := 0.0
var _distance_goal := 0.0
var _dragging := false
var _idle := 0.0


func _ready() -> void:
    _yaw = start_yaw
    _pitch = start_pitch
    _distance = start_distance
    _yaw_goal = _yaw
    _pitch_goal = _pitch
    _distance_goal = _distance
    _place(true)


func configure(cfg: Dictionary) -> void:
    fov = float(cfg.get("fov", fov))
    near = float(cfg.get("near", near))
    far = float(cfg.get("far", far))
    pitch_min = float(cfg.get("pitch_min", pitch_min))
    pitch_max = float(cfg.get("pitch_max", pitch_max))
    min_distance = float(cfg.get("min_distance", min_distance))
    max_distance = float(cfg.get("max_distance", max_distance))
    auto_orbit_delay = float(cfg.get("auto_orbit_delay", auto_orbit_delay))
    auto_orbit_speed = float(cfg.get("auto_orbit_speed", auto_orbit_speed))
    _place(true)


func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton:
        var mb := event as InputEventMouseButton
        if mb.button_index == MOUSE_BUTTON_LEFT or mb.button_index == MOUSE_BUTTON_RIGHT:
            _dragging = mb.pressed
            if mb.pressed:
                _idle = 0.0
        elif mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_UP:
            _distance_goal = clamp(_distance_goal * 0.92, min_distance, max_distance)
        elif mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            _distance_goal = clamp(_distance_goal * 1.08, min_distance, max_distance)
    elif event is InputEventMouseMotion and _dragging:
        var mm := event as InputEventMouseMotion
        _yaw_goal -= mm.relative.x * drag_sensitivity.x
        _pitch_goal = clamp(
            _pitch_goal - mm.relative.y * drag_sensitivity.y,
            pitch_min, pitch_max)
        _idle = 0.0


func _process(delta: float) -> void:
    _idle += delta
    if _dragging:
        _idle = 0.0
    if auto_orbit and _idle > auto_orbit_delay:
        var ease: float = clampf((_idle - auto_orbit_delay) * 0.4, 0.0, 1.0)
        _yaw_goal += auto_orbit_speed * delta * ease

    var k := 1.0 - exp(-delta * 6.0)
    _yaw = lerp_angle(_yaw, _yaw_goal, k)
    _pitch = lerp(_pitch, _pitch_goal, k)
    _distance = lerp(_distance, _distance_goal, k)
    _place(false)


func set_view(t: Vector3, yaw_deg: float, pitch_deg: float, dist: float) -> void:
    target = t
    _yaw = yaw_deg
    _pitch = pitch_deg
    _distance = dist
    _yaw_goal = yaw_deg
    _pitch_goal = pitch_deg
    _distance_goal = dist
    _place(true)


func _place(instant: bool) -> void:
    var yr := deg_to_rad(_yaw)
    var pr := deg_to_rad(_pitch)
    var offset := Vector3(
        sin(yr) * cos(pr),
        sin(pr),
        cos(yr) * cos(pr)
    ) * _distance
    global_position = target + offset
    if offset.length() > 0.01:
        look_at(target, Vector3.UP)
    if instant:
        reset_physics_interpolation()
