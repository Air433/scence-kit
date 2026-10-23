# 竞技场场景生成工具 · 使用与扩展指南

这是一个 **Blender → GLB → Godot** 的程序化场景生成项目。引擎在 `arena_kit/`，每个场景只是 `scenes/<name>/scene.py` 里的一份参数表。

目标：新建一个竞技场时**不复制代码**，只写参数；需要换风格时再按需覆盖材质/贴图。

---

## 1. 三十秒上手

```bash
# 查看已有场景
"D:/software/Blender Foundation/Blender 5.2/blender.exe" -b -P build.py -- --list-scenes

# 完整构建 + 导出 + 快速预览
"D:/software/Blender Foundation/Blender 5.2/blender.exe" -b -P build.py \
  -- --scene elven_arena --phase all --render quick
```

产物：

| 内容 | 路径 |
|---|---|
| GLB | `output/<scene>/<glb_name>` |
| Blender 源文件 | `checkpoints/<scene>/<glb_name 去掉 .glb>.blend` |
| 渲染 | `renders/<scene>/preview_main.png`、`preview_mid.png`、`hero.png` |
| 程序化贴图 | `textures/<scene>/*.png` |

---

## 2. 目录结构

```
build.py                  命令行入口（场景加载、分阶段构建、渲染、导出）
arena_kit/                可复用引擎
  scene.py                场景注册、spec 校验、apply 到 config
  config.py               全部可调参数的运行时副本 + 路径切换
  util.py                 RNG、集合、网格、UV、管道/放样、散布、贴图重定位
  terrain.py              地形（FBM + 中心压平）
  arena.py                看台环阶、石板、入口台阶、符文
  architecture.py         立柱、拱门、祭坛、碎石
  trees.py                树干、板根、分枝、叶片卡片
  foliage.py              蕨、草、苔藓、蘑菇、落叶、远景灌木
  props.py                巨石、倒木、藤蔓、灯笼、萤火虫
  materials.py            PBR / 自发光 / MASK alpha 材质
  textures.py             程序化贴图生成（numpy，无需联网）
  lighting.py             太阳、补光、反弹光、点光、世界体积雾
  camera.py               构图相机
  export.py               glTF 导出 + GLB 结构校验
scenes/
  _template/scene.py      新场景模板（带逐项注释）
  elven_arena/scene.py    第一个场景（精灵森林竞技场）
  island_arena/           热带海岛竞技场（自带 builder.py，见下）
  star_arena/             星空竞技场（自定义 builder.py + 贴图 + 材质）
  <name>/materials.py     可选：该场景自己的材质库
  <name>/textures.py      可选：该场景自己的贴图生成器
  <name>/builder.py       可选：该场景自己的阶段编排（岛屿形状与精灵场景不同）
godot/
  island_arena/           海岛的实时运行时（Godot 4.7），详见其中 README.md
output/  renders/  textures/  checkpoints/   均按场景名分目录
```

`builder.py` 只有在该场景的舞台形状无法用 `arena_kit` 的参数表达时才需要。它实现与 `build.py` 相同的 `build(phases, ...)` 契约，并可选提供 `set_mist_enabled()`；`build.py` 会自动发现它。海岛的岛形、灯塔岬角、沙滩岸线都在 `scenes/island_arena/` 内，`arena_kit` 只保留通用工具和导出器。

生成器**只在调用时**读取 `config.*`，所以 `scene.load()` 直接改写 config 就能换场景，不需要给每个函数传参。

---

## 3. 新建一个场景

### 3.1 复制模板

```bash
cp -r scenes/_template scenes/my_arena
```

把 `scenes/my_arena/scene.py` 里的 `SCENE["name"]` 改成 `"my_arena"`（必须与目录名一致），设置 `seed` 与 `glb_name`。

### 3.2 改参数

最少改三处就能看出差别：

1. `palette` —— 石材、苔藓、地表、树皮、叶子、符文/灯笼的十六进制颜色
2. `world` —— 半径、台阶数、看台进深/高度、柱廊半径
3. `lighting` —— 太阳方向/色温、环境强度、雾密度

其余（树的数量与方位、植被密度、相机）按需调整。

### 3.3 构建

```bash
# 先出快速预览（960×540，24 spp，无雾）
blender -b -P build.py -- --scene my_arena --phase all --render quick

# 构图/光照确认后出带雾的中等预览（1200×675，40 spp）
blender -b -P build.py -- --scene my_arena --phase all --render mid

# 最终主视觉（默认 72 spp，可加 --samples 80/96）
blender -b -P build.py -- --scene my_arena --phase render --render hero --samples 80
```

