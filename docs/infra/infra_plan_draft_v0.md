# 算力与网络规划草案 v0

| 属性 | 内容 |
|------|------|
| **文档编号** | TECH-03 |
| **版本** | v0.0-draft |
| **维护人** | P2 |
| **前置依据** | [系统整体架构设计](../architecture/blueprint_v0.md) |

---

## 一、网络拓扑设计 (满足 <10ms 延迟)

为满足 P1 提出的“端到端控制延迟 <10ms”的 NFR，实验室网络必须与办公网络**物理/逻辑隔离**。

### 1.1 物理与逻辑拓扑图 (Mermaid)

```mermaid
graph TD
    %% 外部网络隔离
    OfficeNet[办公网络 / Internet] -.->|防火墙/VLAN隔离| CoreRouter[实验室主路由 <br> 网关: 192.168.42.1]

    %% 核心交换层
    CoreRouter -->|千兆/万兆上联| CoreSwitch{万兆核心交换机 <br> 10GbE}

    %% 有线接入层 (10GbE / 1GbE)
    subgraph Wired [有线网络接入 (高带宽 / 极低延迟)]
        direction TB
        CoreSwitch ===|10GbE| WS02[lab-ws-02 <br> 192.168.42.12]
        CoreSwitch ===|10GbE| NAS[NAS 存储 <br> 192.168.42.20]
        CoreSwitch ---|1GbE/10GbE| WS01[lab-ws-01 <br> 192.168.42.11]
        CoreSwitch ---|1GbE| Franka[Franka 机械臂 <br> 192.168.42.101]
        CoreSwitch ---|1GbE| Sensors[固定摄像头/传感器 <br> 192.168.42.20x]
    end

    %% 无线接入层 (Wi-Fi 6)
    CoreSwitch ===|2.5G/10GbE PoE| AP((企业级 Wi-Fi 6 AP <br> 专用独立频段))

    subgraph Wireless [无线网络接入 (移动设备)]
        direction TB
        AP -.-|Wi-Fi 6| Humanoid[双足机器人 <br> 192.168.42.5x]
        AP -.-|Wi-Fi 6| Quadruped[四足机器人 <br> 192.168.42.6x]
        AP -.-|Wi-Fi 6| Laptop[现场调试笔记本 <br> 192.168.42.3x]
    end

    %% 样式定义
    classDef switch fill:#f39c12,stroke:#935116,stroke-width:2px,color:#fff;
    classDef router fill:#34495e,stroke:#17202a,stroke-width:2px,color:#fff;
    classDef ap fill:#27ae60,stroke:#145a32,stroke-width:2px,color:#fff;
    classDef wired_node fill:#ebedef,stroke:#5d6d7e,stroke-width:1px;
    classDef wireless_node fill:#e8f8f5,stroke:#1abc9c,stroke-width:1px;

    class CoreSwitch switch;
    class CoreRouter router;
    class AP ap;
    class WS01,WS02,NAS,Franka,Sensors wired_node;
    class Humanoid,Quadruped,Laptop wireless_node;
```

### 1.2 硬件选型与架构
- **核心交换机**：万兆 (10GbE) 交换机，连接 `lab-ws-01`、`lab-ws-02` 及 NAS 存储，保障数据回传无瓶颈。
- **无线覆盖**：企业级 Wi-Fi 6 AP（专用频段，避免办公 Wi-Fi 干扰），专供双足、四足等移动机器人接入。
- **有线接入**：机械臂 (Franka) 及固定传感器直连千兆/万兆交换机。

### 1.2 IP 与 VLAN 规划
- **网段**：`192.168.42.0/24` (与 ROS_DOMAIN_ID=42 呼应)。
- **静态 IP**：所有工作站、机器人主板、NAS 分配静态 IP，便于 SSH 与 ROS 节点发现。

---

## 二、算力分配策略

充分利用现有终端（特别是新配的 5090D 工作站），避免前期盲目采购服务器。

| 节点 | 硬件配置 | 核心角色 (L5/L4) |
|------|----------|------------------|
| **lab-ws-01** | i7-13700K, 4070Ti, 32G | **ROS2 主节点 / 实时控制**：运行轻量级 Plan、Skill 节点及 Safety 模块，保障高实时性。 |
| **lab-ws-02** | 9950X3D, 5090D, 96G | **重负载计算 / 数据中心**：运行大模型 Perception (VLM/视觉)、离线仿真 (Isaac Sim)、rosbag 录制与索引。 |
| **lab-laptop-***| 笔记本 | **现场调试**：SSH 登录、rviz 可视化、运行 `gen_run_id` 脚本。 |

---

## 三、存储与数据生命周期 (满足全量录制)

基于 P1 的基线：“最大 2 台设备并发，全量录制 rosbag”。

### 3.1 吞吐量与容量测算
- **单台吞吐**：假设包含 2 路 1080p 深度相机 + 本体传感器，单台数据产生率约 `50 MB/s`。
- **并发吞吐**：2 台并发 = `100 MB/s`（千兆网理论上限 125MB/s，实际易拥堵，**故核心链路必须万兆**）。
- **日容量**：每天有效实验 4 小时，2 台并发产生约 `1.5 TB/天`。

### 3.2 冷热分层方案
1. **热数据 (0-7天)**：直接录制到 `lab-ws-02` 的 2T NVMe 固态硬盘中，保障高并发写入不丢帧。
2. **冷数据 (归档)**：**新增采购一台 4 盘位 NAS (组 RAID5，约 40TB 可用)**。每天凌晨通过脚本自动将 `lab-ws-02` 上的旧 run_id 数据迁移至 NAS。

---

## 四、系统可用性与容灾
- **代码容灾**：部署本地 Gitea 或使用云端私有库作为 monorepo，所有配置必须提交后方可生成 run_id。
- **节点容灾**：若 `lab-ws-01` 宕机，可通过 Docker 镜像在 15 分钟内于 `lab-ws-02` 拉起备用控制节点。

---

## 五、网络与存储建设成本估算

本节仅估算 P2 负责的网络与存储基础设施建设成本，该部分预算已同步至《实验室总体预算草案》(PLAN-BUDGET-01)。

| 类别 | 物品/型号建议 | 数量 | 预估单价 | 小计 | 优先级 |
|------|---------------|------|----------|------|--------|
| **核心网络** | 万兆核心交换机 (如 TP-Link 8口万兆+千兆电口) | 1 | ¥ 1,500 | ¥ 1,500 | P0 |
| **无线覆盖** | 企业级 Wi-Fi 6 AP (支持 2.5G/10G PoE 上联) | 1 | ¥ 2,000 | ¥ 2,000 | P0 |
| **布线与辅材** | 六类/超六类网线、理线架、水晶头 | 1批 | ¥ 500 | ¥ 500 | P1 |
| **冷数据存储** | 4盘位 NAS (如 群晖 DS923+ 或同级) | 1 | ¥ 4,500 | ¥ 4,500 | P0 |
| **存储介质** | 16TB 企业级机械硬盘 (组 RAID 5) | 4 | ¥ 2,500 | ¥ 10,000 | P0 |
| **总计** | | | | **¥ 18,500** | |

*(注：工作站 `lab-ws-01` 和 `lab-ws-02` 为实验室已有资产，不计入本次建设成本。)*
