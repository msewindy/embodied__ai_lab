# VLA / GR00T 系列博客整理（4 篇）

涵盖 Figure Helix、NVIDIA GR00T N1 全系列及微调部署实践。

---

## 1. Helix — Figure 02 人形 VLA

- **链接**：https://blog.csdn.net/v_JULY_v/article/details/145773235
- **发布**：2025-02-21
- **官方**：https://www.figure.ai/news/helix

### 架构（双系统 VLA）

| 模块 | 规模 | 频率 | 职责 |
|------|------|------|------|
| System 2 (S2) | 7B VLM | 7–9 Hz | 场景理解、语言、任务语义 → 连续 latent 向量 |
| System 1 (S1) | 80M Transformer | 200 Hz | latent + 视觉 → 全身上肢关节目标 |

### 关键能力

- **零样本物体泛化**：未见过的家居物品，自然语言即可抓取
- **双机协作**：一套权重驱动两台 Figure 02 协作（冰箱收纳演示）
- **无需任务示范**：不依赖 per-task demonstration

### 与 GR00T 对比（博客观点）

- 均属「慢思考 VLM + 快反应动作专家」双系统
- Helix 闭源、仅 Figure 硬件；GR00T 开源可微调

### 相关论文：HiRT（清华）

- **链接**：arXiv:2410.05273（CoRL 2024）
- **思想**：VLM 低频输出高层引导，轻量 System 1 高频执行
- 详见 `paper_summaries/09_hirt.md`

### Helix 02 补充（专栏外更新）

- 新增 System 0（1 kHz 全身运动先验）
- 扩展至下肢行走 + 全身 loco-manipulation
- 无公开 arXiv，见 Figure 官方博客

---

## 2. 一文通透 GR00T N1

- **链接**：https://blog.csdn.net/v_JULY_v/article/details/146376514
- **发布**：2025-03-20
- **论文**：arXiv:2503.14734

### 双系统架构

```
图像 + 语言指令
    ↓
System 2: Eagle-2 VLM (~1.34B / 总计 2.2B)
    ↓ 视觉-语言 token
System 1: DiT + Flow Matching 动作专家
    ↓
高频关节动作 chunk（16 步约 63.9ms @ L40）
```

### 训练数据三类

1. **机器人遥操轨迹**（含 Open X-Embodiment）
2. **人类视频** + 潜在动作（类似 LAPA/Genie 的 VQ-VAE latent action）
3. **合成数据**（MimicGen、DexMimicGen、神经视频生成）

### 形态感知设计

- embodiment-specific 状态/动作编码器
- 支持从桌面机械臂到人形双臂的跨形态

### 相关工作影子（博客列举）

Helix、π0、LAPA、Octo、RDT 等

---

## 3. GR00T N1.5 简介与微调

- **链接**：https://blog.csdn.net/v_July_v/article/details/151907116
- **发布**：2025-09-21（专栏另有 2025-06 版本）
- **官方**：https://research.nvidia.com/labs/gear/gr00t-n1_5/

### 相对 N1 的主要改进

| 维度 | N1.5 |
|------|------|
| VLM | 升级为 Eagle 2.5 |
| 训练策略 | **预训练与微调期间冻结 VLM** |
| 连接器 | 简化 MLP adapter + LayerNorm |
| 损失 | FLARE（未来潜在表示对齐） |
| 数据 | DreamGen 合成轨迹，新动词泛化 38.3% vs N1 13.1% |
| 规模 | 3B 参数（N1.5-3B） |

### 微调与部署（博客实操）

七月在线在长沙营地的 G1 真机流程：

1. 仿真中采数 → 格式转换 → ACT/gr00t 训练验证
2. 真机 VR 遥操采数
3. Isaac GR00T 微调
4. 演示任务：纸巾抓取等

### 训练资源参考

- 预训练：~2000 H100 GPU 小时量级（博客引用）
- 微调：取决于任务与 embodiment 配置

---

## 4. GR00T N1.7 简介与微调

- **链接**：https://blog.csdn.net/v_JULY_v/article/details/161454543
- **发布**：2026-05-27

### N1.6 要点（同文介绍）

- Cosmos-2B 内部 VLM 变体
- DiT 扩大 2×（32 层 vs N1.5 的 16 层）
- **状态相对动作**（state-relative action chunks）替代绝对关节角
- 数千小时新增遥操数据

### N1.7 核心升级

| 维度 | N1.7 |
|------|------|
| VLM | Cosmos-Reason2-2B（基于 Qwen3-VL） |
| 预训练 | **EgoScale：20,854 小时人类第一视角视频** |
| 动作空间 | 跨形态相对末端执行器（EE）动作 |
| 全身控制 | SONIC 集成，语言条件 loco-manipulation |
| 许可 | **商业开源**（Apache 2.0 + NVIDIA Open Model License） |
| 升级 | 相对 N1.6 可 drop-in 替换 `--model-path` |

### 与 EgoScale 关系

N1.7 将 EgoScale 人类视频预训练作为核心研究基础，显著提升开箱灵巧操作能力。详见 `04_human_video_vla_series.md` 与 `paper_summaries/07_egoscale.md`。

---

## 系列小结：GR00T 版本选型

| 版本 | 适用场景 |
|------|----------|
| N1 | 研究复现、理解双系统 VLA 基线 |
| N1.5 | 语言跟随增强、G1 等真机微调（成熟生态） |
| N1.6 | 更大 DiT、相对动作、仿真/真机混合 |
| N1.7 | 灵巧操作、商业部署、人类视频先验 |

**仓库**：https://github.com/NVIDIA/Isaac-GR00T  
**模型**：Hugging Face `nvidia/GR00T-N1.7` 等
