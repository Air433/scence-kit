# 星空竞技场 · Godot 导入说明

主文件：`star_arena.glb`（15.36 MiB / 16.11 MB，8 张贴图内嵌，单文件自包含）
源文件：`../../checkpoints/star_arena/star_arena.blend`（Blender 5.2）
预览图：`../../renders/star_arena/hero.png`（Blender Cycles，1600×900，72 samples）

本场景为**纯静态**场景，没有 `godot/star_arena` 实时工程。星空、星系、行星与光环全部烘焙进 GLB：星云是半径 92 m 的内向发光穹顶，不依赖 Godot 天空或着色器。

重新生成：

```bash
blender -b -P build.py -- --scene star_arena --phase all --render quick
blender -b -P build.py -- --scene star_arena --phase export --render hero --samples 72
```

---

## 1. 导入步骤

1. 使用 Godot 4.7.x，渲染器选 **Forward+**（Vulkan）。
2. 把 `star_arena.glb` 复制进工程，等待首次导入。换 GLB 后必须重新导入，否则会继续用旧缓存：
   ```bash
   godot --headless --path <工程目录> --import
   ```
3. 在 Import 面板把 **glTF → Embedded Image Handling** 设为 **Embed as Uncompressed**（`embedded_image_handling=3`）。本场景共 8 张内嵌贴图，内嵌不会产生 sidecar PNG。
4. 实例化 GLB，把 `CAM_Hero` 设为 `current`，或按下面的参数重建相机。
5. **必须**选中 `SKY_Starfield`，把 **Cast Shadow 设为 Off**，并把 **GI Mode 设为 Disabled**。这是一颗半径 92 m 的封闭球体，开着阴影会挡住平行光，整个竞技场会瞬间变黑。
6. glTF 不导出阴影开关：给 `LIGHT_Sun` 开启阴影，`directional_shadow_max_distance` 设为 120 m，`light_angular_distance` 可设 1.1° 模拟 Blender 的太阳张角。11 盏点光默认不投影。
7. **重设点光的 `omni_range`**：glTF 不写 range，Godot 4.7.2 实测全部导入成 **4096 m**。按第 5 节的表改成 6–16 m，并按需提高 `light_energy`。
8. **不要**启用 Draco / meshopt；本 GLB 使用原始网格。
9. Blender 侧的面光（Fill / Rim / Sky）不会导出。需要在 Godot 里补一盏无阴影的平行光，并抬高环境光，见第 6 节。

相机参数（已在 Godot 4.7.2 中实测）：

| 项目 | 值 |
|---|---|
| 节点 | `CAM_Hero` |
| 位置（Godot） | `(1.6, 3.4, 15.2)` |
| 观察目标（Godot） | `(0.0, 7.2, -0.6)` |
| 垂直 FOV | 58.72°（18 mm，36 mm 传感器，16:9） |
| 水平 FOV | 90° |
| 近 / 远裁剪 | 0.05 / 500 m |

---

## 2. 实测导入数据（Godot 4.7.2 / Forward+）

| 项目 | 结果 |
|---|---|
| 节点 / MeshInstance3D / Mesh | 46 / 33 / 33 |
| 三角面 | 196,321 |
| 材质 | 10（全部 `OPAQUE`；8 个双面，`marble` 与 `marble_warm` 单面） |
| 贴图 | 8 张内嵌 PNG（6 × 1024² 大理石贴图，1 × 512×1024 门拱星云，1 × 4096×2048 星空） |
| 灯光 | 1 × DirectionalLight3D + 11 × OmniLight3D，0 Spot |
| 相机 | 1 × Camera3D（`CAM_Hero`） |
| 星空穹顶 | `SKY_Starfield`，半径 92 m，16,128 三角面，双面发光 |
| 文件体积 | 15.36 MiB |
| 单位 | 米制，竞技场中心在原点，广场地面 y = 0 |

`extensionsUsed` 为 `KHR_materials_emissive_strength` 与 `KHR_lights_punctual`（后者是 required）。没有 Draco / meshopt。

材质清单（导出名）：

| 材质 | 金属度 / 粗糙度 | 自发光 | 用途 |
|---|---|---|---|
| `marble` | 0 / 贴图 0.10–0.45 | — | 象牙白大理石：广场、柱、门楼 |
| `marble_warm` | 0 / 贴图 0.10–0.45 | — | 暖白大理石：露台、墙面、平台裙边 |
| `gold` | 1.0 / 0.20 | — | 主金色装饰 |
| `gold_deep` | 1.0 / 0.32 | — | 深金：火盆、地面辐条 |
| `gold_glow` | 1.0 / 0.18 | `#ffcf7a` × 0.9 | 悬浮光环、内轨道 |
| `stone_dark` | 0 / 0.58 | — | 墙面嵌板、门洞底板 |
| `glow` | 0 / 0.45 | `#ffe6b8` × 1.6 | 细金线、尖顶宝石 |
| `sconce` | 0 / 0.45 | `#ffcf8f` × 1.8 | 壁灯、火盆火焰、地面玫瑰环 |
| `portal` | 0 / 1.0 | 星云贴图 × 2.0 | 门拱传送门 |
| `starfield` | 0 / 1.0 | 星空贴图 × 1.2 | 92 m 星空穹顶 |

