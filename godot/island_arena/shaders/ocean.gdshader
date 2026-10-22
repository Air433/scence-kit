shader_type spatial;
render_mode unshaded, cull_disabled, blend_mix, fog_disabled;

// Mirrored-camera planar reflection, filled by main.gd every frame.
uniform sampler2D reflection_tex : filter_linear, repeat_disable;
uniform sampler2D water_normal : filter_linear_mipmap, repeat_enable;
uniform sampler2D foam_tex : filter_linear_mipmap, repeat_enable;

uniform vec4 deep_color : source_color = vec4(0.02, 0.17, 0.21, 1.0);
uniform vec4 shallow_color : source_color = vec4(0.10, 0.54, 0.50, 1.0);
uniform vec4 sky_color : source_color = vec4(0.66, 0.75, 0.81, 1.0);
uniform vec4 sun_color : source_color = vec4(1.0, 0.82, 0.63, 1.0);
uniform vec4 horizon_warm : source_color = vec4(1.0, 0.75, 0.54, 1.0);
uniform vec4 horizon_cool : source_color = vec4(0.39, 0.58, 0.72, 1.0);
uniform vec3 sun_dir = vec3(-0.58, 0.13, -0.80);
uniform float wave_scale = 1.0;
uniform float foam_amount = 1.0;
uniform float reflection_amount = 0.95;
uniform float wind = 0.45;
uniform float night = 0.0;
uniform float storm = 0.0;
uniform float rain = 0.0;
uniform float light_level = 1.0;
uniform float flash = 0.0;

// Shoreline harmonics, set from SceneProfile.SHORE. Each vec3 is
// (amplitude, frequency, phase) and must match scenes/<name>/layout.py.
uniform float shore_base = 33.0;
uniform vec3 shore_wave_1 = vec3(3.0, 3.0, 0.8);
uniform vec3 shore_wave_2 = vec3(1.4, 7.0, 2.2);
uniform vec3 shore_wave_3 = vec3(0.7, 11.0, 0.1);

varying vec3 v_world;
varying float v_wave;

float shore_radius(float a) {
    return shore_base
        + shore_wave_1.x * sin(shore_wave_1.y * a + shore_wave_1.z)
        + shore_wave_2.x * sin(shore_wave_2.y * a + shore_wave_2.z)
        + shore_wave_3.x * sin(shore_wave_3.y * a + shore_wave_3.z);
}

float wave_height(vec2 p, float t) {
    float h = 0.0;
    h += 0.38 * sin(dot(p, vec2(0.86, 0.51)) * 0.105 + t * 0.55);
    h += 0.24 * sin(dot(p, vec2(-0.42, 0.91)) * 0.175 + t * 0.78 + 1.7);
    h += 0.12 * sin(dot(p, vec2(0.97, -0.24)) * 0.330 + t * 1.15 + 3.9);
    h += 0.06 * sin(dot(p, vec2(-0.71, -0.70)) * 0.520 + t * 1.60 + 0.6);
    h += 0.03 * sin(dot(p, vec2(0.13, 0.99)) * 1.050 + t * 2.30 + 2.2);
    return h;
}

float shore_falloff(vec2 p) {
    float a = atan(-p.y, p.x);
    float d = length(p) / max(shore_radius(a), 1.0);
    return mix(0.22, 1.0, smoothstep(0.90, 1.30, d));
}

// Analytic approximation of the island heightfield, used for water depth and
// swash foam.  Dune noise is omitted on purpose; the bands are wide enough.
float terrain_h(vec2 p) {
    float a = atan(-p.y, p.x);
    float d = length(p) / max(shore_radius(a), 1.0);
    float h = 4.35;
    h -= 4.9 * smoothstep(0.68, 0.965, d);
    h -= 1.4 * smoothstep(0.94, 1.045, d);
    if (d > 1.045) {
        h -= 17.0 * pow(d - 1.045, 0.92);
    }
    float dh = (p.x - 20.5) * (p.x - 20.5) + (p.y + 21.5) * (p.y + 21.5);
    h += 7.4 * exp(-dh / 144.5) * (1.0 - smoothstep(1.0, 1.06, d));
    float flat_f = 1.0 - smoothstep(13.75, 18.25, length(p));
    h = mix(h, 4.33, flat_f);
    float dl = length(p - vec2(20.5, -21.5));
    float pad = 1.0 - smoothstep(7.0, 12.0, dl);
    h = mix(h, 6.6, pad);
    return h;
}

void vertex() {
    vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    float amp = wave_scale * shore_falloff(wp.xz);
    float h = wave_height(wp.xz, TIME) * amp;

    float e = 1.5;
    float hx = wave_height(wp.xz + vec2(e, 0.0), TIME) * amp;
    float hz = wave_height(wp.xz + vec2(0.0, e), TIME) * amp;

    VERTEX.y += h;
    NORMAL = normalize(vec3(h - hx, e, h - hz));

    v_world = wp + vec3(0.0, h, 0.0);
    v_wave = h;
}

