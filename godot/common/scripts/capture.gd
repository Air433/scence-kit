class_name ArenaCapture
extends RefCounted

# Shared CLI parsing and screenshot handling for the arena scenes.

static func parse_args() -> Dictionary:
    var out := {
        "shot": "",
        "frames": -1,
        "cam": "",
        "mood": "",
        "random": false,
        "nofog": false,
    }
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--shot="):
            out["shot"] = arg.substr(7)
        elif arg.begins_with("--frames="):
            out["frames"] = int(arg.substr(9))
        elif arg.begins_with("--cam="):
            out["cam"] = arg.substr(6)
        elif arg.begins_with("--mood="):
            out["mood"] = arg.substr(7)
        elif arg == "--random":
            out["random"] = true
        elif arg == "--nofog":
            out["nofog"] = true
    return out


static func take_shot(host: Node, path: String, reflection: SubViewport = null) -> void:
    await RenderingServer.frame_post_draw
    var img := host.get_viewport().get_texture().get_image()
    var err := img.save_png(path)
    print("[shot] ", path, " error=", err, " size=", img.get_size())
    if reflection != null:
        var refl_img := reflection.get_texture().get_image()
        var refl_path := path.get_basename() + "_refl.png"
        refl_img.save_png(refl_path)
        print("[shot] reflection ", refl_path, " size=", refl_img.get_size())
    host.get_tree().quit()
