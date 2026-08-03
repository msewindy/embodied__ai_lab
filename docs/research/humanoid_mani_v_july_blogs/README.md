# 人形操作（mani）专栏资料库

来源：[v_JULY_v CSDN 专栏「人形mani：从宇树XR到人形VLA(如GR00T)」](https://blog.csdn.net/v_july_v/category_12915746.html)

作者为七月在线创始人，专栏共 **15 篇**博客，覆盖从 VR 遥操数采、3D 模仿学习（iDP3）到通用人形 VLA（GR00T 系列）的完整技术链。本目录对专栏内容、涉及论文及工程资源做了结构化整理。

## 目录结构

```
humanoid_mani_v_july_blogs/
├── README.md                 # 本文件
├── 01_technology_roadmap.md  # 技术路线与博客-论文映射
├── blogs/                    # 按主题整理的博客笔记
│   ├── 01_idp3_series.md
│   ├── 02_teleop_series.md
│   ├── 03_vla_groot_series.md
│   └── 04_human_video_vla_series.md
├── papers/                   # 已下载的 arXiv PDF
│   └── papers_index.md
└── paper_summaries/          # 论文详细解读
    ├── 01_dp3.md
    ├── 02_idp3.md
    ├── 03_anyteleop.md
    ├── 04_open_television.md
    ├── 05_groot_n1.md
    ├── 06_egovla.md
    ├── 07_egoscale.md
    ├── 08_hil_daft.md
    ├── 09_hirt.md
    └── 10_helix_and_groot_versions.md
```

## 推荐阅读顺序

1. **遥操与数采**：`blogs/02_teleop_series.md` → 论文 AnyTeleop、Open-TeleVision
2. **3D 模仿学习**：`blogs/01_idp3_series.md` → 论文 DP3、iDP3
3. **人形 VLA 基础**：`blogs/03_vla_groot_series.md` → 论文 GR00T N1、HiRT、Helix 技术说明
4. **人类视频迁移**：`blogs/04_human_video_vla_series.md` → 论文 EgoVLA、EgoScale、HIL-DAFT

## 与本实验室的关联

| 能力层 | 专栏对应技术 | 可落地平台 |
|--------|-------------|-----------|
| 数据采集 | Open-TeleVision / 宇树 avp_teleoperate / Apple Vision Pro | 宇树 G1、傅利叶 GR1 |
| 模仿学习 | iDP3、Fourier-Lerobot、unitree_IL_lerobot | LeRobot 生态 |
| 通用人形策略 | GR00T N1.x、EgoScale 预训练 | Isaac GR00T + G1 |
| 在线精调 | HIL-DAFT（VLA + 人在环 RL） | 精密装配场景 |

## 更新说明

- 整理日期：2026-06-22
- 论文 PDF 来自 arXiv 官方源；Helix、GR00T N1.5/N1.6/N1.7 无独立 arXiv 论文，见 `paper_summaries/10_helix_and_groot_versions.md`
