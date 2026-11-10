# 手势识别与交互搬运


手册核对：[平台手册核对与页码索引](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/%E5%B9%B3%E5%8F%B0%E6%89%8B%E5%86%8C%E6%A0%B8%E5%AF%B9.md)。以下补充采用手册PDF顺序页码，厂商示例与本项目运行记录分别标注。

## 1. 模块简介

保留本机MediaPipe识别、去抖状态机、USB gadget网络HTTP、Jetson接收与可取消SDK执行器。主版本选 `week7/gesture_usb`：app_usb实际导入control、network_link、recognition，receiver_usb导入arm_interrupt；其他目录中的脚本经SHA-256核对相同。Notebook为早期独立/网络实现，接口不混用。对应课程手势搬运基础25分；当前主版本完成指令控制接口，尚无对象选择/目标选择与完整搬运任务链。

## 2. 功能需求

| 功能 | 输入 | 输出 | 实现状态 |
|---|---|---|---|
| 五种手势识别 | 本机相机帧 | 标签、分数、来源、通过状态 | 有源码、报告截图 |
| 去抖/候选/确认 | 连续识别结果 | 单次动作命令 | 源码完整，报告记载测试 |
| BUSY与停止锁 | 本机/远端状态 | 拒绝重入或停止 | 双侧实现；实测原始事件日志待补 |
| 夹爪开合/回零 | One/Two/Three+OK | SDK动作 | 报告记载21条hardware回执，当前无对应原始日志 |
| Five运动中制停 | Five×2、按钮或心跳超时 | cancel+hold | 有源码与报告画面；interrupted回执缺失 |
| 对象选择、目标选择、抓取搬运投放 | 物体与目标任务 | 完整搬运 | 主命令集仅open_gripper/close_gripper/home，待实现/验证 |

## 3. 技术原理

MediaPipe GestureRecognizer使用官方float16模型，检测21个归一化手部关键点（0为腕；4/8/12/16/20为五指尖；5/9/13/17为四指根部），骨架用于绘制与几何判定。模型官方类别Pointing_Up→One、Victory→Two、Open_Palm→Five。

几何距离采用 `d(a,b)=sqrt(((x_a-x_b)·W/H)^2+(y_a-y_b)^2)`，W/H补偿画面宽高比，x/y为归一化像素平面坐标。每指伸直比 `r=d(指尖,根部)/max(d(近端,根部),1e-6)`；OK环距 `c=d(4,8)/max(d(5,17),1e-6)`。

先判OK：c≤0.42且中/无名/小指r≥1.85；再判Three：食/中/无名指r≥1.85且小指r≤1.55；否则映射三个官方类别。Three/OK分数为 `min(0.99,0.70+max(0,余量))`，余量是离判定边界的最小距离，**不是模型分类概率**。统一要求分数≥0.70且仅一只手；num_hands=2用于发现并拒绝多手。检测/存在/跟踪阈值均0.5。

状态机输入为label/score，低分作None。先检查Five连续2帧，再检查stopped/busy/armed；选择与OK都需连续3帧。WAIT→SELECT→CONFIRM→EXECUTE，CONFIRM同帧瞬时经过；候选8s未确认失效。执行消费armed，必须手动准备下一条，持续保持OK不会重发。Five停止可在BUSY且未准备时触发。

网络用HTTP JSON，不是本机到Jetson的串口：Micro-USB形成网卡，服务地址通常为 `http://192.168.55.1:8765`（Jetson端），8888为JupyterLab。服务每次生成TOKEN与session；epoch使停止前已排队的旧命令失效；动作使用UUID并保留结果避免同ID重复执行。心跳每0.25s，接收端约0.1s巡检，超过1.5s停止；单次HTTP超时0.8s。stop使用独立请求，不等待动作锁。

## 4. 代码结构

```text
1.1_code/week7/
├── gesture_usb/
│   ├── app_usb.py、recognition.py、control.py
│   ├── network_link.py、receiver_usb.py、arm_interrupt.py
│   ├── test_usb.py、start_usb_gesture.bat
│   └── USB网络版使用说明.md
├── models/gesture_recognizer.task     recognition.py固定相对路径
├── gesture_recognizer.task            旧发送Notebook固定相对路径
├── week7_gesture_control.ipynb
├── week7_laptop_gesture_sender.ipynb
├── week7_jetson_arm_receiver.ipynb
└── week5_gesture_recognition.ipynb
```

两个模型同SHA-256，保留两条资源路径是为兼容原入口。未复制缺失的`.venv-gesture`；bat中相对路径原样保留，因此不能直接双击视为已部署。

## 5. 核心代码说明

| API | 输入 → 处理 → 输出/返回 |
|---|---|
| `创建识别器(模式)` | 模型/RunningMode → MediaPipe选项 → 识别器；模型缺失抛FileNotFoundError |
| `识别画面(图像,识别器,时间戳=None)` | BGR帧 → RGB推理/几何规则 → 类别/置信度/通过/来源/官方分数/关键点字典 |
| `Controller.feed(label,score,now=None)` | 标签分数 → 去抖与状态迁移 → 动作字符串、stop或None |
| `arm/clear/done` | 生命周期事件 → 一次性准备/解除/复归 → bool或状态变更 |
| `App.tick` | 相机 → 识别/标注/状态机 → UI与异步send；after(100)是调度间隔非固定帧率 |
| `NetworkLink.request(command,timeout=15)` | 命令 → 独立HTTP/结果轮询 → 最终JSON或异常 |
| `Engine.submit(id,command,epoch)` | 会话有效的三种动作 → 心跳/BUSY/停止校验 → running记录并投递单动作线程 |
| `Engine.stop(reason)` | 停止原因 → cancel、epoch递增、hold_pending → 状态字典 |
| `InterruptibleArm.execute(command)` | 三种命令 → SDK开/闭/home并等待停稳 → 正常None，失败抛异常 |
| `InterruptibleArm.hold()` | 新鲜舵机反馈 → 当前角覆盖目标 → hold_sent/feedback_stable字典或异常 |

