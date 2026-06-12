# 具身智能实验室运行框架 (Walking Skeleton)

基于 TECH-09 v1.0-approved 的平台 Pipeline 骨架实现。

## 策略

- **真实**：SQLite 索引、Run 目录、PreFlight、ResourceLock、Artifact 注册
- **Stub**：Isaac 子进程、ROS2、Driver Bridge、Policy 推理

## 快速开始

```bash
cd lab_platform
pip install -e .

# 初始化 data/ 目录
lab init

# 一键跑通全链路
lab demo full

# 查看 runs
lab list

# 查看血缘
lab lineage isaac_YYYYMMDD_HHMMSS_p2_train

# 一键冒烟（清空 data 后跑全流程）
python scripts/smoke_test.py
```

## 包结构

```text
lab_platform/
├── cli.py              # lab 命令入口
├── protocols.py        # 模块间接口 Protocol
├── workspace.py        # init + registry 模板
├── index/              # IndexService (SQLite)
├── preflight/          # PreFlightGate
├── scheduler/          # ResourceScheduler
├── run_manager/        # Run 生命周期编排
├── artifacts/          # ArtifactRegistry
├── pipelines/          # Pipeline A hooks + demo_full
└── stubs/              # 可替换假实现
```

## 并行开发

| 替换 Stub | 负责 |
|-----------|------|
| `StubIsaacLauncher` | Isaac 集成 |
| `StubRealRuntime` | F5/F6 Real 栈 |
| `StubRos2Bridge` | ROS2 run_context |
| `DefaultPreFlightGate` | 补全 PF 检查 |

**不要改**：`RunManager.execute()` 流程、`protocols.py` 接口、Run 目录契约。

设计文档：`docs/modules/framework_skeleton_design_v1.md`
