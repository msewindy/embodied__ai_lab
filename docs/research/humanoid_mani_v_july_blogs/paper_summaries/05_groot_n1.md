# 论文解读：GR00T N1

- **arXiv**：[2503.14734](https://arxiv.org/abs/2503.14734)
- **机构**：NVIDIA GEAR Team
- **PDF**：`papers/groot_n1_2503.14734.pdf`
- **代码/模型**：https://github.com/NVIDIA/Isaac-GR00T

## 1. 定位

首个**开源权重**的通用人形机器人基础 VLA 模型，面向跨形态、语言条件的双臂操作。

## 2. 架构：双系统 VLA

```
┌─────────────────────────────────────┐
│  System 2: Eagle-2 VLM (1.34B)      │  ~10 Hz
│  图像 224×224 + 语言 → VL tokens    │
└──────────────┬──────────────────────┘
               │ cross-attention
┌──────────────▼──────────────────────┐
│  System 1: DiT + Flow Matching      │  实时
│  + embodiment 状态/动作编解码器      │
└──────────────┬──────────────────────┘
               ▼
         动作 chunk（如 16 步）
```

### 2.1 Eagle-2 VLM

- 基于 SigLIP-2 图像编码 + SmolLM2 语言模型
- 每帧 64 图像 token（pixel shuffle）
- 在互联网规模数据上预训练

### 2.2 DiT 动作专家

- Diffusion Transformer + **flow matching**（非 DDPM）
- embodiment-specific encoder/decoder 处理不同 DoF
- 总参数 ~2.2B（GR00T-N1-2B）

## 3. 训练数据

| 类型 | 说明 |
|------|------|
| 真实机器人轨迹 | 多形态遥操数据 |
| 人类 egocentric 视频 | + latent action（VQ-VAE，类似 LAPA） |
| 合成数据 | MimicGen, DexMimicGen, 神经视频生成 |

### 潜在动作预训练

- 无动作标注视频 → VQ-VAE 提取 latent action token
- 类似 Genie / LAPA 思路，增强物理常识

## 4. 实验

### 仿真基准

- 多 embodiment 标准 IL 基准上超越 SOTA 模仿学习基线

### 真机（Fourier GR-1）

- 语言条件双臂桌面操作
- 高数据效率（少量微调）

### 推理性能

- L40 GPU, bf16：16 动作 chunk 采样 **63.9 ms**

## 5. 设计哲学

- 受 Kahneman 双过程理论启发：慢推理 + 快执行
- **端到端联合训练** S1/S2（非严格层级冻结）
- 对比 Helix：GR00T 开源可微调；Helix 闭源零样本泛化更强

## 6. 后续版本演进

| 版本 | 关键变化 |
|------|----------|
| N1.5 | 冻结 VLM, Eagle 2.5, FLARE, DreamGen |
| N1.6 | Cosmos-2B VLM, 32层 DiT, 相对动作 |
| N1.7 | Cosmos-Reason2, EgoScale 20k 小时人类视频 |

详见 `10_helix_and_groot_versions.md`。

## 7. 微调实践（专栏）

- Isaac GR00T 提供 embodiment config + 微调脚本
- 七月在线已在宇树 G1 完成 N1.5 纸巾抓取等任务
- 数据：VR 遥操 → LeRobot 格式 → fine-tune

## 8. 局限

- N1 原始权重为 noncommercial license（N1.7 转商业许可）
- 全身 loco-manipulation 需 N1.6+ 与 SONIC
- 真机安全与 sim2real 仍依赖任务特定调参
