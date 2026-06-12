# Isaac Job Adapter 模块详细设计 v1.0

| 属性 | 内容 |
|------|------|
| **模块** | F2/F3/F4 统一入口 · IsaacJobAdapter |
| **版本** | v1.0-draft |
| **维护人** | P2 |
| **依据** | TECH-09 §5.2；TECH-13 `isaac_job_adapter_v1.md` |

---

## 一、 职责

薄封装 Isaac Sim/Lab 三种操作（play/train/eval），框架侧只做：

1. PreFlight（check_env、gpu_lock、disk、upstream artifact）
2. Run 目录与 metadata
3. subprocess 调用 `tasks/{task_id}/isaac_entry.yaml`
4. 产出扫描与 Artifact 注册

---

## 二、 组件结构

```text
lab_platform/isaac_adapter/
├── cli.py                 # lab isaac run
├── adapter.py             # IsaacJobAdapter 主类
├── preflight.py           # Pipeline A 专用检查子集
├── launcher.py            # subprocess + env 注入
├── scanner/
│   ├── checkpoints.py
│   └── metrics.py
├── manifest_builder.py    # policy_manifest / eval_manifest 生成
└── entry_loader.py        # 读 isaac_entry.yaml
```

---

## 三、 主类设计

```python
@dataclass
class IsaacRunRequest:
    kind: Literal["play", "train", "eval"]
    task_id: str
    config_path: Path | None
    policy_id: str | None
    demo_id: str | None
    eval_protocol_id: str | None
    operator: str
    project_id: str = "lab-default"

class IsaacJobAdapter:
    def __init__(self, index: IndexClient, preflight: PreFlightGate, scheduler: ResourceScheduler): ...

    def run(self, request: IsaacRunRequest) -> IsaacJobResult:
        self.preflight.check_isaac(request)
        locks = self.scheduler.acquire_isaac(request)
        job_id = self._allocate_id(request)
        run_dir = self._init_run_dir(job_id, request)
        try:
            exit_code = self.launcher.invoke(request, run_dir)
            artifacts = self.scanner.collect(run_dir, request)
            self._register_artifacts(job_id, artifacts)
            status = "completed" if exit_code == 0 else "failed"
        finally:
            self.scheduler.release(job_id)
        self.index.patch_run(job_id, status=status)
        return IsaacJobResult(job_id, status, artifacts)
```

---

## 四、 PreFlight 子集（Pipeline A）

| ID | 说明 |
|----|------|
| PF-01 | check_env |
| PF-08 | gpu_lock（train） |
| PF-14 | disk |
| PF-15 | upstream policy/demo 存在 |

不检查 device/zone/experiment_plan（无真机）。

---

## 五、 产出扫描

```python
class OutputScanner:
    def collect(self, run_dir: Path, request: IsaacRunRequest) -> list[ArtifactDraft]:
        entry = load_entry(request.task_id)
        if request.kind == "train":
            return self._scan_policy(run_dir, entry.output_scan)
        if request.kind == "eval":
            return self._scan_eval(run_dir, entry.output_scan, request.eval_protocol_id)
        return []
```

`_scan_policy` 调用 `manifest_builder.build_policy_manifest()`，字段见 `policy_registry_spec.md`。

---

## 六、 配置：isaac_entry.yaml

每个 `task_id` 必须提供；缺失则 adapter 拒绝运行并提示 P2 补 F1 task_manifest。

模板见 `isaac_job_adapter_v1.md` §四。

---

## 七、 错误与日志

- 所有 subprocess stdout/stderr tee 至 `runs/isaac_jobs/{id}/logs/isaac.log`
- structlog 字段：`isaac_job_id`, `kind`, `task_id`, `exit_code`
- native 失败仍保留 run 目录供 debug

---

## 八、 依赖顺序

```
IndexService (MDD-F7-IX)
  → PreFlight PF-01/08/14/15
  → IsaacJobAdapter
  → F1 task_manifest + isaac_entry.yaml（每 task）
```

---

## 九、 验收标准

- [ ] `lab isaac run --kind train --task velocity_rough_go2` 产生 isaac_job_id + PolicyArtifact(draft)
- [ ] train 并发第二个 gpu_lock → 拒绝或排队策略明确
- [ ] eval 达标后 policy promote candidate（可配置阈值）
- [ ] play 消费已有 policy_id 可回放

---

*MDD-ISAAC | isaac_job_adapter_mdd_v1*
