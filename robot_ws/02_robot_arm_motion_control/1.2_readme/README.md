# 机械臂运动控制


手册核对：[平台手册核对与页码索引](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/%E5%B9%B3%E5%8F%B0%E6%89%8B%E5%86%8C%E6%A0%B8%E5%AF%B9.md)。以下补充采用手册PDF顺序页码，厂商示例与本项目运行记录分别标注。

## 1. 模块简介

归档四层方块归位与四方块堆叠Notebook，保留原始点位和动作逻辑。第一周报告补充单关节、多关节、夹爪与原始反馈数据；USB手势执行器由模块4统一保存，通过交叉引用复用。对应课程运动控制基础15分。

## 2. 功能需求

| 功能 | 输入 | 输出 | 实现状态 |
|---|---|---|---|
| 单/多关节运动 | 目标关节角 | 舵机运动 | week1报告记载完成；原控制源码缺失 |
| 点到点与多航点 | xyz、pitch、roll | 抓取—搬运—放置 | week3/4已有实现与报告 |
| 逆运动学预检 | 目标工具位姿 | 可达性、关节解 | week4调用SDK并保留IK OK输出 |
| 夹爪开合 | 开/闭、动作时间 | 夹取/释放 | 已有调用；夹持力未独立测量 |
| 四层归位 | 中央四层与四个目标 | 分区域放置 | 报告11/12成功；代码/报告顺序差异待核实 |
| 四方块堆叠 | 四个独立来源点 | 中央四层塔 | 报告10/12成功；逐Cell启动 |
| 精度评价 | 目标与实测位姿 | mm/°误差 | 【待补充：外部测量数据】 |

## 3. 技术原理

任务采用示教点位和课程SDK运动学，不在Notebook中重新实现完整正逆运动学。五参数位姿为 `(x,y,z,pitch,roll)`：位置单位mm，表中角度为°，调用SDK前用 `radians` 变为rad。第4周调用 `Arm5DoFKinematic().inverse_kinematic(x,y,z_adjusted,pitch,roll)` 返回关节解列表，空列表表示不可达，预检取最后一组解显示角度。该签名与模块3所用机械臂包装类的逆解接口不同。手册PDF第233～241页已补充该类Arm5DoF求解器的代码示例，几何原理可据此解释；当前部署SDK文件仍缺失，不能直接确认与手册示例逐字一致。

通用正运动学关系为 `T_0_tool(q)=∏T_i(q_i)`：q为各关节角，T_i为相邻坐标系变换，乘积顺序沿基座到工具。逆运动学求q使变换达到给定位姿。模块1的六转动关节教学模型尚未与本实体SDK统一，不能直接代入当作实物模型。

第一周反馈是舵机原始角，目标是标准关节角，需经各轴标定K/B映射。手册PDF第227～230页明确 `a_i=k_i·θ_i+b_i`：a为原始舵机角度（°），θ为关节角（rad），k单位°/rad，b单位°；有效且k非零时θ=(a-b)/k，不能将原始反馈与标准关节角直接相减。第4周从 `config/z_error_polyfit.txt` 读取K/B并在预检中使用 `z_adjusted=z+K·sqrt(x²+y²)+B`，x/y/z为工具位置、z_adjusted为补偿高度，K无量纲、B单位mm；这组径向高度补偿与前述关节标定不同。

### 手册给出的正逆运动学与标定依据

[手册PDF第233页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=233)～[手册PDF第241页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=241)给出Arm5DoF示例：5个姿态角命名为θ1/θ2/θ3/θ4/θ6；这里θ6只是求解器变量名，不表示舵机ID6。示例D1/A1/A2/A3/A4=70/0/80/76.15/185.4mm，手册标明仅供参考，未用于覆盖当前代码参数。

令θ23=θ2+θ3，θ234=θ2+θ3+θ4，ρ=A1+A2cosθ2+A3cosθ23+A4cosθ234，则x=ρcosθ1，y=ρsinθ1，z=D1-A2sinθ2-A3sinθ23-A4sinθ234；pitch=θ234+π/2，roll=θ6+π（按示例处理周期）。θ为rad，位置为mm，ρ为基座平面径向距离。逆解枚举基座方向、正负肘解并逐轴限位过滤，返回解列表；公式推导和每个符号见[平台手册核对与页码索引](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/%E5%B9%B3%E5%8F%B0%E6%89%8B%E5%86%8C%E6%A0%B8%E5%AF%B9.md)。

[手册PDF第229页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=229)的calc_kb给出k=(aA-aB)/(θA-θB)、b=aA-kθA，并把六通道结果存入config.py的JOINT2SERVO_K/B。week1第5通道两姿态原始值均3.1°，不足以建立手册要求的0→π/2可逆标定，须复核标准姿态及采样；不据此填造新K/B。

## 4. 代码结构

```text
1.1_code/
├── week3/week3.ipynb
└── week4/Week4_堆叠.ipynb
```

共享SDK应在Notebook工作目录，或其子目录 `2.机械臂实验/` 中。归档保留两本Notebook，不拆分函数。实物USB执行器在模块4 `1.1_code/week7/gesture_usb/arm_interrupt.py`，不再复制到这里。

## 5. 核心代码说明

