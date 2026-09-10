# RDT-1B 源码笔记（RES-OSS-NOTE-09）

| 属性 | 内容 |
|------|------|
| **源码** | `~/project/oss_refs/RDT`（Robotics Diffusion Transformer） |
| **问卷** | [_questions.md](./_questions.md) |
| **commit** | `cd79363` |
| **结论摘要** | **扩散式 VLA / 双臂友好**：`lang + img + state → action chunk`（`RDTRunner`）。借 **多模态 adaptor + pred_horizon**；训练/数据脚本重，作中期后端候选，不替代当前 ACT 主路径。 |

---

## A. 架构

```
models/
  rdt/model.py · rdt_runner.py   # RDT + DDPM/DPM 采样
  multimodal_encoder/            # 语言/视觉编码
train/                           # train.py · dataset.py · sample.py
data/                            # 多数据集 preprocess（aloha、bridge、OXE…）
configs/ · eval_sim/ · scripts/
```

| 能力 | 本仓 |
|------|------|
| RDTRunner 推理 | L1 远期 PolicyBackend |
| 多数据集 preprocess | L0 转换作业（外置） |
| eval_sim | 非 Isaac 主路径；对照评测脚本 |

**A2** 条件 = language tokens + image tokens + state；无独立 Context 服务。  
**A4** `pretrain.sh` / `finetune.sh` / `inference.sh` 分离；无 run_id。

### A5

| 能力 | L0 | L1 | L2 |
|------|----|----|-----|
| action_chunk_size 配置 | export 时序 | ✅ chunk 推理 | profile |
| 多相机/语言 | 录制与 meta | PolicyObs | 任务指令 |
| 异构数据集统一 | 外置 preprocess | — | — |

---

## B. 数据

- `train/dataset.py`：VLA 监督样本；可 `precomp_lang_embed`。  
- 仓内 `data/*` 为各源预处理脚本，产物再进训练。  
- 与本仓：保持 LeRobot v3；若上 RDT，写 **v3→RDT batch** 适配或官方数据格式桥，不把 `data/` 树拷进仓库。

---

## C. 策略接口

- 核心：`RDTRunner` — 训练噪声预测；推理用 `noise_scheduler_sample`（DPM）生成 **`pred_horizon` 动作块**。  
- 条件经 `lang_adaptor` / `img_adaptor` / `state_adaptor` 进统一 hidden。  
- 与 ACT/DP：**同属 chunk 族**；比 OpenVLA 更接近本仓已选的 chunk 控制语义。  
- 注册：配置驱动，非精致 plugin registry。  
- 适配厚度：中等偏厚（编码器权重、相机数、action_dim 填充/mask）。

---

## D–F

- 推理脚本同机；双臂维度靠 state/action mask。  
- **F**：无 WM；多模态条件可视为 Context 投影的一种实现参考。  
- **不抄**：用 RDT 数据湖替换 lab data-root；把整仓 `train/` 当实验 OS。

---

## G

| 项 | 优先级 |
|----|--------|
| L1 chunk + multimodal 条件与 RDT 对齐（设计） | **立即** |
| `lerobot_rdt` / 自定义 Backend | **中期** |
| 本仓预训练 RDT | **远期** |
| 替换 ACT MVP | **不做（当前）** |
