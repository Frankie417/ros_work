# 手势识别与交互控制

## 功能与入口

主入口是 `1.1_code/week7/gesture_usb/app_usb.py`（Windows识别界面）及同目录 `receiver_usb.py`（Jetson HTTP接收）。必须保留 `1.1_code/week7/models/gesture_recognizer.task` 与gesture_usb的相对位置。旧发送/接收Notebook保留原协议，不与新HTTP服务混用。

## 实现与参数

recognition.py使用MediaPipe预训练模型及关键点几何规则：伸直比值1.85，小指弯曲门限1.55，OK环距/掌宽≤0.42，类别分数门限0.70，要求单手。One/Two/Three分别选择张爪、闭爪、Home，OK确认，Five停止。

control.py管理WAIT/SELECT/EXECUTE与一次性准备标志；普通选择/确认连续3帧，Five连续2帧，候选8s失效。network_link.py通过HTTP携带会话和唯一动作ID；receiver_usb.py每0.1s检查心跳，1.5s超时取消。arm_interrupt.py在轨迹回调和写包前检查取消事件，再读取反馈角覆盖未完成目标，保持位置。几何分数不是模型分类概率。

## 安装与运行

Windows仓库根目录：

```powershell
py -3.11 -m venv .venv-gesture
.venv-gesture\Scripts\python.exe -m pip install mediapipe opencv-python numpy pillow
.venv-gesture\Scripts\python.exe robot_ws/04_gesture_recognition_and_interactive_manipulation/1.1_code/week7/gesture_usb/app_usb.py
```

Jetson仓库根目录，先选模拟接收或真机接收其中一种：

```bash
python3 robot_ws/04_gesture_recognition_and_interactive_manipulation/1.1_code/week7/gesture_usb/receiver_usb.py
python3 robot_ws/04_gesture_recognition_and_interactive_manipulation/1.1_code/week7/gesture_usb/receiver_usb.py --hardware --sdk-dir "$PWD/arm5dof_python_uservo" --arm-port /dev/ttyTHS1
```

真机SDK需NumPy与pyserial。界面填写8765端口及接收器本次TOKEN，解除停止→准备→选择→OK。重启后TOKEN和session变化，应重新连接。默认接收器为simulation，模拟模式不需要串口或MediaPipe。

## 实验结果

原报告10轮中9轮正确触发、1轮低分正确不触发，误触发0次。22条done回执含21条真机和1条接收端演练；未据此计作完整搬运。原始回执文件尚未补齐，结果依据见 [实验记录](1.3_experiment_results/实验结果.md)。

## 已知问题与检查

Three/OK临界手形会干扰；停止依赖识别、网络与串口，精确制停延迟未测。当前只实现基础动作，手势选物块和目标位置后的抓放任务待扩展。现有 `test_usb.py` 使用模拟器和本机回环网络，可独立验证互锁、心跳与取消，不代表实体实验。

从仓库根目录运行现有测试：

```bash
python robot_ws/04_gesture_recognition_and_interactive_manipulation/1.1_code/week7/gesture_usb/test_usb.py
```


[返回项目首页](../../README.md) · [历史技术说明](1.2_readme/README.md)
