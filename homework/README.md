# 第五学期课程项目

《机器人感知与控制综合实践》第11组项目，使用 DICE 白熊人工智能实训平台。先按下面的使用说明选择程序，再阅读项目结构、实验结果和技术文档。

## 先选择要运行的代码

| 你要做什么 | 使用哪些代码 | 在哪里运行 |
|---|---|---|
| 查看机械臂模型、调整虚拟关节和观察 TF | [ROS 工作空间](src/robot_modeling/arm2026_ws/README.md) | Ubuntu20.04 / ROS1 Noetic，支持图形显示 |
| 将四个堆叠方块归位，或将四个方块堆成四层 | [week3.ipynb](src/arm_motion_control/week3/week3.ipynb)、[Week4_堆叠.ipynb](src/arm_motion_control/week4/Week4_堆叠.ipynb) | Jetson 上的 Jupyter，需要实体机械臂 |
| 识别四色物块，或从固定 P4 上料区自动分拣 | [week5.ipynb](src/vision_sorting/week5/5.目标识别/week5.ipynb)、[week6.ipynb](src/vision_sorting/week6/week6.ipynb) | Jetson 上的 Jupyter；识别需相机，分拣还需实体机械臂 |
| 用手势控制开爪、闭爪、Home 和停止 | [app_usb.py](src/gesture_control/week7/gesture_usb/app_usb.py)、[receiver_usb.py](src/gesture_control/week7/gesture_usb/receiver_usb.py) | Windows 识别端 + Jetson 接收端 |
| 调用关节、夹爪和末端位姿接口，或查看实际配置 | [共享实体 SDK](sdk/arm5dof_python_uservo/) | Jetson；主程序已配置共享 SDK 路径 |

下面每组命令均从 **`homework/` 根目录**开始。Notebook 在 Jupyter 中按代码单元运行；`.py` 文件按给出的命令从终端启动。

## 1. ROS 模型：编译后打开 RViz

**用途：**查看 Z1 风格教学模型、拖动关节滑条、观察坐标系与 TF。这条链路不连接实体机械臂。

在 Ubuntu / WSLg 终端执行：

```bash
source /opt/ros/noetic/setup.bash
sudo apt install ros-noetic-xacro ros-noetic-joint-state-publisher-gui ros-noetic-robot-state-publisher ros-noetic-rviz
cd src/robot_modeling/arm2026_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
source devel/setup.bash
roslaunch marm_description view_marm_z1_style.launch
```

启动后，在关节 GUI 中调整 `marm_z1_joint1`～`marm_z1_joint6`，用 `marm_z1_gripper_joint` 调整夹爪。RViz 的 Fixed Frame 设为 `marm_z1_base_link`，工具坐标系为 `marm_z1_grasping_frame`。

需要比较第四关节转动方向时，先按 `Ctrl+C` 停止主版，再在已加载环境的终端运行：

```bash
roslaunch marm_description view_marm_z1_style_course_variant.launch
```

主版 joint4 轴为 `(0,1,0)`，课程变体为 `(0,-1,0)`。详细说明见[建模模块 README](src/robot_modeling/README.md)。

## 2. 归位与堆叠：在 Jetson 的 Jupyter 中运行

**准备：**连接机械臂电源及串口，核对实际关节零位、工作区域和示教点。实体 SDK 默认串口为 `/dev/ttyTHS1`，通信设置为 115200、8N1。

先安装依赖并启动 Jupyter：

```bash
python3 -m pip install -r requirements-jetson.txt
python3 -m jupyterlab
```

在 Jupyter 文件浏览器中打开对应 Notebook。后面的视觉实验也可使用这个 Jupyter 会话。

### 四方块归位：week3.ipynb

打开 [src/arm_motion_control/week3/week3.ipynb](src/arm_motion_control/week3/week3.ipynb)。

1. 从上往下运行 SDK 导入、位姿参数、参数检查和动作函数单元。
2. 保持参数区的 `DRY_RUN=True`，运行包含 `run_unstack_sort()` 的单元。程序打印位姿表并完成预览，不连接串口。
3. 核对打印的抓取点、上方点和目标区。当前源码顺序是 `P0 → P2 → P6 → P8`。
4. 准备真机执行时，将参数区的 `DRY_RUN` 设为 `False`，重新运行参数、相关函数及入口单元，使函数默认参数同步更新，再执行归位。

