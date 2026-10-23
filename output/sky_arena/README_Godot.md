# 天空竞技场 · Godot 导入说明

主文件：`sky_arena.glb`（17.24 MiB / 18,073,396 B，13 张贴图内嵌，单文件自包含）
源文件：`../../checkpoints/sky_arena/sky_arena.blend`（Blender 5.2）
预览图：`../../renders/sky_arena/hero.png`（Blender Cycles，1600×900，48 samples，AgX - Medium High Contrast，带预览雾）

这是一座悬浮在云海之上的遗迹圣所：断裂的环形柱廊、半塌的天空之门、中央悬浮的青绿心晶，以及脚下被云层托起的破碎岩体。场景是**纯静态**的——天空、云海、近景与远景浮岛全部烘焙进 GLB，天空是一颗半径 240 m 的内向发光穹顶，不依赖 Godot 天空、着色器或运行时代码。因此没有 `godot/sky_arena` 实时工程，按本文导入即可。

渲染目录另有 `preview_mid.png`（1200×675，40 samples，带雾）与 `preview_main.png`（960×540，24 samples，无雾），用于快速核对构图。

重新生成：

```bash
blender -b -P build.py -- --scene sky_arena --phase all --render quick
blender -b -P build.py -- --scene sky_arena --phase render --render hero --samples 48
```

---

## 1. 导入步骤

1. 使用 Godot 4.7.x，渲染器选 **Forward+**（Vulkan）。
2. 把 `sky_arena.glb` 复制进工程，等待首次导入（约 15–25 秒）。换 GLB 后必须重新导入，否则会继续使用旧缓存：
   ```bash
   godot --headless --path <工程目录> --import
   ```
3. 在 Import 面板把 **glTF → Embedded Image Handling** 设为 **Embed as Uncompressed**（`gltf/embedded_image_handling=3`）。默认的 *Extract Textures* 会在 GLB 旁生成 13 张 sidecar PNG；两种都能用，内嵌方式目录更干净。
4. 实例化 GLB，把 `CAM_Hero` 设为 `current`，或按第 2 节的相机参数重建。
5. **必须**选中 `SKY_Dome`，把 **Cast Shadow 设为 Off**，并把 **GI Mode 设为 Disabled**。这是一颗半径 240 m 的封闭球体，开着阴影会挡住平行光，整座竞技场会瞬间变黑。
6. glTF 不导出阴影开关：给 `LIGHT_Sun` 开启阴影，`directional_shadow_max_distance` 设为 120 m，`light_angular_distance` 设为 **2.4°**，与 Blender 的太阳张角一致。
7. **重设点光的 `omni_range`**：glTF 不写 range，Godot 4.7.2 实测全部导入成 **4096 m**。按第 5 节的表改成 5–9 m，并按需提高 `light_energy`。
8. **不要**启用 Draco / meshopt；本 GLB 使用原始网格。
9. Blender 侧的面光（Fill / Bounce / Sky / CloudBounce）不会导出。需要在 Godot 里补一盏无阴影的平行光并抬高环境光，完整脚本见第 6 节。

相机参数（Godot 4.7.2 无头导入实测）：

| 项目 | 值 |
|---|---|
| 节点 | `CAM_Hero` |
| 位置（Godot） | `(24.0, 10.5, 37.0)` |
| 观察目标（Godot） | `(0.0, 3.6, -1.6)` |
| 垂直 FOV | 49.43°（22 mm，36 mm 传感器，16:9） |
| 水平 FOV | 78.6° |
| 近 / 远裁剪 | 0.05 / 1200 m |

---

## 2. 实测导入数据（Godot 4.7.2 / Forward+）

