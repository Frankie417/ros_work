# 项目检查记录

静态检查由check_project.py生成；不导入或执行机械臂算法。

| 检查对象 | 数量 |
|---|---:|
| markdown_local_links | 613 |
| xml_files | 101 |
| python_files | 111 |
| notebooks | 77 |
| notebook_code_cells | 545 |
| ipython_magic_cells | 8 |
| current_urdf_links | 11 |
| current_urdf_joints | 10 |

原始源码、Notebook、CSV/JSONL及模型资源共225个文件与整理前SHA-256一致。高置信度密钥扫描命中0项；仅报告命中路径和类型，不打印值。普通password字面量候选列入下表，人工区分示例、历史输出和真实配置。

## 问题及历史差异

| 类型 | 文件 | 说明 |
|---|---|---|
| 无 | — | 本次静态检查未发现问题 |

历史清单记录旧版模型、旧路径和旧复制哈希，不重写以伪造历史一致性。本次清单及file_moves.csv是整理后的对应依据。IPython的!/%命令按Notebook专用语法单独计数，不当作普通Python错误。

## 当前环境未测试

当前为Windows文件整理环境，未执行Linux catkin/ROS/GUI、Jetson串口/相机/实体机械臂或Windows实时摄像头识别。未新增实体成功率或停止时延数据。模型URDF的XML与父子连杆引用已静态检查；这不能代替硬件和ROS运行验证。

模拟接收器与状态机的已有测试结果另见simulation_test.txt；若没有该文件，表示尚未执行。依赖版本与第三方许可TODO保留为待核实项，不填造版本或许可证。

## 已执行的软件检查

现有手势模拟和回环网络测试10项通过，四色合成图识别测试通过，见simulation_test.txt。均不计作新增实体实验结果。

Xacro 2.1.1离线展开主版及课程版，均为11 Link、10 Joint、57 visual、13 collision；catkin_pkg成功解析Package，Joint父子引用完整。包查找静态解析到当前目录，不代表ROS运行测试。结果见xacro_check.json。

可用 `python -m pip install --target tmp/semester_qa_deps xacro catkin_pkg` 准备临时工具，再运行 `python docs/maintenance/check_xacro.py`。
