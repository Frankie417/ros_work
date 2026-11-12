# 第五学期课程项目

《机器人感知与控制综合实践》配套工程，使用DICE白熊平台。当前完成ROS模型显示、示教点归位与堆叠、HSV固定P4分拣和Windows手势基础控制。ROS、Jetson视觉/实体控制、Windows手势为分别启动的链路。

项目文件按四模块组织，原始参数、报告和实验记录保留。阅读入口：[报告与代码对应表](报告与代码对应表.md)、[整理记录](docs/文件整理记录.md)、[项目验证报告](docs/项目验证报告.md)和[实验结果索引](results/README.md)。

| 内容 | 位置 |
|---|---|
| 最终课程报告（原样复制） | [reports/课程项目报告.docx](reports/课程项目报告.docx) |
| ROS模型 | [src/robot_modeling/arm2026_ws](src/robot_modeling/arm2026_ws/README.md) |
| 归位 / 堆叠 | [week3.ipynb](src/arm_motion_control/week3/week3.ipynb) / [Week4_堆叠.ipynb](src/arm_motion_control/week4/Week4_堆叠.ipynb) |
| HSV识别 / 固定P4分拣 | [week5.ipynb](src/vision_sorting/week5/5.目标识别/week5.ipynb) / [week6.ipynb](src/vision_sorting/week6/week6.ipynb) |
| Windows手势 / Jetson接收 | [app_usb.py](src/gesture_control/week7/gesture_usb/app_usb.py) / [receiver_usb.py](src/gesture_control/week7/gesture_usb/receiver_usb.py) |
| 共享实体SDK及完整配置 | [sdk/arm5dof_python_uservo](sdk/arm5dof_python_uservo/) |
| 原始实验结果 | [motion_control](results/motion_control/README.md)、[vision](results/vision_sorting/README.md)、[gesture](results/gesture_control/README.md) |
| 原实验周报告 | [reports/original_experiments](reports/original_experiments/) |

## 环境和Notebook入口

建模使用Ubuntu20.04/ROS1 Noetic；Jetson使用Python3、NumPy、pyserial、OpenCV、Jupyter/ipywidgets；Windows手势记录为Python3.11.9，使用MediaPipe Tasks、OpenCV、Pillow及Tkinter。JetPack和完整现场依赖版本仍待核实。[Jetson依赖清单](requirements-jetson.txt)与[Windows手势依赖清单](requirements-gesture.txt)按实际导入列出，未冒充实测版本锁定。

在Jetson的homework根目录安装依赖并打开主Notebook：

```bash
python3 -m pip install -r requirements-jetson.txt
python3 -m jupyterlab
```

归位和堆叠从Notebook当前目录向上查找 `project_paths.py`，因此应在homework或其子目录启动Jupyter。共享SDK只保存一套。主程序显式使用该SDK的config，未改K/B、Z补偿或动作参数。归位默认 `DRY_RUN=True`；堆叠动作Cell和分拣“启动预览”会连接并移动真机，按实验步骤手动运行。

SDK内的01关节标定、02关节弧度控制、03夹爪测试、04末端位姿控制等示例保持原样；这些示例以SDK目录为工作目录：

```bash
cd sdk/arm5dof_python_uservo
python3 -m jupyterlab
```

原始CSV保存在results各模块的data目录。主识别、分拣和手势的新输出统一写到各自 `runtime/` 子目录，不追加到原始数据；runtime由程序运行时创建，并由.gitignore忽略。

## 手势两端入口

Windows在homework根目录：

```powershell
py -3.11 -m venv .venv-gesture
.venv-gesture\Scripts\python.exe -m pip install -r requirements-gesture.txt
.venv-gesture\Scripts\python.exe src/gesture_control/week7/gesture_usb/app_usb.py
```

Jetson在homework根目录选择一种接收模式：

```bash
# 模拟接收，不连接机械臂
python3 src/gesture_control/week7/gesture_usb/receiver_usb.py
# 真机接收，需手动选择并确认现场设备
python3 src/gesture_control/week7/gesture_usb/receiver_usb.py --hardware --sdk-dir "$PWD/sdk/arm5dof_python_uservo" --arm-port /dev/ttyTHS1
```

Windows填入 `http://192.168.55.1:8765` 及本次服务TOKEN。识别端的gesture_usb与models相对位置已经保留；服务重启后重新连接。手势实现范围为开爪、闭爪、Home和软件停止；完整手势搬运与统一ROS控制尚未实现。

## 当前差异和验证

D01的模型joint4版本差异、D03的报告/SDK标定差异、D05归位顺序差异、D07真机/仿真Z补偿差异保留在对应表。手势原始回执及录像仍待补齐。实体结果沿用原报告和数据，没有新增成功率。

本机可运行的软件检查：

```bash
python -B src/gesture_control/week7/gesture_usb/test_usb.py
python -B src/vision_sorting/week5/5.目标识别/self_test_week5.py
```

当前未进行Linux catkin实际构建、RViz窗口和实体机械臂/摄像头联调。视频与MediaPipe模型保留Git LFS属性；本阶段未执行Git提交或推送。


## 技术架构和四模块说明

ROS负责Xacro→robot_description→JointState/TF→RViz。Jetson视觉执行相机→HSV→连续5帧确认→共享SDK固定P4抓放。Windows手势执行MediaPipe/关键点→Controller→HTTP 8765→Jetson Engine→实体SDK。三条链路分别启动，未完成统一ROS集成。

