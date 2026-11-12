当前入口和运行步骤见 [模块README](../README.md)。以下保留原实验版本的技术核对；旧模型统计、旧采样与历史配置不覆盖当前Z1工作空间及最终报告。

# 机器人建模与实验平台搭建


手册核对：[平台手册核对与页码索引](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/%E5%B9%B3%E5%8F%B0%E6%89%8B%E5%86%8C%E6%A0%B8%E5%AF%B9.md)。以下补充采用手册PDF顺序页码，厂商示例与本项目运行记录分别标注。

## 1. 模块简介

归档 ROS1 机械臂描述包、Xacro/URDF、四个 launch、RViz 配置及原有验证记录。实体平台来自第一周 DICE 白熊人工智能实训平台报告；ROS 教学模型与五自由度实物 SDK 分属两条实现链路。任务书本项为基础25分，涉及编译、建模、启动、关节状态与图像话题。

## 2. 功能需求

| 功能 | 输入 | 输出 | 实现状态 |
|---|---|---|---|
| 模型描述 | 几何、父子关系、origin/axis/limit | robot_description | 已有源码、展开文件与解析日志 |
| 关节显示 | GUI 虚拟 JointState | /joint_states、TF、RViz | 既有运行记录；可见视口截图待补 |
| 一键加载模型 | launch 参数 | GUI、状态发布器、RViz | 已有；原模型启动缺省 model 参数问题见第7节 |
| 摄像头采集 | USB 相机 | OpenCV BGR 帧 | 模块3有真实取帧材料 |
| 图像话题与算法统一启动 | ROS 图像消息 | 全系统 | 当前 launch 未包含相机/算法节点，待实现 |
| 实物关节到 ROS 模型映射 | 校准后的关节角 | 与实体一致的 TF | 【待补充：DICE SDK与ROS模型关节对应及标定验证】 |

## 3. 技术原理

主链为 `base_link → link0 → link1 → link2 → link3 → link4 → link5 → link6`；link6 分支连接两个夹爪手指与 `grasping_frame`。模型共11个link、10个joint：6个revolute、1个prismatic、3个fixed。一个手指移动、另一手指固定，不是双指 mimic 模型。手册概述称六自由度，当前SDK按五个姿态角加夹爪组织；手册也列有Arm5DoF与Arm_Lib两套示例。不能仅凭通道数把本模型的6个转动关节直接映射到实物。

`link` 表示刚体；`visual` 控制外观，`collision` 提供碰撞几何，`inertial` 描述质量和惯量；`joint` 的 parent/child 建立树，origin 的 xyz 单位m、rpy单位rad；axis 在关节坐标系内定义运动轴；limit 指定角度或行程、速度和effort上限。

对第i个关节，`T_parent_child(q_i)=T_origin·T_motion(q_i)`，其中 T 是4×4齐次变换矩阵，q_i为转角或位移。根到末端变换为沿树各变换的连乘。GUI发布q后，robot_state_publisher依据此关系发布动态与静态TF。该过程不驱动舵机。

当前 `generated/marm.urdf` 为68个visual、9个collision。其质量宏调用保留为无命名空间的 `cylinder_inertial_matrix` / `box_inertial_matrix` 标签，未得到标准 `<inertial>` 元素；不能据此声称动力学惯性配置已完成。独立 Z1 风格展开版本为57个visual、13个collision、9个inertial，应与主模型分开说明。

## 4. 代码结构

```text
1.1_code/arm2026_ws/
├── .catkin_workspace
├── src/
│   ├── CMakeLists.txt
│   └── marm_description/
│       ├── package.xml、CMakeLists.txt、README.md
│       ├── urdf/  （主模型、课程变体与Z1独立模型，共5份Xacro）
│       ├── launch/  （4份启动文件）
│       ├── urdf.rviz
│       └── urdf_z1_style.rviz
└── scripts/preview_z1_gripper.py
```

`build/`、`devel/` 是原 Linux 环境构建产物，未复制为新工程依赖。第三方 `_reference/` 仍在原始目录，当前课程模型不加载其mesh或控制器。离线生成文件放在实验结果 records/generated，图像在figures/model_previews。

## 5. 核心代码说明

| 文件/入口 | 输入 → 处理 → 输出 |
|---|---|
| `urdf/marm.xacro` | 尺寸、颜色、关节参数 → 组合基础几何及主链 → 主模型 |
| `urdf/marm_course_variant.xacro` | 同样结构 → 仅反转joint4轴 → 课程修改模型 |
| `marm_z1_style_core.xacro` | 参数与宏 → 复用独立外观模型 → 被Z1两个入口包含 |
| `view_marm.launch` | robot_description → GUI、状态发布、RViz → 关节与TF可视化 |
| `view_marm_z1_style*.launch` | 独立Z1入口 → 同类节点 → 独立RViz配置 |
| `preview_z1_gripper.py` | 本地模型数据 → 离线绘图 → 示意预览；非实验截图 |

主模型joint4连接link3/link4，origin xyz=`0 0 -0.15`、rpy=`0 π/2 π`，axis=`1 0 0`，范围约[-π,π]；课程版axis=`-1 0 0`。夹爪移动关节finger_joint1行程[0,0.06]m、轴`0 1 0`。其他关节参数完整列于实验结果 records/模型静态结构.json。

## 6. 环境与依赖

原有记录：WSL2 Ubuntu20.04、ROS1 Noetic、catkin、WSLg；原路径 `/home/cubertzk/arm2026_ws`。包清单声明catkin、roscpp、tf、urdf、xacro；launch还需要joint_state_publisher_gui、robot_state_publisher、rviz，后面三者未完整写入包运行依赖。Windows中的归档不包含ROS运行环境。

