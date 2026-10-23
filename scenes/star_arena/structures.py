"""Arcade, gate and halo assembled into the arch collection."""
from __future__ import annotations

from arena_kit import config, util

from . import arcade, gate


def build_structures(mats):
    util.reset_collection(config.C_ARCH)
    info = {}
    info.update(arcade.build_arcade(mats))
    info.update(gate.build_gate(mats))
    print("[structures] colonnade, gate and halo complete")
    return info
