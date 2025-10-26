#!/usr/bin/env python3
"""
数字人Web管理器
基于Gradio的数字人管理和上传界面
"""

import sys
import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import gradio as gr
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置项目根目录
project_root = Path(__file__).parent.resolve()

# 添加lib目录到Python路径
sys.path.insert(0, str(project_root / "lib"))

from lib.logger import get_logger


class DigitalHumanManager:
    """数字人管理器"""

    def __init__(self):
        """初始化数字人管理器"""
        self.logger = get_logger()
        self.characters_dir = project_root / "characters"
        self.ensure_characters_directory()

    def ensure_characters_directory(self):
        """确保characters目录存在"""
        if not self.characters_dir.exists():
            self.characters_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"创建characters目录: {self.characters_dir}")

    def scan_characters(self) -> List[Dict]:
        """
        扫描characters目录，获取所有数字人信息

        Returns:
            List[Dict]: 数字人信息列表
        """
        characters = []

        if not self.characters_dir.exists():
            return characters

        for char_dir in self.characters_dir.iterdir():
            if not char_dir.is_dir():
                continue

            char_info = self.get_character_info(char_dir.name)
            if char_info:
                characters.append(char_info)

        return characters

    def get_character_info(self, character_name) -> Optional[Dict]:
        """
        获取指定数字人的信息

        Args:
            character_name: 数字人名称（字符串或列表）

        Returns:
            Dict: 数字人信息，如果不存在返回None
        """
        # 处理参数类型：如果是列表，取第一个元素；如果是字符串，直接使用
        if isinstance(character_name, list):
            if not character_name:
                return None
            character_name = character_name[0]

        if not isinstance(character_name, str):
            return None

        char_dir = self.characters_dir / character_name
        if not char_dir.exists():
            return None

        # 检查必要文件
        required_files = {
            'landscape': char_dir / 'landscape.png',
            'portrait': char_dir / 'portrait.png',
            'short': char_dir / 'short.png',
            'audio': char_dir / 'reference.mp3'
        }

        existing_files = {key: path.exists() for key, path in required_files.items()}

        # 检查配置文件
        config_file = char_dir / 'reference.json'
        has_config = config_file.exists()

        # 读取配置信息
        config_data = {}
        if has_config:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception as e:
                self.logger.error(f"读取配置文件失败 {config_file}: {e}")

        char_info = {
            'name': character_name,
            'directory': str(char_dir),
            'files': existing_files,
            'has_config': has_config,
            'config': config_data,
            'status': 'uploaded' if has_config else 'local',
            'landscape_image': str(required_files['landscape']) if existing_files['landscape'] else None,
            'portrait_image': str(required_files['portrait']) if existing_files['portrait'] else None,
            'short_image': str(required_files['short']) if existing_files['short'] else None,
            'audio_file': str(required_files['audio']) if existing_files['audio'] else None
        }

        return char_info

    def upload_character(self, character_name) -> Tuple[bool, str]:
        """
        上传指定数字人

        Args:
            character_name: 数字人名称（字符串或列表）

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        # 处理参数类型
        if isinstance(character_name, list):
            if not character_name:
                return False, "未选择数字人"
            character_name = character_name[0]

        if not isinstance(character_name, str):
            return False, "无效的数字人名称"
        try:
            # 调用main.py的upload功能
            result = subprocess.run(
                [sys.executable, 'main.py', '--upload', character_name],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode == 0:
                return True, f"数字人 {character_name} 上传成功"
            else:
                return False, f"上传失败: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "上传超时，请检查网络连接"
        except Exception as e:
            return False, f"上传过程中发生错误: {str(e)}"

    def upload_all_characters(self) -> Tuple[bool, str]:
        """
        批量上传所有数字人

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 调用main.py的批量上传功能
            result = subprocess.run(
                [sys.executable, 'main.py', '--upload', 'all'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode == 0:
                return True, "批量上传成功"
            else:
                return False, f"批量上传失败: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "批量上传超时，请检查网络连接"
        except Exception as e:
            return False, f"批量上传过程中发生错误: {str(e)}"

    def create_character(self, name: str, landscape_image, portrait_image, short_image, audio_file) -> Tuple[bool, str]:
        """
        创建新的数字人

        Args:
            name: 数字人名称
            landscape_image: 横屏图片
            portrait_image: 竖屏图片
            short_image: 小屏图片
            audio_file: 参考音频

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 验证名称
            if not name or not name.strip():
                return False, "数字人名称不能为空"

            name = name.strip()
            char_dir = self.characters_dir / name

            # 检查是否已存在
            if char_dir.exists():
                return False, f"数字人 {name} 已存在"

            # 创建目录
            char_dir.mkdir(parents=True, exist_ok=True)

            # 复制文件
            file_mappings = [
                (landscape_image, char_dir / 'landscape.png'),
                (portrait_image, char_dir / 'portrait.png'),
                (short_image, char_dir / 'short.png'),
                (audio_file, char_dir / 'reference.mp3')
            ]

            for src_file, dst_file in file_mappings:
                if src_file is not None:
                    shutil.copy2(src_file, dst_file)
                    self.logger.info(f"复制文件: {src_file} -> {dst_file}")

            return True, f"数字人 {name} 创建成功"

        except Exception as e:
            self.logger.error(f"创建数字人失败: {e}")
            return False, f"创建数字人失败: {str(e)}"


class DigitalHumanWebInterface:
    """数字人Web界面"""

    def __init__(self):
        """初始化Web界面"""
        self.manager = DigitalHumanManager()
        self.logger = get_logger()  # 添加logger
        self.setup_interface()

    def refresh_characters(self):
        """刷新数字人列表"""
        return self.manager.scan_characters()

    def get_character_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取数字人信息"""
        return self.manager.get_character_info(name)

    def upload_single_character(self, character_name: str):
        """上传单个数字人"""
        success, message = self.manager.upload_character(character_name)
        # 刷新列表
        characters = self.refresh_characters()
        all_display = self.format_character_display(characters, "all")
        landscape_display = self.format_character_display(characters, "landscape")
        portrait_display = self.format_character_display(characters, "portrait")
        short_display = self.format_character_display(characters, "short")

        # 更新下拉选项
        choices = [char['name'] for char in characters] if characters else []

        return (success, message,
                all_display, landscape_display, portrait_display, short_display,
                gr.Dropdown(choices=choices, value=choices[0] if choices else None))

    def upload_all_characters_handler(self):
        """批量上传所有数字人"""
        success, message = self.manager.upload_all_characters()
        # 刷新列表
        characters = self.refresh_characters()
        all_display = self.format_character_display(characters, "all")
        landscape_display = self.format_character_display(characters, "landscape")
        portrait_display = self.format_character_display(characters, "portrait")
        short_display = self.format_character_display(characters, "short")

        # 更新下拉选项
        choices = [char['name'] for char in characters] if characters else []

        return (success, message,
                all_display, landscape_display, portrait_display, short_display,
                gr.Dropdown(choices=choices, value=choices[0] if choices else None))

    def create_new_character(self, name, landscape_image, portrait_image, short_image, audio_file):
        """创建新数字人"""
        success, message = self.manager.create_character(
            name, landscape_image, portrait_image, short_image, audio_file
        )
        # 刷新列表
        characters = self.refresh_characters()
        all_display = self.format_character_display(characters, "all")
        landscape_display = self.format_character_display(characters, "landscape")
        portrait_display = self.format_character_display(characters, "portrait")
        short_display = self.format_character_display(characters, "short")

        # 更新下拉选项
        choices = [char['name'] for char in characters] if characters else []

        return (success, message,
                all_display, landscape_display, portrait_display, short_display,
                gr.Dropdown(choices=choices, value=choices[0] if choices else None))

    def format_character_display(self, characters: List[Dict], view_type: str = "all"):
        """
        格式化数字人显示信息，增强可视化效果

        Args:
            characters: 数字人列表
            view_type: 视图类型 (all, landscape, portrait, short)
        """
        if not characters:
            return "### 📭 暂无数字人\n\n请在右侧创建新数字人或确保characters目录中有数字人文件夹"

        # 根据视图类型过滤数字人
        if view_type != "all":
            filtered_characters = []
            for char in characters:
                if char['files'].get(view_type, False):
                    filtered_characters.append(char)
            characters = filtered_characters

        if not characters:
            view_names = {
                "landscape": "横屏",
                "portrait": "竖屏",
                "short": "小屏"
            }
            return f"### 📭 暂无{view_names.get(view_type, '')}数字人\n\n请确保数字人目录中有相应的{view_names.get(view_type, '')}图片文件"

        display_text = f"## 📋 {self.get_view_title(view_type)} ({len(characters)}个)\n\n"

        # 统计信息
        uploaded_count = sum(1 for char in characters if char['has_config'])
        display_text += f"📊 **统计**: 已上传 {uploaded_count} / {len(characters)} 个\n\n"

        # 数字人列表
        for i, char in enumerate(characters, 1):
            status_emoji = "✅" if char['has_config'] else "🔶"
            display_text += f"### {i}. {status_emoji} **{char['name']}**\n"

            # 文件状态指示器
            file_indicators = []
            if char['files']['landscape']:
                file_indicators.append("🖥️")
            if char['files']['portrait']:
                file_indicators.append("📱")
            if char['files']['short']:
                file_indicators.append("📺")
            if char['files']['audio']:
                file_indicators.append("🎵")

            if file_indicators:
                display_text += f"**可用资源**: {' '.join(file_indicators)}\n"

            # 详细状态
            if char['has_config']:
                config = char.get('config', {})
                display_text += f"**状态**: 🟢 已上传至服务器\n"
                if config:
                    display_text += f"**配置**: 📋 配置文件完整\n"
            else:
                display_text += f"**状态**: 🔴 本地文件，未上传\n"

            # 快速操作提示
            if not char['has_config']:
                display_text += f"**建议**: 点击上方'上传选中数字人'按钮进行上传\n"

            display_text += "---\n\n"

        return display_text

    def get_view_title(self, view_type: str) -> str:
        """获取视图标题"""
        titles = {
            "all": "全部数字人",
            "landscape": "横屏数字人",
            "portrait": "竖屏数字人",
            "short": "小屏数字人"
        }
        return titles.get(view_type, "全部数字人")

    def get_filtered_characters(self, characters: List[Dict], view_type: str) -> List[Dict]:
        """根据视图类型过滤数字人"""
        if view_type == "all":
            return characters

        filtered = []
        for char in characters:
            if char['files'].get(view_type, False):
                filtered.append(char)
        return filtered

    def get_character_details(self, character_name) -> str:
        """获取数字人详细信息"""
        # 处理参数类型
        if isinstance(character_name, list):
            if not character_name:
                return "### ❌ 未选择数字人\n\n请从下拉菜单中选择一个数字人"
            character_name = character_name[0]

        char_info = self.manager.get_character_info(character_name)
        if not char_info:
            return "### ❌ 未找到数字人信息\n\n请确保选择的数字人存在"

        details = f"## 📊 **{character_name}** 详细信息\n\n"

        # 总体状态
        if char_info['has_config']:
            details += "### 🟢 状态：已上传至服务器\n\n"
        else:
            details += "### 🔴 状态：本地文件，未上传\n\n"

        # 文件状态表格
        details += "### 📁 文件清单\n"
        details += "| 文件类型 | 状态 | 说明 |\n"
        details += "|---------|------|------|\n"

        if char_info['files']['landscape']:
            details += "| 🖥️ 横屏图片 | ✅ 存在 | 请在右侧预览区域查看 |\n"
        else:
            details += "| 🖥️ 横屏图片 | ❌ 缺失 | - |\n"

        if char_info['files']['portrait']:
            details += "| 📱 竖屏图片 | ✅ 存在 | 请在右侧预览区域查看 |\n"
        else:
            details += "| 📱 竖屏图片 | ❌ 缺失 | - |\n"

        if char_info['files']['short']:
            details += "| 📺 小屏图片 | ✅ 存在 | 请在右侧预览区域查看 |\n"
        else:
            details += "| 📺 小屏图片 | ❌ 缺失 | - |\n"

        if char_info['files']['audio']:
            details += "| 🎵 参考音频 | ✅ 存在 | 请在右侧预览区域播放 |\n"
        else:
            details += "| 🎵 参考音频 | ❌ 缺失 | - |\n"

        # 配置信息
        details += "\n### ⚙️ 配置信息\n"
        if char_info['has_config']:
            config = char_info.get('config', {})
            details += "**上传状态**: ✅ 已上传\n\n"
            if config:
                if 'voice_id' in config:
                    details += f"**语音ID**: `{config['voice_id'][-20:]}`...\n"
                if 'landscape_id' in config:
                    details += f"**横屏ID**: `{config['landscape_id'][-20:]}`...\n"
                if 'portrait_id' in config:
                    details += f"**竖屏ID**: `{config['portrait_id'][-20:]}`...\n"
                if 'short_id' in config:
                    details += f"**小屏ID**: `{config['short_id'][-20:]}`...\n"
        else:
            details += "**上传状态**: ❌ 未上传\n"
            details += "**建议**: 点击'上传选中数字人'按钮进行上传\n"

        # 目录信息
        details += f"\n### 📂 存储位置\n```\n{char_info['directory']}\n```"

        # 操作提示
        if not char_info['has_config']:
            details += "\n### 💡 操作提示\n"
            missing_files = []
            if not char_info['files']['landscape']:
                missing_files.append("横屏图片 (landscape.png)")
            if not char_info['files']['portrait']:
                missing_files.append("竖屏图片 (portrait.png)")
            if not char_info['files']['short']:
                missing_files.append("小屏图片 (short.png)")
            if not char_info['files']['audio']:
                missing_files.append("参考音频 (reference.mp3)")

            if missing_files:
                details += f"⚠️ **缺少文件**: {', '.join(missing_files)}\n\n"
                details += "请确保所有必要文件都存在于数字人目录中，然后再进行上传。"

        return details

    def get_character_preview_files(self, character_name) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """获取数字人预览文件路径"""
        # 处理参数类型
        if isinstance(character_name, list):
            if not character_name:
                return None, None, None, None
            character_name = character_name[0]

        char_info = self.manager.get_character_info(character_name)
        if not char_info:
            return None, None, None, None

        # 确保文件路径存在且可访问
        def get_valid_path(file_path):
            if file_path and Path(file_path).exists():
                return str(Path(file_path).resolve())
            return None

        return (
            get_valid_path(char_info['landscape_image']) if char_info['files']['landscape'] else None,
            get_valid_path(char_info['portrait_image']) if char_info['files']['portrait'] else None,
            get_valid_path(char_info['short_image']) if char_info['files']['short'] else None,
            get_valid_path(char_info['audio_file']) if char_info['files']['audio'] else None
        )

    def update_character_info(self, character_name: str):
        """更新数字人信息显示"""
        details = self.get_character_details(character_name)
        landscape_img, portrait_img, short_img, audio_file = self.get_character_preview_files(character_name)

        return details, landscape_img, portrait_img, short_img, audio_file

    def view_character_config(self, character_name) -> str:
        """查看数字人配置文件"""
        # 处理参数类型
        if isinstance(character_name, list):
            if not character_name:
                return "该数字人暂无配置文件"
            character_name = character_name[0]

        char_info = self.manager.get_character_info(character_name)
        if not char_info or not char_info['has_config']:
            return "该数字人暂无配置文件"

        try:
            config_file = Path(char_info['directory']) / 'reference.json'
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            return json.dumps(config_data, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"读取配置文件失败: {str(e)}"

    def delete_character_config(self, character_name) -> Tuple[bool, str]:
        """删除数字人配置文件（重置上传状态）"""
        # 处理参数类型
        if isinstance(character_name, list):
            if not character_name:
                return False, "未选择数字人"
            character_name = character_name[0]

        char_info = self.manager.get_character_info(character_name)
        if not char_info or not char_info['has_config']:
            return False, "该数字人暂无配置文件"

        try:
            config_file = Path(char_info['directory']) / 'reference.json'
            if config_file.exists():
                config_file.unlink()
                self.logger.info(f"删除配置文件: {config_file}")
                return True, "配置文件已删除，上传状态已重置"
            else:
                return False, "配置文件不存在"
        except Exception as e:
            self.logger.error(f"删除配置文件失败: {e}")
            return False, f"删除配置文件失败: {str(e)}"

    def setup_interface(self):
        """设置Gradio界面"""
        # 预先获取数字人列表
        characters = self.refresh_characters()
        character_choices = [char['name'] for char in characters] if characters else []
        default_selection = character_choices[0] if character_choices else None

        with gr.Blocks(title="数字人管理系统", theme=gr.themes.Soft()) as self.interface:
            gr.Markdown("# 🎭 数字人管理系统")

            # 创建一个隐藏的HTML组件来提供manifest.json内容
            manifest_html = gr.HTML(
                value=f"""
                <script>
                // 动态创建manifest
                const manifest = {{
                    "name": "数字人管理系统",
                    "short_name": "数字人管理",
                    "description": "基于Gradio的数字人管理和上传界面",
                    "start_url": "/",
                    "display": "standalone",
                    "background_color": "#ffffff",
                    "theme_color": "#007bff",
                    "orientation": "portrait-primary"
                }};

                // 创建blob URL
                const manifestBlob = new Blob([JSON.stringify(manifest, null, 2)], {{type: 'application/json'}});
                const manifestUrl = URL.createObjectURL(manifestBlob);

                // 动态添加manifest link
                const link = document.createElement('link');
                link.rel = 'manifest';
                link.href = manifestUrl;
                document.head.appendChild(link);
                </script>
                """,
                visible=False
            )

            with gr.Row():
                with gr.Column(scale=2):
                    # 主要内容区域
                    gr.Markdown("## 📋 数字人管理")

                    # 分类视图标签页
                    with gr.Tabs() as view_tabs:
                        with gr.TabItem("🌟 全部", id="all"):
                            all_character_display = gr.Markdown("正在加载...")

                        with gr.TabItem("🖥️ 横屏", id="landscape"):
                            landscape_character_display = gr.Markdown("正在加载...")

                        with gr.TabItem("📱 竖屏", id="portrait"):
                            portrait_character_display = gr.Markdown("正在加载...")

                        with gr.TabItem("📺 小屏", id="short"):
                            short_character_display = gr.Markdown("正在加载...")

                    # 操作按钮区域
                    with gr.Row():
                        refresh_btn = gr.Button("🔄 刷新列表", size="sm")
                        upload_all_btn = gr.Button("📤 批量上传", variant="primary", size="sm")

                    # 单个上传区域
                    gr.Markdown("## 🎯 单个数字人操作")
                    with gr.Row():
                        character_dropdown = gr.Dropdown(
                            choices=character_choices,
                            value=default_selection,
                            label="选择数字人",
                            interactive=True
                        )
                        upload_single_btn = gr.Button("📤 上传选中数字人", variant="secondary")

                    # 操作结果显示
                    result_output = gr.Textbox(label="操作结果", interactive=False, lines=3)

                with gr.Column(scale=1):
                    # 侧边栏
                    with gr.Tabs():
                        with gr.TabItem("📊 配置信息"):
                            # 数字人详情显示
                            character_details = gr.Markdown("请选择数字人查看详情")

                            with gr.Row():
                                view_config_btn = gr.Button("👁️ 查看配置", size="sm")
                                delete_config_btn = gr.Button("🗑️ 删除配置", variant="stop", size="sm")

                            # 预览区域
                            gr.Markdown("### 🖼️ 媒体预览")
                            with gr.Tabs():
                                with gr.TabItem("🖥️ 横屏"):
                                    landscape_preview = gr.Image(
                                        label="横屏图片预览",
                                        interactive=False,
                                        show_label=True,
                                        show_download_button=True,
                                        height=300
                                    )
                                with gr.TabItem("📱 竖屏"):
                                    portrait_preview = gr.Image(
                                        label="竖屏图片预览",
                                        interactive=False,
                                        show_label=True,
                                        show_download_button=True,
                                        height=400
                                    )
                                with gr.TabItem("📺 小屏"):
                                    short_preview = gr.Image(
                                        label="小屏图片预览",
                                        interactive=False,
                                        show_label=True,
                                        show_download_button=True,
                                        height=200
                                    )
                                with gr.TabItem("🎵 音频"):
                                    audio_preview = gr.Audio(
                                        label="参考音频播放",
                                        interactive=False,
                                        show_label=True,
                                        show_download_button=True
                                    )

                            # 配置文件显示
                            gr.Markdown("### 📄 配置文件")
                            config_display = gr.Code(
                                language="json",
                                label="配置文件内容",
                                interactive=False,
                                lines=8
                            )

                        with gr.TabItem("➕ 创建新数字人"):
                            with gr.Group():
                                name_input = gr.Textbox(label="数字人名称", placeholder="请输入数字人名称")

                                gr.Markdown("### 📷 上传图片")
                                landscape_input = gr.Image(label="横屏图片", type="filepath")
                                portrait_input = gr.Image(label="竖屏图片", type="filepath")
                                short_input = gr.Image(label="小屏图片", type="filepath")

                                gr.Markdown("### 🎵 上传音频")
                                audio_input = gr.Audio(label="参考音频", type="filepath")

                                create_btn = gr.Button("✨ 创建数字人", variant="primary")

                            gr.Markdown("## ℹ️ 使用说明")
                            gr.Markdown("""
                            1. **查看数字人**: 主列表显示所有数字人状态
                            2. **上传数字人**: 选择数字人后点击上传按钮
                            3. **批量上传**: 点击"批量上传"上传所有本地数字人
                            4. **创建数字人**: 在右侧填写信息并上传文件来创建新数字人
                            5. **配置管理**: 在配置信息标签页查看和管理数字人配置
                            6. **媒体预览**: 选择数字人后，在右侧预览区域查看/播放媒体文件

                            **状态说明**:
                            - ✅ 已上传: 数字人已成功上传到服务器
                            - ❌ 未上传: 数字人仅在本地存在

                            **文件预览**:
                            - 选择数字人后，图片和音频文件会在右侧预览区域自动加载
                            - 如果预览失败，请检查文件是否存在于对应的数字人目录中
                            """)

            # 事件绑定
            refresh_btn.click(
                fn=self.refresh_and_update,
                outputs=[all_character_display, landscape_character_display,
                        portrait_character_display, short_character_display,
                        character_dropdown]
            )

            upload_all_btn.click(
                fn=self.upload_all_characters_handler,
                outputs=[result_output, all_character_display, landscape_character_display,
                        portrait_character_display, short_character_display, character_dropdown]
            )

            upload_single_btn.click(
                fn=self.upload_single_character,
                inputs=[character_dropdown],
                outputs=[result_output, all_character_display, landscape_character_display,
                        portrait_character_display, short_character_display, character_dropdown]
            )

            create_btn.click(
                fn=self.create_new_character,
                inputs=[name_input, landscape_input, portrait_input, short_input, audio_input],
                outputs=[result_output, all_character_display, landscape_character_display,
                        portrait_character_display, short_character_display, character_dropdown]
            )

            # 配置信息相关事件
            character_dropdown.change(
                fn=self.update_character_info,
                inputs=[character_dropdown],
                outputs=[character_details, landscape_preview, portrait_preview, short_preview, audio_preview]
            )

            view_config_btn.click(
                fn=self.view_character_config,
                inputs=[character_dropdown],
                outputs=[config_display]
            )

            def delete_config_handler(character_name):
                """删除配置处理器"""
                success, message = self.delete_character_config(character_name)
                # 刷新列表和详情
                characters = self.refresh_characters()
                all_display = self.format_character_display(characters, "all")
                landscape_display = self.format_character_display(characters, "landscape")
                portrait_display = self.format_character_display(characters, "portrait")
                short_display = self.format_character_display(characters, "short")

                # 更新下拉选项
                choices = [char['name'] for char in characters] if characters else []
                new_selection = character_name if character_name in choices else (choices[0] if choices else "")

                return (message,
                        all_display, landscape_display, portrait_display, short_display,
                        gr.Dropdown(choices=choices, value=new_selection),
                        self.get_character_details(new_selection),
                        "")

            delete_config_btn.click(
                fn=delete_config_handler,
                inputs=[character_dropdown],
                outputs=[result_output, all_character_display, landscape_character_display,
                        portrait_character_display, short_character_display, character_dropdown,
                        character_details, config_display]
            )

            # 初始加载
            def initial_load():
                """初始加载函数"""
                characters = self.refresh_characters()
                all_display = self.format_character_display(characters, "all")
                landscape_display = self.format_character_display(characters, "landscape")
                portrait_display = self.format_character_display(characters, "portrait")
                short_display = self.format_character_display(characters, "short")
                choices = [char['name'] for char in characters] if characters else []
                selected_value = choices[0] if choices else None

                # 初始化右侧信息
                if selected_value:
                    character_details = self.get_character_details(selected_value)
                    landscape_img, portrait_img, short_img, audio_file = self.get_character_preview_files(selected_value)
                    config_content = self.view_character_config(selected_value)
                else:
                    character_details = "请选择数字人查看详情"
                    landscape_img, portrait_img, short_img, audio_file = None, None, None, None
                    config_content = "暂无配置文件"

                return (all_display, landscape_display, portrait_display, short_display,
                        gr.Dropdown(choices=choices, value=selected_value),
                        character_details, landscape_img, portrait_img, short_img, audio_file,
                        config_content)

            self.interface.load(
                fn=initial_load,
                outputs=[all_character_display, landscape_character_display,
                        portrait_character_display, short_character_display, character_dropdown,
                        character_details, landscape_preview, portrait_preview, short_preview, audio_preview,
                        config_display]
            )

    def refresh_and_update(self):
        """刷新并更新界面"""
        try:
            characters = self.refresh_characters()

            # 生成各视图的显示内容
            all_display = self.format_character_display(characters, "all")
            landscape_display = self.format_character_display(characters, "landscape")
            portrait_display = self.format_character_display(characters, "portrait")
            short_display = self.format_character_display(characters, "short")

            # 更新下拉选项
            choices = [char['name'] for char in characters] if characters else []
            selected_value = choices[0] if choices else None

            return (all_display, landscape_display, portrait_display, short_display,
                    gr.Dropdown(choices=choices, value=selected_value))
        except Exception as e:
            self.logger.error(f"刷新界面失败: {e}")
            error_msg = f"❌ 刷新失败: {str(e)}"
            return (error_msg, error_msg, error_msg, error_msg, gr.Dropdown(choices=[], value=None))

    def launch(self, **kwargs):
        """启动Web界面"""
        self.interface.launch(**kwargs)


def main():
    """主函数 - 包含启动脚本的完整逻辑"""
    try:
        # 确保在项目根目录运行
        os.chdir(project_root)

        print("🚀 启动数字人管理系统...")
        print("📂 项目根目录:", project_root)
        print("📂 数字人目录:", project_root / "characters")
        print("🌐 Web界面将在 http://localhost:7860 启动")

        # 创建管理器
        manager = DigitalHumanWebInterface()

        print("✅ 界面初始化完成，正在启动服务器...")

        # 启动界面
        manager.launch(
            server_name="0.0.0.0",  # 允许外部访问
            server_port=7860,       # 端口号
            share=False,            # 不创建公共链接
            show_error=True,        # 显示错误信息
            quiet=False,            # 显示启动信息
            inbrowser=False,        # 不自动打开浏览器
            allowed_paths=[str(project_root)],  # 允许访问项目根目录
            prevent_thread_lock=False  # 防止线程锁定
        )
    except KeyboardInterrupt:
        print("\n👋 数字人管理系统已停止")
        return True
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    return True


if __name__ == "__main__":
    main()