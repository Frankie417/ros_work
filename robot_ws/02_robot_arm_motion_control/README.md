# 机械臂运动控制

## 功能与文件

`1.1_code/week3/week3.ipynb` 为四层方块归位，`1.1_code/week4/Week4_堆叠.ipynb` 为按层堆叠；原始同名版本保留在根目录week3、week4。SDK使用根目录 `arm5dof_python_uservo`。原始结果和报告在 `1.3_experiment_results`，提交快照在根目录第11组提交包中。

## 核心实现与参数

示教点依次完成开爪、接近、下降、夹持、抬升、Home转移、放置与退出。位置单位mm，姿态表单位°，调用SDK时转rad。归位MOVE_T=1.5s、GRIPPER_T=1.0s、最低抓取Z=10mm、放置上方高度增量55mm；堆叠MOVE_T=0.8s、GRIPPER_T=0.5s。

归位参数记录保留 Roll=85763.7°→83.7°→90°的现场修正。原week3源码目标顺序P0→P2→P6→P8，与最终报告记载P6→P8→P2→P0不同；保持各自来源，不自动覆盖。堆叠来源顺序P0→P2→P8→P6，放置高度33、60、87、112mm。

## 安装与运行

按 [根README](../../README.md) 的Jetson步骤将完整SDK和Notebook复制到现场BASE目录。SDK需NumPy、pyserial及完整config；构造器默认从工作目录 `config/z_error_polyfit.txt` 读取高度补偿。

```bash
cd '/home/jetson/Notebook/4.机械臂OpenCV视觉处理实验'
python3 -m jupyterlab
```

在Jupyter中打开 `week3.ipynb`，先保持 `DRY_RUN=True` 检查点位；堆叠打开 `Week4_堆叠.ipynb`，依次按实际层次运行对应动作Cell。堆叠没有全局预览开关，不能用“运行全部”作为静态检查。

## 实验结果

三轮各4块：归位11/12≈91.7%，堆叠10/12≈83.3%；两项完整成功轮数均2/3。详见 [原始结果](1.3_experiment_results/实验结果.md)。

## 已知问题

SDK配置与实验现场版本、标准姿态采样和源码/报告顺序仍需对应核实。高层退出间隙较小，后续调整需另做对照实验。当前Windows环境未连接串口或执行机械动作。历史技术分析保留在 `1.2_readme/README.md`，其中旧采样数据不覆盖最终报告修订值。


[返回项目首页](../../README.md) · [历史技术说明](1.2_readme/README.md)
