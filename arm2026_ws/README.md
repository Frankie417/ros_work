# Z1 机械臂：启动与可视化说明

本工作空间用于在 **WSL2 Ubuntu / ROS1 Noetic** 中查看 Z1 风格机械臂，使用 RViz 显示模型，使用关节滑条调整姿态。

- 工作空间：`~/ros_work/arm2026_ws`
- ROS 包名：`marm_description`（保留原包名）
- 默认启动文件：`view_marm_z1_style.launch`
- 本项目是使用基础几何体构建的 Z1 风格教学模型，启动命令不会连接或控制真实机械臂。

## 1. 打开 Z1 机械臂

打开 WSL2 Ubuntu 终端，复制执行以下命令。**每行末尾不要加反斜杠 `\`。**

```bash
cd ~/ros_work/arm2026_ws
source /opt/ros/noetic/setup.bash
source ~/ros_work/arm2026_ws/devel/setup.bash
roslaunch marm_description view_marm_z1_style.launch
```

启动后应看到两个图形窗口：

1. **RViz**：显示 Z1 机械臂三维模型和连杆坐标轴。
2. **Joint State Publisher GUI**：显示关节滑条，用于调整机械臂姿态和夹爪开合。

保持启动终端运行。`roslaunch` 会按需启动 ROS Master，无需另开终端运行 `roscore`。不需要传入 `model:=...` 参数。

> 以上路径按当前 root 用户的工作空间编写。如果以后移动工作空间，需要在新位置重新构建并加载对应的 `devel/setup.bash`。

## 2. 调整关节与夹爪

在 Joint State Publisher GUI 中拖动对应滑条：

| 滑条名称 | 作用 |
| --- | --- |
| `marm_z1_joint1` 至 `marm_z1_joint6` | 调整六个机械臂关节角度 |
| `marm_z1_gripper_joint` | 调整活动夹指开合 |

夹爪采用一侧固定、另一侧转动的结构。夹爪关节范围为 `−π/2` 至 `0` rad；`0` 表示闭合，向负方向转动表示打开。

GUI 发布 `/joint_states`，`robot_state_publisher` 根据关节状态更新 TF，RViz 随之显示新的机械臂姿态。

## 3. 在 RViz 中查看坐标与位移

启动文件已经加载专用配置 `urdf_z1_style.rviz`，默认启用 RobotModel 和 TF。

| 设置 | 正确值 |
| --- | --- |
| `Global Options → Fixed Frame` | `marm_z1_base_link` |
| `Z1StyleRobotModel → Robot Description` | `robot_description` |
| 工具坐标系 | `marm_z1_grasping_frame` |

### 显示坐标系名称

在左侧 Displays 中展开 `TF`，勾选 `Show Names`。`Show Axes` 用于显示 XYZ 坐标轴。

### 查看末端相对基座的位置

展开：

```text
TF → Frames → marm_z1_grasping_frame → Position
```

当 Fixed Frame 为 `marm_z1_base_link` 时，Position 就是工具坐标系原点相对基座的 XYZ，单位为米。Orientation 是对应的旋转四元数，不是 RPY 欧拉角。

### 查看相邻连杆的位置关系

在 `TF → Frames` 中展开目标连杆：

- `Parent`：父坐标系名称。
- `Relative Position`：当前坐标系原点在父坐标系中的 XYZ，单位为米。
- `Relative Orientation`：相对父坐标系的旋转四元数。

对于转动关节，Relative Position 可以保持不变，Relative Orientation 随关节转动而变化。

### 查看任意两个坐标系的关系

将 `Global Options → Fixed Frame` 改成参考坐标系，再查看目标坐标系的 Position 和 Orientation。例如，以 `marm_z1_link02` 为 Fixed Frame，查看 `marm_z1_link06` 的数值，即可获得后者相对前者的位姿。查看完后可改回 `marm_z1_base_link`。

## 4. 打开 TF 连接树

保持机械臂启动终端运行，另外打开一个 WSL2 Ubuntu 终端：

```bash
source /opt/ros/noetic/setup.bash
source ~/ros_work/arm2026_ws/devel/setup.bash
rosrun rqt_tf_tree rqt_tf_tree
```

窗口打开后，点击刷新按钮查看 TF 树。该窗口用于观察坐标系父子连接；具体位置数值在 RViz 中查看。

每个新终端都需要重新执行环境加载命令。

## 5. 关闭与切换版本

回到运行 `roslaunch` 的终端，按 **Ctrl+C** 结束本次启动。

默认使用 Z1 主版。只有需要比较第四关节转轴方向时，才在停止主版后启动 Z1 课程版：

```bash
source /opt/ros/noetic/setup.bash
source ~/ros_work/arm2026_ws/devel/setup.bash
roslaunch marm_description view_marm_z1_style_course_variant.launch
```

两版的区别仅为 `marm_z1_joint4` 的轴方向：主版为 `0 1 0`，课程版为 `0 -1 0`。不要同时启动两版，以免共享的模型参数和 TF 相互干扰。

## 6. 常见问题

### 提示 roslaunch 或 rosrun 找不到命令

在当前终端执行：

```bash
source /opt/ros/noetic/setup.bash
```

然后重新执行启动命令。如果提示该 setup.bash 不存在，需要先确认 ROS Noetic 的实际安装位置。

### 提示找不到 marm_description 或启动文件

先检查包路径：

```bash
source /opt/ros/noetic/setup.bash
source ~/ros_work/arm2026_ws/devel/setup.bash
rospack find marm_description
```

正常应输出：

```text
~/ros_work/arm2026_ws/src/marm_description
```

如果工作空间刚移动过，可先在当前终端补充搜索路径：

```bash
export ROS_PACKAGE_PATH="~/ros_work/arm2026_ws/src:$ROS_PACKAGE_PATH"
rospack profile
roslaunch marm_description view_marm_z1_style.launch
```

### 缺少 devel/setup.bash，或需要重新构建

在工作空间中执行：

```bash
cd ~/ros_work/arm2026_ws
source /opt/ros/noetic/setup.bash
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
source ~/ros_work/arm2026_ws/devel/setup.bash
roslaunch marm_description view_marm_z1_style.launch
```

如果构建提示 CMakeCache 引用了旧路径，删除工作空间内的 `build`、`devel` 两个生成目录后，再执行以上构建步骤；不要删除 `src`。

### RViz 打开了，但看不到模型

检查左侧：

1. Fixed Frame 是否为 `marm_z1_base_link`。
2. `Z1StyleRobotModel` 和 `TF` 是否已勾选。
3. Robot Description 是否为 `robot_description`。
4. 关节 GUI 是否仍在运行，启动终端是否有报错。

如果提示无法连接 display，请从支持 Linux 图形窗口的 WSLg 环境启动，并检查 `echo "$DISPLAY"` 是否有值。只在不支持 GUI 的终端中执行命令，无法显示 RViz 窗口。

## 7. 主要文件

以下路径均相对于工作空间根目录。

| 文件或目录 | 用途 |
| --- | --- |
| `src/marm_description/launch/view_marm_z1_style.launch` | 默认 Z1 主版启动入口 |
| `src/marm_description/launch/view_marm_z1_style_course_variant.launch` | Z1 课程版启动入口 |
| `src/marm_description/urdf/marm_z1_style.xacro` | 主模型入口 |
| `src/marm_description/urdf/marm_z1_style_core.xacro` | 共享 Link、Joint 和几何定义 |
| `src/marm_description/urdf/marm_z1_style_course_variant.xacro` | 课程版模型入口 |
| `src/marm_description/urdf_z1_style.rviz` | RViz 配置 |
| `generated/` | 展开的 URDF、构建日志及验证记录 |
| `report_assets/` | Z1 模型离线预览图 |
| `_reference/` | 已裁剪的官方 Z1 参考资源，当前模型不依赖此目录 |
| `_backup/` | Z1 模型历史备份 |

当前主版和课程版均包含 **11 个 Link、10 个 Joint（7 个转动、3 个固定）、57 个 visual、13 个 collision**。
