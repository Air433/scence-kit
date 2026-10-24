# 赛璐璐森林竞技场 · Godot 导入说明

主文件：`cel_forest_arena.glb`（17.5 MiB / 18.3 MB，贴图内嵌，单文件自包含）
源文件：`../../checkpoints/cel_forest_arena/cel_forest_arena.blend`（Blender 5.2）
实时工程：`../../godot/cel_forest_arena`（Godot 4.7.2，Forward+）
预览图：`../../renders/cel_forest_arena/hero.png`（Blender）、`godot_hero.png`（Godot 实机）

重新生成：

```bash
blender -b -P build.py -- --scene cel_forest_arena --phase all --render quick
blender -b -P build.py -- --scene cel_forest_arena --phase render --render hero --samples 56
```

重新导出并注入 MToon：

```bash
blender -b -P build.py -- --scene cel_forest_arena --phase export
# build.py 会自动调用 scenes/cel_forest_arena/post_export.py
```

> 导出阶段结束会打印 `[scene] post-export: scenes/cel_forest_arena/post_export.py`。
> 对已有 GLB 单独补注入：`python scenes/cel_forest_arena/post_export.py output/cel_forest_arena/cel_forest_arena.glb`。

---

## 1. MToon 是怎么进 GLB 的

Blender 没有 MToon 导出器。流程是：

1. 场景用 Blender 侧的赛璐璐管线渲染（调色板重映射贴图、量化光照、合成器 Posterize、预览用反壳描边）。
2. `export_glb()` 写标准 glTF（Principled BSDF、`KHR_materials_emissive_strength`）。
3. `scenes/cel_forest_arena/post_export.py` 在导出后直接改写 GLB 的 JSON chunk，为每个材质写入 `VRMC_materials_mtoon` 1.0 扩展。

扩展字段由 `post_export.py` 的 `_mtoon()` 生成：`shadeColorFactor`、`shadingShiftFactor`、`shadingToonyFactor`、`giEqualizationFactor`、`parametricRimColorFactor`、`rimLightingMixFactor`、`outlineWidthMode/Factor/ColorFactor` 等。

- `extensionsUsed` 增加 `VRMC_materials_mtoon`，**不写入 `extensionsRequired`**，因此不支持该扩展的引擎（含 Godot）仍能正常加载。
- 透明卡片（`leaf` / `litter` / `fern` / `grass`）不写描边；自发光材质（`rune` / `lantern` / `mushroom` / `firefly`）的 shade 色按自发光色压暗。
- 改写 JSON chunk 时同步更新长度并做 4 字节对齐，BIN chunk 原样保留。

Godot 会忽略该扩展。实时工程在运行时用 `shaders/mtoon.gdshader` 复现同一套参数（见第 4 节）。

---

## 2. 导入步骤（独立工程）

1. 使用 Godot 4.7.x，渲染器选 **Forward+**（Vulkan）。
2. 把 `cel_forest_arena.glb` 复制进工程，等待首次导入（约 10–20 秒）。
3. 在 Import 面板把 **glTF → Embedded Image Handling** 设为 **Embed as Uncompressed**（`embedded_image_handling=3`）。默认的 *Extract Textures* 会在 GLB 旁生成 11 张 sidecar PNG；两者都能用，内嵌方式更干净。
4. 实例化 GLB 后，把 `CAM_Hero` 设为 `current`，或按 `godot/cel_forest_arena/scripts/orbit_camera.gd` 的预设重建相机（垂直 FOV 46°，目标 `(0, 2.9, -1.5)`，距离 11.7 m）。
5. glTF 不带阴影开关，平行光需手动开阴影；建议 `directional_shadow_max_distance = 70`。
6. **不要**启用 Draco / meshopt；本 GLB 使用原始网格。

嵌入贴图参数（`assets/cel_forest_arena.glb.import`）：

```ini
gltf/embedded_image_handling=3
```

---

## 3. 实测导入数据（Godot 4.7.2 / Forward+）