| 模块 | 功能与文档 |
|---|---|
| [机器人建模](src/robot_modeling/README.md) | 11 Link/10 Joint、57 visual/13 collision，比较joint4正反方向 |
| [机械臂运动控制](src/arm_motion_control/README.md) | 标定、关节/夹爪、末端位姿、归位及堆叠 |
| [视觉识别与分拣](src/vision_sorting/README.md) | 四色HSV与固定P4、5帧确认、BUSY/RESET |
| [手势交互](src/gesture_control/README.md) | One/Two/Three候选、OK确认、Five停止及HTTP心跳 |

## 实际目录

```text
homework/
├── README.md、报告与代码对应表.md
├── reports/课程项目报告.docx、original_experiments/
├── src/
│   ├── robot_modeling/arm2026_ws/
│   ├── arm_motion_control/basic_control/、week3/、week4/
│   ├── vision_sorting/week5/5.目标识别/、week6/
│   └── gesture_control/week7/gesture_usb/、models/
├── sdk/arm5dof_python_uservo/
├── results/robot_modeling/、motion_control/、vision_sorting/、gesture_control/
└── docs/文件整理记录.md、项目验证报告.md、待核实事项.md
```

完整目录见[最终目录树](docs/最终目录树.txt)。原代码文件名不变。课程报告DOCX保持原字节；按最新要求不交付未成功导出的PDF。

## ROS与课程Notebook入口

Ubuntu20.04/ROS1 Noetic模型启动，从homework根目录：

```bash
source /opt/ros/noetic/setup.bash
sudo apt install ros-noetic-xacro ros-noetic-joint-state-publisher-gui ros-noetic-robot-state-publisher ros-noetic-rviz
cd src/robot_modeling/arm2026_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
source devel/setup.bash
roslaunch marm_description view_marm_z1_style.launch
```

RViz Fixed Frame=marm_z1_base_link。停止主版后可运行 `roslaunch marm_description view_marm_z1_style_course_variant.launch`。

Jetson在homework启动Jupyter后打开以下课程入口。它们均可定位共享SDK/config，无需原始weekX目录。

| 任务 | 入口 |
|---|---|
| 标定 | src/arm_motion_control/basic_control/01.机械臂关节标定.ipynb |
| 关节控制 | 同目录02.机械臂关节弧度控制.ipynb |
| 夹爪 | 同目录03.机械爪测试.ipynb |
| 末端位姿 | 同目录04.末端位姿控制.ipynb |
| 归位 | src/arm_motion_control/week3/week3.ipynb，加载参数后run_unstack_sort |
| 堆叠 | src/arm_motion_control/week4/Week4_堆叠.ipynb，按层run_single_block(0/1/2/3) |
| HSV识别 | src/vision_sorting/week5/5.目标识别/week5.ipynb，Cell1/3及Cell9界面 |
| P4分拣 | src/vision_sorting/week6/week6.ipynb，Cell1/3/5/7和Cell9界面 |

分拣默认摄像头0、串口/dev/ttyTHS1，115200/8N1。启动分拣预览会驱动机械臂到拍摄位姿；运动Cell按实验步骤手动运行。

## 实验结果

| 实验 | 原始结果 | 统计口径 |
|---|---|---|
| 四方块归位 | 11/12≈91.7%；完整2/3轮 | 三轮，每轮4块，按实际放置 |
| 四层堆叠 | 10/12≈83.3%；完整2/3轮 | 首轮高层失败，按块次 |
| 颜色识别 | 主目标28/28；严格22/28≈78.6% | 严格判据要求唯一有效目标且颜色正确 |
| 固定P4分拣 | 两轮8/8人工入桶 | 两轮固定红黄绿蓝；44条调试日志不是44次成功 |
| 手势交互 | 9轮触发、1低分正确拦截、0误触发 | 基础动作，不是完整手势搬运验收 |

![真实颜色识别结果](results/vision_sorting/images/week5_evidence/20261019_144315_891538_result.png)

## 手势实验视频

- [机械臂反应视频](results/gesture_control/videos/手势识别控制机械臂视频%28机械臂反应%29.mp4)：960×544，约57.968s。
- [Windows桌面录屏](results/gesture_control/videos/手势识别控制机械臂视频%28Windows桌面录屏%29.mp4)：2558×1528，约59.233s。

两段原视频未压缩、裁剪或重新编码，复制前后SHA-256一致。与报告轮次、回执和事件流的同步关系待核实。

## 已知问题和后续工作

D01旧模型joint4、D03标定K/B、D05归位顺序、D07高度补偿均保留差异；详见[待核实事项](docs/待核实事项.md)。SDK九点标定示例原缺7张参考图片，set_servo_angle分支仍有is_wait/wait名称风险。完整手势搬运、任意像素抓取、实体轴与教学模型映射和统一ROS启动属于后续工作。

主程序已完成搬离原目录后的导入、软件和资源检查；未新增实体成功率。[文件整理记录](docs/文件整理记录.md)、[项目验证报告](docs/项目验证报告.md)、[实验结果索引](results/README.md)记录证据与验证范围。

## 参考资料

- [课程报告](reports/课程项目报告.docx)、[DICE平台手册](docs/references/DICE_白熊人工智能实训平台用户手册.pdf)、[原周报告](reports/original_experiments/)。
- [ROS Noetic](https://wiki.ros.org/noetic)、[URDF](https://wiki.ros.org/urdf)、[Xacro](https://wiki.ros.org/xacro)。
- [OpenCV颜色空间](https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html)、[MediaPipe Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer)。

实体SDK保留自身LICENSE与来源文件，完整现场依赖版本仍待核实。
