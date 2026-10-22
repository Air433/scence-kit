# 程序化竞技场场景生成器

![热带海岛竞技场](renders/island_arena/hero.png)

Blender 5.2 → GLB → Godot 的竞技场场景工具。引擎在 `arena_kit/`，每个场景是一份 `scenes/<name>/scene.py` 参数表。

```bash
# 列出场景
blender -b -P build.py -- --list-scenes

# 完整构建 + 导出 + 预览
blender -b -P build.py -- --scene elven_arena --phase all --render mid
```

- 新建场景：复制 `scenes/_template` → 改 `scene.py` → 构建
- 完整工作流、参数说明、技术坑与验证清单：见 [GUIDE.md](GUIDE.md)
- 示例场景：
  - `scenes/island_arena/`：热带海岛竞技场。上图为 Blender 离线渲染，Godot 实时版（海浪、反射、三套天气）见 [godot/island_arena/README.md](godot/island_arena/README.md)
  - `scenes/elven_arena/`：精灵森林竞技场，交付物在 `output/elven_arena/`
- Godot 导入与推荐 WorldEnvironment：`output/elven_arena/README_Godot.md`
