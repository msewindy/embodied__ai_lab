# 实验室环境安装与验收清单 v1.0

| 属性 | 内容 |
|------|------|
| **文档编号** | INFRA-01 |
| **版本** | v1.0 |
| **维护人** | P2 |
| **依据** | [TECH-04 版本矩阵](../software/version_matrix_v1.md) · [TECH-03 网络规划](./infra_plan_draft_v0.md) · [TECH-02 ROS2 接口](../software/ros2_interface_v1.md) · [TECH-09 技术架构](../architecture/platform_technical_architecture_v1.md) |
| **用途** | 三节点（ws-02 / ws-01 / onboard）从零配置到可跑 **Walking Skeleton + Go2 real_bringup** 的可执行清单 |

---

## 〇、 配置顺序建议

```text
1. 网络与静态 IP（全节点）     → §一
2. lab-ws-02 基线 + Isaac      → §二（Pipeline A）
3. lab-ws-01 ROS2 + lab 框架   → §三（Pipeline B/C 大脑）
4. Go2 onboard Driver Bridge   → §四（首台真机 / sim onboard）
5. 端到端验收                  → §五
```

**原则（TECH-09）**：

| 节点 | ROS2 域 | 角色 |
|------|:-------:|------|
| **lab-ws-02** | **不进域** | Isaac 训练/评估、Index、Artifact 文件、Gap Job |
| **lab-ws-01** | **进域** | RunManager、Rosbag、慢环、Safety 协调 |
| **onboard** | **进域** | Driver Bridge、Limiter、快环 |

全 Real 栈统一：

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

---

## 一、 全节点公共项（网络 · 仓库 · 基线 OS）

### 1.1 网络与主机名

| 主机 | 建议 hostname | 建议静态 IP | 说明 |
|------|---------------|-------------|------|
| lab-ws-02 | `lab-ws-02` | `192.168.42.12` | 仿真/训练，万兆上联 |
| lab-ws-01 | `lab-ws-01` | `192.168.42.11` | ROS2 主控 |
| quadruped-01 onboard | `go2-onboard` | `192.168.42.61` | Go2 机载（Wi-Fi 6，示例 IP） |
| NAS | `lab-nas` | `192.168.42.20` | 冷归档（可选 Phase 1） |

**安装**：按 [TECH-03](./infra_plan_draft_v0.md) 完成交换机/AP 布线；各机 `/etc/hosts` 或 DNS 可解析上述 hostname。

**验收**（在 ws-01 上执行）：

```bash
ping -c 3 lab-ws-02
ping -c 3 go2-onboard          # 真机 onboard 上线后
ping -c 3 192.168.42.61
# 期望：RTT < 5 ms（有线）；Wi-Fi onboard < 15 ms 为可接受基线
```

### 1.2 操作系统基线

| 项 | 要求 |
|----|------|
| OS | **Ubuntu 24.04 LTS**（Noble），内核 6.8+ |
| 时区 | `Asia/Shanghai`（三台一致，便于 run_id 对齐） |
| 用户 | 建议统一开发用户 `lab`（或团队约定），sudo 可用 |

**安装**（各节点）：

```bash
sudo apt update && sudo apt upgrade -y
sudo timedatectl set-timezone Asia/Shanghai
sudo apt install -y git curl wget vim htop net-tools iputils-ping \
  build-essential cmake python3 python3-pip python3-venv \
  openssh-server
```

**验收**：

```bash
lsb_release -ds          # Ubuntu 24.04.x LTS
uname -r                 # 6.8.x 或更高
timedatectl | grep "Time zone"
python3 --version        # 3.12.x
```

### 1.3 代码仓库

**安装**（ws-02 为主克隆点，ws-01/onboard 可 git clone 或 rsync）：

```bash
sudo mkdir -p /opt/lab && sudo chown $USER:$USER /opt/lab
git clone <monorepo-url> /opt/lab/embodied-lab
cd /opt/lab/embodied-lab
```

**验收**：

```bash
test -d /opt/lab/embodied-lab/lab_platform
test -d /opt/lab/embodied-lab/ros2/embodied_lab_msgs
test -f /opt/lab/embodied-lab/docs/software/version_matrix_v1.md
echo "repo OK"
```

### 1.4 SSH 互信（ws-01 ↔ ws-02 ↔ onboard）

