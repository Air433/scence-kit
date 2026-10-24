extends Camera3D

@export var target := Vector3(0.0, 2.9, -1.5)
@export var start_yaw := 17.9
@export var start_pitch := -1.4
@export var start_distance := 11.7
@export var min_distance := 5.0
@export var max_distance := 30.0
@export var auto_orbit := true
@export var auto_orbit_speed := 0.45

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
    fov = 46.0
    near = 0.1
    far = 400.0
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
        _yaw_goal -= mm.relative.x * 0.16
        _pitch_goal = clamp(_pitch_goal - mm.relative.y * 0.11, -12.0, 60.0)
        _idle = 0.0

func _process(delta: float) -> void:
    _idle += delta
    if _dragging:
        _idle = 0.0
    if auto_orbit and _idle > 5.0:
        var ease: float = clampf((_idle - 5.0) * 0.4, 0.0, 1.0)
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

func _place(_instant: bool) -> void:
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
