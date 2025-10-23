# 视频生成项目主程序使用说明

## 概述

`main.py` 是视频生成项目的主程序，整合了PDF处理、PPT备注提取、视频生成和数字人上传功能。支持运行完整工作流程或单独执行各个步骤。

## 使用方法

### 1. 运行完整工作流程

```bash
uv run python main.py
```

这将依次执行以下步骤：
1. 询问是否清空slides和output目录
2. 处理input目录中的第一个PDF文件
3. 处理与PDF同名的PPT/PPTX文件
4. 生成每个slide的视频
5. 批量处理slides文件并合成最终视频

### 2. 单独执行各个步骤

#### 清空slides和output目录
```bash
uv run python main.py --clear
```

#### 仅处理PDF文件
```bash
uv run python main.py --pdf
```
将input目录中的第一个PDF文件转换为PNG图片并保存到slides目录。

#### 仅处理PPT备注提取
```bash
uv run python main.py --ppt
```
提取与PDF同名的PPT/PPTX文件中的备注，保存为对应的txt文件。

#### 仅生成slide视频
```bash
uv run python main.py --generate
```
为每个slide生成对应的数字人视频。

#### 仅批量处理slides
```bash
uv run python main.py --batch
```
将slides目录中的图片和视频文件合成为最终视频。

#### 上传数字人
```bash
# 上传指定数字人
uv run python main.py --upload man

# 批量上传所有数字人
uv run python main.py --upload all
```

## 目录结构

```
video-generator/
├── input/              # 输入目录（PDF和PPTX文件）
├── slides/             # 幻灯片目录（PNG图片、TXT文本、MP4视频）
├── output/             # 输出目录（最终视频和合并文件）
├── characters/         # 数字人文件目录
├── lib/                # 工具库目录
├── main.py             # 主程序
└── .env                # 环境配置文件
```

## 前置条件

1. **环境配置**：确保`.env`文件包含正确的API配置
2. **输入文件**：确保`input`目录包含要处理的PDF文件
3. **PPT文件**：如果要提取备注，确保有同名的PPT/PPTX文件
4. **数字人文件**：如果要使用数字人功能，确保`characters`目录有相应的数字人文件

## 工作流程详解

### 步骤1：清空目录（可选）
询问用户是否清空`slides`和`output`目录中的所有文件，确保处理过程不受旧文件影响。

### 步骤2：PDF处理
- 扫描`input`目录中的PDF文件
- 选择第一个PDF文件进行处理
- 将PDF的每一页转换为1920x1080的PNG图片
- 保存到`slides`目录，命名为`1.png`, `2.png`等

### 步骤3：PPT备注提取
- 查找与PDF文件同名的PPT/PPTX文件
- 提取每页的备注内容
- 保存为对应的txt文件（`1.txt`, `2.txt`等）
- 支持full模式（文本以`[full]`开头）

### 步骤4：生成slide视频
- 读取每个slide的文本内容
- 调用数字人API生成对应的视频
- 支持跳过已存在的视频文件
- 根据full模式决定输出位置

### 步骤5：批量处理
- 查找slides目录中的图片-视频对
- 将每个对合成为新的视频文件
- 最后将所有结果合并为最终视频`output/result.mp4`

## 注意事项

1. **API配置**：确保`.env`文件中的API密钥正确配置
2. **网络连接**：视频生成需要稳定的网络连接
3. **文件命名**：PPT/PPTX文件需要与PDF文件同名
4. **处理时间**：视频生成可能需要较长时间，请耐心等待
5. **存储空间**：确保有足够的磁盘空间存储生成的文件

## 错误处理

程序包含完善的错误处理机制：
- 会在每个步骤检查前置条件
- 提供详细的错误信息
- 支持跳过已处理的文件
- 在步骤失败时提供友好的提示

## 示例用法

```bash
# 完整流程
uv run python main.py

# 准备阶段 - 清空并处理PDF/PPT
uv run python main.py --clear
uv run python main.py --pdf
uv run python main.py --ppt

# 生成阶段
uv run python main.py --generate

# 合成阶段
uv run python main.py --batch

# 数字人管理
uv run python main.py --upload man
```

## 技术支持

如遇到问题，请检查：
1. 环境配置是否正确
2. 输入文件是否存在且有效
3. 网络连接是否稳定
4. 磁盘空间是否充足
5. API密钥是否有效