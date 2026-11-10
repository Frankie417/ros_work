# 第五学期 机器人感知与控制综合实践

本仓库归档“第五学期”工作区的原始实验资料和整理后的四模块工程，课程代码为 S0610350。统一阅读入口为 [robot_ws 项目说明](robot_ws/README.md)。

## 目录

| 路径 | 内容 |
|---|---|
| [robot_ws/](robot_ws/) | 四模块代码、技术 README、实验结果、图片、原报告索引与来源校验 |
| [arm2026_ws/](arm2026_ws/) | 原 ROS 建模工程、历史验证、构建产物及第三方参考 |
| week1、week3、week4、week5、week6、week7 | 各周原始 Notebook、报告、图像、视频及测试记录 |
| [平台手册核对](robot_ws/参考资料/平台手册核对.md) | DICE 平台手册、接口、标定与运动学的页码说明 |
| [待补充材料清单](robot_ws/待补充材料清单.md) | SDK、环境、版本对应和实测证据的现有缺口 |
| [文件映射表](robot_ws/文件映射表.md) | 原始文件与四模块归档的对应关系 |

## 下载完整资料

视频、ZIP、MediaPipe 模型与参考网格通过 Git LFS 保存。安装 Git LFS 后克隆：

```bash
git lfs install
git clone https://github.com/Frankie417/ros_work.git
cd ros_work
git lfs pull
```

GitHub 网页下载源码 ZIP 不一定包含完整 LFS 文件，复现时应按上述方式克隆并拉取 LFS 对象。

## 运行与验证

各模块运行步骤和依赖见 robot_ws。当前工作区包含原始 build/devel、检查点和历史副本，保留它们用于完整归档；实际开发使用 robot_ws 指定的主版本，并在原 Linux/Jetson 环境重新构建。DICE 部署 SDK/config 等尚缺项已在清单中标注。

只读检查归档完整性：

```bash
python robot_ws/整理记录/静态验证.py
```

此工具只检查哈希、AST、XML和本地链接，不导入控制程序或触发机械臂。图片、成功率与实现状态均按原始材料说明；手册标准图不计作本组实拍。

原始实验源码与参数保持原样。本次上传由 AI 协助整理目录、说明文档及 Git/LFS 配置；代码/实验结论的来源与人工核验事项见 robot_ws。第三方资源的来源、许可证保留在各自原目录，仓库没有为全部资料统一授予新许可证。
