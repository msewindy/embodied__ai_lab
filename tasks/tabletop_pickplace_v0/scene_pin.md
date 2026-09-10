# scene_pin — tabletop_pickplace_v0 @ lab-ws-02

> 本机钉扎；数值几何以 [`scene.yaml`](./scene.yaml) 为准，SSOT 见  
> `external/world_model/docs/FR3_Scene_v0_场景规格.md`。

## 环境

| 项 | 值 |
|----|-----|
| host | lab-ws-02 |
| Isaac Sim | 见 `lab_platform/scripts/m2_env_pin.md` |
| ROS | Jazzy · `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` |
| CTRL-SIM DOMAIN | **43**（禁止与真机 42 混用） |

## 臂资产（已钉 · 沿用 M2）

| 项 | 值 |
|----|-----|
| 工作副本 USD | `/home/ljqy/project/embodied__ai_lab/frankaFR3.usd` |
| Nucleus 参考 | `Isaac/Robots/FrankaRobotics/FrankaFR3/fr3.usd` |
| articulation_prim | `/fr3` |
| frame_id_base | `fr3_link0` |
| Hand | 已加载（`fr3_finger_joint*`） |
| ROS JointStates Graph | `/Graph/ROS_JointStates`（随 FR3 子层带入） |

## 合成场景资产（P0 · 已组装）

| 项 | 状态 | Prim / 备注 |
|----|:----:|-------------|
| 合成 USD | ✅ | [`assets/tabletop_pickplace_v0.usda`](./assets/tabletop_pickplace_v0.usda) |
| 子层 FR3 | ✅ | `@../../../frankaFR3.usd@`（相对 assets/） |
| FR3 `q_home` 覆盖 | ✅ | 根层 `over /fr3/.../fr3_joint*`：`drive:angular:physics:targetPosition` + `state:angular:physics:position`（**度**；来自 `scene.yaml` `robot_cfg.q_home_rad` → 约 `[0,-45,0,-135,0,90,45]`）。官方资产默认全 0 会使 EE≈z0.82，抓放开场前必须用本覆盖。 |
| 桌面 0.8×0.6×0.04，顶面 z=0 | ✅ | `/World/Table` · 中心 (0.50, 0, −0.02) · kinematic |
| `red_cup` 格点 id=4 | ✅ | `/World/red_cup` · (0.42, 0.10, 0.05) · Ø0.065×H0.1 · dynamic + 阻尼/零恢复 |
| `bowl` 底心 (0.58, −0.18, 0) | ✅ | `/World/bowl/visual` 外观；`/World/bowl/collision_pad` **薄垫碰撞**（防实心穿透弹飞） |
| 第三人称相机位姿标记 | ✅ | `/World/CameraThirdPerson`（Xform + lookAt 属性；未接渲染相机） |

**碗说明**：外观仍为完整高度圆柱；碰撞仅为顶面薄垫。PLACE 在碗顶留 `place_clearance_m=0.025` 后开爪。  
**夹爪**：`gripper≈0.44`（开口宽 0.045 m），禁止再用 0.9（会夹穿 Ø65 mm 杯）。

改几何/物理后请重生成并在 Isaac **重新打开** USD：

```bash
/home/ljqy/isaacsim/python.sh \
  ~/project/embodied__ai_lab/tasks/tabletop_pickplace_v0/scripts/assemble_scene_usd.py
```

### 重新生成

```bash
/home/ljqy/isaacsim/python.sh \
  ~/project/embodied__ai_lab/tasks/tabletop_pickplace_v0/scripts/assemble_scene_usd.py
# 可选：--cup-grid-id 0..8
```

无需 GPU / Play；仅需 Isaac 自带 `pxr`。

### Isaac 打开步骤（需本机 GPU 驱动正常）

1. 启动 Isaac Sim 6  
2. File → Open →  
   `~/project/embodied__ai_lab/tasks/tabletop_pickplace_v0/assets/tabletop_pickplace_v0.usda`  
3. 确认 Stage 可见：`/fr3`、`/World/Table`、`/World/red_cup`、`/World/bowl`  
4. 确认关节已是 Home（非全伸直）：`fr3_joint2≈-45°`、`fr3_joint4≈-135°`；EE 名义 ≈ `(0.31, 0, 0.49)`  
5. 启用 `isaacsim.ros2.bridge`（若未随 Graph 自动）；JointStates `targetPrim` → `/fr3`  
6. Play；本机确认：  
   `ROS_DOMAIN_ID=43 ros2 topic echo /joint_states --once`（须有 publisher）  
7. 再跑 lab CTRL-SIM（见下）  
   若改过 `q_home` / 几何：先重跑 `assemble_scene_usd.py`，再 **重新打开** USDA（不要只 Reload 旧内存）

> 打开 FR3 子层时若告警缺少 `fr3_robot_schema.usd`（S3/Nucleus），与 M2 工作副本相同：有网或本地 Nucleus 缓存时可消；不影响 `/fr3` 关节名与 M2 已验证通路时，可继续 Play。

## P-1 标定门禁（Scene 规格 §12）

- [ ] Home 无穿透；`ee_home` FK 实测写入 `scene.yaml`
- [ ] `t_flange_tcp` 与资产一致（实测）
- [ ] 9/9 格预抓 IK 报告（或格点补丁）
- [ ] 相机同框门禁（若启用相机）
- [ ] 工作空间盒外拒绝可演示

标定完成前：**不开**正式抓放采数；空载 `m5_template` 回归不受阻。

## 启动口令（CTRL-SIM）

```bash
cd ~/project/embodied__ai_lab/lab_platform && source .venv/bin/activate
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=43 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source ~/project/embodied__ai_lab/ros2/install/setup.bash

# Isaac：打开 assets/tabletop_pickplace_v0.usda → Play → 确认 /joint_states
lab --data-root ~/embodied-ai-lab-data ctrl-sim run \
  --scene tabletop_pickplace_v0 \
  --profile m5_template \
  --keep-launch
```

验收：run `manifest.json` 含 `task_pack.pack_root`；`logs/scene.yaml` 快照存在；Mid 两步 success（空载相对 Δpose）。

### P1 朝目标（`m5_approach_target`）

```bash
lab --data-root ~/embodied-ai-lab-data ctrl-sim run \
  --scene tabletop_pickplace_v0 \
  --profile m5_approach_target \
  --keep-launch
```

- Oracle：Mid 内嵌发布 `/perception/scene/red_cup/pose` 与 `.../bowl/pose`（名义 GT = scene.yaml）  
- APPROACH → `pregrasp_red_cup` = 杯心 + (0,0,0.12)  
- RETREAT → `retreat_m`  
- 独立调试：`python3 lab_platform/scripts/m5_oracle_publisher.py`

### P2 抓放（`m5_pickplace`）

```bash
lab --data-root ~/embodied-ai-lab-data ctrl-sim run \
  --scene tabletop_pickplace_v0 \
  --profile m5_pickplace \
  --keep-launch
```

验收：六步 mid success；`eval` 中 `place_horizontal_ok` 且 `place_clearance_ok`；manifest 含 `eval.path`。  
改 USD 后须重新 Open/Play，再跑 `m5_pickplace`。
