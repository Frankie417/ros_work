# 机器人感知与控制综合实践

第11组第五学期课程项目，使用 DICE 白熊人工智能实训平台，完成机械臂建模与可视化、示教点运动、HSV 颜色识别与固定区域分拣，以及手势触发机械臂基础动作。

实体机械臂由 Jetson 上的 Python SDK 控制；Windows 端识别手势，通过 Micro-USB 网络上的 HTTP 服务发送命令；ROS1 Noetic 用于教学模型显示与 TF 验证。模型显示、Jetson 实验和 Windows 手势识别分别启动。

最新成果：[最终课程项目报告](homework/reports/课程项目报告.docx) · [报告与代码对应表](homework/报告与代码对应表.md)。整理后的运行代码、共享 SDK 和实验材料集中在 `homework/`，原实验版本与历史资料保留在仓库其他目录中。

## 一、四个技术模块

| 模块 | 说明与运行步骤 | 主要入口 |
|---|---|---|
| 1 | [机器人建模与实验平台搭建](homework/src/robot_modeling/README.md) | [arm2026_ws](homework/src/robot_modeling/arm2026_ws/README.md)：catkin 工作空间、Xacro 模型及 RViz 启动配置 |
| 2 | [机械臂运动控制](homework/src/arm_motion_control/README.md) | [week3.ipynb](homework/src/arm_motion_control/week3/week3.ipynb)、[Week4_堆叠.ipynb](homework/src/arm_motion_control/week4/Week4_堆叠.ipynb) |
| 3 | [视觉目标识别与自动分拣](homework/src/vision_sorting/README.md) | [week5.ipynb](homework/src/vision_sorting/week5/5.目标识别/week5.ipynb)、[week6.ipynb](homework/src/vision_sorting/week6/week6.ipynb) |
| 4 | [手势识别与交互控制](homework/src/gesture_control/README.md) | [app_usb.py](homework/src/gesture_control/week7/gesture_usb/app_usb.py)、[receiver_usb.py](homework/src/gesture_control/week7/gesture_usb/receiver_usb.py) |

- **建模：**用 URDF/Xacro 描述连杆、关节和夹爪，关节 GUI 发布 `/joint_states`，`robot_state_publisher` 更新 TF，RViz 显示模型。当前 Z1 风格教学模型包含11个 Link、10个 Joint，其中7个转动、3个固定。
- **运动：**用示教抓取点、接近点、抬升点和放置点组织四方块归位与四层堆叠。位置使用 mm，参数表中的角度在调用 SDK 前转换为 rad，堆叠入口先进行关键姿态 IK 检查。
- **视觉：**采用 BGR→HSV、双区间红色分割、形态学处理与轮廓筛选识别四色物块；连续5帧确认唯一同色目标后，从固定 P4 上料区抓取并投放到对应桶位。像素中心用于标注和记录。
- **手势：**结合 MediaPipe 与关键点几何规则识别 One、Two、Three、OK、Five，通过候选选择、确认、一次性准备互锁和网络心跳，实现开爪、闭爪、Home 与软件停止。

## 二、目录结构

```text
ros_work/
├── README.md                              仓库首页
├── homework/                              整理后的运行与交付目录
│   ├── README.md                          详细使用说明
│   ├── 报告与代码对应表.md
│   ├── src/
│   │   ├── robot_modeling/arm2026_ws/      ROS 建模工作空间
│   │   ├── arm_motion_control/            基础控制、week3 归位、week4 堆叠
│   │   ├── vision_sorting/                week5 识别、week6 分拣
│   │   └── gesture_control/week7/         gesture_usb、models
│   ├── sdk/arm5dof_python_uservo/          共享实体 SDK 与标定配置
│   ├── reports/                           最终报告与原实验周报告
│   ├── results/                           原始数据、图片、视频及运行输出
│   ├── docs/                              验证、来源、文件清单与参考资料
│   ├── tools/check_project.py             静态检查入口
│   ├── project_paths.py                   共享 SDK 定位
│   ├── requirements-jetson.txt
│   └── requirements-gesture.txt
├── arm2026_ws/                            原建模工作空间
├── robot_ws/                              按四个技术模块保存的归档
├── arm5dof_python_uservo/                  原平台 SDK 与配置
├── arm5dof_visual_grasping/                相机标定与坐标映射参考
├── arm5dof_python_pybullet/                PyBullet 仿真参考
├── week1/、week3/…week7/                   原实验代码及记录
├── 第11组_课程项目提交包/                  历史提交快照
├── docs/                                  原报告、整理与维护记录
├── .gitattributes                         Git LFS 与文件字节规则
└── .gitignore                             本地缓存和环境排除规则
```

