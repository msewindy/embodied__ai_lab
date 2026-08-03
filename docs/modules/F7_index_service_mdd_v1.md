# F7 IndexService 模块详细设计 v1.0

| 属性 | 内容 |
|------|------|
| **模块** | F7 · IndexService |
| **版本** | v1.0-draft |
| **维护人** | R2 |
| **依据** | TECH-09 v1.0-approved §九；TECH-05 §六 |

---

## 一、 职责

- Run / Artifact / Lock 的**统一索引**与查询 API
- 血缘关联（upstream/downstream）
- 存储路径解析（hot/cold tier）
- Policy lifecycle 状态更新

**部署**：`lab-ws-02`（主）；`lab-ws-01` 通过 HTTP/Unix socket **只读+注册**（Real Run 创建时）。

**不加入 ROS2 域**。

---

## 二、 技术选型

| 项 | 首版决策 | 备注 |
|----|----------|------|
| 存储 | **SQLite** `data/index.db` | 3 人实验室足够；后续可迁 PostgreSQL |
| API | **REST** localhost:8787 + Python SDK | ws-01 RunManager 调用 |
| 文件 | 实际 blob 仍在 `data/` 目录树 | Index 只存 path + metadata 摘要 |

---

## 三、 组件结构

```text
lab_platform/index_service/
├── server.py              # FastAPI / Flask
├── db/
│   ├── schema.sql
│   └── migrations/
├── models.py              # Run, Artifact, Lock, Link
├── repositories/
│   ├── runs.py
│   ├── artifacts.py
│   └── locks.py
├── api/
│   ├── runs.py
│   ├── artifacts.py
│   └── locks.py
└── client.py              # IndexClient for RunManager / IsaacAdapter
```

---

## 四、 API 端点（最小）

### Runs

```
POST   /api/v1/runs              # register
PATCH  /api/v1/runs/{id}         # update status
GET    /api/v1/runs/{id}
GET    /api/v1/runs?type=&device=&status=&limit=
```

### Artifacts

```
POST   /api/v1/artifacts
GET    /api/v1/artifacts/{id}
GET    /api/v1/artifacts?type=policy&lifecycle=candidate
PATCH  /api/v1/artifacts/{id}/lifecycle   # promote / deprecate
```

### Locks

```
POST   /api/v1/locks/acquire
POST   /api/v1/locks/release
GET    /api/v1/locks/active?zone=Z-DYN
```

### Links

```
POST   /api/v1/links             # run ↔ artifact upstream/downstream
GET    /api/v1/runs/{id}/lineage # 血缘图 JSON
```

---

## 五、 Schema（SQLite）

见 `run_id_spec.md` §六；补充索引：

```sql
CREATE INDEX idx_runs_type_status ON runs(run_type, status);
CREATE INDEX idx_artifacts_type_lifecycle ON artifacts(artifact_type, lifecycle_status);
CREATE INDEX idx_locks_resource ON resource_locks(lock_type, resource_id);
```

---

## 六、 关键行为

### 6.1 Run 注册

```python
def register_run(record: RunRecord) -> None:
    # 插入 runs 表
    # 写入 storage_path
    # 若有 upstream_artifact_ids → 写 run_artifact_links(relation=upstream)
```

### 6.2 Artifact 注册（Isaac adapter 调用）

```python
def register_artifact(artifact: ArtifactRecord) -> None:
    # 校验 producer_run_id 存在
    # 写 artifacts 表
    # 更新 producer run 的 downstream_artifact_ids
```

### 6.3 Lock acquire（原子）

```sql
-- 伪代码：事务内检查 Z-DYN device_lock count < 2
INSERT INTO resource_locks ... 
ON CONFLICT DO NOTHING;
```

失败返回 409，PreFlight PF-07 fail。

### 6.4 冷热 tier

Cron `lab index migrate-cold --days 7`：
- 打包 `runs/` 至 NAS
- 更新 `runs.storage_tier = cold`, `storage_path`

---

## 七、 CLI

```bash
lab index serve                    # 启动服务
lab index migrate-cold --days 7
lab index lineage --run rd_xxx
lab artifact promote --id pol_xxx --to candidate
```

---

## 八、 与 RunManager 协作

| 调用方 | 操作 |
|--------|------|
| RunManager.create | POST /runs, POST /locks/acquire |
| RunManager.finish | PATCH /runs, POST /locks/release |
| IsaacJobAdapter | POST /runs, POST /artifacts, PATCH /runs |
| PreFlight PF-15 | GET /artifacts/{id} |

---

## 九、 测试计划

- 并发 acquire 第 3 个 Z-DYN lock → 409
- lineage 三跳 isaac → policy → real_deploy 可追溯
- promote draft → candidate 后 PreFlight PF-13 pass
- cold migrate 后 GET run 仍返回 NAS path

---

*MDD-F7-IX | F7_index_service_mdd_v1*
