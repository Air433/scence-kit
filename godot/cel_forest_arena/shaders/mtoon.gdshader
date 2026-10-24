shader_type spatial;
render_mode cull_disabled, specular_disabled, diffuse_lambert, depth_prepass_alpha;

// Runtime approximation of VRMC_materials_mtoon for Godot 4.  The GLB also
// carries the real MToon extension, but Godot ignores unknown extensions, so
// the same parameters are applied here as material overrides.

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 albedo_tint : source_color = vec4(1.0);
uniform float albedo_boost = 1.0;
uniform float use_albedo_tex = 1.0;
uniform float alpha_cut = 0.0;

uniform vec4 shade_color : source_color = vec4(0.35, 0.40, 0.35, 1.0);
uniform float shading_toony = 0.92;
uniform float shading_shift = -0.02;
uniform vec4 rim_color : source_color = vec4(0.42, 0.62, 0.48, 1.0);
uniform float rim_power = 5.0;
uniform float rim_mix = 0.35;
uniform vec4 emission_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float emission_energy = 0.0;

void fragment() {
    vec3 base = albedo_tint.rgb;
    float alpha = albedo_tint.a;
    if (use_albedo_tex > 0.5) {
        vec4 tex = texture(albedo_tex, UV);
        base *= tex.rgb;
        alpha *= tex.a;
    }

    ALBEDO = base * albedo_boost;
    ALPHA = alpha;
    if (alpha_cut > 0.0) {
        ALPHA_SCISSOR_THRESHOLD = alpha_cut;
    }

    METALLIC = 0.0;
    SPECULAR = 0.0;
    ROUGHNESS = 1.0;
    EMISSION = emission_color.rgb * emission_energy;
    AO = 1.0;
    AO_LIGHT_AFFECT = 0.0;
}

void light() {
    float half_lambert = dot(NORMAL, LIGHT) * 0.5 + 0.5;
    float edge = max(0.015, (1.0 - shading_toony) * 0.5);
    float lit = smoothstep(
        0.5 - edge + shading_shift,
        0.5 + edge + shading_shift,
        half_lambert
    );

    vec3 toon = mix(shade_color.rgb, ALBEDO, lit);
    DIFFUSE_LIGHT += toon * LIGHT_COLOR * ATTENUATION / PI;

    float fresnel = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), rim_power);
    DIFFUSE_LIGHT += rim_color.rgb * fresnel * rim_mix * lit * LIGHT_COLOR * ATTENUATION / PI;
}
