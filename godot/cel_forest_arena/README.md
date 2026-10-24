# 赛璐璐森林竞技场 · Godot 实时工程

`godot/cel_forest_arena` 是 `scenes/cel_forest_arena` 的实时运行时。GLB 提供静态几何与调色板贴图；MToon 材质、墨线描边、程序化天空与灯光由本项目在运行时生成。

- 引擎：**Godot 4.7.2**，Forward+，Vulkan
- 分辨率：1600 × 900，MSAA 2×
- 场景：`main.tscn`，入口脚本 `scripts/main.gd`
- 资产：`assets/cel_forest_arena.glb`（与 `output/cel_forest_arena/cel_forest_arena.glb` 完全一致，含 `VRMC_materials_mtoon` 扩展）

## 运行

```bash
# 编辑器
"D:/software/Godot_v4.7.2/Godot_v4.7.2-stable_win64.exe" --path godot/cel_forest_arena

# 直接运行
"D:/software/Godot_v4.7.2/Godot_v4.7.2-stable_win64.exe" --path godot/cel_forest_arena
```

## 操作

| 输入 | 功能 |
|---|---|
| 左/右键拖动 | 环绕、俯仰（指数阻尼平滑） |
| 滚轮 | 推拉（5–30 m） |
| 空闲 5 秒 | 自动环绕；拖动立即接管 |
| `1` / `2` / `3` / `4` | 主视觉 / 祭坛 / 全景 / 俯视 |
| `C` | 开关自动环绕 |
| `H` | 显示 / 隐藏底部提示 |

## 命令行参数（截图 / 自动化）

```bash
Godot_v4.7.2-stable_win64_console.exe --path godot/cel_forest_arena -- \
  --cam=hero --frames=110 \
  --shot=D:/game/scence/linzhongjijichang/renders/cel_forest_arena/godot_hero.png
```

| 参数 | 说明 |
|---|---|
| `--cam=hero\|altar\|wide\|top` | 相机预设；默认 hero |
| `--shot=<绝对路径>` | 截图后退出 |
| `--frames=N` | 第 N 帧截图（默认 90）；留出天空辐照度与描边稳定时间 |
| `--nofog` | 关闭线性雾与体积雾，便于排查 |

截图模式会隐藏 HUD、关闭自动环绕，并固定 1600×900。

## 换 GLB 后必须重新导入

Godot 使用 `.godot/imported/*.scn` 缓存。只替换 `assets/cel_forest_arena.glb` 而不重新导入，运行时会继续使用旧场景。

```bash
cp output/cel_forest_arena/cel_forest_arena.glb godot/cel_forest_arena/assets/cel_forest_arena.glb
"D:/software/Godot_v4.7.2/Godot_v4.7.2-stable_win64_console.exe" \
  --headless --path godot/cel_forest_arena --import
```

`assets/cel_forest_arena.glb.import` 已设 `gltf/embedded_image_handling=3`（贴图内嵌进导入场景），因此 `assets/` 下只保留 GLB 本身，不会生成 11 张 sidecar PNG。

## 结构

```
main.tscn                     Node3D + Camera3D（挂 orbit_camera.gd）
scripts/scene_profile.gd      场景配置：GLB 路径、相机预设、MTOON 材质表、天空、环境、灯光、描边
scripts/main.gd               环境、GLB 加载、材质覆盖、描边 next_pass、灯光、UI、截图
scripts/orbit_camera.gd       平滑环绕相机，垂直 FOV 46°
shaders/mtoon.gdshader        MToon 近似：二段式明暗 + 边缘光 + 自发光
shaders/mtoon_outline.gdshader 反壳描边（cull_front，顶点沿法线外扩）
shaders/cel_sky.gdshader      三段渐变、暖地平线、8 级量化条带、太阳辉光
```

`scene_profile.gd` 只放场景数据、不放逻辑。复制整个工程做新竞技场时，替换 `assets/` 下的 GLB，改这个文件里的 `GLB_PATH` / `CAMERA_PRESETS` / `MTOON` / `SKY` / `ENV` / `SUN` / `HUD` 即可；运行时逻辑与三个着色器都不需要动。

### 运行时构建内容

- **MToon 材质**：遍历 GLB 的 `MeshInstance3D`，按材质名（`stone`、`bark`、`leaf`…）套 `mtoon.gdshader`。参数来自 `scene_profile.gd` 的 `MTOON` 字典，同一材质只创建一次 `ShaderMaterial`。
- **透明卡片**：`leaf` / `litter` / `fern` / `grass` 设 `alpha_cut = 0.5`，双面渲染。
- **自发光**：`rune` / `lantern` / `mushroom` / `firefly` 不走贴图，ALBEDO 用自发光色压暗 0.35，`EMISSION` 按各自 `energy` 输出。**albedo_tint 的 alpha 必须为 1.0**，否则会与 `depth_prepass_alpha` 冲突导致整片不显示。
- **描边**：不透明材质通过 `next_pass` 叠加反壳描边；宽度 = 材质 `outline` × `OUTLINE_SCALE`（默认 2.5）。叶片与自发光体不描边。
- **天空**：`cel_sky.gdshader`，三段渐变 + 暖地平线 + 8 级条带（`band_strength = 0.55`），太阳方向与 `LIGHT_Sun` 一致。
- **环境**：ACES、曝光 1.02、环境光 `#cfe5dd` × 0.36、glow、SSAO、线性雾 + 体积雾、饱和度 1.12 / 对比 1.06。
- **灯光**：覆盖 GLB 里的 `LIGHT_Sun` 能量并开阴影；8 盏串灯与符文点光统一关阴影、设衰减与体积雾能量；另建一盏冷色补光托树冠暗部。

## 性能与调参

- 主要开销：4096 平行光阴影、体积雾、MSAA、每材质一次的描边 next_pass。
- 想更快：把 `PROFILE.SUN["shadow_distance"]` 降到 45；关闭 `env.volumetric_fog_enabled`；把 `OUTLINE_SCALE` 降到 1.5。
- 想更硬的赛璐璐感：降 `ENV.ambient_energy`（0.36 → 0.25）、提高 `ENV.contrast`，或加大 `OUTLINE_SCALE`。
- 想改描边颜色：`PROFILE.OUTLINE_COLOR`，默认 `#0b1a12`。

## 已知限制

- MToon 是运行时近似，不读取 GLB 里的 `VRMC_materials_mtoon` 扩展；改扩展参数不会自动影响 Godot，需要同步 `scene_profile.gd`。
- 反壳描边依赖模型法线连续；共面石板、薄叶片会跳过或出现断线。
- 天空条带按屏幕空间高度量化，相机俯仰很大时条带位置会跟着移动。
- 场景不含水面、天气切换与风；这些在海岛工程 `godot/island_arena` 里。
