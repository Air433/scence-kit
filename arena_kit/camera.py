"""Hero camera."""
from __future__ import annotations

import bpy

from . import config, util


def build_camera():
    data = bpy.data.cameras.new("CAM_Hero")
    data.lens = config.CAMERA_LENS
    data.sensor_width = 36.0
    data.clip_start = 0.05
    data.clip_end = 300.0
    data.dof.use_dof = True
    data.dof.focus_distance = 10.6
    data.dof.aperture_fstop = 4.0

    cam = bpy.data.objects.new("CAM_Hero", data)
    util.link_object(cam, config.C_CAMERA)
    util.link_object(cam, config.C_EXPORT)
    cam.location = config.CAMERA_LOC
    util.look_at(cam, config.CAMERA_TARGET)
    bpy.context.scene.camera = cam
    print(f"[camera] {config.CAMERA_LENS:.0f}mm at {tuple(round(v, 2) for v in config.CAMERA_LOC)}")
    return cam