【待补充：ROS补丁版本、Xacro/GUI/RViz确切版本、可复用的环境清单】。实体报告记DICE实验箱11号；手册确认该平台主控系列为Jetson Nano，摄像头为安装在臂上的USB相机。具体机械臂商品型号、序列号、相机传感器型号与现场板卡配置仍待铭牌核对。

### 手册补充的平台与连接环境

[手册PDF第19页](../../../homework/docs/references/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=19)～[手册PDF第23页](../../../homework/docs/references/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=23)描述Jetson Nano/4GB参考平台，使用Ubuntu18.04，介绍JetPack4.4/L4T32.4.3；这是厂商参考环境，不替代本项目WSL2 Ubuntu20.04/ROS Noetic的历史记录，也不能据此确认当前实验镜像版本。

[手册PDF第29页](../../../homework/docs/references/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=29)～[手册PDF第30页](../../../homework/docs/references/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=30)、[手册PDF第47页](../../../homework/docs/references/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=47)确认Micro-USB gadget网络和Jetson端Jupyter地址`http://192.168.55.1:8888`。该地址指Jetson，不是Windows本机地址。平台整机还包括载板、听觉/传感器模块、10.1英寸屏及无线键鼠；本课题只归档实际使用的机械臂与视觉链路。手册第9.5节的dofbot包教程可作原理参考，不替换当前marm包或复制手册模型尺寸。

## 7. 安装和运行

以下是按源码核对的 Linux 复现步骤，**待验证**，本次未运行ROS。先在ROS Noetic环境安装包依赖：

```bash
sudo apt install ros-noetic-xacro ros-noetic-urdf ros-noetic-tf ros-noetic-roscpp ros-noetic-joint-state-publisher-gui ros-noetic-robot-state-publisher ros-noetic-rviz
source /opt/ros/noetic/setup.bash
```

进入本模块 `1.1_code/arm2026_ws` 的Linux副本。归档中的 `src/CMakeLists.txt` 内容是 `/opt/ros/noetic/share/catkin/cmake/toplevel.cmake` 一行路径文本，不是有效CMake脚本，这是Windows导出后未保留符号链接的现状。在**另建的运行副本**中重建入口：

```bash
cp -a src/CMakeLists.txt src/CMakeLists.txt.exported-path.txt
ln -sfn /opt/ros/noetic/share/catkin/cmake/toplevel.cmake src/CMakeLists.txt
catkin_make
source devel/setup.bash
roslaunch marm_description view_marm.launch model:=marm
```

`model` 参数虽未在命令中使用，但原始及课程变体launch声明它且没有默认值，所以需要显式传入。Z1独立启动文件无此参数要求：`roslaunch marm_description view_marm_z1_style.launch`。RViz Fixed Frame设为`base_link`，观察RobotModel与TF；GUI逐个调节joint1～joint6和finger_joint1。

只读验收命令（待在ROS环境验证）：`rosnode list`、`rostopic list`、`rostopic echo -n 1 /joint_states`、`rosrun tf tf_echo base_link grasping_frame`。相机当前通过OpenCV打开，没有相机图像话题可供此launch验证。

### 平台手册中的摄像头排查

[手册PDF第266页](../../../homework/docs/references/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=266)给出`ls -l /dev/video*`及`cv2.VideoCapture(0)`的排查路线。原厂启动程序可能占用相机；仅在确认现场仍为该厂商镜像、脚本存在且需要结束原厂程序时，按手册执行`sh ~/whitebear/kill_YahboomArm.sh`。本次未运行该命令；摄像头可见不等于已发布ROS图像话题。

手册查系统镜像的资料盘位置为“白熊人工智能实验平台资料/开发环境/系统镜像/whitebear_nano_xxxxxx.img”（PDF第27页）。这提供恢复来源线索，归档不进行镜像烧录。

## 8. 实验结果索引

[实验结果.md](../1.3_experiment_results/%E5%AE%9E%E9%AA%8C%E7%BB%93%E6%9E%9C.md)；静态校验与当前工程缺陷见[静态检查报告.md](../../%E6%95%B4%E7%90%86%E8%AE%B0%E5%BD%95/%E9%9D%99%E6%80%81%E6%A3%80%E6%9F%A5%E6%8A%A5%E5%91%8A.md)。

## 9. 常见问题与解决方法

WSLg视口捕捉黑屏：既有记录保留了节点、话题和TF，计划在可见RViz或Jetson桌面补拍；离线预览图不能代替该证据。答辩报告写53个visual，当前文件和较新技术记录是68个，按版本分别保留。历史catkin_make成功日志对应原Linux路径，当前导出副本仍需重建CMake入口。主模型质量宏未展开、运行依赖未完整声明及实物对应关系均列为待处理事项。

## 10. 参考资料

本地来源：`source_notes/`中的原建模说明、模块实验报告及 `marm_description/README.md`。

- ROS URDF：http://wiki.ros.org/urdf
- Xacro：http://wiki.ros.org/xacro
- robot_state_publisher：http://wiki.ros.org/robot_state_publisher
- 原参考副本注明的Unitree仓库：https://github.com/unitreerobotics/z1_ros （noetic，提交d3bafd38fb48e805096da7abb0c19a15b636975d）；仅外观/组织参考。


新增本地来源：[DICE白熊平台用户手册（相关章节）](../../../homework/docs/references/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=19)；[平台手册核对与页码索引](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/%E5%B9%B3%E5%8F%B0%E6%89%8B%E5%86%8C%E6%A0%B8%E5%AF%B9.md)。
