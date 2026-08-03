# 平台软件架构与部署拓扑图 (Platform Architecture) v1.1

| 属性 | 内容 |
|------|------|
| **文档编号** | TECH-05 |
| **版本** | v1.1 |
| **维护人** | R2 |
| **依据** | [governance_index_v1.md](../org/governance_index_v1.md) · [plan_review_w1.md](../meeting/plan_review_w1.md) · [version_matrix_v1.md](../software/version_matrix_v1.md) · [infra_plan_draft_v0.md](../infra/infra_plan_draft_v0.md) · [ros2_interface_v1.md](../software/ros2_interface_v1.md) · [run_id_spec.md](../data/run_id_spec.md) |
| **说明** | 整合网络、算力、ROS2 接口与数据流的全局工程视图 |

---

## 一、 平台全局架构与部署拓扑图 (Mermaid)

> 此图展示了物理节点（算力/网络）、软件模块（ROS2 节点）、数据流（Run_ID/Rosbag）以及版本基线的全局映射关系。

```mermaid
graph TD
    %% --------------------------------------------------------
    %% 1. 物理网络与算力层 (Infrastructure)
    %% --------------------------------------------------------
    subgraph Network ["专用万兆局域网 (VLAN: 192.168.42.0/24) | 延迟 < 10ms"]
        direction TB
        
        subgraph WS02 ["lab-ws-02 (数据与大模型中心)"]
            OS2["Ubuntu 24.04 + CUDA 12.4+"]
            VLM["大模型推理 (Perception)"]
            Sim["Isaac Sim (仿真)"]
            Recorder["Rosbag 录制节点"]
            HotStorage[("热数据 (NVMe) <br> 1.5TB/天")]
        end

        subgraph WS01 ["lab-ws-01 (实时控制主节点)"]
            OS1["Ubuntu 24.04 + ROS2 Jazzy"]
            PlanNode["规划节点 (Plan)"]
            SkillNode["技能节点 (Skill)"]
            SafetyNode["全局安全节点 (Safety)"]
        end

        subgraph NAS ["NAS 存储"]
            ColdStorage[("冷数据归档 <br> (RAID 5)")]
            IndexDB[("实验索引库 <br> index.csv")]
        end

        subgraph Devices ["异构机器人集群 (电池供电)"]
            D1["双足 (Humanoid)"]
            D2["四足 (Quadruped)"]
            D3["机械臂 (Franka)"]
        end
    end

    %% --------------------------------------------------------
    %% 2. ROS2 逻辑数据流 (Data Flow & Interfaces)
    %% --------------------------------------------------------
    %% 感知流
    D1 -.->|"/perception/.../joint_states"| PlanNode
    VLM -.->|"/perception/scene/objects"| PlanNode

    %% 控制流
    PlanNode ==>|"/plan/.../trajectory"| SkillNode
    SkillNode ==>|"/skill/.../command"| D1
    SkillNode ==>|"/skill/.../command"| D2

    %% 安全流 (最高优先级)
    SafetyNode ===>|"/safety/global_state (ESTOP)" <br> QoS: Reliable| D1
    SafetyNode ===>|"/safety/global_state (ESTOP)"| D2
    
    %% 物理急停上报
    EStop["物理急停按钮 (E1/E2)"] -->|GPIO 弱电信号| SafetyNode

    %% --------------------------------------------------------
    %% 3. 实验追溯与数据落盘 (Run_ID Spec)
    %% --------------------------------------------------------
    subgraph Pipeline ["CI/CD & 实验流水线"]
        Git["Monorepo (Git)"]
        GenRunID["gen_run_id.py"]
    end

    Git -->|Commit Hash| GenRunID
    GenRunID -->|生成 run_id| Recorder
    Recorder -->|写入| HotStorage
    HotStorage -.->|Cron 定时迁移| ColdStorage
    GenRunID -.->|更新| IndexDB

    %% 样式定义
    classDef hardware fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef software fill:#d4e6f1,stroke:#2874a6,stroke-width:1px;
    classDef safety fill:#fadbd8,stroke:#c0392b,stroke-width:2px,color:#c0392b;
    classDef storage fill:#e8daef,stroke:#7d3c98,stroke-width:1px;

    class WS01,WS02,NAS,Devices hardware;
    class PlanNode,SkillNode,VLM,Sim,Recorder software;
    class SafetyNode,EStop safety;
    class HotStorage,ColdStorage,IndexDB storage;
```

---

## 二、 架构图解读 (R2 视角)

本图将 R2 负责的 4 份文档（算力网络、ROS2接口、版本矩阵、数据规范）融为一体：

1. **部署拓扑 (对应 `infra_plan_draft_v0.md`)**：
   - 清晰展示了 `lab-ws-01` 负责轻量级高实时性任务（Plan/Skill/Safety）。
   - `lab-ws-02` 负责吃显存、吃硬盘的重负载任务（VLM/仿真/录包）。
   - 明确了热数据在 `ws-02`，冷数据在 `NAS` 的物理流向。

2. **接口与数据流 (对应 `ros2_interface_v1.md`)**：
   - 虚线为感知流，实线为控制流，**红色粗实线**为 Safety 模块的一票否决控制流。
   - 物理急停按钮的 GPIO 信号如何接入 Safety 节点形成了闭环。

3. **版本与基线 (对应 `version_matrix_v1.md`)**：
   - 节点框内直接标明了 OS 和中间件的基线要求（Ubuntu 24.04 + ROS2 Jazzy / CUDA 12.4+）。

4. **实验追溯 (对应 `run_id_spec.md`)**：
   - 左下角的流水线展示了代码版本（Git Hash）如何通过 `gen_run_id.py` 注入到录包节点（Recorder），最终落盘到存储中。

---

## 三、 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0-draft | 2026-06 | 首版架构拓扑图 |
| **v1.1** | 2026-07-09 | 软件基线 24.04/Jazzy；角色口径 R2；对齐 W1 冻结决策 |
