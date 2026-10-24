# 热带海岛竞技场 · Godot 实时工程

`godot/island_arena` 是 `scenes/island_arena` 的实时运行时：静态岛屿来自 GLB，海面、天空、反射、天气、风力植被和灯光全部由本项目在运行时生成。它和 `godot/cel_forest_arena` 同属 `godot/` 下的一个 Godot 工程，共用 `godot/common/` 里的相机、HUD 与截图逻辑。

- 引擎：**Godot 4.7.2**，Forward+，Vulkan（实测 GTX 1050 Ti）
- 分辨率：1600 × 900，MSAA 2×
- 场景：`island_arena/main.tscn`，入口脚本 `island_arena/scripts/main.gd`
- 资产：`island_arena/assets/island_arena.glb`（与 `output/island_arena/island_arena.glb` 完全一致）

## 运行

```bash
# 编辑器（打开合并工程，再选 island_arena/main.tscn）
"D:/software/Godot_v4.7.2/Godot_v4.7.2-stable_win64.exe" --editor --path godot

# 直接运行
"D:/software/Godot_v4.7.2/Godot_v4.7.2-stable_win64.exe" \
  --path godot res://island_arena/main.tscn -- --mood=night
```

## 操作

| 输入 | 功能 |
|---|---|
| 左/右键拖动 | 环绕、俯仰（指数阻尼平滑） |
| 滚轮 | 推拉（16–130 m） |
| 空闲 5 秒 | 自动环绕；拖动立即接管 |
| `1` / `2` / `3` | 晴天 / 暴雨 / 夜晚 |
| `R` | 随机天气（不会重复当前） |
| `C` | 开关自动环绕 |
| `H` | 显示 / 隐藏底部提示 |

自动换天气在进入场景 82 秒后开始，之后每 62–96 秒随机切换；过渡由 `blend_speed = 0.24` 平滑插值（约 4 秒）。

## 命令行参数（截图 / 自动化）

```bash
Godot_v4.7.2-stable_win64_console.exe --path godot res://island_arena/main.tscn -- \
  --mood=storm --cam=hero --frames=160 \
  --shot=D:/game/scence/linzhongjijichang/renders/island_arena/godot_storm.png
```

| 参数 | 说明 |
|---|---|
| `--mood=sunny\|storm\|night` | 初始天气；默认 sunny |
| `--random` | 随机初始天气 |
| `--cam=hero\|shore\|low\|east\|top` | 相机预设；默认 hero |
| `--shot=<绝对路径>` | 截图后退出；同时输出同目录 `<name>_refl.png`（反射缓冲） |
| `--frames=N` | 第 N 帧截图（默认 100）；留出着色器/反射稳定时间 |
| `--nofog` | 关闭线性雾与体积雾，便于排查 |

截图模式会隐藏 HUD、关闭自动天气与自动环绕，并固定 1600×900。

## 换 GLB 后必须重新导入

Godot 使用 `.godot/imported/*.scn` 缓存。只替换 `island_arena/assets/island_arena.glb` 而不重新导入，运行时会继续使用旧场景。

```bash
cp output/island_arena/island_arena.glb godot/island_arena/assets/island_arena.glb
"D:/software/Godot_v4.7.2/Godot_v4.7.2-stable_win64_console.exe" \
  --headless --path godot --import
```

`island_arena/assets/island_arena.glb.import` 已设 `gltf/embedded_image_handling=3`（贴图内嵌进导入场景），因此 `assets/` 下不会再生成 24 张 sidecar PNG；整个工程只需要 GLB + `water_normal.png` + `foam.png`。

## 结构

```
godot/project.godot                    共用工程：Forward+、1600×900、MSAA 2×、4096 阴影
godot/common/scripts/orbit_camera.gd   两场景共用的平滑环绕相机
godot/common/scripts/hud.gd            共用 HUD：标题、副标题、底部提示
godot/common/scripts/capture.gd        共用命令行解析与截图
godot/island_arena/main.tscn           Node3D + Camera3D
godot/island_arena/scripts/scene_profile.gd  场景配置：GLB、节点名、相机、岸线、HUD
godot/island_arena/scripts/main.gd     环境、GLB 加载、海面、平面反射、雨、UI、天气插值
godot/island_arena/scripts/weather.gd  三套天气参数表 + 时间流逝
godot/island_arena/shaders/sky.gdshader      程序化天空：渐变、太阳、月亮、云、星空、闪电
godot/island_arena/shaders/ocean.gdshader    波形、浅深水、反射、泡沫、太阳高光、远海雾
godot/island_arena/shaders/terrain.gdshader  按世界高度/坡度/噪声混合湿沙、沙、草、岩石
godot/island_arena/shaders/wind.gdshader     叶片 UV.y 加权摆动 + 高频颤动
godot/island_arena/shaders/vignette.gdshader 暗角
```

