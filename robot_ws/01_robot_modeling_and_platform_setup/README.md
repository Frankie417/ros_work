# 机器人建模与实验平台搭建

## 功能与入口

当前入口是根目录 `arm2026_ws`，完整保留 catkin 工作空间及 `marm_description` 包。模块内 `1.1_code/arm2026_ws` 是旧实验版本，不与当前工作空间同时加入 ROS_PACKAGE_PATH。

当前模型通过 Xacro 共享核心定义，提供 Z1 主版及第四关节轴反向的课程版。11个Link、10个Joint（7转动、3固定）、57个visual、13个collision。夹爪角度范围 −π/2 至0 rad，0为闭合。

## 文件与实现

- `../../arm2026_ws/src/marm_description/urdf/`：当前模型与公共核心。
- `../../arm2026_ws/src/marm_description/launch/`：两版启动文件，分别加载关节GUI、robot_state_publisher和RViz。
- `1.3_experiment_results/`：历史预览、原报告及来源。离线预览属于模型说明，不作为实体运行证据。

## 运行

从仓库根目录进入 `arm2026_ws`：

```bash
source /opt/ros/noetic/setup.bash
cd arm2026_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
source devel/setup.bash
roslaunch marm_description view_marm_z1_style.launch
```

依赖安装命令见根README。RViz Fixed Frame为 `marm_z1_base_link`，工具坐标系为 `marm_z1_grasping_frame`。另一个终端加载相同环境后运行 `rosrun rqt_tf_tree rqt_tf_tree` 查看连接树。需要比较关节方向时停止主版，再用 `view_marm_z1_style_course_variant.launch`。

## 实验结果与问题

原记录及报告截图支持模型加载、关节状态更新和TF可视化。当前模型为六关节教学模型，实体SDK为五个姿态轴加夹爪；逐轴映射未完成。Windows保存的 `src/CMakeLists.txt` 可能表现为链接目标文本；应在Linux克隆并构建，必要时运行 `catkin_init_workspace src` 恢复入口。当前检查未启动ROS、WSLg或RViz。


[返回项目首页](../../README.md) · [历史技术说明](1.2_readme/README.md)
