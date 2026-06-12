# TECH-09 架构短评审记录 v1

| 属性 | 内容 |
|------|------|
| **日期** | 2026-06-10 |
| **文档** | TECH-09 `platform_technical_architecture_v1.md` |
| **结论** | **通过** → 升版 `v1.0-approved` |
| **参与** | P1（契约）、P2（架构）、P3（安全/资产） |

---

## 评审范围

- §二 大脑-小脑部署与交互分类
- §四–§六 Run / Artifact / 产物清单
- §七 Real 运行时 Pipeline 与 ROS2 边界
- §八 Lab Operations Layer（PreFlight、ResourceScheduler、Pipeline C）
- §九 数据与索引逻辑模型

## 决议

| # | 议题 | 决议 |
|---|------|------|
| 1 | Run 模型 | 维持三条 Pipeline（A/B/C）+ Artifact 传递，废弃旧 6 Run 命名 |
| 2 | ws-02 无 ROS2 | **冻结**，checkpoint 仅文件同步 |
| 3 | Driver Bridge | **强制 onboard**，大脑不得跨网调 SDK |
| 4 | 2 台并发 | ResourceScheduler `zone_lock` + `device_lock` 落实 |
| 5 | PreFlight | Pipeline B 全量门禁；Pipeline A 至少 GPU 锁 + check_env |
| 6 | Bridge 成熟度 | L0–L4 与 collect/deploy/eval 门槛绑定 |
| 7 | 下游 | 同步导出 P0 规范后，按 F7 → Isaac → Pipeline C → Real 开 MDD |

## 开放项（不阻塞 MDD）

- NFR 具体数值（Skill 环 p99 等）在 Real 栈 MDD 中定
- `ros2_interface_v1.md` 在 Real 栈 MDD 阶段重写
- `project_id` 权限、Artifact 退役策略延后至项目接入期

## 签字

| 角色 | 姓名 | 日期 |
|------|------|------|
| P1 | P1 | 2026-06-10 |
| P2 | P2 | 2026-06-10 |
| P3 | P3 | 2026-06-10 |
