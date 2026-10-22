shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx, cull_disabled;

uniform sampler2D albedo_sand : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D albedo_wet : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D albedo_grass : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D albedo_rock : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_sand : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_grass : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_rock : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float uv_scale = 7.0;

varying vec3 world_pos;
varying vec3 world_normal;

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(
		mix(hash12(i), hash12(i + vec2(1.0, 0.0)), u.x),
		mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), u.x),
		u.y);
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec2 uv = world_pos.xz / uv_scale;
	float slope = 1.0 - clamp(world_normal.y, 0.0, 1.0);
	float n = vnoise(world_pos.xz * 0.055) * 0.62 + vnoise(world_pos.xz * 0.21) * 0.38;

	float rock_mask = smoothstep(0.055, 0.165, slope + (n - 0.5) * 0.05);
	float h = world_pos.y + (n - 0.5) * 0.45;
	float upland = smoothstep(1.45, 2.35, h);

	vec3 wet_col = texture(albedo_wet, uv).rgb;
	vec3 sand_col = texture(albedo_sand, uv).rgb;
	vec3 grass_col = texture(albedo_grass, uv).rgb;
	vec3 wn = abs(world_normal);
	float wsum = wn.x + wn.y + wn.z + 1e-4;
	vec3 rock = (texture(albedo_rock, world_pos.zy / uv_scale).rgb * wn.x
		+ texture(albedo_rock, world_pos.xz / uv_scale).rgb * wn.y
		+ texture(albedo_rock, world_pos.xy / uv_scale).rgb * wn.z) / wsum;

	vec3 base = mix(wet_col, sand_col, smoothstep(0.35, 1.45, h));
	base = mix(base, grass_col, upland);
	vec3 col = mix(base, rock, rock_mask);

	float wet = 1.0 - smoothstep(0.55, 1.5, h);
	col *= mix(1.0, 0.70, wet);

	float macro = vnoise(world_pos.xz * 0.018);
	col *= 0.93 + 0.14 * macro;

	ALBEDO = col;
	ROUGHNESS = mix(mix(0.92, 0.86, rock_mask), 0.58, wet);
	SPECULAR = 0.10;

	vec3 nmap = texture(normal_sand, uv).rgb;
	nmap = mix(nmap, texture(normal_grass, uv).rgb, upland);
	nmap = mix(nmap, texture(normal_rock, uv).rgb, rock_mask);
	NORMAL_MAP = nmap;
	NORMAL_MAP_DEPTH = 0.85;
}