> Cycles 用 CPU 渲染。在受限沙箱里运行时会被内存上限杀掉，需要关闭沙箱执行。

### 3.4 只改光照时，不要重建几何

```bash
blender -b -P build.py -- --scene my_arena --phase lighting --resume --render mid
```

`--resume` 会加载 checkpoint，只重建指定阶段。确认后要写回 checkpoint 并重新导出，用一次完整构建或写一段小脚本调用 `export.save_blend()` + `export.export_glb()`。

---

## 4. 场景参数速查

完整字段与默认值见 `scenes/_template/scene.py`。所有未知字段会被 `arena_kit/scene.py` **直接报错**并列出合法 key，避免拼写错误静默失效。

> `island_arena` 的岛形、岸线、灯塔与棕榈由 `scenes/island_arena/builder.py` 编排，参数结构与本节的圆环竞技场不同；以 `scenes/island_arena/scene.py` 与 GUIDE 第 9 节为准。下面的通用字段适用于 `elven_arena` 与从 `_template` 新建的场景。

### 4.1 `world`（米）

| 字段 | 含义 |
|---|---|
| `terrain_size` / `terrain_res` | 地形边长 / 每边顶点数 |
| `inner_r` | 竞技场平整地面半径 |
| `tier_count` / `tier_tread` / `tier_rise` | 看台层数 / 踏面深 / 每级高 |
| `colonnade_r` | 立柱环半径 |
| `rune_r` | 中央符文半径 |
| `floor_z` / `terrain_base_z` | 地面高度 / 地形基准面 |

`OUTER_R = inner_r + tier_count × tier_tread` 自动推导。

### 4.2 `trees`

| 字段 | 含义 |
|---|---|
| `hero_count` | 主树数量，必须等于两个数组长度 |
| `bg_count` | 远景简化树数量 |
| `hero_angles` | 每棵主树的方位角（度） |
| `hero_radii` | 每棵主树的半径距离（米） |

主树半径建议 > `colonnade_r + 2`，否则板根会插进看台。

### 4.3 `counts`

`ferns` / `grass` / `mushrooms` / `boulders` / `fireflies` 是**上限**；实际数量会被碰撞与相机楔形区拒绝一部分。

### 4.4 `camera`

`loc`、`target`、`lens`。相机同时用于所有渲染并导出为 `CAM_Hero`。

### 4.5 `palette`

固定 14 个 key：`stone`、`stone_dark`、`stone_warm`、`moss`、`moss_bright`、`ground`、`bark`、`leaf`、`leaf_light`、`rune`、`lantern`、`mushroom`、`wood`、`shadow`。

十六进制会转成线性 RGB；材质、顶点色、灯光颜色都从这里取。

### 4.6 `sky_stops`

`(0..1 天顶方向高度, 十六进制颜色)` 列表，仅用于 Cycles 预览天空，**不导出**。

### 4.7 `lighting`

| 字段 | 说明 |
|---|---|
| `sun_energy` | Blender 太阳强度；**glTF 导出恒为 1.0**，此值只影响 Blender 渲染 |
| `sun_temperature` / `sun_angle_deg` | 色温 / 角直径（越大阴影越软） |
| `sun_pos` / `sun_target` | 太阳位置与照射目标（决定长阴影方向） |
| `fill_*` / `bounce_*` | 冷色补光与暖色反弹光，**仅预览**，不导出 |
| `exposure` | Blender 曝光 |
| `world_strength` | 天空环境光强度（预览） |
| `mist_*` | 地面雾：密度 / 高度 / 颜色 / 各向异性；`mist_density = 0` 关闭，**仅预览** |
| `lantern_*` | 导出的灯笼点光强度（近/远）与色温 |
| `rune_light_energy` | 符文点光强度 |

### 4.8 `materials`

自发光强度：`rune_emission`、`lantern_emission`、`mushroom_emission`、`firefly_emission`。大于 1 会写成 `KHR_materials_emissive_strength`。

---

## 5. 构建阶段

```
materials → camera → terrain → arena → arch → trees → foliage → props → lighting
```

- `--phase <阶段>`（不带 `--resume`）：**清空场景**，从 materials 顺序构建到该阶段。
- `--phase <阶段> --resume`：加载 checkpoint，**只重建该阶段**。
- `--phase export` / `--phase render`：只加载 checkpoint，导出 / 渲染。
- `--export`：单阶段构建后额外导出。
- `--no-save`：不写 checkpoint。
- `--seed`：临时覆盖场景种子（用于试不同随机布局）。

