# 精灵森林竞技场 · Godot 导入说明

主文件：`forest_arena_elven.glb`（25.6 MB，贴图内嵌，单文件自包含）
源文件：`forest_arena_elven.blend`（Blender 5.2）
预览图：`../../renders/elven_arena/hero.png`（Blender 主视觉）、`../../renders/elven_arena/godot_check.png`（Godot 4.7.2 实机渲染）

重新生成：

```bash
blender -b -P build.py -- --scene elven_arena --phase all --render mid
```

---

## 1. 导入步骤

1. 新建 Godot 4.x 工程（推荐 **Forward+** 渲染器；本文件在 **4.7.2** 上实测通过）。
2. 把 `forest_arena_elven.glb` 拖进 FileSystem 面板，或复制到工程目录后让编辑器自动导入。
   - 首次导入约 10–20 秒（26 MB GLB，23 张内嵌贴图）。
3. 把 GLB 拖进场景，或新建 Node3D 后实例化它。
4. 导入的相机 `CAM_Hero` 已经是主视觉构图，可直接 `current = true` 使用。
5. glTF 不携带阴影开关，导入后请手动开启平行光阴影（见第 4 节）。

> **不要**开启 Draco / meshopt 压缩预设；本 GLB 使用原始网格，所有材质都是标准 PBR。

---

## 2. 实测导入数据（Godot 4.7.2 / Forward+）

| 项目 | 结果 |
|---|---|
| 网格（MeshInstance3D） | 42 |
| 三角面 | 316,070 |
| 材质 | 16 个 StandardMaterial3D |
| 贴图 | 23 张（全部内嵌） |
| 灯光 | 1 × DirectionalLight3D + 9 × OmniLight3D |
| 相机 | 1 × Camera3D（`CAM_Hero`，24 mm） |
| 包围盒（Y-up） | X −38.3 … 39.8，Y −0.46 … 31.4，Z −39.3 … 39.2 |
| 单位 | 米制，竞技场中心在世界原点，地面约 y = 0 |

材质透明度：

- 12 个 `OPAQUE`
- 4 个 `MASK`（蕨类、草、落叶、叶片 / 下层灌木），使用 **Alpha Scissor**，双面渲染
- 8 个双面材质

如果叶片出现黑边，把对应材质的 `Alpha Cut` 设为 `Opaque Pre-Pass` 或微调 `Alpha Scissor Threshold`（默认 0.5）。本场景已按 0.5 导出。

---

## 3. 灯光

导出使用 **COMPAT 光照单位**，Blender 的强度直接写入 glTF，Godot 导入后的数值正好落在合理区间：

| 灯光 | 强度（Godot energy） | 色温 / 颜色 | 范围 |
|---|---|---|---|
| `LIGHT_Sun`（DirectionalLight3D） | 1.0 | 4200 K（暖白） | — |
| `LIGHT_Lantern_00…05` | 7.56 | 2700 K（暖金） | 未指定（Godot 按 4096 处理） |
| `LIGHT_Lantern_06…07` | 5.17 | 2700 K | 未指定（Godot 按 4096 处理） |
| `LIGHT_Rune` | 3.02 | 青绿 `#10DE94` | 未指定（Godot 按 4096 处理） |

> glTF 不写点光源的 `range`，所以 Godot 会按 4096 m 处理，相当于没有距离衰减终点。
> 若希望灯笼真正照亮附近的地面和树干，把每盏的 `omni_range` 设为 **6–10 m**，并把
> `light_energy` 提到 **12–20**（符文灯可设 8–12）。不调整也可以，灯笼的暖色自发光
> 加上 Glow 已经提供了主要的视觉光点。

**注意**：glTF 不导出 Blender 的阴影开关，因此导入后所有灯默认无阴影。推荐：

```gdscript
for l in arena.find_children("*", "DirectionalLight3D", true, false):
    l.shadow_enabled = true          # 平行光阴影是画面成立的关键
```

灯笼可以只开 1–2 盏阴影以控制开销；其余靠自发光与辉光即可。

