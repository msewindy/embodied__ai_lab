# 技术解读：Helix 与 GR00T N1.5/N1.6/N1.7

本文档覆盖**无独立 arXiv 论文**或**以技术博客为主**的版本说明。

---

## 1. Helix（Figure AI）

### 官方资料

- Helix 发布：https://www.figure.ai/news/helix
- Helix 02：https://www.figure.ai/news/helix-02
- 专栏博客：https://blog.csdn.net/v_JULY_v/article/details/145773235

### Helix（2025.02）

**定位**：首个控制人形**整个上半身**（含手指）的 VLA，单权重、自然语言条件。

| 模块 | 参数 | 频率 | 功能 |
|------|------|------|------|
| S2 | 7B 开源 VLM | 7–9 Hz | 单目图像 + 语言 + 腕/指状态 → latent |
| S1 | 80M Visuomotor Transformer | 200 Hz | latent + 视觉 → 上肢关节目标 |

**能力亮点**：

- 零样本抓取数千种未见家居物品
- 两台 Figure 02 **共享一套权重**协作
- 无需 per-task 示范或手工编程
- 全 onboard GPU，无云端依赖

**训练数据**：未完全公开；推断为大规模多模态 + 机器人数据混合。

### Helix 02（2026.01）

| 模块 | 频率 | 功能 |
|------|------|------|
| S2 | 慢 | 场景理解、长时域任务规划 |
| S1 | 200 Hz | 全传感器 → 全身关节目标 |
| **S0（新）** | **1 kHz** | 全身运动先验，平衡/接触/协调 |

- 扩展至**下肢行走 + 操作**统一系统
- 新增掌部相机、指尖触觉
- 替代约 10 万行手写 C++ 控制代码（Figure 宣称）

### 与开源生态关系

- 闭源，不可直接用于宇树 G1 等第三方硬件
- 架构思想影响 GR00T、Hume 等双系统设计
- 技术报告曾通过 Figure 链接发布（非 arXiv 正式编号）

---

## 2. GR00T N1.5

### 官方资料

- https://research.nvidia.com/labs/gear/gr00t-n1_5/
- 专栏：https://blog.csdn.net/v_JULY_v/article/details/151907116

### 相对 N1 改进

| 项目 | 内容 |
|------|------|
| VLM | Eagle **2.5** |
| 训练 | **冻结 VLM**（预训练+微调均冻结） |
| Adapter | 简化 MLP + 输入 LayerNorm |
| FLARE | Future Latent Representation Alignment |
| DreamGen | 合成轨迹扩展动词/场景 |
| 规模 | 3B（GR00T-N1.5-3B） |

### 实验提升

- GR-1 真机：语言跟随显著优于 N1
- DreamGen 12 新动词：成功率 38.3% vs N1 13.1%
- 仿真操作基准全面超越 N1

### 工程

- 集成 HuggingFace LeRobot
- 七月在线 G1 部署案例：VR 采数 → 微调 → 纸巾抓取

---

## 3. GR00T N1.6

### 官方资料

- Isaac GR00T 文档：https://nvidia-isaac-gr00t.mintlify.app/concepts/model-overview

### 架构升级

| 项目 | N1.5 | N1.6 |
|------|------|------|
| VLM | Eagle 2.5 | **Cosmos-Reason-2B** 内部变体 |
| DiT 层数 | 16 | **32（2×）** |
| VLM 微调 | 冻结 | 预训练时**解冻 top 4 层** |
| Adapter | 有 4 层 transformer adapter | **移除**，简化 |
| 动作 | 绝对关节/EEF | **状态相对 action chunks** |
| 图像 | 固定分辨率 | **灵活分辨率** |

### 微调 checkpoint 示例

- GR00T-N1.6-G1-PnPAppleToPlate（宇树 G1 移动抓取）
- Bridge, Fractal, BEHAVIOR1k, DROID 等

---

## 4. GR00T N1.7

### 官方资料

- HuggingFace 博客：https://huggingface.co/blog/nvidia/gr00t-n1-7
- 专栏：https://blog.csdn.net/v_JULY_v/article/details/161454543

### 核心升级

| 项目 | 内容 |
|------|------|
| VLM | **Cosmos-Reason2-2B**（Qwen3-VL 架构） |
| 预训练 | **EgoScale 20,854 小时人类视频** |
| 动作空间 | 跨形态**相对末端执行器（EE）** |
| 全身 | **SONIC** 集成，语言条件 loco-manipulation |
| 许可 | **商业开源**（Apache 2.0 + NVIDIA Open Model License） |
| 参数 | 3B（GR00T-N1.7-3B） |

### Action Cascade 架构

- S2：Cosmos-Reason2 推理（多步任务、子任务分解）
- S1：32 层 DiT flow matching
- 相对 N1.6：**drop-in 替换**模型路径即可

### 性能叙事（NVIDIA）

- 人类数据 1k→20k 小时：任务完成率 >2×
- 开箱灵巧操作优于 N1.6（微调前）
- 早期接入：AeiRobot, Foxlink, NEURA, Lightwheel 等

---

## 5. 版本选型速查

```
研究/复现双系统 VLA     → N1 论文
G1 真机微调（成熟）     → N1.5 / N1.6 checkpoint
灵巧操作 + 商业部署     → N1.7 + EgoScale 先验
参考闭源 SOTA 架构      → Helix 技术博客
理解双系统学术原型      → HiRT 论文
```

---

## 6. SONIC（N1.7 相关，专栏外补充）

- NVIDIA GEAR 全身控制通用追踪器
- 统一 token 空间：VR 遥操 / 人类视频 / VLA 输出
- 博客：https://blog.csdn.net/v_JULY_v/article/details/156147131
- 案例：GR00T N1.5 + SONIC 在 G1 上「苹果到盘子」移动操作 95% 成功率

---

## 7. 参考文献链接

- GR00T N1 论文：arXiv:2503.14734（见 `05_groot_n1.md`）
- EgoScale 论文：arXiv:2602.16710（见 `07_egoscale.md`）
- HiRT：arXiv:2410.05273（见 `09_hirt.md`）
- Helix：Figure AI News（无 arXiv）