每个阶段结束都会保存 checkpoint（完整构建时）。checkpoint 文件名由 `glb_name` 推导。

---

## 6. 什么时候改哪里

| 需求 | 改哪里 |
|---|---|
| 换配色、尺寸、密度、太阳方向、相机 | `scenes/<name>/scene.py` |
| 换石材/地表/树叶贴图 | 新场景的 `textures.py`（复用 `arena_kit/textures.py` 的噪声与 stamp 工具） |
| 换材质组合或自发光参数 | 新场景的 `materials.py`，实现 `build_materials(force_textures=False)` 与 `get_materials()` |
| 加新的装饰物/建筑构件 | `arena_kit/architecture.py` / `props.py`，然后用配置开关控制是否生成 |
| 换整个主题（沙漠、火山、地底） | 先改 palette + textures；结构生成器通常不用动 |

场景级 `materials.py` 由 `build.py` 自动发现，不需要改引擎。

---

## 7. 技术约束与已知坑

这些都是实际踩过的，改动前务必阅读。

1. **glTF 只认图片贴图**。程序化节点、粒子、几何节点、体积雾、合成器辉光都不会导出。项目里所有材质只用图片 + Principled。
2. **alpha 必须用 MASK**：
   `Image Alpha → Math(GREATER_THAN, 0.5) → Principled Alpha`，并关闭背面剔除。
   直接连 Alpha 会导出成 `BLEND`，在 Godot 中排序异常。
3. **灯光单位必须用 COMPAT 导出**：
   `export_import_convert_lighting_mode="COMPAT"`。用 SPEC 时 Godot 亮度会高约 700 倍（95 W → 5163）。
4. **不要开 Draco / meshopt / gltfpack**，Godot 没有对应解压扩展。
5. **Blender 5.2 Cycles 会静默丢弃超大物体体积**（约 24 m 以上，调步长无效）。地面雾因此放在 **world volume** 里，用高度渐变衰减；world shading 不导出。
6. **材质要 `use_fake_user = True`**，否则阶段的孤立数据清理会把它们删掉。
7. **确定性**：固定 `SEED`，各子系统用 `zlib.crc32(f"{SEED}:{name}")` 派生，绝不用 Python `hash()`。
8. **贴图路径**：`.blend` 保存的是绝对路径。移动贴图目录后调用 `util.relocate_images()`（`build.load_checkpoint()` 与导出前已自动调用），否则导出会静默丢贴图。
9. **相机楔形区**：植被散布会避开相机视线楔形，保证主视觉不被挡。改相机后需要重建 foliage。
10. **Cycles CPU 渲染在受限沙箱中会 OOM**，需要关闭沙箱运行。

---

## 8. 验证流程

每次交付前至少跑一遍：

1. **GLB 结构**（导出时自动打印）：
   - `alpha {'OPAQUE': …, 'MASK': 4}`，MASK 材质为叶片/草/蕨/落叶
   - `images` 数量与贴图文件数一致，无 “image has no size” 警告
   - `extensionsUsed` 只包含 `KHR_materials_emissive_strength` 与 `KHR_lights_punctual`
   - 三角面在预算内（参考：31.6 万）
2. **渲染**：`preview_mid.png` 检查构图、雾、明暗与细节；`hero.png` 检查最终质感。
3. **Godot**：新建临时工程导入 GLB，确认材质、自发光、灯光、相机都在；每个场景的导入参数见 `output/<scene>/README_Godot.md`。
4. **尺度**：竞技场中心在原点，地面约 y = 0；1.7 m 参考人形应到成年人高度。

---

## 9. Godot 交付

三个场景的导入说明：

- `output/elven_arena/README_Godot.md` —— 静态竞技场的导入参数、灯光强度表、已验证的 `WorldEnvironment`（`ProceduralSkyMaterial` + AgX + Glow + SSAO + 线性雾 + 体积雾）。
- `output/island_arena/README_Godot.md` —— 海岛 GLB 的实测数据与导入设置；动态海面、天空、天气与平面反射由 `godot/island_arena` 实时工程提供。
- `output/star_arena/README_Godot.md` —— 星空竞技场的实测数据；重点在星穹不投影、点光 range 重设、太阳阴影、面光不导出后的环境光/补光，以及 ReflectionProbe。

### 海岛实时工程

`godot/island_arena` 是完整的 Godot 4.7 工程，可直接运行：

```bash
"D:/software/Godot_v4.7.2/Godot_v4.7.2-stable_win64.exe" --path godot/island_arena
```

