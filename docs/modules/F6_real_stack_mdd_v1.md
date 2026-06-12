# F5/F6 Real 栈模块详细设计 v1.0（骨架）

| 属性 | 内容 |
|------|------|
| **模块** | F5 Teleop · F6 大脑-小脑 · Rosbag |
| **版本** | v1.0-skeleton |
| **维护人** | P2 |
| **依据** | TECH-09 §三 F5/F6、§七 |
| **阻塞依赖** | `ros2_interface_v1.md`（P1 阶段重写） |

---

## 一、 状态说明

本文档为 **Real 栈 MDD 骨架**，在 `ros2_interface_v1.md` 定稿前**不冻结接口**。

可并行推进：
- RunManager `/system/run_context` 联调占位
- Driver Bridge 插件接口草案
- TeleopAdapter 设备驱动

必须等待 ros2_interface 后冻结：
- Topic 名、msg 字段、QoS
- SkillIntent / PlanOutput 语义

---

## 二、 模块拆分

```text
lab_platform/real/
├── teleop/                 # F5
│   ├── teleop_adapter_node.py
│   ├── devices/            # VR, LeaderArm, SpaceMouse
│   └── demo_recorder.py
├── brain/                  # F6B @ ws-01
│   ├── perception_fusion_node.py
│   ├── plan_node.py
│   └── policy_runner_high_node.py
├── cerebellum/             # F6C @ onboard
│   ├── policy_runner_low_node.py
│   ├── wbc_node.py
│   └── limiter_node.py
├── driver_bridge/          # onboard 插件
│   ├── base.py
│   └── plugins/
│       ├── franka_panda/
│       └── unitree_go2/
├── safety/
│   ├── safety_coordinator_node.py   # ws-01
│   └── estop_subscriber.py          # onboard
└── rosbag/
    └── recorder_node.py             # ws-01
```

---

## 三、 部署矩阵

| 组件 | 主机 | 频率 |
|------|------|------|
| TeleopAdapter | ws-01 | 事件驱动 |
| DemoRecorder | ws-01 | 与 collect 同步 |
| Perception/Plan/PolicyHigh | ws-01 | 10–50 Hz |
| SafetyCoordinator | ws-01 | 10 Hz |
| RosbagRecorder | ws-01 | 录制 |
| PolicyLow/WBC/Limiter | onboard | 100–500 Hz |
| DriverBridge | onboard | 与快环同步 |

---

## 四、 Run 类型映射

| Run | 启动组件 | 产出 |
|-----|----------|------|
| real_collect | Teleop + DemoRecorder + DriverBridge | DemoArtifact |
| real_deploy | PolicyHigh/Low + Safety | rosbag |
| real_eval | 同 deploy + eval 脚本 | EvalArtifact |

均由 RunManager 发布 `run_context` 后启动。

---

## 五、 Driver Bridge 插件契约（草案）

```python
class DriverBridgePlugin(ABC):
    @abstractmethod
    def configure(self, device_id: str, params: dict) -> None: ...

    @abstractmethod
    def read_state(self) -> RobotState: ...

    @abstractmethod
    def write_command(self, cmd: JointCommand) -> None: ...

    @abstractmethod
    def health(self) -> BridgeHealth: ...
```

- 插件元数据：`data/vendor/{model}/plugin.yaml`
- bringup smoke 调用 `health()`
- **禁止** ws-01 直接 import 厂商 SDK

---

## 六、 控制环（TECH-09 §七）

```
慢环 ws-01:
  Perception ← onboard 状态 Topic
  Plan / PolicyHigh → SkillIntent → onboard

快环 onboard:
  PolicyLow/WBC → Limiter → DriverBridge → HW
  HW → DriverBridge → 状态 Topic → ws-01
```

Topic 清单占位（待 ros2_interface 填充）：

| 语义 | 方向 | 备注 |
|------|------|------|
| joint_states | onboard → ws-01 | 快环反馈 |
| SkillIntent | ws-01 → onboard | 慢环意图 |
| SafetyState/ESTOP | ws-01 → onboard | 安全 |
| run_context | ws-01 → all | 实验对齐 |

---

## 七、 NFR 目标（待实测标定）

| 指标 | 首版目标 | 记录位置 |
|------|----------|----------|
| Skill 环 p99 延迟 | ≤ 100 ms（局域网） | real_deploy metadata |
| Teleop 端到端 | ≤ 150 ms | real_collect metadata |
| 快环频率 | ≥ 100 Hz locomotion | onboard logs |

---

## 八、 实施顺序（Real 栈）

1. **ros2_interface_v1.md** 重写（P1）
2. Driver Bridge base + 首设备 plugin（franka 或 go2 择一）
3. real_bringup 联调 BU-01–06
4. real_collect（Teleop + DemoRecorder）
5. real_deploy（Policy 加载 + 慢快环）
6. real_eval（eval_protocol 脚本）

---

## 九、 验收标准（骨架级）

- [ ] ros2_interface 评审通过
- [ ] onboard 仅 ROS2，无 ws-01 直调 SDK
- [ ] real_collect 产出 DemoArtifact
- [ ] real_deploy 加载 PolicyArtifact(candidate+)
- [ ] ESTOP 三级中软件 ESTOP 在 rosbag 可回放

---

*MDD-F6-REAL | F6_real_stack_mdd_v1 · skeleton*
