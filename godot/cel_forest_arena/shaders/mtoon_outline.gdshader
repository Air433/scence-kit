shader_type spatial;
render_mode unshaded, cull_front, shadows_disabled, depth_draw_opaque;

// Inverted-hull ink line, equivalent to MToon's worldCoordinates outline
// (outlineColorFactor + outlineWidthFactor from post_export.py).

uniform float outline_width = 0.02;
uniform vec4 outline_color : source_color = vec4(0.02, 0.04, 0.03, 1.0);

void vertex() {
    VERTEX += NORMAL * outline_width;
}

void fragment() {
    ALBEDO = outline_color.rgb;
}
