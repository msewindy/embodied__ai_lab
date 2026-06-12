# 数据与实验记录规范 (Run & Artifact Spec) v1.0

| 属性 | 内容 |
|------|------|
| **文档编号** | TECH-05 |
| **版本** | v1.0 |
| **维护人** | P2 |
| **依据** | TECH-09 v1.0-approved §五–§九 |

---

## 一、 标识符体系

### 1.1 Run ID

Run 是一次可审计的执行实例。ID **全局唯一**，写入 IndexService 与目录名。

| Run 类型 | ID 格式 | 示例 |
|----------|---------|------|
| `isaac_job` | `isaac_{YYYYMMDD}_{HHMMSS}_{operator}_{kind}` | `isaac_20260610_143000_p2_train` |
| `real_collect` | `rc_{YYYYMMDD}_{HHMMSS}_{operator}_{device_id}` | `rc_20260610_150000_p1_franka-01` |
| `real_deploy` | `rd_{YYYYMMDD}_{HHMMSS}_{operator}_{device_id}` | `rd_20260610_160000_p2_quadruped-01` |
| `real_eval` | `re_{YYYYMMDD}_{HHMMSS}_{operator}_{device_id}` | `re_20260610_170000_p2_quadruped-01` |
| `real_bringup` | `rb_{YYYYMMDD}_{HHMMSS}_{operator}_{device_id}` | `rb_20260610_090000_p3_franka-01` |
| `calibration_session` | `cal_{YYYYMMDD}_{HHMMSS}_{operator}_{device_id}` | `cal_20260610_100000_p2_franka-01` |

**Job ID**（非 Run，无机器人参与）：

| Job 类型 | ID 格式 | 示例 |
|----------|---------|------|
| `sim2real_gap_job` | `gap_{YYYYMMDD}_{HHMMSS}_{operator}` | `gap_20260610_180000_p2` |

### 1.2 Artifact ID

| Artifact | ID 格式 | 示例 |
|----------|---------|------|
| PolicyArtifact | `pol_{YYYYMMDD}_{task_slug}_{seq}` | `pol_20260610_velocity_go2_v1` |
| DemoArtifact | `demo_{YYYYMMDD}_{device_id}_{seq}` | `demo_20260610_franka-01_001` |
| EvalArtifact | `eval_{YYYYMMDD}_{protocol_id}_{seq}` | `eval_20260610_loco_vel_v1_001` |
| CalibrationArtifact | `calib_{device_id}_{type}_{YYYYMMDD}` | `calib_franka-01_handeye_20260610` |
| SceneManifest | `scene_{layout_version}_{slug}` | `scene_v3_pickplace_bench` |

---

## 二、 根目录结构

```text
data/
├── index.db
├── tasks/
├── artifacts/
│   ├── policies/{policy_id}/
│   ├── demos/{demo_id}/
│   ├── evals/{eval_id}/
│   ├── calibrations/{calibration_id}/
│   └── scenes/{scene_id}/
├── runs/
│   ├── isaac_jobs/{isaac_job_id}/
│   ├── real_collect/{run_id}/
│   ├── real_deploy/{run_id}/
│   ├── real_eval/{run_id}/
│   ├── real_bringup/{run_id}/
│   └── calibration_session/{run_id}/
├── jobs/
│   └── sim2real_gap/{job_id}/
├── registry/
│   ├── device_capabilities.yaml
│   ├── bridge_maturity.yaml
│   └── eval_protocols/
└── vendor/
```

**热/冷迁移**：最近 7 天 Run 目录在 `lab-ws-02` NVMe；超期 Cron 打包至 NAS。IndexService 记录 `storage_tier`（hot/cold）。

---

## 三、 通用 metadata.json 字段

所有 Run 的 `metadata.json` **必须**包含：

```json
{
  "run_id": "rd_20260610_160000_p2_quadruped-01",
  "run_type": "real_deploy",
  "pipeline": "B",
  "status": "completed",
  "created_at": "2026-06-10T16:00:00+08:00",
  "ended_at": "2026-06-10T16:45:00+08:00",
  "operator": "p2",
  "host": "lab-ws-01",
  "project_id": "lab-default",
  "git_commit": "a1b2c3d4e5f6",
  "software_versions": {
    "ros2": "jazzy",
    "ubuntu": "24.04"
  },
  "device_ids": ["quadruped-01"],
  "upstream_artifact_ids": ["pol_20260610_velocity_go2_v1"],
  "downstream_artifact_ids": [],
  "experiment_plan_id": "exp_20260610_go2_deploy",
  "preflight_passed_at": "2026-06-10T15:59:30+08:00",
  "preflight_checklist": [],
  "resource_locks_acquired": [
    {"lock_type": "device_lock", "resource_id": "quadruped-01"},
    {"lock_type": "zone_lock", "resource_id": "Z-DYN"}
  ],
  "safety_events": []
}
```