**安装**（ws-01 生成密钥，分发到 ws-02 / onboard）：

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
ssh-copy-id lab@lab-ws-02
ssh-copy-id lab@go2-onboard     # onboard 就绪后
```

**验收**：

```bash
ssh lab@lab-ws-02 'hostname'
ssh lab@go2-onboard 'hostname'  # 可选，真机阶段
```

---

## 二、 lab-ws-02（仿真 · 训练 · 数据索引）

> **禁止**：日常 Isaac/训练会话中启动 ROS2 节点或设置 `ROS_DOMAIN_ID`（避免污染 Real 域）。

### 2.1 硬件驱动与 GPU

| 组件 | 版本 |
|------|------|
| NVIDIA Driver | ≥ 560.x |
| CUDA Toolkit | 12.4+ |
| cuDNN | 9.x |

**安装**（示例，以 NVIDIA 官方 Ubuntu 24.04 指引为准）：

```bash
# 安装驱动（方式之一：ubuntu-drivers）
sudo ubuntu-drivers install
sudo reboot

# 重启后安装 CUDA 12.4 toolkit（若 Isaac 安装包未 bundled）
# 参考 https://developer.nvidia.com/cuda-downloads
```

**验收**：

```bash
nvidia-smi
# 期望：Driver >= 560，可见 RTX 5090D，无 ECC/XID 报错

nvcc --version 2>/dev/null || echo "nvcc optional if Isaac bundle includes CUDA"
# 期望：CUDA 12.4+（若已装 toolkit）
```

### 2.2 PyTorch（Python 3.12）

**安装**：

```bash
python3 -m venv ~/venvs/lab
source ~/venvs/lab/bin/activate
pip install -U pip wheel
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install pyyaml
```

**验收**：

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# 期望：2.4.x+ True RTX 5090D
```

### 2.3 Isaac Sim 6.0 + Isaac Lab 3.0

**安装**（按 NVIDIA 官方 Omniverse / Isaac Lab 文档；路径因安装方式而异）：

```bash
# 1. 安装 Omniverse Launcher → Isaac Sim 6.0.0
# 2. 克隆 Isaac Lab 3.0 并按官方脚本安装到同一 Python/conda 环境
#    https://isaac-sim.github.io/IsaacLab/

# 示例：将 Isaac Lab 置于 ~/IsaacLab，并完成 _isaac_sim 链接
```

**验收**：

```bash
# 按 Isaac Lab 文档运行官方 smoke（headless）
cd ~/IsaacLab
./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py --headless
# 期望：进程 exit 0，日志无 GPU OOM

# Go2 任务环境可导入（与 demo 任务一致）
./isaaclab.sh -p -c "import gymnasium as gym; print('Isaac-Velocity-Rough-Go2-v0' in [e.id for e in gym.envs.registry.values()])" 2>/dev/null \
  || echo "manual: verify Isaac-Velocity-Rough-Go2-v0 in task registry"
```

### 2.4 lab_platform（Pipeline A + Index）

**安装**：

```bash
cd /opt/lab/embodied-lab/lab_platform
source ~/venvs/lab/bin/activate
pip install -e .
lab init --data-root /opt/lab/data
```

**验收**：

```bash
lab --data-root /opt/lab/data init
lab --data-root /opt/lab/data list
python scripts/smoke_test.py
# 期望：=== ALL SMOKE TESTS PASSED ===（Stub 模式，无需 ROS2/Isaac 真机）

# 检查 registry 与 Go2 设备条目
grep -A2 quadruped-01 /opt/lab/data/registry/device_capabilities.yaml
test -f /opt/lab/data/vendor/unitree_go2/plugin.yaml && echo "Go2 plugin OK"
```

### 2.5 存储与 NAS 挂载（可选，建议 P0）

**安装**：

```bash
sudo mkdir -p /opt/lab/data /mnt/nas
# 按 NAS 文档挂载 192.168.42.20:/volume1/lab → /mnt/nas
# /etc/fstab 添加 nfs/cifs 条目
```

**验收**：

```bash
df -h /opt/lab/data
df -h /mnt/nas 2>/dev/null || echo "NAS skip until ready"
# 期望：/opt/lab/data 剩余 > 200 GB（热数据）
```

### 2.6 ws-02 禁止项自检

**验收**：

