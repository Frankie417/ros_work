# 视觉目标识别与自动分拣


手册核对：[平台手册核对与页码索引](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/%E5%B9%B3%E5%8F%B0%E6%89%8B%E5%86%8C%E6%A0%B8%E5%AF%B9.md)。以下补充采用手册PDF顺序页码，厂商示例与本项目运行记录分别标注。

## 1. 模块简介

归档独立HSV识别、目标像素中心、固定P4抓取与四色投桶。`week5.ipynb`是第5周主入口；`week6/week6.ipynb`是与第6周报告对应的固定P4自动版本。其他同名分拣程序保留在history，分别标注映射路线和验证状态。对应课程视觉与分拣基础15分。

## 2. 功能需求

| 功能 | 输入 | 输出 | 实现状态 |
|---|---|---|---|
| BGR→HSV与四色分割 | USB相机OpenCV帧 | Mask、类别 | 有源码、60张同帧证据、28条测试 |
| 像素目标定位 | 轮廓外接矩形 | 像素中心 | 已实现；不是矩法重心 |
| 相机到机械臂坐标映射 | 像素/标定参数 | 工作空间坐标 | 主版本不使用；历史路线依赖缺失文件 |
| 颜色到垃圾桶映射 | red/yellow/green/blue | 固定桶上方位姿 | 已实现，表与代码可核对 |
| 固定P4抓取投放 | 连续5帧唯一同色 | 抓放、回零、拍摄位 | 报告/人工CSV记8/8成功 |
| 任意像素位置抓取 | 标定转换后的物体坐标 | 随目标移动的抓取点 | 【待补充：标定文件和对应联调证据】 |
| ROS图像消息接入 | sensor_msgs/Image | BGR帧 | 当前主版本直接VideoCapture，未实现ROS订阅 |

## 3. 技术原理

相机帧先裁ROI，再 `cvtColor(...,COLOR_BGR2HSV)`，用 `inRange` 按H/S/V上下限生成二值掩膜。红色两区间用bitwise_or合并；5×5全1核先MORPH_OPEN去噪、再MORPH_CLOSE填小孔；`findContours(RETR_EXTERNAL,CHAIN_APPROX_SIMPLE)`提外轮廓，`contourArea≥700`保留目标。

`boundingRect`产生(x,y,w,h)，目标中心为 `u=x+floor(w/2)+offset_x`、`v=y+floor(h/2)+offset_y`，u/v是完整画面像素坐标，offset是ROI起点。它是外接矩形中心，并未计算图像矩 `m10/m00`。

第5周主Notebook阈值如下，H取0～179，S/V取0～255：

| 色 | H | S | V |
|---|---|---|---|
| 红 | 0～10 ∪ 170～179 | 90～255 | 70～255 |
| 黄 | 18～38 | 80～255 | 80～255 |
| 绿 | 40～90 | 60～255 | 35～255 |
| 蓝 | 95～135 | 80～255 | 50～255 |

第6周独立阈值为：红S≥80/V≥50，黄S≥80/V≥60，绿S≥60/V≥35，蓝H90～135/S≥75/V≥45。不能将两组配置混作同一标定。

第6周ROI=`(240,210,440,390)`的语义是(x1,y1,x2,y2)，范围200×180像素；第5周ROI为(x,y,width,height)，默认None。第6周识别中心用于日志，**抓取XYZ固定为P4**，没有把(u,v)换算为机械臂坐标，因此无需主版本中不存在的单应矩阵标定。

决策：READY中唯一目标连续5帧同色→先置BUSY→动作线程→RESET→检测为空后READY；无目标、多目标、换色都会中断确认。只抑制重复任务，不保证物块入桶。停止预览只设置退出事件，正在执行的抓放不会立即被该按钮中断。

### 与手册示例的对应

