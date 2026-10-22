shader_type canvas_item;

uniform float strength : hint_range(0.0, 1.0) = 0.45;
uniform vec4 tint : source_color = vec4(0.012, 0.014, 0.022, 1.0);

void fragment() {
    vec2 uv = SCREEN_UV - vec2(0.5);
    uv.x *= 1.22;
    float r = length(uv);
    float a = smoothstep(0.30, 0.82, r) * strength;
    COLOR = vec4(tint.rgb, a);
}