| 项目 | 结果 |
|---|---|
| 节点 / 网格 | 53 / 42 |
| 三角面 | 316,724 |
| 材质 | 16（12 `OPAQUE` + 4 `MASK`） |
| 贴图 | 11 张（全部内嵌） |
| 灯光 | 1 × DirectionalLight3D + 9 × OmniLight3D |
| 相机 | 1 × Camera3D（`CAM_Hero`，垂直 FOV ≈ 45.8°） |
| 单位 | 米制，竞技场中心在原点，石板地面 y ≈ 0，祭坛在 −z 方向 |

MASK 材质：`leaf`（树冠）、`litter`（落叶）、`fern`（蕨类）、`grass`（草卡）。四者都用 `Alpha Scissor` 0.5、双面渲染。

`extensionsUsed`：`KHR_materials_emissive_strength`、`KHR_materials_specular`、`KHR_lights_punctual`、`VRMC_materials_mtoon`。

坐标映射：Blender `(x, y, z)` → Godot `(x, z, -y)`。相机在 Blender 中位于 `(3.6, -9.6, 2.62)`，对应 Godot 目标 `(0, 2.9, -1.5)`。

---

## 4. Godot 侧的 MToon 复现

`godot/cel_forest_arena` 不使用 GLB 里的材质，而是加载后按材质名套 `ShaderMaterial`：

- `mtoon.gdshader`：`half-Lambert → smoothstep` 二段式着色，`shade_color` 与贴图色混合；自发光走 `EMISSION`；透明卡片用 `ALPHA_SCISSOR_THRESHOLD`。
- `mtoon_outline.gdshader`：`next_pass` 反壳描边，`cull_front` + 顶点沿法线外扩；宽度取 `scene_profile.gd` 里每个材质的 `outline` × `OUTLINE_SCALE`。
- `cel_sky.gdshader`：三段渐变 + 暖地平线 + 8 级量化条带 + 太阳辉光。

每个材质的 `shade` / `rim` / `outline` / `emission` 参数集中在 `scripts/scene_profile.gd` 的 `MTOON` 字典。共 16 个键，与 GLB 材质名一一对应。

调参入口：

```gdscript
const OUTLINE_COLOR := Color("#0b1a12")   # 墨线颜色
const OUTLINE_SCALE := 2.5                # 全局描边倍率
```

---

## 5. 已知差异与坑

- Godot 实机比 Blender 主视觉亮、过渡软：实时版没有 Cycles 的二次反弹与合成器 Posterize，只靠着色器量化与 ACES。想要更硬的赛璐璐感，先降 `ENV.ambient_energy`，再加 `OUTLINE_SCALE`。
- 自发光材质的 `albedo_tint` 必须保持 **alpha = 1.0**。用 `Color(r, g, b, 1.0) * 0.35` 会把 alpha 也乘成 0.35，配合 `depth_prepass_alpha` 会让整片符文/灯球/蘑菇完全消失。
- 符文面片只高出石板 2–14 mm；如果自行改动地面高度，需要同步抬高 `ARENA_Rune`，否则会被石材盖住。
- 反射、体积雾、MSAA 都会影响描边观感；描边宽度是世界单位外扩，近景偏粗、远景偏细，属反壳法线的正常现象。
- 换 GLB 后必须重新导入，否则 Godot 继续使用 `.godot/imported/*.scn` 缓存：

```bash
cp output/cel_forest_arena/cel_forest_arena.glb godot/cel_forest_arena/assets/cel_forest_arena.glb
"D:/software/Godot_v4.7.2/Godot_v4.7.2-stable_win64_console.exe" \
  --headless --path godot/cel_forest_arena --import
```

---

## 6. 灯光

| 灯光 | 类型 | 能量 | 说明 |
|---|---|---|---|
| `LIGHT_Sun` | Directional | 7.0（Blender）/ 1.45（Godot 覆盖） | 暖白 5600 K，角度 2.2°，开阴影 |
| `LIGHT_Lantern_00…07` | Omni | 95 W / 2700 K | 串灯，Godot 内 `range = 9` |
| `LIGHT_Rune` | Omni | 38 W | 竞技场中心符文补光，Godot 内 `range = 8` |

Godot 运行时会额外创建一盏冷色补光 `LIGHT_FillRuntime`（能量 0.45，不投影），用来托住树冠暗部。
