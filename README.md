# 机器人感知与控制综合实践

第11组第五学期课程项目，使用 DICE 白熊人工智能实训平台，完成机械臂建模与可视化、示教点运动、HSV 颜色识别与固定区域分拣，以及手势触发机械臂基础动作。

实体机械臂由 Jetson 上的 Python SDK 控制；Windows 端识别手势，经 Micro-USB 网络上的 HTTP 服务发送命令。ROS1 Noetic 负责教学模型显示与 TF 验证。三条运行链路分别启动，尚未统一为一个 ROS 系统。

最新成果：[最终课程项目报告](docs/reports/课程项目报告_最终修订版_格式规范化.docx)。原始实验记录与源码版本保留在各周目录、模块结果目录及提交包中。

## 四个技术模块

| 模块 | 说明与运行步骤 | 主要入口 |
|---|---|---|
| 1 | [机器人建模与实验平台搭建](robot_ws/01_robot_modeling_and_platform_setup/README.md) | arm2026_ws：当前完整 catkin 工作空间 |
| 2 | [机械臂运动控制](robot_ws/02_robot_arm_motion_control/README.md) | week3/week3.ipynb、week4/Week4_堆叠.ipynb |
| 3 | [视觉目标识别与自动分拣](robot_ws/03_visual_target_recognition_and_sorting/README.md) | week5 主识别 Notebook、week6/week6.ipynb |
| 4 | [手势识别与交互控制](robot_ws/04_gesture_recognition_and_interactive_manipulation/README.md) | 模块内 week7/gesture_usb/app_usb.py、receiver_usb.py |

- **建模**：URDF/Xacro 描述连杆、关节与夹爪，关节 GUI 发布 `/joint_states`，robot_state_publisher 更新 TF，RViz 显示模型。当前 Z1 教学模型含11个 Link、10个 Joint，其中7个转动、3个固定；57个 visual、13个 collision。
- **运动**：用示教抓取、接近、抬升和放置点组织归位与堆叠；角度在调用 SDK 前由度转换为弧度，逆解失败时结束后续动作。保留各轮实验对应的参数版本。
- **视觉**：BGR 转 HSV、双区间红色分割、形态学处理与轮廓筛选；连续5帧唯一同色后，固定在 P4 抓取并投放到对应桶。像素中心用于识别记录，当前验收流程没有实现任意像素位置抓取。
- **手势**：MediaPipe 加关键点几何规则识别 One/Two/Three/OK/Five，通过候选选择、确认、执行互锁与网络心跳控制张爪、闭爪、Home 和软件停止。

## 目录结构

```text
ros_work/
├── README.md
├── arm2026_ws/                    当前 Z1 建模工作空间，src/package 保持完整
├── robot_ws/
│   ├── 01_robot_modeling_and_platform_setup/
│   ├── 02_robot_arm_motion_control/
│   ├── 03_visual_target_recognition_and_sorting/
│   ├── 04_gesture_recognition_and_interactive_manipulation/
│   ├── 参考资料/                  SDK、手册与版本差异说明
│   └── 整理记录/                  历史来源、哈希、代码版本索引
├── arm5dof_python_uservo/          平台真机 SDK、运动学与标定配置
├── arm5dof_visual_grasping/        相机标定与坐标映射参考，非当前分拣主入口
├── arm5dof_python_pybullet/        独立仿真参考
├── week1/、week3/…week7/           原始实验记录及代码，不移动其内部资源
├── 第11组_课程项目提交包/          历史提交快照，含当时源码、报告与数据
├── docs/
│   ├── reports/                   最终报告、任务书和审校说明
│   ├── references/                DICE 平台手册
│   └── maintenance/               本次文件清单、移动映射、去重与检查记录
└── .gitignore
```

模块目录中的 `1.1_code` 保存对应实验版本，`1.3_experiment_results` 保存真实截图、数据和报告来源。模块1的旧代码副本用于追溯；当前建模入口是根目录的 `arm2026_ws`。不把不同版本的 SDK、示教点表与识别阈值拼接成一套配置。

