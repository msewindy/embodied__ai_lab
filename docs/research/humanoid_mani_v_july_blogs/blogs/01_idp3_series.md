# iDP3 系列博客整理（5 篇）

本系列构成专栏的**技术底座**：从论文原理到源码、遥操、LeRobot 封装的完整 iDP3 落地路径。

---

## 1. 斯坦福通用人形策略 iDP3

- **链接**：https://blog.csdn.net/v_JULY_v/article/details/143180794
- **发布**：2024-10-23

### 核心内容

**问题**：人形机器人在开放世界中的自主操作受限于泛化能力与数据采集成本。原始 DP3 依赖相机标定与点云分割，难以部署到移动人形平台。

**iDP3 三大贡献**：

1. **遥操系统**：基于 Apple Vision Pro 的全身遥操，采集人类示范
2. **以自我为中心的 3D 表征**：点云在相机坐标系而非世界坐标系，无需标定与分割
3. **改进编码器**：金字塔卷积编码器替代 MLP，提升精度与平滑度

**实验**：在 Fourier GR1 人形上完成 Pick&Place、Pour、Wipe 等任务；2000+ 次真实评估，可泛化到未见场景与物体。

**与 DP3 关系**：iDP3 = DP3 的以自我中心改进版 + 人形遥操管线。详见 `paper_summaries/01_dp3.md` 与 `02_idp3.md`。

---

## 2. iDP3 Learning 代码解析

- **链接**：https://blog.csdn.net/v_JULY_v/article/details/145183110
- **仓库**：https://github.com/YanjieZe/Improved-3D-Diffusion-Policy

### 代码结构

```
diffusion_policy_3d/
├── config/
│   ├── dp_224x224_r3m.yaml    # 2D 图像扩散（对比用）
│   └── idp3.yaml              # 3D 点云扩散（主配置）
├── workspace/idp3_workspace.py # Hydra 训练入口
├── model/                      # U-Net + 点云编码器
└── policy/
    ├── diffusion_image_policy.py      # 2D 版
    └── diffusion_pointcloud_policy.py # 3D/iDP3 版
```

### 训练流程要点

- `iDP3Workspace.run()`：数据集加载 → 归一化 → EMA → epoch 循环 → `predict_action` 验证 → checkpoint
- 损失：扩散模型预测噪声的 MSE
- 配置 `idp3.yaml` 指定 `DiffusionPointcloudPolicy` 为策略类

---

## 3. iDP3 训练与部署代码解析

- **链接**：https://blog.csdn.net/v_JULY_v/article/details/145260121

### 关键脚本

| 脚本 | 功能 |
|------|------|
| `vis_dataset.py` | Zarr 格式数据可视化，验证转换是否正确 |
| `train.py` / workspace | 启动训练，加载 checkpoint |
| `deploy.py` | 加载权重，订阅相机点云，推理输出关节指令 |

### 数据格式

- 训练数据为 **Zarr** 格式（经 `convert_demos.py` 从原始遥操数据转换）
- 观测：稀疏点云 + 机器人本体状态
- 动作：关节位置或末端执行器指令序列（action chunk）

### 部署要点

- 推理：从纯噪声迭代去噪生成 action chunk，按时间步执行
- 需改写 `deploy.py` 中的通信接口以适配不同机器人（七月在线的通用化实践）

---

## 4. iDP3 人形遥操代码分析

- **链接**：https://blog.csdn.net/v_JULY_v/article/details/145347655
- **仓库**：https://github.com/YanjieZe/Humanoid-Teleoperation

### 端到端流程

```
数据采集(collect_data.py) → 格式转换(convert_demos.py) → 训练 → 部署
```

### 遥操架构

- **客户端**：Apple Vision Pro 捕获手/头/腕姿态，经 gRPC/Zenoh 流式传输
- **服务端**（机器人板载）：`retarget.py` 核心
  - `ArmRetarget`：手臂 IK
  - `HandRetarget`：多指灵巧手重定向
  - `UpperBodyRetarget`：头/腰姿态
  - `OneEuroFilter`：动作平滑

### 硬件要求

- Apple Vision Pro、RealSense 多相机、机器人本体（GR1 等）

---

## 5. Fourier-Lerobot 封装 iDP3

- **链接**：https://blog.csdn.net/v_JULY_v/article/details/146448646
- **仓库**：https://github.com/FFTAI/fourier-lerobot

### 相对 huggingface/lerobot 的扩展

1. **数据集**：Fourier ActionNet 格式支持与转换工具
2. **策略**：`lerobot/common/policies/idp3/`
   - `configuration_idp3.py`
   - `modeling_idp3.py`（IDP3Policy + IDP3Model）
   - `pointnet_extractor.py`（PointNet 点云编码）
3. **训练/推理**：与 LeRobot 统一 CLI，`select_action` 管理 action queue

### 调用关系

```
IDP3Policy.select_action
  └─ IDP3Model.generate_actions
       ├─ obs_encoder (PointNet)
       ├─ conditional_sample (DDPM/DDIM 去噪)
       └─ 返回 action chunk
```

### 七月在线落地备注

博客提及在 B 端人形订单中将 fourier-lerobot 作为 iDP3 落地选项之一，与官方 Improved-3D-Diffusion-Policy 仓库并行评估。

---

## 系列小结

| 阶段 | 推荐入口 | 输出 |
|------|----------|------|
| 理解原理 | 博客 #1 + iDP3 论文 | 算法与泛化能力认知 |
| 采数据 | 博客 #4 + Humanoid-Teleoperation | Zarr 训练集 |
| 训练 | 博客 #2/#3 或 fourier-lerobot | checkpoint |
| 部署 | deploy.py 或 LeRobot 推理 | 真机自主操作 |
