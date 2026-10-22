"""Hero camera for the island render (wide, deep DOF)."""
from __future__ import annotations

from arena_kit import camera as kit_camera


def build_camera():
    cam = kit_camera.build_camera()
    cam.data.clip_end = 900.0
    cam.data.dof.focus_distance = 45.0
    cam.data.dof.aperture_fstop = 4.0
    return cam