| 项目 | 结果 |
|---|---|
| 节点 / MeshInstance3D / Mesh | 52（含实例根）/ 42 / 42 |
| 三角面 | 92,748 |
| 材质 | 16 个材质实例（13 `OPAQUE` + 3 `ALPHA_SCISSOR`），14 个唯一名字 |
| 贴图 | 13 张内嵌 PNG（9 × 1024²、3 × 512²、1 × 4096×2048） |
| 灯光 | 1 × DirectionalLight3D + 7 × OmniLight3D，0 Spot |
| 相机 | 1 × Camera3D（`CAM_Hero`） |
| 天空穹顶 | `SKY_Dome`，半径 240 m，16,128 三角面，双面发光 |
| 文件体积 | 17.24 MiB |
| 单位 | 米制，竞技场中心在原点，广场地面 y = 0 |

`extensionsUsed` 只有 `KHR_materials_emissive_strength` 与 `KHR_lights_punctual`，没有 Draco / meshopt。

材质清单（导出名）：

| 材质 | 贴图 / 颜色 | 金属度 / 粗糙度 | 自发光 | 用途 |
|---|---|---|---|---|
| `paving` | base / rough / normal，1024² | 0 / 贴图 | — | 广场铺地、符文台顶盖 |
| `limestone` | base / rough / normal，1024² | 0 / 贴图 | — | 台阶、柱、门楼、基座 |
| `limestone_warm` | `#c8a670` | 0 / 0.58 | — | 露台压顶、拱楣、甲板暖边 |
| `rock` | base / rough / normal，1024² | 0 / 贴图 | — | 浮空岩体、碎石、浮岛 |
| `stone_dark` | `#6a5f4c` | 0 / 0.82 | — | 甲板底面、门楼嵌板 |
| `gold` | `#f2c964` | 0.88 / 0.26 | 微弱暖金 | 金环、辐条、心晶环 |
| `gold_deep` | `#bd8a3a` | 0.85 / 0.36 | 极弱 | 甲板下的金托架 |
| `rune` | 深青底 + 青色发光 | 0 / 0.45 | `#6cf2da` × 1.95 | 符文、心晶、碎片、浮尘 |
| `flame` | 深橙底 + 暖橙发光 | 0 / 0.45 | `#ffc47c` × 3.20 | 火盆火焰 |
| `ground` | `#657f3f` | 0 / 0.90 | — | 浮岛草皮 |
| `grass` | `grass_card`，512² | 0 / 0.80 | — | 草簇、垂藤（MASK） |
| `leaf` | `leaf_card`，512² | 0 / 0.80 | — | 灌木叶片（MASK） |
| `moss` | `moss_card`，512² | 0 / 0.80 | — | 苔藓（MASK） |
| `sky` | `sky`，4096×2048 | 0 / 1.0 | 贴图 × 1.0 | 240 m 天空穹顶 |

说明：

- `grass` / `leaf` / `moss` 导入为 `ALPHA_SCISSOR`，阈值 0.5，双面渲染；Godot 会自动生成 alpha scissor 的阴影裁剪，无需额外设置。
- `limestone` 与 `rock` 各出现两次（GLB 材质列表第 5/6 项与第 12/13 项，从 1 计），参数与贴图完全一致。这是导出器按网格属性分组产生的重复条目，不影响渲染；按名字查找会拿到第一份。
- `paving`、`limestone`、`rock` 为单面；其余材质双面。单面材质在 Godot 中 `cull_mode = Back`。
- 发光材质的强度通过 `KHR_materials_emissive_strength` 保留；如果符文或火焰不够亮，先检查 Glow 是否开启，再调材质的 `emission_energy_multiplier`，不要直接改颜色。

---

## 3. 坐标与尺度

坐标映射：Blender `(x, y, z)` → Godot `(x, z, -y)`。天空之门在 Blender `+Y`，因此在 Godot 的 **−Z** 一侧；主相机位于 `+Z` 一侧，从东南方向俯看全岛。

主要尺度（Godot 坐标）：

