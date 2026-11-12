# 机械臂运动控制

用共享实体SDK完成反馈标定、关节/夹爪控制、末端位姿、四方块归位和四层堆叠。SDK提供正逆运动学、Minimum Jerk轨迹和串口协议；课程Notebook组织示教点及抓放步骤。

| 入口 | 功能 |
|---|---|
| [01.机械臂关节标定.ipynb](basic_control/01.机械臂关节标定.ipynb) | 两姿态采样、calc_kb；只输出K/B |
| [02.机械臂关节弧度控制.ipynb](basic_control/02.机械臂关节弧度控制.ipynb) | set_joint_angle_list及软运动 |
| [03.机械爪测试.ipynb](basic_control/03.机械爪测试.ipynb) | 30°/0°和开闭接口 |
| [04.末端位姿控制.ipynb](basic_control/04.末端位姿控制.ipynb) | set_tool_pose、get_tool_pose |
| [week3.ipynb](week3/week3.ipynb) | Pose、pick_and_place、run_unstack_sort |
| [Week4_堆叠.ipynb](week4/Week4_堆叠.ipynb) | validate_all_poses、pick_and_stack、run_single_block |

## 方法和参数

动作经过张爪、抓取上方、下降夹持、抬升、Home转运、放置、松爪和退出。位置mm，参数表角度°，调用SDK时转rad。归位MOVE_T=1.5s、GRIPPER_T=1s、最低Z=10mm、放置上方增量55mm；第2/3层Roll保留90°修正。代码目标顺序P0/P2/P6/P8，未改成报告中的P6/P8/P2/P0。

堆叠来源P0/P2/P8/P6，放置高度33/60/87/112mm，运动0.8s、夹爪0.5s、释放角0.40rad。每块有独立位姿；在构造硬件对象前检查20项IK。实体SDK高度补偿保持0.1405/-33.9720，不与报告的另一组系数混用。

## 环境与步骤

Jetson/Linux、Python3、NumPy、pyserial、Jupyter。homework根目录：

```bash
python3 -m pip install -r requirements-jetson.txt
python3 -m jupyterlab
```

打开表中课程Notebook。它们从当前目录向上定位project_paths.py和共享SDK，构造器显式传入其config。归位依次加载Cell2/4/5/7/9，入口run_unstack_sort，默认DRY_RUN=True。堆叠Cell2加载参数和纯IK，Cell4定义动作，Cell6/8/10/12分别运行run_single_block(0/1/2/3)。这些动作Cell会控制真机，应按层执行。

基础控制副本保留原文件名；SDK中的同名示例作为来源快照保留。报告整套±20°/0.35s演示未找到完全对应的串联脚本。

## 结果与证据

归位三轮4/4、3/4、4/4，共11/12；堆叠2/4、4/4、4/4，共10/12。两项均2/3完整成功轮次。统计来自原报告和转录CSV，未与逐块视频时间和源码哈希完全绑定。

[归位视频](../../results/motion_control/videos/11组_第三章_实验视频.mp4) · [堆叠视频](../../results/motion_control/videos/11组_第四章_实验视频_week4.mp4) · [数据与截图](../../results/README.md)

SDK的is_wait/wait名称问题、报告与配置的K/B差异和历史IK版本差异见[待核实事项](../../docs/待核实事项.md)。

[返回项目](../../README.md) · [项目验证](../../docs/项目验证报告.md)
