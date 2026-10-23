"""Hero camera for the deep-space arena."""
from __future__ import annotations

import bpy

from arena_kit import config, util


def build_camera():
    util.reset_collection(config.C_CAMERA)
    data = bpy.data.cameras.new("CAM_Hero")
    data.lens = config.CAMERA_LENS
    data.sensor_width = 36.0
    data.clip_start = 0.05
    data.clip_end = 500.0
    data.dof.use_dof = False

    cam = bpy.data.objects.new("CAM_Hero", data)
    util.link_object(cam, config.C_CAMERA)
    util.link_object(cam, config.C_EXPORT)
    cam.location = config.CAMERA_LOC
    util.look_at(cam, config.CAMERA_TARGET)
    bpy.context.scene.camera = cam
    print(f"[camera] {config.CAMERA_LENS:.0f}mm at "
          f"{tuple(round(v, 2) for v in config.CAMERA_LOC)}")
    return cam