void fragment() {
    vec3 N = normalize(NORMAL);
    vec2 p = v_world.xz;

    vec2 uv1 = p * 0.048 + vec2(TIME * 0.011, TIME * 0.007);
    vec2 uv2 = p * 0.125 - vec2(TIME * 0.017, TIME * 0.012);
    vec3 n1 = texture(water_normal, uv1).xyz * 2.0 - 1.0;
    vec3 n2 = texture(water_normal, uv2).xyz * 2.0 - 1.0;
    float nstrength = 0.24 + clamp(wind, 0.0, 1.5) * 0.20;
    N = normalize(N + vec3(n1.x + n2.x * 0.7, 0.0, n1.y + n2.y * 0.7) * nstrength);

    if (rain > 0.01) {
        vec3 rn = texture(water_normal, p * 0.62 + vec2(TIME * 0.03, TIME * 0.55)).xyz * 2.0 - 1.0;
        N = normalize(N + vec3(rn.x, 0.0, rn.y) * rain * 0.30);
    }

    vec3 V = normalize(CAMERA_POSITION_WORLD - v_world);
    float ndv = clamp(dot(N, V), 0.0, 1.0);
    float fres = 0.02 + 0.98 * pow(1.0 - ndv, 5.0);

    float depth = -terrain_h(p);
    float deep_t = smoothstep(0.7, 10.0, max(depth, 0.0));

    vec3 body = mix(shallow_color.rgb, deep_color.rgb, deep_t);
    body *= 0.38 + 0.85 * light_level;
    body = mix(body, sky_color.rgb * (0.14 + 0.55 * light_level), fres * 0.42);
    body *= 1.0 - storm * 0.18;

    vec2 ruv = vec2(SCREEN_UV.x, 1.0 - SCREEN_UV.y);
    ruv += vec2(n1.x + n2.x, -(n1.y + n2.y)) * 0.012;
    ruv = clamp(ruv, vec2(0.002), vec2(0.998));
    vec3 refl = texture(reflection_tex, ruv).rgb * 1.06;
    float rlum = dot(refl, vec3(0.2126, 0.7152, 0.0722));
    refl *= 1.0 - 0.55 * smoothstep(0.62, 1.0, rlum);

    float refl_amt = clamp(fres * reflection_amount, 0.0, 1.0);
    vec3 col = mix(body, refl, refl_amt);

    vec3 L = normalize(sun_dir);
    vec3 H = normalize(L + V);
    float nh = max(dot(N, H), 0.0);
    float glint = pow(nh, 300.0) * 1.7 + pow(nh, 64.0) * 0.10;
    col += sun_color.rgb * glint * (0.25 + 0.85 * light_level) * (1.0 - night * 0.55);

    float shore_a = atan(-p.y, p.x);
    float lace = texture(foam_tex, p * 0.075 + vec2(TIME * 0.004, TIME * 0.009)).a;
    float lace2 = texture(foam_tex, p * 0.190 - vec2(TIME * 0.011, TIME * 0.005)).a;
    float lace_big = texture(foam_tex, p * 0.021 + vec2(TIME * 0.002, -TIME * 0.0014)).a;
    float lace_mix = clamp(lace * 0.85 + lace2 * 0.55, 0.0, 1.3);

    // Break the analytic depth rings with low-frequency foam noise so the
    // swash reads as broken surf instead of concentric circles.
    float ang_n = sin(shore_a * 13.0 + p.x * 0.07) * 0.45 + sin(shore_a * 29.0 - p.y * 0.11) * 0.22;
    float wobble = (lace_big - 0.5) * 1.15 + (lace - 0.5) * 0.45;
    float dvar = max(depth, 0.0) + wobble + ang_n * 0.45;
    float foam_zone = 1.0 - smoothstep(0.05, 2.1, dvar);

    float wave_phase = dvar * 6.2 - TIME * 1.35 + sin(shore_a * 7.0 + lace_big * 2.6) * 1.15 + ang_n * 2.2;
    float band = smoothstep(-0.25, 0.42, sin(wave_phase));
    float foam = foam_zone * (0.06 + 0.65 * lace_mix) * (0.25 + 0.75 * band);

    float swash = 1.0 - smoothstep(0.0, 0.55, abs(dvar));
    foam += swash * (0.12 + 0.35 * lace_mix) * 0.35;

    float crest = smoothstep(0.55, 1.0, v_wave / max(wave_scale, 0.25));
    foam += crest * (0.12 + 0.42 * lace_big) * 0.20 * foam_amount;
    foam *= foam_amount * (0.85 + storm * 0.5);
    foam = clamp(foam, 0.0, 0.86);

    vec3 foam_col = vec3(0.92, 0.95, 0.95) * (0.18 + 0.90 * light_level);
    foam_col += sun_color.rgb * 0.08 * (1.0 - night);
    col = mix(col, foam_col, foam);

    col += vec3(0.30, 0.40, 0.50) * flash;

    // Far water dissolves into the same horizon gradient the sky draws, so the
    // plane edge never reads as a hard line.
    vec3 vd = normalize(vec3(p.x - CAMERA_POSITION_WORLD.x, 0.0,
        p.y - CAMERA_POSITION_WORLD.z) + vec3(1e-5));
    vec3 fs = normalize(vec3(L.x, 0.0, L.z) + vec3(1e-5));
    float az = acos(clamp(dot(vd, fs), -1.0, 1.0));
    vec3 hcol = mix(horizon_cool.rgb, horizon_warm.rgb, exp(-az * 2.2));
    hcol += sun_color.rgb * exp(-az * 1.7) * 0.20 * (1.0 - night) * (1.0 - storm * 0.55);
    float dist = length(CAMERA_POSITION_WORLD.xz - p);
    float haze = smoothstep(2200.0, 16000.0, dist);
    col = mix(col, hcol, haze * 0.88);

    // Shallow water is translucent so the sand and seabed read through the
    // surf; deep water becomes fully opaque a few metres out.
    float alpha = mix(0.30, 0.97, smoothstep(0.0, 5.0, max(depth, 0.0)));
    alpha = max(alpha, fres * 0.80);
    alpha = max(alpha, foam * 0.92);
    ALPHA = clamp(alpha, 0.0, 1.0);

    ALBEDO = col;
}