日常运行使用 `homework/` 下的入口。运动、分拣和手势接收端共用 [实体 SDK](homework/sdk/arm5dof_python_uservo/)，程序通过 `project_paths.py` 定位 SDK 及其配置。新运行产生的数据写入对应的 `results/**/runtime/`，原始实验数据单独保留。

完整交付目录见 [最终目录树](homework/docs/最终目录树.txt)，文件来源、整理过程和哈希见 [文件整理记录](homework/docs/文件整理记录.md) 与 [文件清单](homework/docs/文件清单.csv)。

## 三、开发环境

| 运行链路 | 环境与依赖 | 配置依据 |
|---|---|---|
| ROS 模型显示 | Ubuntu 20.04 / WSL2、ROS1 Noetic、catkin、Xacro、RViz、joint_state_publisher_gui、robot_state_publisher | 建模工作空间的 Package、Launch 与 RViz 配置 |
| Jetson 运动与视觉 | Linux、Python3（Notebook 元数据多为3.8.10）、NumPy、pyserial、OpenCV、ipywidgets、JupyterLab | 共享 SDK、Notebook 及 [Jetson 依赖清单](homework/requirements-jetson.txt) |
| Windows 手势识别 | Windows 11、记录为 Python 3.11.9；MediaPipe Tasks、OpenCV、NumPy、Pillow、Tkinter | 识别界面、识别程序及 [Windows 依赖清单](homework/requirements-gesture.txt) |
| Jetson 手势接收 | Python3 与 HTTP 标准库；实体模式另需 NumPy、pyserial 和共享 SDK | receiver_usb.py、arm_interrupt.py 与 SDK 配置 |

ROS 图形界面需要 Linux 桌面或 WSLg。JetPack、Jetson 系统镜像及现场依赖的完整版本仍需核实；依赖清单提供安装入口，实机版本对应情况见 [待核实事项](homework/docs/待核实事项.md)。

## 四、下载与安装

先安装 Git 和 Git LFS，再克隆仓库并拉取大文件。视频、模型和部分归档资源由 Git LFS 管理。

```bash
git lfs install
git clone https://github.com/Frankie417/ros_work.git
cd ros_work
git lfs pull
```

**以下各小节均从仓库根目录 `ros_work/` 的新终端开始。** Jetson 和 Windows 分别准备仓库；进入 `homework/` 后执行对应程序。保留现有 SDK 配置，并在运行前核对实际设备、串口、关节零位与示教点。

### 4.1 ROS 编译与 RViz

在已安装 ROS1 Noetic 的 Ubuntu 20.04 / WSLg 环境执行：

```bash
sudo apt update
sudo apt install ros-noetic-xacro ros-noetic-joint-state-publisher-gui \
  ros-noetic-robot-state-publisher ros-noetic-rviz
source /opt/ros/noetic/setup.bash
cd homework/src/robot_modeling/arm2026_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
source devel/setup.bash
roslaunch marm_description view_marm_z1_style.launch
```

启动后，用关节 GUI 调整 `marm_z1_joint1`～`marm_z1_joint6`，用 `marm_z1_gripper_joint` 调整夹爪。RViz 的 Fixed Frame 设置为 `marm_z1_base_link`，工具坐标系为 `marm_z1_grasping_frame`。

比较第四关节方向时，先停止主版，再在已加载工作空间环境的终端执行：

```bash
roslaunch marm_description view_marm_z1_style_course_variant.launch
```

主版 joint4 轴为 `(0,1,0)`，课程变体为 `(0,-1,0)`。该启动链路用于教学模型显示与 TF 观察，实体控制入口见下节。

### 4.2 Jetson 运动、识别与分拣

在 Jetson 仓库根目录安装依赖并启动 JupyterLab：

```bash
cd homework
python3 -m pip install -r requirements-jetson.txt
python3 -m jupyterlab
```

