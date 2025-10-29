# 🎬 AI视频生成器

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-Package%20Manager-green.svg)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个基于AI的视频内容生成自动化工具，支持从PDF到完整数字人讲解视频的全流程制作。

## ✨ 核心功能

- 📄 **PDF转幻灯片**: 自动将PDF转换为高清PNG图片序列
- 📝 **智能脚本处理**: 从PPT备注提取脚本或AI生成内容
- 🤖 **数字人视频**: 通过RunningHub API生成数字人讲解视频
- 🎞️ **视频合成**: 将幻灯片与数字人视频合成
- 🎨 **PPT自动生成**: Gamma API自动生成演示文稿
- 🎮 **Web管理界面**: 可视化数字人管理器
- 🤖 **GLM大模型**: 支持脚本生成、内容分割和标题创建
- 📺 **B站上传**: 自动上传视频到B站

## 📖 使用方法

### 快速上手

```bash
# 准备输入文件：将PDF放到input/目录，讲稿保存到input/prompt.txt
# 运行完整流程
uv run python main.py

# 指定数字人
uv run python main.py --digital-human woman
```

### 主要命令

```bash
# 完整流程
uv run python main.py

# 分步执行
uv run python main.py --clear        # 清空目录
uv run python main.py --pdf          # 处理PDF
uv run python main.py --ppt          # 提取PPT备注
uv run python main.py --generate     # 生成数字人视频
uv run python main.py --batch        # 合成视频

# AI功能
uv run python main.py --prepare      # 生成标题、封面和讲稿
uv run python main.py --create-ppt   # 自动生成PPT

# 数字人管理
uv run python digital-human-web-manager.py  # Web管理界面
uv run python main.py --upload man           # 上传数字人
```

### Web管理界面

```bash
# 启动数字人管理器
uv run digital-human-web-manager.py
# 访问 http://localhost:7860
```

### B站上传

```bash
# 使用biliup上传视频
.\biliup\biliup_win.exe upload -c ..\assets\biliconfig.yaml
```

## 📁 项目结构

```
video-generator/
├── input/              # 输入文件（PDF、PPT、讲稿）
├── slides/             # 处理后的幻灯片和视频
├── output/             # 最终视频输出
├── characters/         # 数字人配置
├── lib/                # 核心功能模块
├── tools/              # 工具脚本
├── assets/             # 资源和配置文件
├── main.py             # 主程序
└── digital-human-web-manager.py  # Web管理器
```

## ⚙️ 工作流程

### 完整流程
1. **准备输入**: PDF文件、讲稿内容
2. **PDF处理**: 转换为PNG图片序列
3. **内容提取**: 从PPT备注或使用AI生成的脚本
4. **视频生成**: 调用RunningHub API生成数字人视频
5. **视频合成**: 合成最终视频文件

### AI辅助功能
- **自动生成讲稿**: 基于文章内容生成口播稿
- **智能分页**: 自动将长内容分割为幻灯片页面
- **标题生成**: 生成吸引人的视频标题
- **PPT生成**: 通过Gamma API自动生成演示文稿

## 🔧 技术栈

- **Python 3.12+**: 主要开发语言
- **uv**: 包管理器
- **RunningHub API**: 数字人视频生成
- **GLM API**: 大模型AI服务
- **Gamma API**: PPT自动生成
- **Gradio**: Web界面框架
- **FFmpeg**: 视频处理

## ❓ 常见问题

**Q: 支持哪些文件格式？**
A: 支持PDF演示文稿和PPT/PPTX文件。

**Q: 如何选择数字人？**
A: 使用`--digital-human`参数指定，如`man`、`woman`等。

**Q: 生成的视频分辨率？**
A: 默认输出1920x1080高清视频。

**Q: API如何获取？**
A: RunningHub、Gamma、GLM分别在其官网注册获取。

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件了解详情。

---

<div align="center">

**🎬 让AI帮你制作专业视频内容！**

如果这个项目对你有帮助，请考虑给个 ⭐️

</div>
