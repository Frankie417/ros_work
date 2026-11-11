# 视觉目标识别与自动分拣

## 功能与文件

`1.1_code/week5/5.目标识别/week5.ipynb` 是独立颜色识别主Notebook；`1.1_code/week6/week6.ipynb` 是固定P4分拣主版本。CLI `week5_color_recognition.py` 和history中的Notebook为不同实验版本。原图、result、Mask及测试CSV在 `1.3_experiment_results`。

## 实现与参数

BGR→HSV→inRange→5×5开闭运算→外轮廓筛选，面积门限700px²。红色分两段H区间。独立识别：红H0～10/170～179、S≥90/V≥70；黄H18～38、S/V≥80；绿H40～90、S≥60/V≥35；蓝H95～135、S≥80/V≥50。

分拣独立阈值保留在week6：ROI=(240,210,440,390)，表示左上/右下角，即200×180像素。唯一目标连续5帧同色后进入BUSY，按颜色投桶，P4清空后重新READY；换色或多目标重新计数。MOVE_T=1.5s，夹爪0.5s。抓取位置固定P4，不用像素中心反算抓取XYZ。

## 运行

按 [根README](../../README.md) 部署Jetson的BASE目录、SDK和Notebook，运行 `python3 -m jupyterlab`。独立识别打开week5主Notebook；自动分拣打开week6，按顺序初始化并启动界面，确认单块放置在P4。

CLI参考可在仓库根目录运行，参数由源码parse_args定义：

```bash
python3 'week5/5.目标识别/week5_color_recognition.py' --help
```

CLI绿色V下限及记录判据与主Notebook不同，不能用其统计替换28次实验结果。相机扩展代码在根目录 `arm5dof_visual_grasping`，其默认config路径与随包vconfig需显式对应，当前固定P4验收不依赖这条扩展链路。

## 实验结果

主目标颜色28/28正确；按“唯一有效目标且颜色正确”通过22/28≈78.6%。最终固定顺序两轮分拣8/8实际入桶，无重复抓取。调试CSV中的P4清空不能单独当作入桶成功。

![同帧识别实拍](1.3_experiment_results/figures/week5_evidence/20261019_144315_891538_result.png)

## 已知问题

光照、背景伪轮廓和同物块裂成多轮廓仍影响识别；尚未验收任意位置抓取、严格乱序和统一ROS图像订阅。当前只检查文件结构和语法，未打开摄像头或执行分拣。详细原参数和版本差异见 `1.2_readme/README.md`。


[返回项目首页](../../README.md) · [历史技术说明](1.2_readme/README.md)