在 Jupyter 文件浏览器中打开对应 Notebook，按代码单元顺序加载参数与函数，再运行实验入口。

| 实验 | Notebook | 运行要点 |
|---|---|---|
| 四方块归位 | [week3.ipynb](homework/src/arm_motion_control/week3/week3.ipynb) | 默认 `DRY_RUN=True`，先执行 `run_unstack_sort()` 检查位姿与顺序；核对后切换实机模式，并重新运行参数、函数和入口单元 |
| 四层堆叠 | [Week4_堆叠.ipynb](homework/src/arm_motion_control/week4/Week4_堆叠.ipynb) | `run_single_block(0)`～`run_single_block(3)` 按层执行；各入口先做20项 IK 预检，动作单元会直接控制真机 |
| 独立颜色识别 | [week5.ipynb](homework/src/vision_sorting/week5/5.目标识别/week5.ipynb) | 启动相机、选择真实颜色、记录测试与保存截图；只进行识别和记录 |
| 固定 P4 分拣 | [week6.ipynb](homework/src/vision_sorting/week6/week6.ipynb) | 启动预览会连接机械臂并移动到拍摄位姿；连续5帧确认唯一同色目标后抓放，待 P4 清空后接收下一块 |

实体 SDK 默认串口为 `/dev/ttyTHS1`，通信设置为 115200、8N1；视觉 Notebook 默认相机编号为 `0`。分拣桶位来自 Notebook 内的 `bin_map`，按现场位置核对。堆叠按层运行；分拣的“停止预览”只结束预览流程，机械动作的完成情况需单独确认。

基础关节标定、关节弧度、夹爪和末端位姿示例位于 [basic_control](homework/src/arm_motion_control/basic_control/)。报告与 SDK 的 K/B、高度补偿及归位顺序存在版本差异，具体参数和实验步骤见 [运动模块说明](homework/src/arm_motion_control/README.md) 与 [视觉模块说明](homework/src/vision_sorting/README.md)。

### 4.3 Windows 手势识别与 Jetson 通信

通过 Micro-USB 建立 Windows 与 Jetson 的网络连接。手势服务默认地址为 `http://192.168.55.1:8765`，Jupyter 使用独立的 `8888` 端口。

先在 Jetson 仓库根目录启动接收端，默认运行模拟模式：

```bash
cd homework
python3 -m pip install -r requirements-jetson.txt
python3 src/gesture_control/week7/gesture_usb/receiver_usb.py
```

终端会打印本次服务的 URL、`TOKEN` 与 `MODE`。需要实体控制时，停止模拟服务，在同一 `homework/` 目录改用：

```bash
python3 src/gesture_control/week7/gesture_usb/receiver_usb.py \
  --hardware --sdk-dir "$PWD/sdk/arm5dof_python_uservo" \
  --arm-port /dev/ttyTHS1
```

两种接收模式择一启动。随后在 Windows 仓库根目录打开 PowerShell，安装依赖并启动识别界面：

```powershell
cd homework
py -3.11 -m venv .venv-gesture
.\.venv-gesture\Scripts\python.exe -m pip install -r requirements-gesture.txt
.\.venv-gesture\Scripts\python.exe src/gesture_control/week7/gesture_usb/app_usb.py
```

虚拟环境和依赖首次配置后可复用，之后直接运行最后一条启动命令。

1. 在界面填写接收端 URL 和本次 `TOKEN`，点击“连接并查询”，确认接收模式。
2. 选择相机并启动摄像头，解除停止，再点击“准备下一条”。
3. 用 One 选择开爪、Two 选择闭爪、Three 选择 Home，用 OK 确认执行；Five 请求软件停止。
4. 动作结束后重新准备下一条。服务重启后重新填写 `TOKEN` 并连接。

保留 `gesture_usb/` 与同级 `models/gesture_recognizer.task` 的相对结构。截图、CSV 和事件输出写入 `homework/results/gesture_control/runtime/`；识别门限、心跳和停止互锁见 [手势模块说明](homework/src/gesture_control/README.md)。

## 五、实验结果

