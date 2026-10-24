shader_type sky;

uniform vec4 horizon_color : source_color = vec4(0.62, 0.85, 0.89, 1.0);
uniform vec4 mid_color : source_color = vec4(0.34, 0.70, 0.87, 1.0);
uniform vec4 zenith_color : source_color = vec4(0.18, 0.50, 0.82, 1.0);
uniform vec4 warm_color : source_color = vec4(0.86, 0.69, 0.45, 1.0);
uniform vec4 ground_color : source_color = vec4(0.35, 0.48, 0.36, 1.0);
uniform vec4 sun_color : source_color = vec4(1.0, 0.89, 0.65, 1.0);
uniform vec3 sun_dir = vec3(-0.68, 0.58, 0.53);
uniform float sun_glow = 0.32;
uniform float band_strength = 0.35;

void sky() {
    vec3 d = normalize(EYEDIR);
    float h = d.y;

    vec3 col = horizon_color.rgb;
    col = mix(col, mid_color.rgb, smoothstep(0.0, 0.16, h));
    col = mix(col, zenith_color.rgb, smoothstep(0.12, 0.72, h));

    float warm = 1.0 - smoothstep(0.0, 0.09, max(h, 0.0));
    col = mix(col, warm_color.rgb, warm * 0.55);
    col = mix(col, ground_color.rgb, 1.0 - smoothstep(-0.05, 0.02, h));

    // Quantise the gradient for the flat cel backdrop.
    vec3 bands = floor(col * 8.0 + 0.5) / 8.0;
    col = mix(col, bands, band_strength);

    float sd = max(dot(d, normalize(sun_dir)), 0.0);
    col += sun_color.rgb * pow(sd, 24.0) * sun_glow;

    COLOR = col;
}
