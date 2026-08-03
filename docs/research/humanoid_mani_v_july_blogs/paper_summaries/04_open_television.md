# 论文解读：Open-TeleVision

- **arXiv**：[2407.01512](https://arxiv.org/abs/2407.01512)
- **会议**：CoRL 2024（PMLR 270:2729–2749）
- **作者**：Xuxin Cheng, Jialong Li, Shiqi Yang, Ge Yang, Xiaolong Wang
- **机构**：UC San Diego, MIT
- **PDF**：`papers/open_television_2407.01512.pdf`
- **代码**：https://github.com/OpenTeleVision/TeleVision

## 1. 动机

遥操数据质量决定 IL 上限。传统第三人称视角或延迟视觉降低操作员空间感知，长时域精细任务困难。

## 2. 核心设计

### 2.1 沉浸式主动视觉

- 机器人头戴立体相机 → 流式传输至 VR（Apple Vision Pro 等）
- 操作员获得**第一人称立体深度感知**
- 「主动」：头部运动改变观测视角

### 2.2 动作镜像

- 人体手臂/手部动作实时重定向到机器人
- 多指手：retargeting；夹爪：简化映射
- 手臂：腕根位置 IK → 末端执行器

### 2.3 远程遥操

- Web 服务器架构，支持跨网络
- 降低现场操作负担

## 3. 验证平台与任务

| 机器人 | 末端 | 任务类型 |
|--------|------|----------|
| Unitree H1 | 多指灵巧手 | 长时域双臂 |
| Fourier GR1 | 平行夹爪 | 长时域双臂 |

任务：Can Sorting, Can Insertion, Folding, Unloading

## 4. 学习管线

- 采集示范 → **ACT**（Action Chunking Transformer）训练
- 部署：自主执行长时域任务，高成功率

## 5. 与 AnyTeleop 对比

| 维度 | AnyTeleop | Open-TeleVision |
|------|-----------|-----------------|
| 视觉 | 第三人称相机 | VR 立体 egocentric |
| 沉浸感 | 低 | 高 |
| 远程 | Web 支持 | Web + 流式立体 |
| 下游 IL | 通用 | ACT 为主 |

## 6. 工程结构（专栏源码解读）

```
TeleVision/
├── teleop/          # 遥操与流式传输
├── act/             # ACT 训练（detr 子模块）
└── requirements.txt # Python 3.8 环境
```

关键流程：Vision Pro 姿态 → 服务器 retarget → 机器人控制 + 立体画面回传

## 7. 影响

- 宇树 `avp_teleoperate` 的重要参考实现
- iDP3 论文引用为全身人形遥操前身之一
- 催生 Bunny-VisionPro 等变体

## 8. 局限

- 依赖 VR 硬件与低延迟网络
- ACT 策略对未见物体泛化有限（非 VLA）
- 全身下半身躯干控制未充分覆盖