| 实验 | 原记录结果 | 统计口径 |
|---|---|---|
| 四方块归位 | 11/12，约91.7%；完整成功2/3轮 | 三轮，每轮4块，按实际放置结果统计 |
| 四层堆叠 | 10/12，约83.3%；完整成功2/3轮 | 按块次统计，首轮高层失败计入 |
| 独立颜色识别 | 主目标颜色28/28正确；严格判据22/28，约78.6% | 严格判据要求颜色正确且只有一个有效目标 |
| 固定 P4 分拣 | 两轮8/8人工观察正确入桶 | 固定红、黄、绿、蓝投放顺序，小样本现场记录 |
| 手势交互 | 10轮：9轮正确触发、1轮低分正确拦截、0误触发 | 覆盖基础动作选择、确认与停止 |

结果来自原报告、原始 CSV 和报告转录表，来源及对应章节见 [实验结果索引](homework/results/README.md)。P4 分拣的人工入桶记录与44条调试日志尚未逐条绑定；手势原回执及视频与测试轮次的同步关系仍待补齐。

下图为原相机实验保存的四色识别结果，同帧 raw、result 与 masks 文件一并保留：

![原相机四色识别结果](homework/results/vision_sorting/images/week5_evidence/20261019_144315_891538_result.png)

实验视频：[四方块归位](homework/results/motion_control/videos/11组_第三章_实验视频.mp4) · [四层堆叠](homework/results/motion_control/videos/11组_第四章_实验视频_week4.mp4) · [机械臂手势响应](homework/results/gesture_control/videos/手势识别控制机械臂视频%28机械臂反应%29.mp4) · [Windows 手势识别录屏](homework/results/gesture_control/videos/手势识别控制机械臂视频%28Windows桌面录屏%29.mp4)。

## 六、完成情况与后续工作

已完成教学模型显示与关节方向验证、共享 SDK 路径整理、示教点归位与堆叠、HSV 颜色识别、固定 P4 自动分拣，以及手势驱动开爪、闭爪、Home 和软件停止。代码、报告、数据与视频已按模块建立对应索引。

当前三条运行链路分别启动，教学模型与实体关节的逐轴映射、统一 ROS 图像与控制启动链路，以及手势选择物块和目标区域后的完整搬运仍待完成。后续工作包括：

1. 复核实机 SDK、K/B、示教点与高度补偿版本，记录 Jetson 系统和依赖版本。
2. 补充乱序投放、不同光照与重复实验，记录独立颜色识别和完整搬运的结果。
3. 测量实体停止时延，补齐原始回执、事件日志与视频时间对应关系。
4. 完成模型与实体轴映射，扩展相机定位抓取、手势任务选择与 ROS 集成。

SDK 九点标定原示例缺少7张参考图片，部分辅助分支仍有已记录的问题；详细差异与待补材料见 [待核实事项](homework/docs/待核实事项.md)。

## 七、检查与参考资料

在已安装相应 Python 依赖的环境中，从仓库根目录执行：

```bash
cd homework
python -B tools/check_project.py
python -B src/gesture_control/week7/gesture_usb/test_usb.py
python -B 'src/vision_sorting/week5/5.目标识别/self_test_week5.py'
```

三项检查分别覆盖源码、Notebook、XML、Markdown 链接与文件哈希，手势模拟器与回环 HTTP，以及 CLI 识别类的合成图测试。检查结果及环境限制见 [项目验证报告](homework/docs/项目验证报告.md)；ROS 实际构建、RViz 窗口、相机与实体机械臂需在对应平台验证。

- [最终课程项目报告](homework/reports/课程项目报告.docx)、[原实验周报告](homework/reports/original_experiments/)、[报告与代码对应表](homework/报告与代码对应表.md)。
- [文件整理记录](homework/docs/文件整理记录.md)、[文件来源与哈希](homework/docs/文件清单.csv)、[实验结果索引](homework/results/README.md)。
- [DICE 白熊人工智能实训平台用户手册](homework/docs/references/DICE_白熊人工智能实训平台用户手册.pdf)。
- [ROS Noetic](https://wiki.ros.org/noetic)、[URDF](https://wiki.ros.org/urdf)、[Xacro](https://wiki.ros.org/xacro)。
- [OpenCV 颜色空间](https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html)、[形态学处理](https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html)。
- [MediaPipe Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer)。

第三方 SDK 与模型参考保留各自 LICENSE 和来源文件；课程程序、原始实验数据与报告保留版本和来源记录。