[手册PDF第266页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=266)～[手册PDF第269页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=269)确认平台是随臂USB摄像头、VideoCapture(0)和ipywidgets显示路线，支持当前代码在抓放后恢复capture_image再检测的设计。手册PDF第31页还说明出厂大程序可能占用摄像头；现场核实占用与镜像后按第266页关闭原厂程序，本次未执行。

[手册PDF第439页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=439)～[手册PDF第445页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=445)介绍多视角HSV调节和阈值文件保存，可用于解释光照标定；但这些代码使用dofbot_config/Arm_Lib，阈值与当前项目不同，未复制覆盖。第446～448页按颜色调用固定区域抓放，也不能补证当前历史版本的camera.py/image2workspace.py或任意像素位置标定。手册未提供这些当前接口的完整配置。

## 4. 代码结构

```text
1.1_code/
├── week5/5.目标识别/
│   ├── week5.ipynb                 主入口，独立实现
│   ├── week5_color_recognition.py  CLI历史入口
│   ├── week5_多面投票识别版.ipynb
│   ├── week5_多面投票识别修复版.ipynb
│   ├── self_test_week5.py
│   ├── test01.ipynb、test02.ipynb
│   └── 2.1.在OpenCV 中调用摄像头.ipynb、README.md
├── week6/week6.ipynb、bin_map.csv
└── history/week7/5.目标识别/
    ├── week6.ipynb、week6_color_garbage_sorting.ipynb
    ├── frank_week6.ipynb
    └── frank_week5 (1).ipynb、frank_week5(2).ipynb、week5_fixed.ipynb
```

测试与历史版本不合并覆写。颜色证据与CSV集中在本模块实验结果中，运行时会在源码原有默认目录生成新记录，不会把归档记录当作新实验。手势程序与模型统一在模块4。

## 5. 核心代码说明

| API | 输入 → 处理 → 输出 |
|---|---|
| `week5.detect_colors(frame)` | BGR帧 → HSV/Mask/轮廓 → (annotated,masks,detections) |
| `HsvColorRecognizer.detect(frame,roi=None)` | 帧/ROI → 同类识别 → 标注图、Mask字典、color/center/area/bbox列表 |
| `record_trial`（Notebook） | 真值颜色、检测列表、备注 → 要求唯一且同色 → 追加CSV并返回success/detected |
| `save_evidence` | 同帧raw/标注/Mask → 时间戳PNG → 文件路径 |
| `week6.detect_color(frame,colors=None,roi=None)` | 帧 → 固定ROI检测 → (detections,canvas,masks)，字段pixel/box/area |
| `checked_pose(arm,name,pose)` | xyz/pitch/roll → adjust_tool_posi、inverse_kinematic → 原pose；失败抛ValueError |
| `pose_from_values(values)` | mm与度 → Roll %360并转弧度 → (xyz,pitch,roll) |
| `run_pick_place(target)` | 目标color → 预检P4、home、桶、拍摄位并抓放 → “桶内待人工确认”的说明字符串 |
| `verify_p4_cleared(frame,color)` | 最新画面与原颜色 → 重新检测 → 仍有同色则报错 |

**原CLI与Notebook口径不同**：CLI绿色V下限仍为50，且record_trial只要求真值色出现在检测颜色集合；主Notebook为V≥35，并要求检测列表仅一个且颜色相符。28条CSV按主Notebook严格规则记录，不能用CLI规则覆盖它。

P4抓取位姿 `(200.2,-12.8,45.0,132.7°,179.0°)`，上方位姿 `(198.2,-12.8,75.0,132.7°,179.0°)`。代码注释仍提旧Roll=144.5°，实际参数变量为179°，以执行表达式为准。动作顺序：开爪→P4上方→下降→闭爪→抬升→home→桶上方→开爪→home→拍摄位。

| 色/桶 | X/mm | Y/mm | Z/mm | Pitch/° | 归一化Roll/° |
|---|---|---|---|---|---|
| 红/有害垃圾 |103.3|-132.5|175.1|104.0|159.6|
| 黄/其他垃圾 |219.0|99.8|175.6|100.0|169.9|
| 绿/厨余垃圾 |122.8|114.8|172.8|104.0|159.6|
| 蓝/可回收垃圾 |207.8|-141.3|173.3|99.5|169.9|