太阳方向已调成左前方低角度（约 20° 仰角），在场景中形成长投影和树干右侧的暖色轮廓光。若想要更强的“晨光”，把 Sun 的 `light_energy` 提到 1.5–2.5。

---

## 4. 推荐 WorldEnvironment（已实机验证）

下面的参数与 `renders/godot_check.png` 一致，可直接粘贴使用：

```gdscript
var env := Environment.new()
env.background_mode = Environment.BG_SKY

var sky := Sky.new()
var sky_mat := ProceduralSkyMaterial.new()
sky_mat.sky_top_color = Color("#4d7d8c")
sky_mat.sky_horizon_color = Color("#e8c9a6")
sky_mat.sky_curve = 0.18
sky_mat.ground_bottom_color = Color("#1d2418")
sky_mat.ground_horizon_color = Color("#7b7050")
sky_mat.sun_angle_max = 18.0
sky_mat.sun_curve = 0.08
sky.sky_material = sky_mat
env.sky = sky

env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
env.ambient_light_energy = 0.65
env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY

env.tonemap_mode = Environment.TONE_MAPPER_AGX   # 或 FILMIC；AgX 高光更柔和
env.tonemap_exposure = 1.0

env.glow_enabled = true
env.glow_intensity = 0.45
env.glow_bloom = 0.08
env.glow_hdr_threshold = 1.0

env.ssao_enabled = true
env.ssao_radius = 1.6
env.ssao_intensity = 1.8

# 远景薄雾（线性雾）
env.fog_enabled = true
env.fog_light_color = Color("#c8ccb8")
env.fog_light_energy = 0.5
env.fog_density = 0.0010
env.fog_sky_affect = 0.55

# 体积雾（森林光柱与层次）
env.volumetric_fog_enabled = true
env.volumetric_fog_density = 0.0025
env.volumetric_fog_albedo = Color("#dfe4dd")
env.volumetric_fog_anisotropy = 0.55
env.volumetric_fog_length = 64.0
env.volumetric_fog_ambient_inject = 0.15

var we := WorldEnvironment.new()
we.environment = env
add_child(we)
```

调参建议：

- **想更浓的晨雾**：`volumetric_fog_density` 0.0025 → 0.004～0.006；超过 0.01 会发白、丢细节。
- **想更通透**：把体积雾密度降到 0.0015 以下，或干脆关闭体积雾只保留线性雾。
- **雾太亮/发灰**：优先降 `volumetric_fog_ambient_inject`（0.10–0.20），再降 `fog_light_energy`。
- `volumetric_fog_length` 决定雾的计算距离，64 m 已覆盖整个竞技场；降低它可显著省性能。

---

## 5. 相机与构图

- `CAM_Hero`：位于竞技场南侧看台（约 y = 2.62 m），24 mm 广角，轻微仰角，朝向北端祭坛。
- 想要更“游戏化”的视角：把相机下移到 1.7 m，改用 35–40 mm。
- 场景中心 (0, 0, 0) 是符文圆环，可以直接作为出生点或镜头环绕中心。

---

## 6. 性能参考

- 42 个网格、约 31.6 万三角面，桌面级 GPU 无压力；移动端建议先关体积雾与 SSAO。
- 9 盏 OmniLight 中只有符文灯默认建议开阴影（已在 Blender 侧设置），其余灯光若全部开阴影会明显增加开销。
- 不需要 SDFGI；天空光 + SSAO + 体积雾已经足够支撑氛围。

---

## 7. 已知差异（Blender 预览 vs Godot）

| 效果 | Blender 预览 | Godot |
|---|---|---|
| 地面晨雾 | 世界体积（仅渲染，不导出） | 由 WorldEnvironment 的体积雾重建 |
| 补光（Fill / Bounce） | 仅 Blender 预览 | 不导出，由天空环境光替代 |
| 辉光 / 光晕 | AgX + Cycles | Glow 后处理 |
| 阴影 | Cycles 光线追踪 | 需手动开启并调 `directional_shadow_max_distance` |

以上参数组合可复现 `godot_check.png` 的画面。若替换天空或调整太阳强度，微调 `ambient_light_energy` 与雾密度即可保持协调。