程序通过共享 SDK 完成开爪、抓取、抬升、Home 转运、放置和退出。预览开关只适用于这本归位 Notebook。

### 四层堆叠：Week4_堆叠.ipynb

打开 [src/arm_motion_control/week4/Week4_堆叠.ipynb](src/arm_motion_control/week4/Week4_堆叠.ipynb)。

1. 运行参数与运动学单元，再运行定义动作函数的单元。
2. 根据实际摆放，依次运行下面四个已有动作单元，每次等待上一层完成并检查结果：

| 动作入口 | 任务 |
|---|---|
| `run_single_block(0)` | P0 方块 → P4 底层 |
| `run_single_block(1)` | P2 方块 → P4 第2层 |
| `run_single_block(2)` | P8 方块 → P4 第3层 |
| `run_single_block(3)` | P6 方块 → P4 第4层 |

每次入口先做20项关键姿态 IK 预检，再创建机械臂对象。堆叠没有全局 `DRY_RUN` 开关，动作单元会直接驱动真机，按层运行，不使用“运行全部”。

两本 Notebook 均通过 `project_paths.py` 定位 `sdk/arm5dof_python_uservo/`，并显式使用该 SDK 的 `config/`。详细参数和原结果见[运动控制模块 README](src/arm_motion_control/README.md)。

## 3. HSV 识别与 P4 分拣：先识别，再运行抓放

使用上节的 Jetson 依赖和 Jupyter 会话，连接 USB 相机。两本 Notebook 的相机默认编号均为 `0`；设备编号变化时在各自参数区核对。

### 只做颜色识别：week5.ipynb

打开 [src/vision_sorting/week5/5.目标识别/week5.ipynb](src/vision_sorting/week5/5.目标识别/week5.ipynb)。这本程序只读取相机和记录识别结果，不控制机械臂。

1. 运行相机、HSV 阈值和路径参数单元，再运行检测与记录函数单元。
2. 可先运行包含 `test_image` 的离线自检单元，检查四个合成色块是否全部检出。
3. 运行相机探测单元检查取帧，再运行界面单元。
4. 点击“启动实时画面”，观察目标颜色、边框和四色掩膜。
5. 放入已知颜色的物块，点击相应真实颜色按钮，再点击“记录一次测试”；需要取证时点击“保存截图”。结束时点击“停止”。

新输出保存在 `results/vision_sorting/runtime/week5/`，原28次识别数据保留在 `results/vision_sorting/data/week5_test_records.csv`。

### 固定 P4 自动分拣：week6.ipynb

打开 [src/vision_sorting/week6/week6.ipynb](src/vision_sorting/week6/week6.ipynb)。这本程序会调用实体机械臂。

1. 核对相机、P4 上料区、桶位、机械臂串口和共享 SDK 配置。
2. 顺序运行参数、Roll 归一化、颜色检测、动作函数和界面单元。
3. 点击“启动预览”。**该操作会连接机械臂并移动到拍摄位姿。**
4. 将单个物块放在 P4。程序在连续5帧检测到唯一同色目标后进入 `BUSY`，完成抓取、投桶和复位。
5. 动作结束后，程序检查 P4 清空，再回到可接收下一块的状态。实际是否入桶仍需观察记录。

分拣使用 Notebook 内的 `bin_map`，不会读取 CSV 自动覆盖桶位。新输出位于 `results/vision_sorting/runtime/week6/`。“停止预览”结束相机预览，正在执行的机械动作仍需等待完成或使用设备急停。

算法、阈值和结果说明见[视觉模块 README](src/vision_sorting/README.md)。

## 4. 手势控制：先启动 Jetson 接收端，再连接 Windows 界面

**准备：**通过 Micro-USB 建立 Windows 与 Jetson 网络连接，确保能访问 Jetson 的 `192.168.55.1`。手势服务默认端口为 `8765`，与 Jupyter 的 `8888` 端口不同。

### 第一步：Jetson 启动接收端

先安装上节的 Jetson 依赖。做软件演练时执行：

```bash
python3 src/gesture_control/week7/gesture_usb/receiver_usb.py
```

终端会打印本次服务的 URL、`TOKEN` 和 `MODE`。默认是模拟模式，不连接机械臂。

准备使用实体机械臂时，停止模拟服务，改用下面的命令：