| 部件 | 位置 / 尺寸 |
|---|---|
| 中央广场 | 半径 12.6 m，y = 0 |
| 环形台阶 | 12.6–13.3 m（y = 0.17）、13.3–14.0 m（y = 0.34） |
| 露台 | 半径 13.9–20.6 m，顶面 y = 0.34 |
| 断边甲板 | 内缘 20.5 m，外缘 21.6–24.8 m（随角度起伏），顶面 y ≈ 0.30 |
| 甲板底面 | 16.2–20.7 m 环带，下探至 −1.45 m |
| 浮空岩体 | y = −0.55 → −17.5 m，底部收成岩尖 |
| 柱廊 | 半径 16.7 m；12 个柱位，5 根完整（高 7.94 m）、5 根残柱（1.8–5.2 m）、2 个空位 |
| 拱楣 | 两段，y = 7.90–8.67 m，顶部压檐至 9.04 m |
| 天空之门 | 中心 z = −19.75 m，正面 z = −18.57 m；主门楣顶 12.80 m，西塔柱顶 11.24 m，断塔 8.50 m |
| 门洞 | 半宽 2.15 m，起拱 6.9 m，拱顶约 9.05 m |
| 门楼台阶 | z = −16.55 / −17.15 / −17.75，顶面 y = 0.46 / 0.58 / 0.70 |
| 符文方尖碑 | x = ±5.25，z = −17.15，顶 3.33 m，悬浮符文至 3.73 m |
| 中央符文台 | 底裙半径 4.9 m，台面 y = 0.45；心晶 y = 2.00–4.10；符文环 y = 2.15 / 3.85 / 4.25 |
| 符文浮尘 | 绕心晶 1.35–2.85 m 半径，y = 3.05–5.30 |
| 火盆 | 半径 10.8 m，碗口 y = 2.28；点光 y = 2.56 |
| 近景浮岛 | 5 座，半径 2.2–4.6 m，分布在云海上下 −6 → 3 m；两座带遗迹 |
| 远景浮岛 | 6 座，距离 90–145 m，半径 6.0–8.0 m |
| 天空穹顶 | 半径 240 m，中心在原点 |

近景浮岛（Godot `x, y, z`，`y` 为岛顶高度）：

| 编号 | 位置 | 半径 | 遗迹 |
|---|---|---|---|
| 1 | `(-36.0, 3.0, 4.0)` | 4.6 m | 断柱 + 倒地柱鼓 |
| 2 | `(26.0, 0.5, -26.0)` | 4.0 m | 双柱残拱 |
| 3 | `(-24.0, -2.0, 20.0)` | 2.8 m | — |
| 4 | `(38.0, -6.0, -8.0)` | 2.2 m | — |
| 5 | `(10.0, -1.5, -60.0)` | 3.2 m | — |

---

## 4. 天空穹顶

- `SKY_Dome` 是一颗**内向** UV 球，半径 240 m，材质 `sky`：4096×2048 等距柱状贴图直接接到 Emission，发光强度 **1.0**，双面。
- 贴图预烘焙了：暖色地平线、青绿中层天空、深蓝天顶、积云、铺满下半球的云海、太阳盘与日晕。太阳盘固定在**方位角 211°、仰角 26°**，与 GLB 里的 `LIGHT_Sun` 一致。
- 在 Godot 里它只是几何体：**不会**参与环境光，也**不会**自动成为 `Environment` 的天空或反射源。需要另加环境光与 ReflectionProbe（第 6 节）。
- 必须关闭 `cast_shadow`（见第 1 节第 5 条），否则平行光被整颗球挡住。
- 若使用 SDFGI，把穹顶的 `gi_mode` 设为 `Disabled`，避免整颗球进入 GI 造成漏光；本场景推荐直接用 ReflectionProbe，不必开 SDFGI。
- 穹顶半径 240 m，相机 near/far 已覆盖；不要把它缩放到相机远裁剪面之外。
- 天空是静态的：没有昼夜循环、云层流动或天气。若需要动态天空，应隐藏这颗穹顶，改用 Godot 天空着色器，并同步重调第 6 节的环境光与雾。
- 想保留烘焙天空但改变光照时间时，可以整体旋转 `SKY_Dome`；但太阳盘与投影会错位。可接受的范围约 ±15°，再大就会看出光从天上来、影子却指向别处。

