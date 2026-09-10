# A 轨 `low.jsonl` → LeRobot Dataset v3 字段映射

| 属性 | 内容 |
|------|------|
| **文档编号** | DATA-MAP-01 |
| **版本** | v1.1 |
| **日期** | 2026-08-07 |
| **上位** | [PLAN-STRUCT-01](../plan/lab_strategy_runtime_structure_v0.md) §5.4 / §13.4 · [TECH-12](./policy_registry_spec.md) |
| **实现** | `lab_platform/ctrl_sim/lerobot_export.py` · CLI：`lab data export --format lerobot-v3` |
| **状态** | Phase-1 可执行（无相机；默认 Index 注册） |

---

## 1. 产物布局（B 轨）

```text
<data-root>/datasets/lerobot_v3/<run_id>/
├── meta/
│   ├── info.json
│   ├── stats.json
│   ├── tasks.parquet
│   ├── lab_source.json          # 反向链到源 run
│   └── episodes/chunk-000/file-000.parquet
└── data/chunk-000/file-000.parquet
```

源 run `manifest.json` 写入：

- `tracks.B.path` / `tracks.B.lerobot_dataset_path` / **`tracks.B.dataset_id`**
- 顶层 `lerobot_dataset_path`、`dataset_id`（STRUCT 互链纪律）
- `lerobot_exports[]` 历史记录

Index（默认）：`ArtifactHub.register_dataset` → artifact_type=`dataset`；`--no-register` 可关。

---

## 2. 帧级映射

| LeRobot feature | dtype / shape | 来源（A 轨） | 说明 |
|-----------------|---------------|--------------|------|
| `observation.state` | float32 `[8]` | `low.q[7]` + `low.gripper_width` | 关节角 + 夹爪开合 |
| `action` | float32 `[7]` | `intent.ee_delta[6]` + `intent.gripper` | `intent is null` → 全 0 |
| `timestamp` | float32 | `t - t0` | 相对首帧秒 |
| `frame_index` | int64 | 行序 | 0…N-1 |
| `episode_index` | int64 | 常量 0 | 单 run = 单 episode |
| `index` | int64 | 全局帧序 | 同 `frame_index`（单集） |
| `task_index` | int64 | 常量 0 | 见 `meta/tasks.parquet` |

### `observation.state` 名

`q_0`…`q_6`, `gripper_width`

### `action` 名

`ee_dx`, `ee_dy`, `ee_dz`, `ee_droll`, `ee_dpitch`, `ee_dyaw`, `gripper`

与 Task Pack `scene.yaml`：

```yaml
action_schema:
  type: ee_delta_gripper
  ee_delta_dim: 6
  gripper_dim: 1
  frame_id: fr3_link0
cameras: []
```

对齐：`meta/info.json.lab.action_schema` / `cameras`。

---

## 3. 未导出（本阶段）

| A / 场景字段 | 原因 |
|--------------|------|
| `ee_pose_actual` / `ee_pose_desired` | 可加为扩展 state；默认关节态即可训 Δpose 策略 |
| `dq` / `tracking_error` / `ik_status` | 评测旁证，非 v3 最小集 |
| 相机 / `videos/` | `cameras: []`；约定见下；真采图后置 |
| `mid_steps.json` | Mid 自描述，留在 A 轨 |

### 3.1 相机约定（P4.4 · 契约预留）

Task Pack `scene.yaml`：

```yaml
cameras:
  - key: observation.images.third_person   # → LeRobot feature / videos/ 目录名
    prim: /World/CameraThirdPerson
    fps: 10
    encoding: mp4
```

当前 `cameras: []`：B 轨无 `videos/`；`lab policy train` 的 `lerobot_state` 仅用 `observation.state`。

---

## 4. CLI

```bash
lab --data-root ~/embodied-ai-lab-data data export \
  --run-id <run_id> --format lerobot-v3 [--overwrite] [--no-register]
```

正式 CTRL-SIM run **默认录 A 轨**（`--no-record` 可关）。导出为事后主路径（STRUCT：Phase-1 不强制 record 双写 B）。  
下游训练：`lab policy train --dataset ds_<run_id> …`（见 TECH-12 / SOP）。