```bash
python3 src/gesture_control/week7/gesture_usb/receiver_usb.py --hardware --sdk-dir "$PWD/sdk/arm5dof_python_uservo" --arm-port /dev/ttyTHS1
```

两种接收模式择一启动。保留终端，供 Windows 端填写本次 `TOKEN`。

### 第二步：Windows 启动识别界面

在 Windows 的 `homework/` 根目录执行：

```powershell
py -3.11 -m venv .venv-gesture
.venv-gesture\Scripts\python.exe -m pip install -r requirements-gesture.txt
.venv-gesture\Scripts\python.exe src/gesture_control/week7/gesture_usb/app_usb.py
```

创建虚拟环境、安装依赖只需在首次使用时执行；之后直接用该环境的 Python 启动 `app_usb.py`。

### 第三步：连接并操作

1. 界面填写 `http://192.168.55.1:8765` 和接收器本次打印的 `TOKEN`，点击“连接并查询”，确认接收模式。
2. 选择正确相机编号并启动摄像头。
3. 解除停止，点击“准备下一条”。
4. 用 One 选择张爪、Two 选择闭爪、Three 选择 Home，再用 OK 确认执行；Five 请求软件停止。
5. 动作完成后，重新准备下一条。接收器重启后需填写新 `TOKEN` 并重新连接。

`gesture_usb/` 与同级 `models/gesture_recognizer.task` 必须一起保留。新截图、CSV 和事件输出位于 `results/gesture_control/runtime/`。

两端协议、识别门限和互锁说明见[手势模块 README](src/gesture_control/README.md)。

## 5. 共享 SDK：主程序自动加载，基础实验使用课程示例

[sdk/arm5dof_python_uservo/](sdk/arm5dof_python_uservo/) 保存一套实体机械臂 SDK，包含运动学、舵机接口、软运动轨迹和完整配置。

- 运行前面的归位、堆叠、分拣和手势程序时，按各自入口启动，程序会使用这套 SDK；不需要把 SDK 再复制进各个 week 目录。
- 要学习单项接口，在 Jetson 的 `homework/` 根目录启动 Jupyter，然后打开下面的课程示例。

| 课程示例 | 使用方法 |
|---|---|
| [01.机械臂关节标定.ipynb](src/arm_motion_control/basic_control/01.机械臂关节标定.ipynb) | 连接机械臂，按标准姿态采集反馈，运行 `calc_kb` 计算 K/B；该程序不自动覆盖配置 |
| [02.机械臂关节弧度控制.ipynb](src/arm_motion_control/basic_control/02.机械臂关节弧度控制.ipynb) | 按单元测试关节角和多关节软运动 |
| [03.机械爪测试.ipynb](src/arm_motion_control/basic_control/03.机械爪测试.ipynb) | 按单元测试夹爪角度、张开和闭合 |
| [04.末端位姿控制.ipynb](src/arm_motion_control/basic_control/04.末端位姿控制.ipynb) | 调用 `set_tool_pose`，并读取末端位姿反馈 |

课程示例已配置共享 SDK 路径。SDK 目录内另保留同名原始示例；如果直接运行这些原始示例，应在 SDK 目录启动 Jupyter：

```bash
cd sdk/arm5dof_python_uservo
python3 -m jupyterlab
```

| 配置文件 | 用途 |
|---|---|
| `sdk/arm5dof_python_uservo/config.py` | 默认串口、关节ID、K/B、Home和拍摄位姿、轨迹步长 |
| `sdk/arm5dof_python_uservo/config/z_error_polyfit.txt` | 实体机械臂高度补偿 |
| `sdk/arm5dof_python_uservo/config/` 内其他文件 | 工作台标定、坐标变换及物体配置 |

保留当前 SDK 的实际配置。报告中的 K/B 和高度补偿与这套配置有版本差异，先核实现场版本，再决定实验调整，详见[待核实事项](docs/待核实事项.md)。

## 项目结构与开发环境

```text
homework/
├── README.md
├── 报告与代码对应表.md
├── reports/                         最终报告和原实验报告
├── src/
│   ├── robot_modeling/arm2026_ws/    ROS工作空间
│   ├── arm_motion_control/          basic_control、week3、week4
│   ├── vision_sorting/              week5/5.目标识别、week6
│   └── gesture_control/week7/       gesture_usb、models
├── sdk/arm5dof_python_uservo/        共享实体SDK
├── results/                         原数据、截图、视频及新运行输出
├── docs/                            整理、验证和来源记录
├── tools/check_project.py           静态检查工具
└── project_paths.py                 共享SDK定位
```