---

## 5. 灯光

导入后的实测值（GLB 使用 COMPAT 光照单位，“导入 energy”就是 Godot 的 `light_energy`）：

| 灯光 | 类型 | 导入 energy | 导入颜色（Godot 显示） | 建议 energy | 建议 range |
|---|---|---:|---|---:|---:|
| `LIGHT_Sun` | Directional | 1.0 | `(1.130, 0.974, 0.815)` | 1.15 | — |
| `LIGHT_DaisRune` | Omni | 4.775 | `(0.424, 0.949, 0.855)` | 6.0 | 7 m |
| `LIGHT_Heart` | Omni | 2.069 | `(0.424, 0.949, 0.855)` | 3.0 | 5 m |
| `LIGHT_GateRune` | Omni | 2.387 | `(0.424, 0.949, 0.855)` | 4.0 | 7 m |
| `LIGHT_Brazier_00–03` | Omni | 4.377 | `(1.316, 0.916, 0.505)` | 5.5 | 9 m |

位置（Godot 坐标）：

| 灯光 | 位置 |
|---|---|
| `LIGHT_Sun` | 节点位移 `(-40, 26, 24)`，指向 `(0, 3.5, 0)` |
| `LIGHT_DaisRune` | `(0, 1.15, 0)` |
| `LIGHT_Heart` | `(0, 3.05, 0)` |
| `LIGHT_GateRune` | `(0, 11.7, -18.3)` |
| `LIGHT_Brazier_00` | `(7.637, 2.56, -7.637)` |
| `LIGHT_Brazier_01` | `(-7.637, 2.56, -7.637)` |
| `LIGHT_Brazier_02` | `(-7.637, 2.56, 7.637)` |
| `LIGHT_Brazier_03` | `(7.637, 2.56, 7.637)` |

注意：

- 所有灯光导入后 `shadow_enabled = false`，这是 glTF 的限制；至少给太阳开阴影，否则柱廊、门楼和栏杆会失去投影，立体感会明显变差。
- 7 盏点光的 range 全部是 4096 m。不改 range 时它们会照亮整座竞技场且近处过曝；务必按表重设。
- 点光默认不投影，性能友好；不建议给火盆或符文开阴影。符文光位于石台内部附近，开阴影反而容易出现漏光与噪点。
- 太阳颜色来自 Blender 4400 K + 暖色；导入后的 HDR 颜色分量可以大于 1，不要手动 clamp。表中的建议 energy 是配合第 6 节环境光实测的平衡点。

---

## 6. 推荐的 WorldEnvironment、补光与反射

天空是几何体，没有天空着色器可用。下面这套参数按 Blender 预览的明暗关系配置，可直接放进一个新场景的根节点：

