class_name ArenaHud
extends RefCounted

# Shared HUD for every arena.  Text and palette come from scene_profile.HUD.

const FONT_NAMES := [
    "Microsoft YaHei UI", "Microsoft YaHei", "SimHei",
    "Noto Sans CJK SC", "Source Han Sans SC",
]

const DEFAULT_OUTLINE := Color(0.03, 0.03, 0.04, 0.7)
const DEFAULT_HINT_SIZE := 15


static func make_font() -> SystemFont:
    var font := SystemFont.new()
    font.font_names = PackedStringArray(FONT_NAMES)
    return font


static func build(host: Node, cfg: Dictionary) -> Dictionary:
    var font := make_font()
    var outline: Color = cfg.get("outline_color", DEFAULT_OUTLINE)

    var hud := CanvasLayer.new()
    hud.layer = 20
    host.add_child(hud)

    var root := Control.new()
    root.mouse_filter = Control.MOUSE_FILTER_IGNORE
    hud.add_child(root)
    root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

    var title := label(cfg.get("title", ""), 32,
            cfg.get("title_color", Color(1.0, 0.96, 0.90)), font, outline)
    title.position = Vector2(56, 38)
    root.add_child(title)

    var subtitle := label(cfg.get("subtitle", ""), 14,
            cfg.get("subtitle_color", Color(1.0, 0.88, 0.72, 0.85)), font, outline)
    subtitle.position = Vector2(59, 84)
    root.add_child(subtitle)

    var hint := label(cfg.get("hint", ""), int(cfg.get("hint_size", DEFAULT_HINT_SIZE)),
            cfg.get("hint_color", Color(1.0, 0.95, 0.88, 0.72)), font, outline)
    hint.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
    hint.position = Vector2(56, -72)
    hint.size = Vector2(1100, 34)
    root.add_child(hint)

    return {
        "hud": hud,
        "root": root,
        "font": font,
        "outline": outline,
        "title": title,
        "subtitle": subtitle,
        "hint": hint,
    }


static func label(text: String, size: int, color: Color, font: Font,
        outline: Color = DEFAULT_OUTLINE) -> Label:
    var l := Label.new()
    l.text = text
    l.add_theme_font_override("font", font)
    l.add_theme_font_size_override("font_size", size)
    l.add_theme_color_override("font_color", color)
    l.add_theme_color_override("font_outline_color", outline)
    l.add_theme_constant_override("outline_size", 8)
    l.mouse_filter = Control.MOUSE_FILTER_IGNORE
    return l