`shadow` 材质没有物体使用，未导出。

---

## 3. 坐标与尺度

坐标映射：Blender `(x, y, z)` → Godot `(x, z, -y)`。门楼在 Blender `+Y`，因此在 Godot 的 `-Z` 一侧；主相机位于 `+Z` 一侧。

主要尺度（Godot 坐标）：

| 部件 | 位置 / 尺寸 |
|---|---|
| 广场地面 | 半径 15.9 m，y = 0 |
| 竞技场栏杆 | 半径 12.4 m，高 1.17 m；8 座鎏金瓮最高 1.76 m |
| 环形台阶 / 露台 | 台阶 15.3–16.9 m；露台 16.8–22.4 m，顶面 y = 0.30 |
| 悬浮甲板 | 半径 25.2 m，外缘顶面 y ≈ 0.28，裙边向下至 −2.0 |
| 甲板底部 | 收束至 y = −8.55 的发光宝石 |
| 两层拱廊 | 半径 18.4 m，20 跨（门洞占 1 跨，实际 19 根柱） |
| 下层柱 / 檐口 | 柱顶 8.42 m，下层檐口 7.62–8.42 m |
| 上层柱 / 檐口 | 柱顶 13.66 m，上层檐口 12.88–13.66 m |
| 外墙 | 半径 20.0–20.7 m，顶 13.66 m |
| 屋顶主尖塔 | 5 座，半径 19.45 m，最高 17.60 m；另有 10 个小金尖 |
| 门楼 | 宽 ±5.68 m，正面 z = −17.15，檐口 14.85 m，中尖塔 16.72 m |
| 门拱开口 | 宽 5.2 m，起拱 8.40 m，拱顶 11.0 m |
| 门楼台阶 | 3 级，z = −15.55 / −16.15 / −16.75，顶面 0.10 / 0.20 / 0.30 |
| 门楼玫瑰窗 | 中心 `(0, 13.0, −17.08)`，外径 1.34 m |
| 悬浮光环 | 中心 `(0, 21.2, −18.65)`，半径 6.10 m，顶部约 27.3 m |
| 光环水晶 | 中心同光环，半径 1.05 m，高 3.05 m |
| 星穹 | 半径 92 m，中心在原点 |

---

## 4. 星空穹顶

- `SKY_Starfield` 是一颗**内向** UV 球，材质 `starfield`：黑色底色 + 4096×2048 等距柱状贴图接到 Emission，发光强度 **1.2**，双面。
- 贴图里预烘焙了：主螺旋星系、伴星系、6 个小星系、一颗带椭圆环的行星、银河带、14,000 颗星点与 40 颗带衍射芒的亮星。
- 在 Godot 里它只是几何体：**不会**参与环境光，也**不会**自动成为反射源。需要另加环境光与 ReflectionProbe（第 6 节）。
- 必须关闭 `cast_shadow`（见第 1 节第 5 条），否则平行光被整颗球挡住。
- 若使用 SDFGI，把穹顶的 `gi_mode` 设为 `Disabled`，避免整颗球体进入 GI 造成漏光或噪点；本场景推荐直接用 ReflectionProbe，不必开 SDFGI。
- 穹顶半径 92 m，相机 near/far 已够用；不要把它缩放到相机远裁剪面之外。
- 贴图没有 alpha，星空亮度完全靠 Glow 提亮；Glow 关闭时星点会显得干、星系缺少光晕。

---

## 5. 灯光

导入后的实测值（GLB 使用 COMPAT 光照单位，“导入 energy”就是 Godot 的 `light_energy`）：

| 灯光 | 类型 | 导入 energy | 导入颜色 | 建议 energy | 建议 range |
|---|---|---:|---|---:|---:|
| `LIGHT_Sun` | Directional | 1.0 | `#fffdfd` | 1.15 | — |
| `LIGHT_Halo` | Omni | 5.968 | `#ffe9c8` | 18 | 16 m |
| `LIGHT_Portal` | Omni | 2.387 | `#ffd9a0` | 7 | 12 m |
| `LIGHT_Plaza` | Omni | 1.114 | `#ffd9a0` | 3 | 10 m |
| `LIGHT_Sconce_00–03` | Omni | 0.796 | `#ffc98a` | 2.5 | 6 m |
| `LIGHT_Brazier_00–03` | Omni | 1.432 | `#ff9d5c` | 5 | 8 m |