原始Roll为-945200.4或137329.9，代码 `%360` 归一化。bin_map.csv是对照表，当前Notebook没有读取它来替换内嵌bin_map。

## 6. 环境与依赖

报告记Jetson/JetPack、USB UVC相机640×480、Python3.8、OpenCV、NumPy、Jupyter、ipywidgets；主Notebook元数据还记录Python3.11.9，说明元数据与报告环境并非同一环境证明。摄像头示例原输出提供OpenCV4.5.1记录，不能据此确定全部版本都使用4.5.1。

第6周BASE硬编码 `/home/jetson/Notebook/4.机械臂OpenCV视觉处理实验`，需要该处 `arm5dof_uservo.py`、uservo/串口依赖与 `config.ARM_POSE_DICT`、标定文件。历史坐标映射版本还依赖 `camera.py`、`image2workspace.py` 与相机标定文件，当前均缺失。完整版本清单【待补充：JetPack、OpenCV、NumPy及实体SDK精确版本】。

厂商参考环境见[手册PDF第19页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=19)、[手册PDF第23页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=23)：Jetson Nano/Ubuntu18.04，介绍JetPack4.4/L4T32.4.3。它补充平台背景，现场Python3.8.10及OpenCV4.5.1记录仍独立保留；实际镜像是否升级需在实验箱核对，不强行统一为手册版本。

## 7. 安装和运行

按主Notebook恢复课程环境后，在 `1.1_code/week5/5.目标识别` 启动 `jupyter notebook week5.ipynb`，逐格配置→函数→离线自检→相机探测→实时界面；该命令仅依据入口核对，**待验证**。原CLI示例（待验证）为 `python week5_color_recognition.py --camera 0 --roi 0,285,640,195`；使用前应理解前述阈值与评分口径差异。

第6周应在原Jetson SDK目录打开归档Notebook，确认BASE/config与设备一致，逐格运行；点击“启动预览”会先调用move_to_capture实际运动。该版本无纯预览硬件隔离，不能作为本次静态检查入口。主版本用VideoCapture(0)而不强制capture.set；CLI会设置宽高/FPS，是不同打开策略。

## 8. 实验结果索引

[实验结果.md](../1.3_experiment_results/%E5%AE%9E%E9%AA%8C%E7%BB%93%E6%9E%9C.md)，包含28条原始CSV核对、60张同帧图、44条调试日志及8条人工分拣记录。[静态检查报告.md](../../%E6%95%B4%E7%90%86%E8%AE%B0%E5%BD%95/%E9%9D%99%E6%80%81%E6%A3%80%E6%9F%A5%E6%8A%A5%E5%91%8A.md)列出版本差异与依赖缺口。

## 9. 常见问题与解决方法

绿色正面V约40～48：Notebook把V下限从50降35；CLI仍保留50。背景伪轮廓与裂块使object_count>1，导致6条严格判定失败。摄像头打开无帧时原报告采用设备级v4l2验证、拔插和释放占用；主Notebook避免强制设置分辨率。第6周抓取/蓝桶逆解不可达已记录，当前蓝桶Pitch=99.5°，历史日志104.5°；缺少控制变量复验，不能断言仅此改动解决全部问题。

## 10. 参考资料

原week5/6报告、原README及ZIP内Ch5/Ch6任务要求；OpenCV官方说明：https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html 、https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html 。历史相机/映射库的发布来源厂商通用API/标定示例已补入手册索引；【待补充：当前camera/image2workspace工具与部署SDK的版本文档】。


新增本地来源：[DICE白熊平台用户手册（相关章节）](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=266)；[平台手册核对与页码索引](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/%E5%B9%B3%E5%8F%B0%E6%89%8B%E5%86%8C%E6%A0%B8%E5%AF%B9.md)。
