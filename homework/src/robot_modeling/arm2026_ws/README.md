# 当前Z1模型工作空间

本目录是完整catkin运行工作空间，包名为marm_description。模型使用基本几何体，主链无需旧版ROS包、官方Unitree SDK或外部网格。

在Ubuntu20.04 / ROS1 Noetic终端，从homework根目录进入：

```bash
source /opt/ros/noetic/setup.bash
sudo apt install ros-noetic-xacro ros-noetic-joint-state-publisher-gui ros-noetic-robot-state-publisher ros-noetic-rviz
cd src/robot_modeling/arm2026_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
source devel/setup.bash
roslaunch marm_description view_marm_z1_style.launch
```

Fixed Frame为 `marm_z1_base_link`。GUI发布关节状态，robot_state_publisher更新TF。停止主版后可启动课程变体：

```bash
roslaunch marm_description view_marm_z1_style_course_variant.launch
```

两版均为11 Link、10 Joint、57 visual、13 collision。joint4轴主版为 `(0,1,0)`，课程版为 `(0,-1,0)`，安装位置 `(0.19,0,0.05)m`，限位±1.51844rad。报告3.2中的旧X轴模型仅作追溯，位于homework的docs/references/legacy_model，不放入当前src。

`src/CMakeLists.txt` 已将Windows导出的绝对链接文本转换为查找catkin的入口；生成目录需在新机器重新构建。`generated/`保留原展开结果及历史验证记录，不能视为本次Linux实测。`scripts/preview_z1_gripper.py`是离线几何预览工具，运行会生成指定输出文件。

[返回项目说明](../../../README.md)
