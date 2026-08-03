# 遥操系列博客整理（4 篇）

覆盖 UCSD 遥操技术演进、Open-TeleVision 源码、以及宇树 G1 二次开发工程路径。

---

## 1. UC San Diego 遥操发展史

- **链接**：https://blog.csdn.net/v_JULY_v/article/details/140384810
- **发布**：2024-07-12

### 三篇核心工作关系

```
AnyTeleop (2023, RSS)  →  通用视觉遥操 + dex-retargeting
        ↓
Open-TeleVision (2024, CoRL)  →  VR 立体视觉 + 沉浸式反馈
        ↓
Bunny-VisionPro  →  后续变体（专栏提及，待深入）
```

### AnyTeleop 要点

- **机构**：UCSD + NVIDIA
- **创新**：解耦手臂（腕部位姿 IK）与手部（dex-retargeting 优化重定向）
- **通用性**：仅需 URDF 即可适配新机器人；Web 浏览器可视化；支持仿真与真机
- **论文**：arXiv:2307.04577（RSS 2023）

### Open-TeleVision 要点

- **机构**：UCSD（Xuxin Cheng, Xiaolong Wang 等）
- **创新**：
  - 立体流式传输 → VR 主动深度感知
  - 人机动作镜像，沉浸感强
  - 支持远程网络遥操（Web 服务）
- **验证平台**：宇树 H1（多指）、傅利叶 GR1（夹爪）
- **任务**：Can Sorting、Can Insertion、Folding、Unloading 等长时域精细任务
- **论文**：arXiv:2407.01512（CoRL 2024）

### dex-retargeting

- 开源库：https://github.com/dexsuite/dex-retargeting
- 基于优化的手部关键点→机器人关节映射，AnyTeleop / Open-TeleVision / iDP3 均依赖

---

## 2. Open-TeleVision 源码解析

- **链接**：https://blog.csdn.net/v_JULY_v/article/details/147183534
- **仓库**：https://github.com/OpenTeleVision/TeleVision

### 系统模块

| 模块 | 说明 |
|------|------|
| `teleop/` | 遥操主程序，手部姿态捕获与流式传输 |
| `act/` | ACT 模仿学习训练（与遥操数据配套） |
| Web 服务 | 支持 Vision Pro / iPad / iPhone 接入 |
| 仿真示例 | Isaac Gym 双手遥操 `teleop_hand.py` |

### 数据流

1. VR 设备捕获人体手/头/腕姿态
2. 服务器执行 retargeting + IK → 机器人关节目标
3. 立体相机图像回传 VR（主动视觉）
4. 录制示范 → ACT 训练 → 真机自主执行

### 与宇树方案关系

宇树 `avp_teleoperate` 基于 Open-TeleVision 改造，是 G1 数采的常用入口（见下一篇）。

---

## 3. 宇树 VR 遥操与 IL

- **链接**：https://blog.csdn.net/v_JULY_v/article/details/147216841
- **发布**：2025-04-14

### 宇树生态双库

| 库 | 策略 | 说明 |
|----|------|------|
| unitree_IL_lerobot | π0, ACT, Diffusion Policy | 宇树官方 LeRobot 集成 |
| Fourier-Lerobot | iDP3 | 傅利叶对人形的 iDP3 封装 |

### 推荐开发路径（博客总结）

**第一步 遥操采数**

- 宇树开源 `avp_teleoperate`（基于 Open-TeleVision）
- 或 iDP3 官方 Humanoid-Teleoperation（3D 点云数据）

**第二步 策略训练**

| 目标 | 工具链 |
|------|--------|
| iDP3 | fourier-lerobot 或官方 Improved-3D-Diffusion-Policy |
| π0 | unitree_IL_lerobot |
| ACT | lerobot / unitree_IL_lerobot |

**第三步 部署**

- 各库均提供推理脚本；需匹配 G1 的消息接口与相机配置

### 训练命令示例（unitree_IL_lerobot）

```bash
cd unitree_lerobot/lerobot
python lerobot/scripts/train.py \
  --dataset.repo_id=unitreerobotics/G1_ToastedBread_Dataset \
  --policy.type=pi0
```

策略类型可选：`act`、`diffusion`、`pi0`。

### 数据格式

- G1 遥操数据存于 LeRobot 兼容格式（如 `G1_Dex3_ToastedBread_Dataset`）
- 3D 策略（iDP3）需点云；π0 等主要用 2D 图像，可做格式转换

---

## 4. （交叉引用）iDP3 遥操

遥操实现细节见 `01_idp3_series.md` 第 4 篇。三篇遥操路线的选择建议：

| 场景 | 推荐 |
|------|------|
| 宇树 G1 + π0/ACT | avp_teleoperate + unitree_IL_lerobot |
| 傅利叶 GR1 + iDP3 | Open-TeleVision 或 iDP3 官方遥操 |
| 跨平台研究 | AnyTeleop + dex-retargeting |

---

## 系列小结

遥操质量直接决定模仿学习上限。专栏强调：

1. **沉浸感**（立体视觉）提升长时域任务数采效率
2. **重定向**（dex-retargeting）是多人形平台复用的关键
3. **工程封装**（LeRobot）降低从采数到训练的门槛