```bash
# 确认未加入 ROS2 域（日常 shell profile）
grep -E 'ROS_DOMAIN_ID|RMW_IMPLEMENTATION' ~/.bashrc ~/.profile 2>/dev/null \
  && echo "WARN: remove ROS_DOMAIN_ID from ws-02 profile" \
  || echo "ws-02 ROS env clean OK"

# 确认无 ROS2 daemon 常驻
pgrep -a ros2 || echo "no ros2 processes OK"
```

---

## 三、 lab-ws-01（ROS2 大脑 · RunManager · Rosbag）

### 3.1 ROS2 Jazzy 基础

**安装**：

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-jazzy-desktop ros-dev-tools \
  python3-colcon-common-extensions \
  ros-jazzy-rmw-cyclonedds-cpp
```

**验收**：

```bash
source /opt/ros/jazzy/setup.bash
ros2 --version
# 期望：ros2 cli 可用

ros2 doctor --report | head -30
# 期望：无 critical missing dependency
```

### 3.2 Cyclone DDS 与域配置

**安装**（写入 shell profile，如 `~/.bashrc`）：

```bash
cat >> ~/.bashrc << 'EOF'

# embodied lab Real 域（TECH-02）
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /opt/ros/jazzy/setup.bash
EOF
source ~/.bashrc
```

可选 `/etc/cyclonedds.xml`（多网卡时绑定实验室 VLAN）：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS xmlns="https://cdds.io/config">
  <Domain Id="42">
    <General><NetworkInterfaceAddress>auto</NetworkInterfaceAddress></General>
    <Internal><Watermarks><WhcHigh>500kB</WhcHigh></Watermarks></Internal>
  </Domain>
</CycloneDDS>
```

```bash
export CYCLONEDDS_URI=file:///etc/cyclonedds.xml   # 若使用上述文件
```

**验收**：

```bash
echo "ROS_DOMAIN_ID=$ROS_DOMAIN_ID RMW=$RMW_IMPLEMENTATION"
# 期望：42 rmw_cyclonedds_cpp

# 终端 A
ros2 run demo_nodes_cpp talker &
sleep 2
# 终端 B（同机）
ros2 topic echo /chatter --once
# 期望：收到一条 String 消息
pkill -f demo_nodes_cpp/talker
```

### 3.3 编译 embodied_lab ROS2 工作区

**安装**：

```bash
cd /opt/lab/embodied-lab/ros2
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

rosdep install --from-paths . --ignore-src -r -y   # 首次
colcon build --symlink-install
echo 'source /opt/lab/embodied-lab/ros2/install/setup.bash' >> ~/.bashrc
source install/setup.bash
```

**验收**：

```bash
ros2 pkg list | grep -E 'embodied_lab_msgs|go2_driver_bridge|embodied_lab_bringup'
# 期望：三包均可见

ros2 interface show embodied_lab_msgs/msg/RunContext
ros2 interface show embodied_lab_msgs/srv/BridgeSmoke
# 期望：打印 msg/srv 定义，含 task_id / eval_protocol_id / scene_id
```

### 3.4 lab_platform（含 ROS bringup 路径）

**安装**：

```bash
python3 -m venv ~/venvs/lab-ws01
source ~/venvs/lab-ws01/bin/activate
pip install -U pip
cd /opt/lab/embodied-lab/lab_platform
pip install -e .
# 若 bringup --ros 需在同一 venv 内 import rclpy：
pip install /opt/ros/jazzy/lib/python3.12/site-packages/rclpy 2>/dev/null \
  || sudo apt install -y ros-jazzy-rclpy
```

**验收（Stub，无 launch）**：

```bash
lab --data-root /opt/lab/data ops bringup --device quadruped-01
# 期望：status completed, bridge_level L1（Stub 路径）
```

**验收（ROS sim，需 §3.5 launch 已起）**：

```bash
lab --data-root /opt/lab/data ops bringup --device quadruped-01 --ros --sim
# 期望：BU-01..06 pass，bridge_level L1
cat /opt/lab/data/runs/real_bringup/rb_*/results/bringup_report.json | tail -20
```

### 3.5 Go2 real_bringup 栈（ws-01 侧 launch）

**安装**：已在 §3.3 colcon；无额外 deb。

**启动**（验收用，终端 1 常驻）：

```bash
source /opt/lab/embodied-lab/ros2/install/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

ros2 launch embodied_lab_bringup go2_bringup.launch.py \
  device_id:=quadruped-01 sim:=true
```