```gdscript
extends Node3D

var arena: Node3D

func _ready() -> void:
	arena = (preload("res://sky_arena.glb") as PackedScene).instantiate()
	add_child(arena)

	var cam := arena.find_child("CAM_Hero", true, false) as Camera3D
	cam.current = true

	# 太阳阴影
	var sun := arena.find_child("LIGHT_Sun", true, false) as DirectionalLight3D
	sun.light_energy = 1.15
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 120.0
	sun.light_angular_distance = 2.4

	# 点光：重设 range 与能量
	var tuning := {
		"LIGHT_Brazier_00": [5.5, 9.0],
		"LIGHT_Brazier_01": [5.5, 9.0],
		"LIGHT_Brazier_02": [5.5, 9.0],
		"LIGHT_Brazier_03": [5.5, 9.0],
		"LIGHT_DaisRune": [6.0, 7.0],
		"LIGHT_Heart": [3.0, 5.0],
		"LIGHT_GateRune": [4.0, 7.0],
	}
	for light_name in tuning:
		var light := arena.find_child(light_name, true, false) as OmniLight3D
		light.light_energy = tuning[light_name][0]
		light.omni_range = tuning[light_name][1]
		light.shadow_enabled = false

	# 穹顶：不投影、不进 GI
	var dome := arena.find_child("SKY_Dome", true, false) as GeometryInstance3D
	dome.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	dome.gi_mode = GeometryInstance3D.GI_MODE_DISABLED

	# Blender 面光不导出：补一盏相机侧冷色平行光
	var fill := DirectionalLight3D.new()
	fill.name = "FILL_Camera"
	fill.light_color = Color("#cfe9f4")
	fill.light_energy = 0.35
	fill.shadow_enabled = false
	add_child(fill)
	fill.look_at_from_position(Vector3(17, 15, 26), Vector3(0, 3, -2), Vector3.UP)

	# 世界环境
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("#9fc7dd")
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = 1.0
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("#cfe6f0")
	env.ambient_light_energy = 0.42
	env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	env.glow_enabled = true
	env.glow_intensity = 0.7
	env.glow_bloom = 0.05
	env.glow_hdr_threshold = 1.0
	env.ssao_enabled = true
	env.ssao_radius = 1.2
	env.ssao_intensity = 1.1
	env.fog_enabled = true
	env.fog_light_color = Color("#cfe4ee")
	env.fog_density = 0.0025
	env.fog_sky_affect = 0.0
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.08
	env.adjustment_contrast = 1.04
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	# 反射探针：捕捉穹顶与金色结构
	var probe := ReflectionProbe.new()
	probe.name = "REFL_SkyArena"
	probe.position = Vector3(0, 8, 0)
	probe.size = Vector3(70, 60, 70)
	probe.box_projection = true
	probe.interior = true
	probe.update_mode = ReflectionProbe.UPDATE_ONCE
	probe.ambient_mode = ReflectionProbe.AMBIENT_DISABLED
	add_child(probe)
```

说明：

- **环境光必须抬高**。Blender 里的 Fill / Bounce / Sky / CloudBounce 四盏面光都不会导出，只靠 GLB 里的太阳，柱廊内侧会死黑。`0.42` 的冷色环境光配合 `0.35` 的无阴影补光是折中点；环境光偏冷、补光偏青，能保住石材阴影里的空气感。
- 环境光色 `#cfe6f0` 取自天空中层；如果想让画面更暖，改成 `#e8e2d2`，能量保持不变。
- 探针会从中心捕捉穹顶的云海与金色结构；`gold`、`gold_deep`、`rune` 才有东西可反射。不加探针时，金属度 0.88 的金色在 Godot 里会接近黑色，只剩高光点。
- 探针分辨率由项目设置 `rendering/reflections/reflection_atlas/reflection_size` 控制（默认 256），不是 ReflectionProbe 的属性；静态场景可调到 512，`UPDATE_ONCE` 即可。
- 探针尺寸 70×60×70 覆盖主体与近景浮岛；`box_projection` 必须拼写正确（不是 `box_project`）。
- `env.fog_sky_affect = 0.0` 是刻意的：天空与云海已经在贴图里，环境雾只作用于几何体，避免把烘焙天空再洗一遍。
- 背景色只是穹顶缝隙的兜底；穹顶完整覆盖视野时看不到它。若把穹顶隐藏改用天空着色器，请把这个颜色同步成天空地平线色。
- 若想更接近 Blender 的 AgX - Medium High Contrast 观感，可把 `adjustment_contrast` 提到 1.10、`adjustment_saturation` 提到 1.10；Godot 没有 Blender 的同名 look，需要手动配。
- 低配机器可关闭 SSAO，或把 `ssao_intensity` 降到 0.8；Glow 不建议全关，否则符文、心晶与火盆会显得干。

