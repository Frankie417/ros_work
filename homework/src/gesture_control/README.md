# 手势识别与机械臂交互

Windows识别手势，经候选、确认和一次性准备互锁，通过HTTP JSON向Jetson请求开爪、闭爪、Home和软件停止。识别和执行分别运行。

| week7下文件 | 用途 |
|---|---|
| gesture_usb/app_usb.py | Tkinter界面、相机、动作调度和记录 |
| recognition.py（gesture_usb内） | MediaPipe与Three/OK几何规则 |
| control.py、network_link.py | 候选/armed/互锁，TOKEN/session/epoch及心跳 |
| receiver_usb.py | Jetson HTTP接收和Engine，默认模拟 |
| arm_interrupt.py | 可取消轨迹、反馈保持和SimulatedArm |
| test_usb.py | 模拟器与回环网络测试 |
| models/gesture_recognizer.task | 官方模型，与gesture_usb同级 |

## 方法和门限

One/Two/Five映射Pointing_Up/Victory/Open_Palm；Three/OK根据21点几何。伸直比1.85、小指弯曲1.55、OK环距/掌宽≤0.42，分数≥0.70且单手通过。选择/OK连续3帧，Five连续2帧，候选8s失效，执行消费一次armed。

客户端约0.25s心跳，服务端0.1s检查，1.5s超时取消。停止事件在轨迹回调和写包前检查，用实测角覆盖未完成目标；相邻变化≤0.5°、距目标≤1°连续两次确认保持。未测量实体制停时延。

## Windows识别端

Windows11、Python3.11、MediaPipe Tasks、OpenCV、NumPy、Pillow、Tkinter。homework根目录：

```powershell
py -3.11 -m venv .venv-gesture
.venv-gesture\Scripts\python.exe -m pip install -r requirements-gesture.txt
.venv-gesture\Scripts\python.exe src/gesture_control/week7/gesture_usb/app_usb.py
```

模型从recognition.py自身位置定位。无需原week7目录。新截图、CSV、事件流写到results/gesture_control/runtime。

## Jetson接收端

Python3及HTTP标准库；真机模式另需NumPy、pyserial和共享SDK。选择一种模式：

```bash
python3 src/gesture_control/week7/gesture_usb/receiver_usb.py
python3 src/gesture_control/week7/gesture_usb/receiver_usb.py --hardware --sdk-dir "$PWD/sdk/arm5dof_python_uservo" --arm-port /dev/ttyTHS1
```

Windows填http://192.168.55.1:8765与当次TOKEN。解除停止→准备→One/Two/Three选择→OK执行；Five请求停止。接收器重启后重新连接，恢复后重新解除停止和准备。

## 结果、图片和视频

报告10轮中9触发、1低分Five正确拦截、0误触发。报告22条done含21次hardware及1次simulation，原回执尚未提供；现有10项软件测试本次通过。

- [机械臂反应视频](../../results/gesture_control/videos/手势识别控制机械臂视频%28机械臂反应%29.mp4)：23531367字节、960×544、约57.968s。
- [Windows桌面录屏](../../results/gesture_control/videos/手势识别控制机械臂视频%28Windows桌面录屏%29.mp4)：120931940字节、2558×1528、约59.233s。
- [10轮报告转录](../../results/gesture_control/data/week7_报告10轮表转录.csv)和[图像索引](../../results/README.md)。

两段视频保持完整字节，已检查容器和首帧，并抽查约10%/55%时点，画面分别为机械臂现场和Windows手势界面；与原10轮表、22条回执的时间对应仍待核实。原VID和事件记录缺失；完整手势选物块、选投放区后的搬运尚未实现。

```bash
python -B src/gesture_control/week7/gesture_usb/test_usb.py
```

测试为模拟器和127.0.0.1回环HTTP，不等同于实体重测。

[返回项目](../../README.md) · [项目验证](../../docs/项目验证报告.md)