**验收**（终端 2）：

```bash
source /opt/lab/embodied-lab/ros2/install/setup.bash
export ROS_DOMAIN_ID=42

# Topic 存在
ros2 topic list | grep -E '/system/|/perception/quadruped-01|/safety/'
# 期望：/system/run_context, /system/health, /perception/quadruped-01/joint_states 等

# 频率抽检（5s）
ros2 topic hz /perception/quadruped-01/joint_states
# 期望：average rate ~100 Hz（sim bridge）

# Bridge smoke 服务
ros2 service call /go2_driver_bridge/quadruped-01/smoke embodied_lab_msgs/srv/BridgeSmoke {}
# 期望：ok: true, sdk_version: unitree_go2_sim_1.0

# Health
ros2 topic echo /system/health --once
# 期望：node_name: go2_driver_bridge, status: 0
```

### 3.6 ws-01 与 ws-02 数据同步

**安装**（rsync 或 NFS，checkpoint / data 共享）：

```bash
# 示例：ws-02 导出 data 目录给 ws-01（按实际选 NFS 或 rsync cron）
sudo apt install -y rsync
# crontab 或手动：rsync -av lab@lab-ws-02:/opt/lab/data/ /opt/lab/data/
```

**验收**：

```bash
test -f /opt/lab/data/registry/device_capabilities.yaml && echo "data sync OK"
ssh lab@lab-ws-02 'test -d /opt/lab/data && echo ws-02 data OK'
```

---

## 四、 onboard（Go2 · quadruped-01 · 首台设备）

> Driver Bridge **必须**在 onboard 运行；ws-01 **不得**直接调用 Unitree SDK 控电机（TECH-02）。

### 4.1 硬件与网络

| 项 | 要求 |
|----|------|
| 设备 ID | `quadruped-01`（与 `device_capabilities.yaml` 一致） |
| 连接 | 实验室 Wi-Fi 6 或机载以太网 → `192.168.42.0/24` |
| 电源 | 电池供电；软件 ESTOP 必须可用（见 [SFT-01](../safety/safety_sop_v1.md)） |

**验收**：

```bash
# 在 ws-01 上
ping -c 3 go2-onboard
ssh lab@go2-onboard 'hostname && uptime'
```

### 4.2 OS 与 ROS2 Jazzy

**安装**（若机载为 Ubuntu 24.04）：

```bash
# 与 §3.1 相同步骤安装 ros-jazzy-ros-base（onboard 无需 desktop）
sudo apt install -y ros-jazzy-ros-base ros-jazzy-rmw-cyclonedds-cpp \
  python3-colcon-common-extensions
```

若机载为 **Unitree 出厂系统**（非 24.04）：按厂商文档评估兼容或容器化部署 Bridge；**必须在 CR 中记录偏差**。

**验收**：

```bash
source /opt/ros/jazzy/setup.bash
ros2 --version
```

### 4.3 Unitree Go2 SDK / 官方 ROS2（real 模式）

**安装**（以 Unitree 官方文档为准，示例占位）：

```bash
# 1. 安装 unitree_ros2 / unitree_sdk2（版本与 Go2 固件匹配）
# 2. 确认 lowstate / sport 等 topic 名称
# 3. 设置与实验室相同的 ROS_DOMAIN_ID=42
```

**验收**（真机 standing safe 状态，人员远离）：

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 topic list | grep -i unitree
# 期望：可见 /lf/lowstate 或厂商等价 topic（以实机为准）

ros2 topic hz /lf/lowstate
# 期望：> 100 Hz
```

### 4.4 部署 go2_driver_bridge（本仓库）

**安装**：

```bash
# 代码同步至 onboard（与 ws-01 同 commit）
rsync -av /opt/lab/embodied-lab/ros2/ lab@go2-onboard:/opt/lab/ros2/

ssh lab@go2-onboard bash -lc '
  source /opt/ros/jazzy/setup.bash
  export ROS_DOMAIN_ID=42
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  cd /opt/lab/ros2
  rosdep install --from-paths . --ignore-src -r -y
  colcon build --packages-select embodied_lab_msgs go2_driver_bridge --symlink-install
'
```

**启动**（onboard，真机）：

```bash
source /opt/lab/ros2/install/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

ros2 launch go2_driver_bridge go2_bridge.launch.py \
  device_id:=quadruped-01 \
  sim:=false \
  sdk_version:=unitree_go2_sdk_1.0 \
  unitree_lowstate_topic:=/lf/lowstate