---

## 7. 性能参考

- 92.7 k 三角面、42 个网格、16 个材质、13 张贴图、8 盏灯，桌面 GPU 无压力。
- 主要开销：4096×2048 天空贴图、4096 方向光阴影、SSAO、Glow、ReflectionProbe。
- 天空穹顶 16,128 三角面双面渲染，开销可以忽略。
- 贴图未压缩时约 99 MiB 显存（除 4096×2048 天空外，其余为 1024² / 512²）；Godot 默认对 3D 纹理做 VRAM 压缩，显存会明显下降。
- 点光不投影，7 盏可以同时开；如果给火盆开阴影，会多出 4 张 6 面立方体阴影，收益不大。
- 移动端建议：天空贴图降到 2048 宽、2× MSAA、关闭 SSAO / SSR、Glow 强度降到 0.5、反射探针 `UPDATE_ONCE`、点光 range 保持 5–9 m。
- 场景完全是静态的，没有骨骼、动画或脚本；GLB 加载后即可停止处理，适合做背景关卡或主菜单场景。

---

## 8. 已知差异

| 效果 | Blender 预览 | Godot 静态导入 |
|---|---|---|
| 天空 / 云海 | Cycles 世界背景 + 240 m 发光穹顶 | 仅发光穹顶（几何体），需 Glow 提亮 |
| 雾 | world volume 体积雾（仅预览，不导出） | Environment 指数雾，密度 0.0025 |
| 补光 | 冷色面光 + 暖色反弹光 + 顶部天光 + 云海反弹 | 面光不导出；用环境光 0.42 + 无阴影补光 0.35 |
| 阴影 | Cycles 光线追踪，太阳 2.4° 张角 | 仅太阳阴影；点光默认无阴影 |
| 泛光 | 合成器 Fog Glow（仅预览） | 需启用 Glow；阈值 1.0 才能只让符文与天空发亮 |
| 色调 | AgX - Medium High Contrast | AGX + 饱和度 / 对比度微调 |
| 点光衰减 | 物理平方反比 | 导入 range 4096 m，必须重设 |
| 动画 | 无 | 无（纯静态）；可按第 9 节加轻微动效 |
| 太阳位置 | 方位 211° / 仰角 26° | 同一角度；旋转穹顶或太阳超过 ±15° 会看出错位 |

---

## 9. 可选的轻量动效

GLB 没有烘焙动画，但几个节点是独立网格，可以在 Godot 里做很轻的循环：

```gdscript
func _process(delta: float) -> void:
	var t := Time.get_ticks_msec() * 0.001
	var motes := arena.find_child("DAIS_Motes", true, false) as Node3D
	motes.rotate_y(delta * 0.06)

	var rings := arena.find_child("DAIS_HeartRings", true, false) as Node3D
	rings.rotate_y(-delta * 0.10)

	var heart := arena.find_child("DAIS_Heart", true, false) as Node3D
	heart.position.y = sin(t * 0.9) * 0.06

	for i in 4:
		var b := arena.find_child("LIGHT_Brazier_%02d" % i, true, false) as OmniLight3D
		b.light_energy = 5.5 * (1.0 + 0.07 * sin(t * 7.0 + i * 1.7))
```

- `DAIS_Motes` 的顶点绕世界原点分布，`rotate_y` 会让整圈浮尘缓慢公转。
- `DAIS_Heart` 的顶点中心在 y≈3.05，节点原点在 0；只改 `position.y` 做上下浮动，不要旋转它，否则心晶会绕广场中心甩动。
- `DAIS_HeartRings` 是三个同心金环，绕 Y 旋转最自然。
- 火盆闪烁只改灯光能量，不改材质；四个相位错开即可，不要用过高的频率。
