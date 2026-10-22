shader_type sky;

uniform vec4 zenith_color : source_color = vec4(0.17, 0.31, 0.45, 1.0);
uniform vec4 horizon_color : source_color = vec4(1.0, 0.69, 0.45, 1.0);
uniform vec4 horizon_cool : source_color = vec4(0.62, 0.72, 0.80, 1.0);
uniform vec4 ground_color : source_color = vec4(0.13, 0.20, 0.24, 1.0);
uniform vec4 cloud_lit : source_color = vec4(1.0, 0.81, 0.62, 1.0);
uniform vec4 cloud_shadow : source_color = vec4(0.42, 0.40, 0.46, 1.0);
uniform vec4 sun_color : source_color = vec4(1.0, 0.82, 0.63, 1.0);
uniform vec4 moon_color : source_color = vec4(0.80, 0.87, 1.0, 1.0);
uniform vec3 sun_dir = vec3(-0.58, 0.13, -0.80);
uniform vec3 moon_dir = vec3(0.45, 0.55, -0.70);
uniform float cloud_cover = 0.5;
uniform float cloud_speed = 0.6;
uniform float night = 0.0;
uniform float storm = 0.0;
uniform float flash = 0.0;

float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float vnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), u.x),
               mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), u.x), u.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.52;
    for (int i = 0; i < 4; i++) {
        v += a * vnoise(p);
        p = p * 2.04 + vec2(11.3, 7.1);
        a *= 0.5;
    }
    return v;
}

void sky() {
    vec3 d = normalize(EYEDIR);
    float h = d.y;
    float up = clamp(h, 0.0, 1.0);

    vec3 sd3 = normalize(sun_dir);
    float sd = max(dot(d, sd3), 0.0);

    // Peach near the sun azimuth, cool marine blue on the far side.
    vec3 flat_d = normalize(vec3(d.x, 0.0, d.z) + vec3(1e-5));
    vec3 flat_s = normalize(vec3(sd3.x, 0.0, sd3.z) + vec3(1e-5));
    float az = acos(clamp(dot(flat_d, flat_s), -1.0, 1.0));
    float az_warm = exp(-az * 2.2);
    vec3 hcol = mix(horizon_cool.rgb, horizon_color.rgb, az_warm);

    vec3 col = mix(hcol, zenith_color.rgb, pow(up, 0.46));
    col = mix(col, ground_color.rgb, 1.0 - smoothstep(-0.14, 0.0, h));

    float horizon_glow = exp(-az * 1.7) * exp(-abs(h) * 5.0);
    col += sun_color.rgb * horizon_glow * 0.32 * (1.0 - night) * (1.0 - storm * 0.55);

    col += sun_color.rgb * pow(sd, 90.0) * 0.42 * (1.0 - night) * (1.0 - storm * 0.6);
    float disk = smoothstep(0.99955, 0.99985, sd);
    col += sun_color.rgb * disk * 16.0 * (1.0 - night) * (1.0 - storm * 0.8);

    vec3 md3 = normalize(moon_dir);
    float md = max(dot(d, md3), 0.0);
    col += moon_color.rgb * pow(md, 48.0) * 0.09 * night;

    if (night > 0.02 && h > 0.0) {
        vec2 sp = d.xz / (d.y + 0.22) * 150.0;
        vec2 cell = floor(sp);
        vec2 f = fract(sp) - 0.5;
        float rnd = hash12(cell);
        float star = smoothstep(0.05, 0.0, length(f)) * step(0.90, rnd);
        star *= 0.55 + 0.45 * sin(TIME * (1.2 + rnd * 2.2) + rnd * 40.0);
        col += vec3(0.72, 0.82, 1.0) * star * night * smoothstep(0.02, 0.20, h) * 1.7;
    }

    float cover = 0.0;
    if (h > -0.02) {
        vec2 p = d.xz / max(h + 0.11, 0.055);
        vec2 drift = vec2(TIME * 0.0032, TIME * 0.0011) * cloud_speed;
        vec2 uv = p * 0.52 + drift;
        float n = fbm(uv * 1.35);
        float n2 = fbm(uv * 3.30 + vec2(7.3, 1.9) - drift * 0.7);
        float t = n * 0.68 + n2 * 0.32;
        cover = smoothstep(1.0 - cloud_cover * 0.96, 1.03 - cloud_cover * 0.48, t);
        cover *= smoothstep(-0.05, 0.55, h) * (1.0 - smoothstep(0.75, 1.0, h) * 0.25);
        cover *= 1.0 - smoothstep(0.985, 0.9996, md) * 0.9;
    }

    float lit = clamp(0.28 + pow(sd, 2.5) * 0.9 + pow(1.0 - up, 3.0) * 0.35, 0.0, 1.0);
    vec3 cloud_col = mix(cloud_shadow.rgb, cloud_lit.rgb, lit);
    cloud_col += sun_color.rgb * pow(sd, 6.0) * 0.22 * (1.0 - storm * 0.7);
    cloud_col = mix(cloud_col, hcol, pow(1.0 - up, 5.0) * 0.85);
    col = mix(col, cloud_col, cover * 0.9);

    col = mix(col, hcol * 1.03, pow(1.0 - up, 9.0) * 0.26 * (1.0 - night * 0.7));

    col += moon_color.rgb * smoothstep(0.99962, 0.99982, md) * 2.2 * night;
    col += moon_color.rgb * pow(md, 220.0) * 0.22 * night;

    col += vec3(0.70, 0.80, 1.0) * flash * (0.35 + cover * 1.4);

    COLOR = col;
}