完整文件清单见 [整理前清单](docs/maintenance/inventory_before.csv)、[原目录树](docs/maintenance/tree_before.txt)、[移动及去重映射](docs/maintenance/file_moves.csv)和[整理说明](docs/maintenance/organization.md)。

## 开发环境

| 运行链路 | 环境与依赖 | 配置依据 |
|---|---|---|
| 模型显示 | WSL2 / Ubuntu20.04、ROS1 Noetic、catkin、Xacro、RViz、joint_state_publisher_gui、robot_state_publisher | 当前 Package 与 Launch |
| Jetson 点位与视觉 | Linux、Python3（Notebook 元数据多为3.8.10）、NumPy、pyserial、OpenCV、ipywidgets、Jupyter | SDK 导入、Notebook 与实验记录 |
| Windows 手势识别 | Windows11、记录为 Python3.11.9；MediaPipe Tasks、OpenCV、NumPy、Pillow、Tkinter | recognition.py、app_usb.py 与实验报告 |
| Jetson 手势接收 | Python3、HTTP 标准库，真机模式另需 NumPy、pyserial 和平台 SDK | receiver_usb.py、arm_interrupt.py |

JetPack、Jetson 系统镜像及多数依赖的完整实测版本没有锁定。厂商手册中的 Ubuntu18.04 / JetPack4.4 是参考环境，不能当作本组实测版本。真机 SDK 为 `arm5dof_python_uservo`；它与 Unitree 外观参考资源和 PyBullet 仿真 SDK 分开保存。

## 下载与安装

视频、ZIP 和 MediaPipe 模型使用 Git LFS。模型网格中同时存在历史普通 Git 文件和 LFS 管理文件，保持各版本原始字节。

```bash
git lfs install
git clone https://github.com/Frankie417/ros_work.git
cd ros_work
git lfs pull
```

### ROS 编译与 RViz

在 Ubuntu / WSLg 终端、仓库根目录运行：

```bash
sudo apt update
sudo apt install ros-noetic-xacro ros-noetic-joint-state-publisher-gui ros-noetic-robot-state-publisher ros-noetic-rviz ros-noetic-rqt-tf-tree
source /opt/ros/noetic/setup.bash
cd arm2026_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
source devel/setup.bash
roslaunch marm_description view_marm_z1_style.launch
```

RViz Fixed Frame 为 `marm_z1_base_link`。比较第四关节转轴时，停止主版后运行 `roslaunch marm_description view_marm_z1_style_course_variant.launch`。模型启动不连接实体机械臂。

### Jetson 运动、识别与分拣

在 Jetson 仓库根目录准备原程序要求的运行位置。复制 SDK 和 Notebook 作为运行副本，原始归档保持不变：

```bash
python3 -m pip install numpy pyserial opencv-python ipywidgets jupyterlab
BASE='/home/jetson/Notebook/4.机械臂OpenCV视觉处理实验'
mkdir -p "$BASE"
cp -an arm5dof_python_uservo/. "$BASE/"
cp -n week3/week3.ipynb "$BASE/"
cp -n 'week4/Week4_堆叠.ipynb' "$BASE/"
cp -n 'week5/5.目标识别/week5.ipynb' "$BASE/"
cp -n week6/week6.ipynb "$BASE/"
cd "$BASE"
python3 -m jupyterlab
```

在 Jupyter 中按实验打开对应 Notebook：`week3.ipynb` 归位（默认 `DRY_RUN=True`）、`Week4_堆叠.ipynb` 分层堆叠、`week5.ipynb` 独立识别、`week6.ipynb` 固定 P4 分拣。堆叠各动作 Cell 会控制真机，应按层执行；分拣需确认相机、串口 `/dev/ttyTHS1` 和现场标定。已有运行目录中的配置不被上述复制命令覆盖。详细参数和报告/代码差异见各模块 README。

### Windows 手势识别与 Jetson 通信

在 Windows 仓库根目录执行：