One→open_gripper；Two→close_gripper；Three→home；OK确认；Five停止。home调用 `set_tool_pose(pose_name='home',T=2.0,is_soft_move=True,callback=check)`。停止检查嵌入轨迹回调与运动写包前；hold逐舵机读取当前角，用interval=0/power=0覆盖未完成目标，再要求距目标≤1°、相邻反馈变化≤0.5°连续2次，观察窗口1.5s。以上为**程序判据**，没有本次整理产生的真机测量值。

默认Engine使用SimulatedArm；只有--hardware才创建真实串口对象，舵机ID须0～5。返回 `done/interrupted/error` 与 `simulation/hardware` 区分流程结束和设备模式，done不能替代物块夹取/落桶的外部确认。

## 6. 环境与依赖

报告记Windows11/Python3.11.9；本机依赖OpenCV、NumPy、MediaPipe Tasks、Pillow、Tkinter。Jetson接收器注明Python3.6+兼容分支，实体SDK还需NumPy/pyserial及config，不需要在Jetson安装MediaPipe。模型随代码归档；确切MediaPipe/OpenCV/SDK版本【待补充：本机与Jetson依赖锁定清单】。

本机bat所需 `.venv-gesture` 不存在，实体SDK `arm5dof_uservo.py`、`uservo.py` 与config均缺失。报告提到的 `week7_gesture_control.py` 当前不存在，实际可见主入口是app_usb.py；不能引用缺失包装器作为已可用命令。

### 手册对网络与实体侧的补充

[手册PDF第29页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=29)～[手册PDF第30页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=30)、[手册PDF第47页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=47)确认Micro-USB gadget网络中`192.168.55.1`是Jetson端；`:8888`是JupyterLab。本项目`:8765`、TOKEN/session/epoch是新增USB程序协议，不是手册规定的服务；不能把Jupyter密码用于代替该程序生成的TOKEN。

[手册PDF第214页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=214)～[手册PDF第219页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=219)补上pyserial、uservo、/dev/ttyTHS1、115200/8N1和ID0～5的厂商依据，与接收器ID检查一致。手册Arm5DoF标定资料在PDF第226～230页；现场仍需恢复对应config和完整SDK。手册旧手势/Arm_Lib案例不提供本项目MediaPipe、三帧确认或hold实测结果。

## 7. 安装和运行

以下命令按源码参数核对，**待验证**；本次未启动GUI、网络服务或机械臂：

```powershell
# 本机：进入 1.1_code/week7/gesture_usb，使用已恢复的匹配环境
python app_usb.py
```

Jetson仅上传receiver_usb.py和arm_interrupt.py即可进行接收端演练：`python3 receiver_usb.py`，默认simulation。把当次TOKEN填入本机界面，连接并查询，解除停止、准备、选择、OK。旧Notebook服务不提供session/epoch/token这一套协议，不能与新NetworkLink混接。

原说明中的真机命令（待在现场补齐SDK并核对后使用，本次不执行）：

```bash
python3 receiver_usb.py --hardware --sdk-dir '/home/jetson/Notebook/4.机械臂OpenCV视觉处理实验' --arm-port /dev/ttyTHS1
```

原 `test_usb.py` 使用模拟器及回环网络；它是现有测试程序，本次未执行，其结果不计入真机成功率。静态检查只做AST/XML/路径与哈希校验。

## 8. 实验结果索引

[实验结果.md](../1.3_experiment_results/%E5%AE%9E%E9%AA%8C%E7%BB%93%E6%9E%9C.md)。主要图像来自实验七原报告；实验5中重复引用的手势截图不重复列作不同实验。当前唯一events.jsonl属于旧分拣连接异常，归模块3。

## 9. 常见问题与解决方法

报告记录Invalid token：每次服务重启需复制当次TOKEN并重新连接；摄像头被占用时关闭旧窗口并选对设备。Three/OK临界手形互扰时按已定几何阈值规范摆手，现代码先OK后Three。Five截图分数0.60未过0.70阈值，不能作为成功制停证据。报告记断线触发看门狗制停，当前缺少带时间戳的原始反馈日志。软件停止依赖识别/网络/调度/串口，不能给出未测量的固定制停延迟。

## 10. 参考资料

实验七报告、原USB网络版使用说明及实验5第5.4节；MediaPipe官方指南：https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer 。模型下载源由旧发送Notebook给出：https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task 。


新增本地来源：[DICE白熊平台用户手册（相关章节）](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=30)；[平台手册核对与页码索引](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/%E5%B9%B3%E5%8F%B0%E6%89%8B%E5%86%8C%E6%A0%B8%E5%AF%B9.md)。
