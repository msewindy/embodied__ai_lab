# 本地外部资料挂载（不进 Git）

本目录用于在**本机工作区**挂载仓库外的大资料/兄弟项目，便于统一浏览与路径引用。

## 纪律（必须遵守）

1. **不**把外部项目拷贝进本仓库  
2. **不**使用 Git Submodule / Subtree 引用外部 Git 仓库  
3. **不**把挂载点提交进 Git（见根目录 `.gitignore`）  
4. 本仓库只提交：本 `README.md`、建链脚本、以及本仓库内撰写的规划/适配文档  

## 世界模型资料（本地挂载）

| 项 | 值 |
|----|-----|
| 挂载点 | `external/world_model/` |
| 常见源路径（Linux） | `~/project/world_model`（与 `embodied__ai_lab` 同级） |
| 常见源路径（Windows） | `D:\project\世界模型` |
| 创建方式 | **symlink**（Linux） / Directory Junction（Windows） |

### lab-ws-02（Ubuntu）推荐命令

目录布局示例：

```text
~/project/
├── embodied__ai_lab/     # 本仓库
└── world_model/          # 世界模型资料（仓库外）
```

在仓库根目录执行：

```bash
cd ~/project/embodied__ai_lab
chmod +x scripts/link_external_world_model.sh
./scripts/link_external_world_model.sh
# 或显式指定：
# ./scripts/link_external_world_model.sh ~/project/world_model
```

等价手写（不跑脚本时）：

```bash
cd ~/project/embodied__ai_lab
mkdir -p external
ln -sfn ../world_model external/world_model
ls -ld external/world_model
test -f external/world_model/README.md && echo OK
```

### Windows PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\link_external_world_model.ps1
# 自定义源路径：
# .\scripts\link_external_world_model.ps1 -SourcePath "D:\path\to\世界模型"
```

### 校验

```bash
# Linux
ls -ld external/world_model
readlink -f external/world_model
test -f external/world_model/README.md && echo OK
```

```powershell
# Windows
Test-Path .\external\world_model\README.md
Get-Item .\external\world_model | Select-Object FullName, LinkType, Target
```

### 文档入口（挂载成功后）

- 资料库总览：`external/world_model/README.md`
- 主调研：`external/world_model/docs/` 下调研报告
- FR3 落地设计：`external/world_model/docs/` 下 FR3 验证框架文档
- **融合规划（本仓库）**：[`docs/plan/platform_wm_fusion_plan_v0.md`](../docs/plan/platform_wm_fusion_plan_v0.md)

---

*维护：R1 · 机制说明随仓库提交；挂载内容始终留在源目录*