```powershell
py -3.11 -m venv .venv-gesture
.venv-gesture\Scripts\python.exe -m pip install mediapipe opencv-python numpy pillow
.venv-gesture\Scripts\python.exe robot_ws/04_gesture_recognition_and_interactive_manipulation/1.1_code/week7/gesture_usb/app_usb.py
```

该入口旁边的 `models/gesture_recognizer.task` 已保留。不要单独运行缺少同级 models 的旧 `week7/gesture_usb` 副本。

Jetson 仓库根目录启动接收器：

```bash
# 先进行不连接硬件的接收端演练
python3 robot_ws/04_gesture_recognition_and_interactive_manipulation/1.1_code/week7/gesture_usb/receiver_usb.py
# 真机模式，使用实际 SDK 与串口
python3 robot_ws/04_gesture_recognition_and_interactive_manipulation/1.1_code/week7/gesture_usb/receiver_usb.py --hardware --sdk-dir "$PWD/arm5dof_python_uservo" --arm-port /dev/ttyTHS1
```

两种接收模式择一启动。Windows 界面填入 `http://192.168.55.1:8765` 和接收器本次生成的 TOKEN，解除停止并准备后，One/Two/Three 选择动作，OK 确认，Five 请求停止。服务重启后重新填写 TOKEN。Jupyter 的8888端口不用于手势命令。

## 实验结果

| 实验 | 原记录结果 | 统计口径 |
|---|---|---|
| 四方块归位 | 11/12，约91.7%；完整成功2/3轮 | 三轮，每轮4块 |
| 四层堆叠 | 10/12，约83.3%；完整成功2/3轮 | 按块次，高层失败计入 |
| 独立颜色识别 | 主目标颜色28/28正确；综合判据22/28，约78.6% | 综合判据要求颜色正确且只有一个有效目标 |
| 固定区域分拣 | 两轮8/8正确入桶，未观察到重复抓取 | 固定红、黄、绿、蓝投放顺序，小样本现场验收 |
| 手势交互 | 10轮：9轮正确触发、1轮低分正确拦截、0误触发 | 基础动作与停止，不是完整搬运成功率 |

数据来源：各模块 `1.3_experiment_results/records`、原始周报告，以及提交包 `实验数据/` 中的CSV。手势22条回执和10项自动测试的结果按原报告记载，原始回执文件仍待补齐。

下图来自原相机实验保存的识别结果，配套 raw 和 masks 同帧文件一并保留：

![真实颜色识别结果](robot_ws/03_visual_target_recognition_and_sorting/1.3_experiment_results/figures/week5_evidence/20261019_144315_891538_result.png)

## 完成情况与后续工作

已实现模型显示与关节方向验证、示教点归位/堆叠、HSV识别、固定P4分拣，以及手势驱动夹爪开闭、回零和软件停止。尚未完成统一 ROS 图像/控制启动链路、教学模型与实体关节的逐轴映射、手势选择物块和目标位置后的完整搬运。后续补充乱序与光照测试、停止时延测量和完整原始日志，再扩展相机标定抓取。

## 检查与参考资料

```bash
python docs/maintenance/check_project.py
```

检查只读取源码、Notebook、XML、链接及文件哈希，不启动相机或机械臂。检查结果与当前环境未执行项见 [检查记录](docs/maintenance/quality_report.md)。历史来源核验脚本仍在 `robot_ws/整理记录/`，用于旧清单，不代替本次清单。

- [课程项目报告](docs/reports/课程项目报告_最终修订版_格式规范化.docx)、[DICE 平台手册](docs/references/DICE_白熊人工智能实训平台用户手册.pdf)。
- [ROS Noetic](https://wiki.ros.org/noetic)、[URDF](https://wiki.ros.org/urdf)、[Xacro](https://wiki.ros.org/xacro)。
- [OpenCV 颜色空间](https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html)、[形态学操作](https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html)。
- [MediaPipe Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer)。
- 第三方 SDK 与模型参考保留各自来源和许可；课程自主程序、实验记录与第三方参考按模块说明区分。
