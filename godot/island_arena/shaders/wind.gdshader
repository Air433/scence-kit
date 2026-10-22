shader_type spatial;
render_mode cull_disabled, depth_prepass_alpha;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float sway_amount = 0.35;
uniform float flutter = 1.0;
uniform float wind = 0.45;
uniform vec3 wind_dir = vec3(0.78, 0.0, 0.55);
uniform float alpha_cut = 0.45;
uniform float brightness = 1.0;

void vertex() {
    vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    float height = clamp(UV.y, 0.0, 1.0);
    float bend = height * height;
    float strength = 0.30 + wind;

    float phase = dot(wp.xz, vec2(0.115, 0.085)) + TIME * (0.85 + wind * 0.55);
    float sway = sin(phase) * 0.65 + sin(phase * 1.73 + wp.z * 0.21) * 0.25;
    vec2 dir = normalize(wind_dir.xz + vec2(1e-4));
    vec2 offset = dir * (sway * sway_amount * bend * strength);

    offset += vec2(sin(TIME * 5.1 + wp.z * 1.7), cos(TIME * 4.3 + wp.x * 1.9))
        * (0.032 * flutter * bend) * strength;

    vec3 world_off = vec3(offset.x, 0.0, offset.y);
    VERTEX += inverse(mat3(MODEL_MATRIX)) * world_off;
}

void fragment() {
    vec4 tex = texture(albedo_tex, UV);
    ALBEDO = tex.rgb * tint.rgb * brightness;
    ALPHA = tex.a * tint.a;
    ALPHA_SCISSOR_THRESHOLD = alpha_cut;
    ROUGHNESS = 0.82;
    SPECULAR = 0.12;
    BACKLIGHT = vec3(0.17, 0.24, 0.07) * (0.6 + wind);
}