`scene_profile.gd` 只放场景数据、不放逻辑。新增竞技场时复制 `godot/island_arena/` 成 `godot/<name>/`，替换 `assets/` 下的 GLB，改这个文件里的 `GLB_PATH` / `NODES` / `CAMERA` / `CAMERA_PRESETS` / `SHORE` / `HUD`，再按新场景改 `weather.gd` 的配色即可。相机、HUD、命令行与截图已抽到 `godot/common/`，不需要复制；运行时本身的逻辑（海面、反射、天气插值、雨）也不需要动。`shaders/ocean.gdshader` 里的 `terrain_h()` 仍是海岛地形的解析近似，换地形轮廓时需同步调整。

### 运行时构建内容

- **海面**：程序化网格（168 环，半径 24 km），顶点位移与着色器使用同一套正弦波；海床深度解析自 `layout.py` 的岸线公式，由 `SceneProfile.SHORE` 以 uniform 传入着色器，用于岸边透明度和泡沫。
- **平面反射**：960×540 `SubViewport`，镜像相机 Y 翻转 + 斜裁剪；反射相机排除海床（`LAYER_SEABED` = 2）、水面（`LAYER_WATER` = 4）和特效层（`LAYER_FX` = 8，雨/闪光不进反射），并禁用火焰、灯泡、窗户等自发光面，避免镜像视角下的错误曝光。
- **地形**：GLB 的 `TERRAIN_Island` 用 `material_override` 换成连续混合着色器，消除按面分配材质造成的锯齿，并保留贴图法线。
- **天气**：`weather.gd` 中每套天气是一组标量/颜色/向量；`_mix_state` 插值后统一写入天空、海面、雾、灯光、雨和风。
- **雨**：11000 个 GPUParticles3D，27 m 盒形发射，1.35 s 生命，锥形渐变长条贴图。
- **闪电**：暴雨时随机 5.5–13 s 触发，短时提升平行光 + HUD 闪白 + 天空闪电参数。
- **灯塔光束**：夜间可见的 SpotLight，随夜色增强，绕塔缓慢旋转。
- **夜间**：月亮与程序化星空由天空着色器绘制；火把、串灯、灯塔、罗盘各自的点光随 `night` 增强。

## 图层

| 常量 | 值 | 用途 |
|---|---|---|
| `ALL_LAYERS` | `0xFFFFF` | 主相机 |
| `LAYER_SEABED` | `2` | 海床（主相机可见，不投影，不进入反射） |
| `LAYER_WATER` | `4` | 海面（主相机可见，不进入反射） |
| `LAYER_FX` | `8` | 雨与特效（不进入反射） |

## 性能与调参

- 主要开销：960×540 平面反射（每帧二次渲染）、体积雾、4096 平行光阴影、MSAA。GTX 1050 Ti 在 1600×900 下可交互运行。
- 想更快：把 `refl_vp.size` 降到 640×360；关闭 `env.volumetric_fog_enabled`；把 `sun.directional_shadow_max_distance` 从 280 降到 180。
- 想更清晰：提高 `refl_vp.size` 到 1280×720，并把 `msaa_3d` 提到 4×。
- 海面与天空的远景颜色按太阳方位角匹配（`horizon_warm` / `horizon_cool`）；换天空配色时同步检查 `_apply_state` 里的这两个 uniform，否则远处会出现海天分界。
- 海面 `fog_disabled`：环境雾只作用于陆地，海天衔接由着色器自己完成。

## 已知限制

- 反射是平面镜像，只对海平面成立；水下物体和折射不参与。
- Godot 的 `.godot/` 缓存不入库，首次打开共享工程需要导入两个场景的 GLB（约 30–40 秒）。
- 场景依赖 `scenes/island_arena/layout.py` 的岸线函数；改动岛屿轮廓后，需要同步 `ocean.gdshader` 里的 `shore_radius`。
