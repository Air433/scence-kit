# AGENTS.md — AI 助手入口

这是 Blender 5.2 → glTF/GLB → Godot 的程序化**竞技场场景**生成工具。
本文件只放必须先知道的内容；完整工作流、参数表、坑与验证清单见 **[GUIDE.md](GUIDE.md)**。

## 工作方式

- 一个场景 = `scenes/<name>/scene.py` 的一份参数表；共用引擎在 `arena_kit/`。
- 新场景：复制 `scenes/_template/` 到 `scenes/<name>/`，改 `name` / `seed` / `glb_name` / `palette` 等。
- 能在参数表里表达的，**不要改 `arena_kit/`**；场景专属逻辑放 `scenes/<name>/`（可选 `materials.py`、`textures.py`、`builder.py` 钩子）。
- 需要实时海面/天气/动态天空时，Godot 工程放 `godot/<name>/`，GLB 以副本形式放进其 `assets/`。
- 生成物按场景分目录：`output/<name>/`、`renders/<name>/`、`textures/<name>/`、`checkpoints/<name>/`。这些目录不入库；`output/<name>/README_Godot.md` 例外。

## 常用命令

Blender 路径：`D:/software/Blender Foundation/Blender 5.2/blender.exe`

```bash
blender -b -P build.py -- --list-scenes
blender -b -P build.py -- --scene <name> --phase all --render quick   # 首次构建 + 低采样预览
blender -b -P build.py -- --scene <name> --phase lighting --resume --render mid  # 调光迭代
blender -b -P build.py -- --scene <name> --phase export              # 导出并打印 GLB 校验
```

阶段顺序：`materials → camera → terrain → arena → arch → trees → foliage → props → lighting`。

Godot 路径：`D:/software/Godot_v4.7.2/Godot_v4.7.2-stable_win64_console.exe`

```bash
godot --path godot/island_arena                              # 运行海岛实时工程
godot --headless --path godot/island_arena --import          # 换 GLB 后必须重新导入
godot --path godot/island_arena -- --mood=night --cam=hero --frames=160 --shot=<png>
```

海岛的实时层（波形海面、平面反射、程序化天空、雨/闪电、风力植被、三套天气）在 `godot/island_arena/`，细节见其中 `README.md`。只替换 `assets/island_arena.glb` 而不重新导入，会继续使用旧缓存。

## 硬约束（都是踩坑换来的，不要"简化"）

1. 导出必须 `export_import_convert_lighting_mode="COMPAT"`，否则 Godot 灯光亮约 700 倍。
2. 植被 alpha 走 `Image Alpha → GREATER_THAN 0.5 → Principled Alpha`，双面；否则 Godot 排序错误。
3. Blender 5.2 Cycles 会静默丢弃 ≥ ~24 m 的物体体积；地面雾必须用 **world volume**（只用于预览，不导出）。
4. 禁止 Draco / meshopt / gltfpack；Godot 无法解压。
5. 材质要 `use_fake_user = True`，否则阶段清理会删掉。
6. `.blend` 存绝对贴图路径；移动贴图目录后需 `util.relocate_images()`（checkpoint 加载与导出已自动调用）。
7. 随机数用固定种子 + `zlib.crc32` 派生，禁用内置 `hash()`，保证可复现。
8. Cycles CPU 渲染在受限沙箱里会 OOM，需要放宽沙箱/内存限制运行。

## 交付标准

- GLB 在 `output/<scene>/`，贴图内嵌，单文件自包含。
- 预览在 `renders/<scene>/`：`preview_main.png`（快速）、`preview_mid.png`（迭代）、`hero.png`（主视觉）。
- 导出校验：`images` 数量正确、MASK 材质数量与场景设计一致（精灵 4 / 海岛 3）、无 "image has no size" 警告、灯光/相机齐全。
- Godot 导入参数见 `output/<scene>/README_Godot.md`；换场景后天空色、雾密度、环境光要重调。
- 实时场景额外提供 `godot/<scene>/README.md`，写清运行方式、操作、截图参数与换 GLB 后的重导入命令。

## 给 AI 会话的开场白

用户新建场景时通常会给出：场景名、风格、规模、时间与光、配色、相机、特殊元素。
按 GUIDE.md 第 11 节流程执行即可。