位置（Godot 坐标）：

| 灯光 | 位置 |
|---|---|
| `LIGHT_Sun` | 节点位移 `(-34, 40, 28)`，指向 `(0, 6, 0)` |
| `LIGHT_Halo` | `(0, 19.4, -18.4)` |
| `LIGHT_Portal` | `(0, 6.2, -18.6)` |
| `LIGHT_Plaza` | `(0, 1.4, 0)` |
| `LIGHT_Sconce_00` | `(11.26, 4.55, -15.49)` |
| `LIGHT_Sconce_01` | `(-11.26, 4.55, -15.49)` |
| `LIGHT_Sconce_02` | `(-11.26, 4.55, 15.49)` |
| `LIGHT_Sconce_03` | `(11.26, 4.55, 15.49)` |
| `LIGHT_Brazier_00` | `(8.17, 2.15, -8.17)` |
| `LIGHT_Brazier_01` | `(-8.17, 2.15, -8.17)` |
| `LIGHT_Brazier_02` | `(-8.17, 2.15, 8.17)` |
| `LIGHT_Brazier_03` | `(8.17, 2.15, 8.17)` |

注意：

- 所有灯光导入后 `shadow_enabled = false`，这是 glTF 的限制；至少给太阳开阴影，否则拱廊、门楼和栏杆会失去投影，立体感会明显变差。
- 11 盏点光的 range 全部是 4096 m。不改 range 时它们会照亮整座竞技场且近处过曝；务必按表重设。表中 energy 是配合第 6 节环境光实测的数值，直接使用导入值会明显偏暗。
- 点光默认不投影，性能友好；不建议给火盆或壁灯开阴影。`LIGHT_Halo` 如要投影，会多出 6 面立方体阴影，收益不大。
- 太阳的颜色来自 Blender 6500 K；`#fffdfd` 是 Godot 导入后的显示值。

---

## 6. 推荐的 WorldEnvironment、补光与反射

星穹是几何体，没有天空着色器可用。下面这套参数在 Godot 4.7.2 / Forward+ / GTX 1050 Ti 上实测，效果接近 Blender 主视觉：

```gdscript
var arena: Node3D = (preload("res://star_arena.glb") as PackedScene).instantiate()
add_child(arena)

var cam := arena.find_child("CAM_Hero", true, false) as Camera3D
cam.current = true

# 太阳阴影
var sun := arena.find_child("LIGHT_Sun", true, false) as DirectionalLight3D
sun.light_energy = 1.15
sun.shadow_enabled = true
sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
sun.directional_shadow_max_distance = 120.0
sun.light_angular_distance = 1.1   # 可选：模拟 Blender 的 1.1° 太阳张角

# 点光：重设 range 与能量
var tuning := {
    "LIGHT_Halo": [18.0, 16.0],
    "LIGHT_Portal": [7.0, 12.0],
    "LIGHT_Plaza": [3.0, 10.0],
    "LIGHT_Sconce_00": [2.5, 6.0],
    "LIGHT_Sconce_01": [2.5, 6.0],
    "LIGHT_Sconce_02": [2.5, 6.0],
    "LIGHT_Sconce_03": [2.5, 6.0],
    "LIGHT_Brazier_00": [5.0, 8.0],
    "LIGHT_Brazier_01": [5.0, 8.0],
    "LIGHT_Brazier_02": [5.0, 8.0],
    "LIGHT_Brazier_03": [5.0, 8.0],
}
for light_name in tuning:
    var light := arena.find_child(light_name, true, false) as OmniLight3D
    light.light_energy = tuning[light_name][0]
    light.omni_range = tuning[light_name][1]
    light.shadow_enabled = false

# 星穹：不投影、不进 GI
var dome := arena.find_child("SKY_Starfield", true, false) as GeometryInstance3D
dome.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
dome.gi_mode = GeometryInstance3D.GI_MODE_DISABLED

# Blender 面光不导出：补一盏无阴影的相机侧平行光
var fill := DirectionalLight3D.new()
fill.name = "FILL_Camera"
fill.light_color = Color("#fff4e4")
fill.light_energy = 0.35
fill.shadow_enabled = false
add_child(fill)
fill.look_at_from_position(Vector3(14, 10, 22), Vector3(0, 5, 0), Vector3.UP)

# 世界环境
var env := Environment.new()
env.background_mode = Environment.BG_COLOR
env.background_color = Color.BLACK
env.tonemap_mode = Environment.TONE_MAPPER_ACES
env.tonemap_exposure = 1.0
env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
env.ambient_light_color = Color("#22252f")
env.ambient_light_energy = 1.0
env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
env.glow_enabled = true
env.glow_intensity = 0.85
env.glow_bloom = 0.05
env.glow_hdr_threshold = 1.0
env.ssao_enabled = true
env.ssao_radius = 1.2
env.ssao_intensity = 1.1
var we := WorldEnvironment.new()
we.environment = env
add_child(we)

# 反射探针：捕捉星穹与金色结构
var probe := ReflectionProbe.new()
probe.name = "REFL_Arena"
probe.position = Vector3(0, 7, 0)
probe.size = Vector3(64, 36, 64)
probe.box_projection = true
probe.interior = true
probe.update_mode = ReflectionProbe.UPDATE_ONCE
probe.ambient_mode = ReflectionProbe.AMBIENT_DISABLED
add_child(probe)
```

