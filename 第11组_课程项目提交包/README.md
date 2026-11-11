当前最终报告见 [规范化课程项目报告](../docs/reports/课程项目报告_最终修订版_格式规范化.docx)，当前运行入口见 [仓库README](../README.md)。

本目录及对应ZIP保留为2026-11-10的历史提交快照；下文中的分工、待补项和模型版本是当时状态，不作为当前工程说明。

# 机械臂颜色分拣与手势交互控制系统

第11组：方仲全、童忠焜、付思杰；班级24060911；课程代码S0610350。

先阅读根目录课程项目报告，再按技术模块查看源代码。报告依据原实验报告记录的数据、参数和效果；源码保持实际内容，差异集中保存在核对记录。分工暂不填写，报告中待补事项均为红色加粗。

## 提交目录

| 目录 | 内容 |
|---|---|
| 课程项目报告.docx | 独立课程报告，按背景、设计、实现、验证、分析与总结组织 |
| 源代码/01_机器人建模 | marm_description包、模型、Launch和RViz配置 |
| 源代码/02_运动控制 | 四方块归位、四层堆叠两个原样Notebook |
| 源代码/03_视觉分拣 | 主颜色识别、固定P4分拣、独立CLI参考 |
| 源代码/04_手势交互 | gesture_usb全套程序与同级models/模型 |
| 源代码/SDK | 真机库及配置、视觉标定与坐标映射参考 |
| 源代码/仿真参考 | 独立PyBullet实现，配置与真机库分别保留 |
| 实验数据 | 原CSV、颜色图像证据、手势10轮报告转录 |
| 核对记录 | 参数差异、原始报告、原文件映射及SHA-256 |

## 实际完成结果

归位11/12块次成功，堆叠10/12块次成功。颜色主目标28/28判断正确，综合单目标判据22/28通过；最终固定上料区分拣8/8成功。手势10轮中9轮正确触发、1轮低分正确拒绝，误触发0次；22条done回执包括21条真机与1条接收端演练。停止、心跳与互锁逻辑的10项自动测试按实验报告记载通过。

姿态无逆解已在实际调试中解决。配套归位Notebook的参数单元保留了原始Roll85763.7°→取模83.7°→可行边界90°的处理说明和修正值；调用单元把角度转换为rad。报告不把全部Pitch统一限为±90°。

## 环境与程序入口

### ROS模型

使用Ubuntu20.04和ROS1 Noetic。将marm_description放入独立catkin工作空间的src目录，安装xacro、joint_state_publisher_gui、robot_state_publisher和RViz后构建。加载ROS和工作空间环境，再运行：

```bash
roslaunch marm_description view_marm.launch model:=marm
```

固定坐标系为base_link，显示RobotModel和TF。该入口负责模型显示，不下发实体舵机命令。

### Jetson运动与分拣

依赖Python3、NumPy、pyserial、OpenCV、Jupyter、ipywidgets。真机SDK为源代码/SDK/arm5dof_python_uservo，config目录必须完整保留。原Notebook按课程现场目录查找SDK，因此部署时：

1. 将真机SDK内容整体放入现场课程SDK目录，保留config文件及许可证。
2. 将需运行的Notebook复制到该SDK目录作为运行副本，再通过Jupyter打开，确保内核工作目录能访问SDK/config。
3. 固定区域分拣Notebook原BASE是`/home/jetson/Notebook/4.机械臂OpenCV视觉处理实验`；按该现场目录部署SDK。其他位置部署时，应在另存的运行副本中配置路径，并另行记录修改，不覆盖本提交包的原始文件。
4. 归位默认DRY_RUN=True；堆叠有四个按层启动的执行单元。先核对现场姿态和路径，再分别启动需要执行的单元。

报告的归位顺序、堆叠Z补偿与归档副本有差异，见核对记录/实验参数与代码差异.csv。文件整理没有替换配置、改变顺序或用离线计算重新定义实验结果。

### Windows手势与Jetson接收

Windows识别端采用Python3.11.9及MediaPipe Tasks、OpenCV、NumPy、Pillow、Tkinter。在手势模块目录安装匹配依赖后启动：

```bash
python gesture_usb/app_usb.py
```

gesture_usb与models保持同级。原bat引用现场虚拟环境，移机时使用上面的明确入口。

Jetson在gesture_usb目录启动接收服务。网络演练与真机模式分开选择；真机入口为：

```bash
python3 receiver_usb.py --hardware --sdk-dir /现场SDK绝对路径/arm5dof_python_uservo --arm-port /dev/ttyTHS1
```

界面地址通常为`http://192.168.55.1:8765`，复制当次TOKEN连接，解除停止并准备后，One/Two/Three选择，OK确认，Five停止。Jupyter的8888端口与该服务不同。

### 相机映射与仿真参考

视觉参考代码在arm5dof_visual_grasping。Camera与Image2Workspace默认查找config，而随包资料放在vconfig；使用此扩展路线时，在运行副本显式传入vconfig路径并确认现场标定。当前分拣验收使用固定P4。

PyBullet参考保留自身README、URDF和STL。它的Z补偿、释放高度与轨迹步长和真机库不同，分别使用各自配置。

## 文件与数据核对

`核对记录/源代码与资料文件映射.csv`保存原始路径、提交路径及SHA-256，记录中的每份文件均按字节复制。`实验结论依据.csv`定位报告中的结果来源。源代码、模型、配置和原始实验数据没有为匹配报告而修改。

完整手势搬运中的对象选择、目标选择和自动抓放组合尚需扩展；本次已完成的交互范围为张爪、闭爪、回零与软件停止。综合演示视频、完整手势原日志与录像、现场环境版本及分工按报告红色项补充。
