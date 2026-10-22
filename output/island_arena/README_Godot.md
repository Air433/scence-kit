# 热带海岛竞技场 · Godot 导入说明

主文件：`island_arena.glb`（23.9 MiB / 25.0 MB，贴图内嵌，单文件自包含）
源文件：`../../checkpoints/island_arena/island_arena.blend`（Blender 5.2）
实时工程：`../../godot/island_arena`（Godot 4.7.2，Forward+）
预览图：`../../renders/island_arena/hero.png`（Blender）、`godot_sunny.png`、`godot_sunny_shore.png`、`godot_storm.png`、`godot_night.png`（Godot 实机）

重新生成：

```bash
blender -b -P build.py -- --scene island_arena --phase all --render quick
blender -b -P build.py -- --scene island_arena --phase render --render hero --samples 64
```

---

## 1. 交付方式：直接运行实时工程

本场景的波浪、反射、天空、雨、风和天气切换**不在 GLB 里**，由 `godot/island_arena` 在运行时生成。推荐直接打开该工程：

```bash
"D:/software/Godot_v4.7.2/Godot_v4.7.2-stable_win64.exe" --path godot/island_arena
```

需要单独把 GLB 导入自己的工程时，按第 2 节操作；此时只得到静态岛屿（地形、看台、灯塔、棕榈、道具、灯光），海面与天空需要自行实现。

---

## 2. 导入步骤（独立工程）

1. 使用 Godot 4.7.x，渲染器选 **Forward+**（Vulkan）。
2. 把 `island_arena.glb` 复制进工程，等待首次导入（约 10–20 秒）。
3. 在 Import 面板把 **glTF → Embedded Image Handling** 设为 **Embed as Uncompressed**（`embedded_image_handling=3`）。默认的 *Extract Textures* 会在 GLB 旁生成 24 张 sidecar PNG；两者都能用，内嵌方式更干净。
4. 实例化 GLB 后，把 `CAM_Hero` 设为 `current`，或按 `godot/island_arena/scripts/orbit_camera.gd` 的预设重建相机（FOV 38°，目标 `(0, 4.5, -2)`，距离 62 m）。
5. glTF 不带阴影开关，平行光需手动开阴影。
6. **不要**启用 Draco / meshopt；本 GLB 使用原始网格。

---

## 3. 实测导入数据（Godot 4.7.2 / Forward+）

| 项目 | 结果 |
|---|---|
| 节点 / 网格 | 106 / 91 |
| 三角面 | 235,016 |
| 材质 | 19（16 `OPAQUE` + 3 `MASK`） |
| 贴图 | 24 张（全部内嵌），26 个 texture 引用 |
| 灯光 | 1 × DirectionalLight3D + 11 × OmniLight3D + 1 × SpotLight3D |
| 相机 | 1 × Camera3D（`CAM_Hero`，垂直 FOV ≈ 37.3°） |
| 单位 | 米制，竞技场中心在原点，海平面 y = 0，看台地面 y ≈ 4.35 |

MASK 材质：`bush_leaf`（灌木叶）、`grass_card`（草卡）、`palm_frond`（棕榈叶）。三者都用 `Alpha Scissor` 0.5，双面渲染；在实时工程里还会被换成风力着色器。

`extensionsUsed` 只有 `KHR_materials_emissive_strength` 与 `KHR_lights_punctual`。

坐标映射：Blender `(x, y, z)` → Godot `(x, z, -y)`。灯塔光束原点约在 `(20.5, 22.7, -21.5)`，灯塔所在岬角位于场景东北。

---

## 4. 灯光

导出使用 **COMPAT** 光照单位（`export_import_convert_lighting_mode="COMPAT"`），否则 Godot 会亮约 700 倍。

| 灯光 | 类型 | energy | 颜色 |
|---|---|---|---|
| `LIGHT_Sun` | Directional | 1.0 | 暖白（约 2950 K） |
| `LIGHT_Torch_00…07` | Omni | 1.43 | 琥珀 `#FFB45C` |
| `LIGHT_Lighthouse` | Omni | 14.32 | 暖黄 |
| `LIGHT_LighthouseBeam` | Spot | 143.24 | 暖黄 |
| `LIGHT_String` | Omni | 1.91 | 暖金 |
| `LIGHT_Compass` | Omni | 0.64 | 金橙 |

glTF 不写点光 `range`，Godot 按 4096 m 处理。实时工程在 `main.gd` 里重设了有效的 `omni_range`（火把 18 m、灯塔 36 m），并按夜色动态提升强度；同时删除 GLB 的 `LIGHT_Sun` 与 `LIGHT_LighthouseBeam`，改用运行时平行光和可旋转的聚光灯。

---

## 5. 推荐的 WorldEnvironment

实时工程的 `_build_environment()`（`godot/island_arena/scripts/main.gd`）已经给出一套实测参数，要点：

```gdscript
env.tonemap_mode = Environment.TONE_MAPPER_ACES
env.tonemap_exposure = 1.05
env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY

env.glow_enabled = true
env.glow_intensity = 0.85
env.glow_hdr_threshold = 1.0

env.ssao_enabled = true
env.fog_enabled = true
env.volumetric_fog_enabled = true
env.volumetric_fog_length = 240.0
```

- 天空使用自定义 `sky.gdshader`（程序化渐变 / 太阳 / 月亮 / 云 / 星空），不是 `ProceduralSkyMaterial`。
- 海面着色器设置 `fog_disabled`，环境雾只作用于陆地；远海颜色按太阳方位与天空地平线匹配，避免出现海天接缝。
- 换配色时至少同步：`ambient_light_color`、`fog_light_color`、`ocean` 的 `horizon_warm` / `horizon_cool`。

---

## 6. 性能参考

- 235 k 三角面 + 24 张 1K–2K 贴图，桌面 GPU 无压力。
- 实时工程的主要开销是 960×540 平面反射、体积雾、4096 阴影与 MSAA；GTX 1050 Ti 在 1600×900 下可交互。
- 关掉反射（把 `reflection_amount` 设为 0）或把反射缓冲降到 640×360 可显著提速。
- 移动端需关闭体积雾、SSAO 与平面反射。

---

## 7. 已知差异

| 效果 | Blender 预览 | Godot 实时 |
|---|---|---|
| 海面 | Cycles 平面 + 置换，预览用 | 运行时网格 + 波形着色器 + 平面反射 |
| 天空 / 云 | 程序化世界背景（不导出） | `sky.gdshader`，可随时间/天气变化 |
| 地面雾 | world volume（仅预览） | 线性雾 + 体积雾，按天气插值 |
| 补光 / 反弹光 | 仅预览，不导出 | 运行时 `LIGHT_FillRuntime` 冷色补光 |
| 阴影 | Cycles 光线追踪 | 4096 平行光阴影，需手动开启 |
| 火把闪烁 / 灯塔旋转 | 静态 | 运行时正弦闪烁与旋转光束 |

以上差异均由 `godot/island_arena` 补齐；只导入 GLB 时看不到动态部分。