**Pipeline B 附加必填**：`experiment_plan_id`、`preflight_passed_at`、`preflight_checklist`。

**real_eval 附加必填**：`scene_id`、`eval_protocol_id`。

---

## 四、 各 Run 目录结构

### 4.1 isaac_job

```text
runs/isaac_jobs/{isaac_job_id}/
├── metadata.json       # job_kind: play|train|eval
├── inputs/             # task/policy/demo config 快照
├── workspace/          # Isaac 工作目录
├── logs/
├── outputs.manifest.json
└── native/             # Isaac 原生输出（checkpoints 等）
```

| job_kind | 额外产物 | Artifact 注册 |
|----------|----------|---------------|
| play | 可选录屏 | 消费 PolicyArtifact |
| train | native/checkpoints/ | **产出** PolicyArtifact |
| eval | native/metrics/ | **产出** EvalArtifact |

### 4.2 real_collect

```text
runs/real_collect/{run_id}/
├── metadata.json
├── configs/
├── rosbags/
├── logs/
├── results/result.json
└── demo.manifest.json    # → DemoArtifact 索引
```

### 4.3 real_deploy / real_eval

```text
runs/real_deploy/{run_id}/   # real_eval 结构相同
├── metadata.json
├── configs/
├── rosbags/
├── logs/
└── results/
    ├── result.json
    └── metrics.json        # eval 时必填
```

### 4.4 real_bringup

```text
runs/real_bringup/{run_id}/
├── metadata.json
├── logs/
└── results/bringup_report.json
```

### 4.5 calibration_session

```text
runs/calibration_session/{run_id}/
├── metadata.json
├── logs/
├── raw/                    # 标定原始数据
└── results/calibration.manifest.json  # → CalibrationArtifact
```

---

## 五、 Artifact 目录契约

### 5.1 PolicyArtifact

```text
artifacts/policies/{policy_id}/
├── policy_manifest.yaml    # 见 policy_registry_spec.md
├── checkpoints/
│   └── best.pt
├── metrics_summary.json
└── producer_run.json       # 指向 isaac_job_id
```

### 5.2 DemoArtifact

```text
artifacts/demos/{demo_id}/
├── demo_manifest.yaml
├── episodes/                 # 或指向 runs/.../rosbags
└── producer_run.json
```

### 5.3 EvalArtifact

```text
artifacts/evals/{eval_id}/
├── eval_manifest.yaml
├── metrics.json
├── episodes/
└── producer_run.json
```

### 5.4 CalibrationArtifact

```text
artifacts/calibrations/{calibration_id}/
├── calibration.yaml
├── data/
└── producer_run.json
```

### 5.5 SceneManifest

```text
artifacts/scenes/{scene_id}/
├── scene_manifest.yaml
└── layout/                 # 可选布局图或 pose 文件
```

---

## 六、 IndexService 表结构（最小）

### runs

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | run_id |
| run_type | TEXT | isaac_job / real_* / calibration_session |
| pipeline | TEXT | A / B / C |
| job_kind | TEXT | play/train/eval（仅 isaac） |
| status | TEXT | pending/running/completed/failed/interrupted |
| operator | TEXT | |
| project_id | TEXT | |
| created_at | TEXT ISO8601 | |
| storage_path | TEXT | |
| preflight_passed_at | TEXT | |

### artifacts

| 字段 | 类型 | 说明 |
|------|------|------|
| artifact_id | TEXT PK | |
| artifact_type | TEXT | policy/demo/eval/calibration/scene |
| lifecycle_status | TEXT | draft/candidate/production/deprecated/active |
| producer_run_id | TEXT FK | |
| storage_path | TEXT | |

### resource_locks

| 字段 | 类型 | 说明 |
|------|------|------|
| lock_type | TEXT | device_lock / zone_lock / gpu_lock |
| resource_id | TEXT | |
| holder_run_id | TEXT FK | |
| acquired_at | TEXT | |
| expires_at | TEXT | TTL 兜底释放 |

### run_artifact_links

| 字段 | 类型 | 说明 |
|------|------|------|
| run_id | TEXT | |
| artifact_id | TEXT | |
| relation | TEXT | upstream / downstream |

---

## 七、 CLI 约定

```bash
# 创建 Run（内部：PreFlight → 分配 ID → 建目录 → 写 index）
lab run create --type real_deploy --device quadruped-01 --policy pol_xxx --plan exp_xxx

# 结束 Run
lab run finish --id rd_xxx --status completed

# 查询
lab run list --type real_deploy --device quadruped-01
lab artifact show pol_xxx
```

Isaac 入口见 `isaac_job_adapter_v1.md`。

---

*TECH-05 | run_id_spec v1.0 · 依据 TECH-09 approved*