- 操作：拖动旋转、滚轮缩放、`1/2/3` 切换晴/暴雨/夜、`R` 随机天气、`C` 自动环绕、`H` 隐藏提示；空闲 5 秒后自动环绕。
- 动态内容：波形海面、960×540 平面反射、岸边泡沫、程序化天空/云/月亮/星空、风力棕榈与草、雨与闪电、火把闪烁、旋转灯塔光束。
- 天气由 `scripts/weather.gd` 的参数表驱动，切换时约 4 秒平滑插值。
- 场景数据集中在 `scripts/scene_profile.gd`：GLB 路径、GLB 节点名、材质键、天气时长、相机预设、灯光范围、灯塔光束、岸线谐波、HUD 文案。复用工程做新场景时只改这里（加 `weather.gd` 的配色），运行时逻辑不动。

> **换 GLB 后必须重新导入**：只替换 `godot/island_arena/assets/island_arena.glb` 而不跑导入，Godot 会继续使用 `.godot/imported` 里的旧缓存。

```bash
cp output/island_arena/island_arena.glb godot/island_arena/assets/island_arena.glb
"D:/software/Godot_v4.7.2/Godot_v4.7.2-stable_win64_console.exe" \
  --headless --path godot/island_arena --import
```

工程使用 `gltf/embedded_image_handling=3`（贴图内嵌进导入场景），因此不会在 `assets/` 下生成 sidecar PNG。`.godot/` 缓存已加入 `.gitignore`。

换场景后：**天空色、雾密度、环境光强度**要按新配色重调；静态场景的其余导入步骤不变。

---

## 10. 给后续 LLM 会话的工作约定

- 先读本文件与 `scenes/<name>/scene.py`，不要先读 `arena_kit/` 全部源码。
- 新需求优先用场景参数表达；参数表达不了再改生成器。
- 改光照/配色时用 `--resume --phase lighting --render mid` 快速迭代，不要每次全量重建。
- 任何导出改动后，检查 GLB 的 `images` 数量与 MASK 材质数量。
- 不要把场景专属逻辑写进 `arena_kit/`；把它放进 `scenes/<name>/`。
- 交付物路径固定为 `output/<scene>/`，渲染在 `renders/<scene>/`。

---

## 11. 新建场景时可以直接对 LLM 说的话

仓库根目录的 `AGENTS.md` 是给 AI 的入口（Claude Code 会通过 `CLAUDE.md` 自动加载，其他工具让它先读一次即可），架构、常用命令和技术坑都在里面，不需要重复交代。最短只要一句：

> 在 `D:\game\scence\linzhongjijichang` 新建场景 `<scene_name>`：`<一句话描述风格>`。先读 `AGENTS.md` 和 `GUIDE.md`，从 `scenes/_template` 复制，再构建、渲染、导出并给出 Godot 参数。

想要更可控就用下面的模板，按需填写：

```text
在 D:\game\scence\linzhongjijichang 新建一个竞技场场景：<scene_name>

风格：<例：火山熔岩竞技场，黑曜石看台、暗红天光、空气里有火星>
规模：<例：比精灵竞技场小一圈 / 保持默认>
时间与光：<例：黄昏逆光 / 夜晚冷月光 / 清晨薄雾>
配色：<主色 + 点缀色，例：玄武岩黑 + 熔岩橙>
相机：<例：更低的平视视角，35 mm / 保持默认>
特殊元素：<例：不要符文圆环，中央改成火盆；保留灯笼>

请按这个顺序做：
1. 读 AGENTS.md 与 GUIDE.md，复制 scenes/_template 到 scenes/<scene_name>
2. 只改 scene.py（name/seed/glb_name/palette/world/lighting），不动 arena_kit
3. --phase all --render quick 先确认构图和尺度
4. --resume --phase lighting --render mid 迭代光照，再出 hero
5. --phase export，检查贴图数 / MASK 数 / 灯数
6. 按新配色更新 Godot 的 WorldEnvironment（天空、雾密度、环境光）
```

补充几个说法上的技巧：

- **说风格，不说参数**：“黄昏逆光、地面有薄雾” 比 “sun_energy 调低” 更容易得到协调的结果；LLM 会翻译成参数。
- **给参照物**：“比精灵竞技场小一圈”“树更稀疏”“看台 5 级” 都可以直接落到 `world` / `trees` / `counts`。
- **明确要不要动引擎**：默认约定是只改 `scene.py`；确实需要新几何或新材质时，直接说“允许新增 arena_kit 模块 / 场景级 materials.py”。
- **交付标准**：说清要不要 GLB、hero 渲染、Godot 参数三件套，避免只出一张预览图就结束。