```

**验收**（在 **ws-01** 上跨机发现）：

```bash
export ROS_DOMAIN_ID=42
ros2 topic hz /perception/quadruped-01/joint_states
# 期望：≥ 50 Hz

ros2 service call /go2_driver_bridge/quadruped-01/smoke embodied_lab_msgs/srv/BridgeSmoke {}
# 期望：ok: true
```

### 4.5 onboard 禁止项

**验收**：

```bash
# ws-01 上不应有 unitree_sdk 直接控电机进程
ssh lab@lab-ws-01 'pgrep -af unitree || echo "ws-01 no unitree sdk OK"'

# onboard 不应运行 Isaac / 训练
ssh lab@go2-onboard 'pgrep -af isaac || echo "onboard no isaac OK"'
```

---

## 五、 端到端验收（三节点联合）

按优先级排列；**E1–E3 为 Phase 1 最低可交付**（Go2 sim bringup + Skeleton）。

| ID | 场景 | 执行位置 | 命令 / 步骤 | 通过标准 |
|----|------|----------|-------------|----------|
| **E1** | Skeleton 全流程 | ws-02 | `cd lab_platform && python scripts/smoke_test.py` | ALL PASSED |
| **E2** | ROS2 包编译 | ws-01 | `colcon build` in `ros2/` | 无 failed packages |
| **E3** | Go2 sim bringup | ws-01 | 终端1: `go2_bringup.launch.py sim:=true`；终端2: `lab ops bringup --ros --sim` | `bringup_report.json` overall=pass；Bridge **L1** |
| **E4** | 跨机 Topic | ws-01 + onboard | ws-01 `ros2 topic hz /perception/quadruped-01/joint_states` | ≥ 50 Hz |
| **E5** | Isaac train smoke | ws-02 | `lab isaac run --kind train --task velocity_rough_go2`（Isaac 就绪后） | Run completed；PolicyArtifact 注册 |
| **E6** | checkpoint 同步 | ws-02 → ws-01 | rsync/NFS policy 目录 | ws-01 可读 `policy_manifest.yaml` |
| **E7** | 真机 BU 全项 | ws-01 + onboard | `lab ops bringup --device quadruped-01 --ros --no-sim` | BU-01..06 全 pass |

**E3 一键记录示例**：

```bash
# ws-01
lab --data-root /opt/lab/data ops bringup --device quadruped-01 --ros --sim \
  | tee /tmp/bringup_e3.log

RUN=$(ls -t /opt/lab/data/runs/real_bringup/ | head -1)
cat /opt/lab/data/runs/real_bringup/$RUN/results/bringup_report.json
grep quadruped-01 /opt/lab/data/registry/bridge_maturity.yaml
# 期望：level: L1
```

---

## 六、 验收签字表（建议打印）

| 节点 | 负责人 | 安装完成日 | 验收命令 ID | 签字 |
|------|--------|------------|-------------|------|
| 网络 / NAS | P2 | | §一 | |
| lab-ws-02 | P2 | | E1, E5 | |
| lab-ws-01 | P2 | | E2, E3 | |
| Go2 onboard | P2+P3 | | E4, E7 | |
| 安全 ESTOP | P3 | | BU-05 实机 | |

---

## 七、 常见问题

| 现象 | 排查 |
|------|------|
| ws-01 看不到 onboard topic | 检查 `ROS_DOMAIN_ID` 均为 42；防火墙 `iptables`；Wi-Fi 是否隔离 AP |
| `ros2 topic hz` 为 0 | Bridge 未起；`sim:=true/false` 与模式不一致；域 ID 不同 |
| `lab ops bringup --ros` 回退 Stub | venv 未装 rclpy；未 source ros2/install；launch 未起 |
| ws-02 GPU OOM | 降低 Isaac 并行 env 数；检查 `nvidia-smi` 占用 |
| BU-04 SDK 版本 fail | 更新 `data/vendor/unitree_go2/plugin.yaml` 与 bridge 参数 `sdk_version` |

---

## 八、 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v1.0** | 2026-06-11 | 首版：ws-02/01/onboard 分列安装与验收；对齐 Go2 首台 real_bringup |

---

*INFRA-01 | 环境清单 · 依据 TECH-04 / TECH-09 / TECH-02 v1.1*
