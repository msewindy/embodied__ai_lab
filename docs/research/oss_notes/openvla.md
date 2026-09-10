# OpenVLA 源码笔记（RES-OSS-NOTE-07）

| 属性 | 内容 |
|------|------|
| **源码** | `~/project/oss_refs/openvla` |
| **问卷** | [_questions.md](./_questions.md) |
| **commit** | `c8f03f4` |
| **结论摘要** | **VLA 训练/推理参考**：`image + instruction →` 离散 action token → 反归一化连续动作。借 **推理签名与 deploy 服务形态**；不借 Prismatic 训练栈作 L1 核心。主路径仍 ACT/LeRobot，VLA 后置。 |

---

## A. 架构

```
prismatic/
  models/vlms · vlas/openvla.py   # OpenVLA.predict_action
  vla/ · training/ · preprocessing/
  extern/hf/                      # HF 兼容 Modeling/Processor
vla-scripts/                      # train · deploy(OpenVLAServer)
experiments/robot/                # 真机/评测胶水
```

| 模块 | 本仓 |
|------|------|
| VLA 权重与 generate | L1 远期 `PolicyBackend`（`openvla`） |
| OXE 数据预处理 | L0 数据适配（后置） |
| deploy HTTP/服务 | 对标 LeRobot async；非 ROS 替代 |
| 实验治理 | **L0 自建** |

**A2** 上下文 = 单图（或双骨干像素）+ 自然语言；无显式记忆模块。  
**A3** Robot 胶水在 `experiments/robot`；模型侧极简 `predict_action(image, instruction)`。

### A5

| 能力 | L0 | L1 | L2 |
|------|----|----|-----|
| 图像+语言落盘 | recorder / export | PolicyObs | 任务指令 |
| ActionTokenizer + norm stats | Artifact 旁路 stats | ✅ 与权重绑定 | — |
| 大模型训练 | 可选外置作业 | 薄封装 | — |

---

## B. 数据

- 预训练对齐 Open X-Embodiment；动作用分位数统计反归一化（`q01`/`q99` + mask）。  
- 与 LeRobot v3：**不同栈**；若日后 VLA，需 L0 转换或走社区已有 OXE↔LeRobot 工具。  
- B5：当前 FR3 不要求；设计预留 `instruction` 与相机帧即可。

---

## C. 策略接口（要点）

```python
# OpenVLA.predict_action
# image: PIL · instruction: str → np.ndarray 连续动作（常为 EE delta）
```

- **单步**（一次 generate 出 action_dim 个 token），非 ACT 式长 chunk 队列。  
- `unnorm_key` 选择数据集统计。  
- HF 路径：`OpenVLAForActionPrediction.predict_action`。  
- 注册：`VLAConfig` / Draccus choice。  
- 对我们：适配层 = 相机帧→PIL + 任务字符串 + 动作空间映射到 Franka；**厚在动作空间与控制接口，不在重写模型**。

---

## D–F

- `vla-scripts/deploy.py`：`OpenVLAServer.predict_action` 远程推理。  
- **无** HOLD；失败在调用方。  
- **F**：语言是任务条件，不是 spatiotemporal WM。  
- **不抄**：用 OpenVLA 训练框架替换 lab CLI；把 Prismatic 放进 `strategy_runtime` 核心依赖。

---

## G

| 项 | 优先级 |
|----|--------|
| PolicyBackend 预留 `(images, language) → action` | **立即（设计）** |
| deploy 与 Mid 进程边界 | **中期** |
| 本仓训 OpenVLA | **远期** |
| 替代 ACT 主路径 | **不做（当前）** |