完整目录见[最终目录树](docs/最终目录树.txt)。

| 运行链路 | 环境与依赖 |
|---|---|
| ROS模型 | Ubuntu20.04 / WSL2、ROS1 Noetic、catkin、Xacro、RViz及关节状态发布组件 |
| Jetson运动和视觉 | Linux、Python3（Notebook元数据多为3.8.10）、NumPy、pyserial、OpenCV、Jupyter/ipywidgets |
| Windows手势 | Windows11、记录为Python3.11.9、MediaPipe Tasks、OpenCV、NumPy、Pillow、Tkinter |
| Jetson手势接收 | Python3标准库；实体模式另需NumPy、pyserial及本项目SDK |

依赖入口为 [requirements-jetson.txt](requirements-jetson.txt) 和 [requirements-gesture.txt](requirements-gesture.txt)。JetPack及现场完整库版本仍待核实。ROS模型、Jetson分拣、Windows手势各自运行，尚未统一为一个ROS控制系统。

## 实验结果和视频

| 实验 | 原记录结果 | 判定口径 |
|---|---|---|
| 四方块归位 | 11/12，约91.7%；完整成功2/3轮 | 三轮，每轮4块，按实际放置结果 |
| 四层堆叠 | 10/12，约83.3%；完整成功2/3轮 | 按块次，首轮高层失败计入 |
| 独立颜色识别 | 主目标28/28；严格判据22/28，约78.6% | 严格判据要求颜色正确且唯一有效目标 |
| 固定P4分拣 | 两轮8/8人工观察入桶 | 固定红黄绿蓝顺序；与44条调试日志未逐条绑定 |
| 手势交互 | 9轮触发、1轮低分正确拦截、0误触发 | 基础动作，不是完整手势搬运验收 |

![原相机颜色识别结果](results/vision_sorting/images/week5_evidence/20261019_144315_891538_result.png)

- [机械臂反应视频](results/gesture_control/videos/手势识别控制机械臂视频%28机械臂反应%29.mp4)：960×544，约57.968秒。
- [Windows手势识别录屏](results/gesture_control/videos/手势识别控制机械臂视频%28Windows桌面录屏%29.mp4)：2558×1528，约59.233秒。
- [归位视频](results/motion_control/videos/11组_第三章_实验视频.mp4)、[堆叠视频](results/motion_control/videos/11组_第四章_实验视频_week4.mp4)。

原始数据、图片、录像和报告章节的联系见[实验结果索引](results/README.md)。手势视频与原测试轮次、回执的同步关系仍待核实。

## 检查与已知问题

从 `homework/` 根目录执行以下不连接实体设备的检查：

```bash
python -B tools/check_project.py
python -B src/gesture_control/week7/gesture_usb/test_usb.py
python -B 'src/vision_sorting/week5/5.目标识别/self_test_week5.py'
```

上述检查分别验证静态文件与链接、模拟器和回环HTTP、CLI参考类的合成图识别。实际执行结果见[项目验证报告](docs/项目验证报告.md)。Linux实际构建、RViz窗口、相机和实体机械臂仍需在对应环境验证。

当前需保留的差异包括报告与SDK的K/B、归位顺序和高度补偿；SDK九点标定原缺7张参考图片，部分辅助分支仍有已记录的问题。完整手势搬运、任意位置抓取、教学模型与实体轴映射和统一ROS集成属于后续工作，详见[待核实事项](docs/待核实事项.md)。

## 报告与参考资料

- [最终课程报告 DOCX](reports/课程项目报告.docx)、[原实验周报告](reports/original_experiments/)。
- [报告与代码对应表](报告与代码对应表.md)、[文件整理记录](docs/文件整理记录.md)、[项目验证报告](docs/项目验证报告.md)、[文件来源与哈希](docs/文件清单.csv)。
- [DICE平台手册](docs/references/DICE_白熊人工智能实训平台用户手册.pdf)。
- [ROS Noetic](https://wiki.ros.org/noetic)、[URDF](https://wiki.ros.org/urdf)、[Xacro](https://wiki.ros.org/xacro)。
- [OpenCV颜色空间](https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html)、[MediaPipe Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer)。

平台 SDK 保留自身 LICENSE 与来源文件；报告和实验数据保留原始记录。