| API | 输入 → 处理 → 输出/返回 |
|---|---|
| `Pose` | x/y/z/pitch_deg/roll_deg → 存储示教参数 → xyz列表与角度属性 |
| `zone_pose(name)` | P0/P2/P6/P8 → 平面点+Z补偿、姿态表 → Pose |
| `validate_parameters(start_block,end_block)` | 1～4的执行范围 → 检查数量/高度 → 正常无返回，错误抛异常 |
| `move_to(arm,pose,label)` | arm与Pose → 弧度转换、set_tool_pose → False时抛错 |
| `pick_and_place(arm,index,name,target)` | 顶到底索引0～3 → Approach/Pick/Lift/Home/Transfer/Place/Retreat/Home → 顺序执行 |
| `run_unstack_sort(...,dry_run=True)` | 1-based范围 → 参数检查/预览或真机序列 → 正常返回None |
| `validate_pose_ik` / `validate_all_poses` | 第4周位姿 → 高度补偿与逆解检查 → 不可达报错，已有输出记录关节解 |
| `pick_and_stack(arm,index)` | 来源/堆放层索引 → 抓取搬运和释放 → 单块堆叠 |
| `run_single_block(index)` | 0～3 → 预检、创建Arm对象、单块执行 → 每Cell单独启动 |

第3周实际 `TARGETS` 顺序为 **P0→P2→P6→P8**；报告描述P6→P8→P2→P0，不能视为同一执行配置。`MOVE_T=1.5s`、`GRIPPER_T=1.0s`、`MIN_PICK_Z=10mm`、放置上方Z增加55mm；抓取Z从顶到底为81.0/57.1/44.3/13.8mm，第二、三层Roll=90°。异常路径包含松爪和home调用，仍会动作。

第4周来源顺序P0→P2→P8→P6，分别堆到第1～4层；`MOVE_T=0.8s`、`GRIPPER_T=0.5s`。四个Cell各调用一次run_single_block，并非一键全塔；上层退出高度差只有5mm和1mm是报告分析的风险，尚无修改后对照测试。

SDK接口按调用处核对：`set_tool_pose(xyz,tool_pitch,tool_roll,T,is_soft_move=True,is_wait=True)`；False表示调用处认为无解/失败；其他成功返回语义待SDK确认。`gripper_open/close(T,is_wait=True)`执行开合，`home()`回预设位。其返回值未在这些Notebook中完整判断，不能据此推断物块已成功夹住。

### 手册底层API补充

[手册PDF第214页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=214)～[手册PDF第217页](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=217)：`uservo.UartServoManager`接收pyserial串口对象；默认`/dev/ttyTHS1`、115200、8N1，ID0～5。`query_servo_angle(id)`返回原始角°；`set_servo_angle(id,angle,interval=...,velocity=...,t_acc=...,t_dec=...,power=...)`中interval/t_acc/t_dec单位ms，velocity单位°/s，power单位mW；`wait(timeout)`的timeout单位ms。不能与set_tool_pose的T秒混用。

底层驱动资料路径线索为`/Notebook/1.基础实验/uservo.py`，机械臂标定示例在Notebook的机械臂实验目录。恢复SDK时还应核对手册Arm5DoFKinematic依赖的transform、pose及config。手册的`Arm_Lib.Arm_Device`用另一套编号/直接角度接口，不能替换当前Arm5DoFUServo。

## 6. 环境与依赖

Notebook元数据Python3.8.10，课程平台Jetson/Linux/Jupyter。week3依赖 `arm5dof_uservo.py`；week4还需要 `arm5dof_kinematic.py`、NumPy和配置文件。当前项目目录及原ZIP仍无完整部署SDK/config；新增PDF含uservo接口表和Arm5DoFKinematic示例，提供恢复线索，但不是可直接导入的SDK文件包。确切SDK、NumPy、pyserial和JetPack版本【待补充：实体控制环境版本及SDK发布版本】。

## 7. 安装和运行

本次只解析Notebook，不执行Cell。以下是原平台复现说明，**待验证**：恢复该实验箱的原SDK及config，把Notebook放入课程工作目录或SDK同级工作区，再用匹配环境启动 `jupyter notebook`。

第3周默认DRY_RUN=True，但首个Cell仍导入SDK，SDK缺失时不能直接预览。第4周没有全局预览开关，执行四个动作Cell会直接连接并运动，必须按原现场操作分块执行。不要使用“运行全部”进行静态验收。归档不自动生成替代SDK、不调整控制参数。

## 8. 实验结果索引

[实验结果.md](../1.3_experiment_results/%E5%AE%9E%E9%AA%8C%E7%BB%93%E6%9E%9C.md)；week1平台原报告位于模块1的original_reports；两张姿态配图由本模块保存，现已核实为手册标准姿态图的引用，不计作本组实拍。

## 9. 常见问题与解决方法

第3周第二、三层Roll原值归一化83.7°时逆解不可行，现代码为90°；报告记第三轮恢复成功，仍须按SDK运行时判定。第2轮P0偏移未测方向和距离，原因尚未确定。第4周第一轮高层失败，后两轮成功；提高退出点和调整释放参数是后续方案，无修改后实验可核实。标定K接近0的问题尚待复测，不沿用异常参数。

## 10. 参考资料

week1/3/4原始报告、Notebook内代码与已存输出；SDK类名为Arm5DoFUServo、Arm5DoFKinematic。厂商说明已由本地手册补齐；【待补充：实际部署SDK文件、版本及发布资料包】。


新增本地来源：[DICE白熊平台用户手册（相关章节）](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/DICE_%E7%99%BD%E7%86%8A%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%AE%9E%E8%AE%AD%E5%B9%B3%E5%8F%B0%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C.pdf#page=229)；[平台手册核对与页码索引](../../%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99/%E5%B9%B3%E5%8F%B0%E6%89%8B%E5%86%8C%E6%A0%B8%E5%AF%B9.md)。
