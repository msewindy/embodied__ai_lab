# Task Pack：`tabletop_pickplace_v0`

L2 任务包（STRUCT PLAN-STRUCT-01）。正式实验必须经 L0：

```bash
lab --data-root ~/embodied-ai-lab-data ctrl-sim run \
  --scene tabletop_pickplace_v0 \
  --profile m5_template|m5_pickplace \
  --keep-launch
  # 正式 run 默认录 A 轨；调试可加 --no-record
  # B 轨：lab data export --run-id <id> --format lerobot-v3
```

| 文件 | 作用 |
|------|------|
| `scene.yaml` | 可执行几何/ε/`fps`/`action_schema`/`cameras` |
| `scene_pin.md` | 本机 USD/prim/DOMAIN 钉扎 |
| `assets/tabletop_pickplace_v0.usda` | 合成场景（FR3 子层 + 桌/杯/碗原语） |
| `scripts/assemble_scene_usd.py` | 从 scene.yaml 重生成 USDA（`isaacsim/python.sh`） |
| `profiles/m5_template.yaml` | 空载回归（相对 Δpose） |
| `profiles/m5_pickplace.yaml` | 抓放序列（P2；朝目标 Mid 就绪后启用） |

数值 SSOT：`external/world_model/docs/FR3_Scene_v0_场景规格.md`（不进本 Git 的挂载资料）。

## 演进

| 阶段 | 状态 |
|------|:----:|
| P0 Task Pack + `lab` 加载 | ✅ |
| P0 Isaac 桌/杯/碗组装（USDA） | ✅ |
| P0 Isaac Play + `m5_template` 空载回归 | ✅ |
| P1 Oracle + toward-target Mid | ✅ |
| P2 `m5_pickplace` + `eval.json` | ✅（`cs_20260806_105823`） |
| P3 A→B export + 默认录制 + 门禁 | ✅ |
| P4 PolicyBackend + state MLP train/rollout | ✅ |

### P1 验收命令

```bash
lab --data-root ~/embodied-ai-lab-data ctrl-sim run \
  --scene tabletop_pickplace_v0 \
  --profile m5_approach_target \
  --keep-launch
```

### P2 抓放验收

```bash
lab --data-root ~/embodied-ai-lab-data ctrl-sim run \
  --scene tabletop_pickplace_v0 \
  --profile m5_pickplace \
  --keep-launch
```

序列：APPROACH → GRASP(闭合) → LIFT → MOVE_ABOVE → PLACE(张开) → RETREAT。  
产物：`logs/mid_steps.json` + `logs/eval.json`（manifest 互链）。  
说明：Oracle 位姿为静态 GT；`eval` 检查释放 ee 水平距 + 杯底相对碗顶净空（非 Isaac 物体 GT；2s 保持未强制）。

抗弹飞要点：碗薄垫碰撞、PLACE 净空 2.5 cm、夹爪 0.44、杯阻尼/零恢复。改场景后重跑 `assemble_scene_usd.py` 并重新打开 USD。