说明：

- **环境光必须抬高**。Blender 里的 Fill / Rim / Sky 三盏面光都不会导出，只靠 GLB 里的太阳，拱廊内侧会死黑。`1.0` 的环境光配合 `0.35` 的补光平行光是实测的平衡点；只调环境光会显得平，只加补光会保住明暗关系。
- 探针会从中心捕捉到星穹的星系、行星与金色结构；`gold`、`gold_deep`、`gold_glow` 才有东西可反射。
- 探针分辨率由项目设置 `rendering/reflections/reflection_atlas/reflection_size` 控制（默认 256），不是 ReflectionProbe 的属性；静态场景可调到 512，用 `UPDATE_ONCE` 即可。
- 不加探针时，Metallic 1.0 的金色在 Godot 里会接近黑色，只剩高光点。
- 探针尺寸 64×36×64 覆盖整座竞技场与光环；`box_projection` 必须拼写正确（不是 `box_project`）。
- 若想更贴近 Blender 的 AgX 观感，可把 `tonemap_mode` 改成 `Environment.TONE_MAPPER_AGX`；当前 ACES 的金色更亮、对比更强。Godot 没有 Blender 的 “AgX - Punchy” look。
- 背景保持纯黑，因为星穹本身就是几何体；若改用天空着色器重做星穹，需要隐藏 GLB 内的 `SKY_Starfield`，否则会重复。
- 太阳阴影距离 120 m 足够覆盖门楼、光环和整圈拱廊；阴影贴图默认 4096，低配可降到 2048。

---

## 7. 性能参考

- 196.3 k 三角面、33 个网格、10 个材质、8 张内嵌贴图、12 盏灯，桌面 GPU 无压力；GTX 1050 Ti 在 1600×900 / Forward+ 下可正常实时查看。
- 主要开销：4096 方向光阴影、11 盏点光、SSAO、Glow、ReflectionProbe。
- 点光不投影，11 盏可以同时开；如果给 `LIGHT_Halo` 开阴影，会多一张 6 面立方体阴影。
- 4096×2048 星空贴图未压缩时约占 32 MiB 显存（含 mipmap 约 43 MiB）；6 张 1024² 大理石贴图另占约 32 MiB（含 mipmap）。低显存设备可把星空降到 2048 宽或改用 VRAM 压缩（BC7），但深空渐变容易出现色带。
- 移动端建议：2× MSAA、关闭 SSAO / SSR、Glow 强度降到 0.5、点光 range 保持 6–12 m、反射探针 `UPDATE_ONCE`。
- 星穹 16 k 三角面双面渲染，开销可以忽略。

---

## 8. 已知差异

| 效果 | Blender 预览 | Godot 静态导入 |
|---|---|---|
| 星空 / 星系 | Cycles 世界背景 + 星空穹顶 | 仅星空穹顶（发光几何），需 Glow 提亮 |
| 补光 | 前侧白色面光 + 后上方暖色面光 + 顶部冷色天光 | 面光不导出；用环境光 1.0 + 无阴影补光 0.35 |
| 阴影 | Cycles 光线追踪，太阳与面光都有软阴影 | 仅太阳阴影；点光默认无阴影 |
| 泛光 | Cycles 无 Bloom | 需启用 Glow，否则发光条、星点与传送门会显得干 |
| 色调 | AgX + Punchy | ACES（金色更亮、青色更少）；可改 AgX 接近 |
| 点光衰减 | 物理平方反比 | 导入 range 4096 m，必须重设 range |
| 世界背景 | 深空渐变（强度 0.12） | 纯黑；星穹完全提供天空 |
| 动画 | 无 | 无（纯静态场景） |

补充：导出时 `ARCADE_Marble`、`GATE_Marble`、`GATE_Portal`、`PLATFORM_UnderMarble`、`PLAZA_Floor` 会报 “Could not calculate tangents”（四边形/多边形网格），GLB 不写 TANGENT。实测 Godot 4.7.2 导入时会自动生成切线，大理石法线贴图正常，无需处理。
