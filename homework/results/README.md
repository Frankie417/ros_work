# 实验结果与证据索引

统计沿用原报告与原始CSV。本次软件模拟和合成图验证另列在项目验证报告，不增加实体实验次数。转录表、自动日志与人工观察分别标注。

| 实验名称 | 报告章节 | 源代码路径 | 证据文件 | 证据来源 |
|---|---|---|---|---|
| Z1建模与坐标 | 3.1～3.3、5.1 | [模型模块](../src/robot_modeling/README.md) | [RViz图3-3](robot_modeling/images/final_report/image5.png)、[模型图3-1](robot_modeling/images/final_report/image3.png)、[连接图3-2](robot_modeling/images/final_report/image4.png) | 从主报告word/media原样提取；连接图/离线图仅作模型说明 |
| 模型预览和TF | 3章 | [当前工作空间](../src/robot_modeling/arm2026_ws/README.md) | [预览](robot_modeling/previews/)、[TF图](robot_modeling/frames.pdf) | 原工作空间，离线预览与历史验证分开理解 |
| 归位 | 4.3、5.2 | [week3.ipynb](../src/arm_motion_control/week3/week3.ipynb) | [数据](motion_control/data/week3_报告测试表转录.csv)、[视频](motion_control/videos/11组_第三章_实验视频.mp4)、[图片](motion_control/images/) | 原周报告转录、原录像和报告图片；11/12 |
| 堆叠 | 4.3、5.2 | [Week4_堆叠.ipynb](../src/arm_motion_control/week4/Week4_堆叠.ipynb) | [数据](motion_control/data/week4_报告测试表转录.csv)、[视频](motion_control/videos/11组_第四章_实验视频_week4.mp4) | 原周报告转录及原录像；10/12 |
| HSV识别 | 4.4、5.3 | [week5.ipynb](../src/vision_sorting/week5/5.目标识别/week5.ipynb) | [28次CSV](vision_sorting/data/week5_test_records.csv)、[60张raw/result/masks](vision_sorting/images/week5_evidence/) | 原相机数据；主色28/28、严格22/28 |
| P4分拣 | 4.5、5.4 | [week6.ipynb](../src/vision_sorting/week6/week6.ipynb) | [8次人工表](vision_sorting/data/两轮8次分拣记录.csv)、[44条日志](vision_sorting/data/week6_action_log.csv)、[投桶图](vision_sorting/images/report_week6/) | 人工入桶8/8；日志不等于入桶，尚未逐条绑定 |
| 手势基础交互 | 4.6、5.5 | [app_usb.py](../src/gesture_control/week7/gesture_usb/app_usb.py) | [10轮转录](gesture_control/data/week7_报告10轮表转录.csv)、[报告图片](gesture_control/images/report_week7/) | 原报告9触发、1拦截、0误触发；部分手势由回执反推 |
| 手势实体反应 | 4.6、5.5 | [接收与动作程序](../src/gesture_control/week7/gesture_usb/receiver_usb.py) | [机械臂反应视频](gesture_control/videos/手势识别控制机械臂视频%28机械臂反应%29.mp4) | 用户新增原MP4，约57.968s，原报告轮次对应待核实 |
| 手势界面与识别 | 4.6、5.5 | [识别程序](../src/gesture_control/week7/gesture_usb/recognition.py) | [Windows录屏](gesture_control/videos/手势识别控制机械臂视频%28Windows桌面录屏%29.mp4) | 用户新增原MP4，约59.233s，原回执同步关系待核实 |
| 软件互锁和停止 | 4.6、5.5方法 | [test_usb.py](../src/gesture_control/week7/gesture_usb/test_usb.py) | [本次测试输出](../docs/软件测试输出.txt) | 模拟器及回环HTTP，非新增真机记录 |

主报告：[课程项目报告.docx](../reports/课程项目报告.docx)。所有原周报告位于[original_experiments](../reports/original_experiments/)。视频逐文件大小、时长、分辨率及SHA-256见[视频核对](../docs/补充视频检查.json)和[文件清单](../docs/文件清单.csv)。

原始data/images/videos保持字节，新运行只写runtime。完整手势原回执和原VID未提供，保持待核实。
