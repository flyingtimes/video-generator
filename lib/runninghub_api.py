"""
RunningHub API文件上传工具
用于上传数字人相关文件到RunningHub服务
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class RunningHubAPI:
    """RunningHub API客户端"""

    def __init__(self, api_key: str = None, base_url: str = "https://www.runninghub.cn"):
        """
        初始化API客户端

        Args:
            api_key: API密钥，如果为None则从环境变量获取
            base_url: API基础URL
        """
        self.api_key = api_key if api_key else get_api_key()
        self.base_url = base_url
        self.upload_url = f"{base_url}/task/openapi/upload"
        self.generate_url = f"{base_url}/task/openapi/ai-app/run"
        self.status_url = f"{base_url}/task/openapi/outputs"

    def upload_file(self, file_path: str, file_type: str = "input") -> Optional[str]:
        """
        上传单个文件到RunningHub

        Args:
            file_path: 要上传的文件路径
            file_type: 文件类型，默认为"input"

        Returns:
            Optional[str]: 上传成功返回文件名，失败返回None
        """
        try:
            if not os.path.exists(file_path):
                print(f"错误: 文件 {file_path} 不存在")
                return None

            # 准备上传数据
            files = {'file': open(file_path, 'rb')}
            data = {
                'apiKey': self.api_key,
                'fileType': file_type
            }

            print(f"正在上传文件: {file_path}")

            # 发送请求
            response = requests.post(self.upload_url, files=files, data=data)
            files['file'].close()

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    file_name = result.get('data', {}).get('fileName')
                    print(f"✅ 上传成功: {file_name}")
                    return file_name
                else:
                    print(f"❌ 上传失败: {result.get('msg', '未知错误')}")
                    return None
            else:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ 上传文件时发生异常: {str(e)}")
            return None

    def load_reference_json(self, character_dir: str) -> Optional[Dict[str, str]]:
        """
        加载reference.json文件

        Args:
            character_dir: 数字人目录路径

        Returns:
            Optional[Dict[str, str]]: 加载成功返回配置字典，失败返回None
        """
        reference_file = Path(character_dir) / "reference.json"

        if reference_file.exists():
            try:
                with open(reference_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"✅ 已加载reference.json文件")
                    return config
            except Exception as e:
                print(f"❌ 读取reference.json文件失败: {str(e)}")
                return None
        else:
            print(f"📝 reference.json文件不存在，需要重新上传")
            return None

    def save_reference_json(self, character_dir: str, config: Dict[str, str]) -> bool:
        """
        保存reference.json文件

        Args:
            character_dir: 数字人目录路径
            config: 配置字典

        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            reference_file = Path(character_dir) / "reference.json"
            with open(reference_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            print(f"✅ 已保存reference.json文件到: {reference_file}")
            return True
        except Exception as e:
            print(f"❌ 保存reference.json文件失败: {str(e)}")
            return False

    def process_character_files(self, character_dir: str, character_name: str) -> bool:
        """
        处理数字人文件上传

        Args:
            character_dir: 数字人目录路径
            character_name: 数字人名称

        Returns:
            bool: 处理成功返回True，失败返回False
        """
        print(f"\n{'='*50}")
        print(f"处理数字人: {character_name}")
        print(f"目录: {character_dir}")
        print('='*50)

        # 首先检查是否已存在reference.json
        existing_config = self.load_reference_json(character_dir)
        if existing_config:
            print("✅ 数字人文件已上传，无需重复处理")
            return True

        # 定义需要上传的文件类型和对应文件名
        file_mappings = {
            'voice_id': 'reference.mp3',
            'landscape_id': 'landscape.png',
            'portrait_id': 'portrait.png',
            'short_id': 'short.png'
        }

        config = {}
        character_path = Path(character_dir)

        # 逐个上传文件
        for config_key, filename in file_mappings.items():
            file_path = character_path / filename

            if not file_path.exists():
                print(f"❌ 文件不存在: {file_path}")
                continue

            # 上传文件
            uploaded_filename = self.upload_file(str(file_path))
            if uploaded_filename:
                config[config_key] = uploaded_filename
            else:
                print(f"❌ 上传文件失败: {filename}")
                return False

        # 检查是否所有文件都上传成功
        if len(config) != len(file_mappings):
            print(f"❌ 文件上传不完整: {len(config)}/{len(file_mappings)}")
            return False

        # 保存配置到reference.json
        if self.save_reference_json(character_dir, config):
            print(f"✅ 数字人 {character_name} 处理完成")
            return True
        else:
            print(f"❌ 保存配置文件失败")
            return False

    def gen_short_Video(self, short_image: str, reference_audio: str, text: str, mode: str = "short") -> Optional[str]:
        """
        生成短视频（数字人说话视频）

        Args:
            short_image: 图片文件名（已上传到RunningHub的文件名）
            reference_audio: 音频文件名（已上传到RunningHub的文件名）
            text: 要生成的文本内容
            mode: 模式类型，可以是"short", "portrait", "landscape"

        Returns:
            Optional[str]: 成功返回任务ID，失败返回None
        """
        try:
            # 获取对应模式的webappId
            webapp_id = get_webapp_id(mode)
            print(webapp_id)
            # 构建请求数据
            data = {
                "webappId": webapp_id,
                "apiKey": self.api_key,
                "nodeInfoList": [
                    {
                        "nodeId": "48",
                        "fieldName": "image",
                        "fieldValue": short_image,
                        "description": "image"
                    },
                    {
                        "nodeId": "47",
                        "fieldName": "audio",
                        "fieldValue": reference_audio,
                        "description": "audio"
                    },
                    {
                        "nodeId": "38",
                        "fieldName": "text",
                        "fieldValue": text,
                        "description": "text"
                    }
                ]
            }

            print(f"正在生成短视频...")
            print(f"模式: {mode}")
            print(f"WebApp ID: {webapp_id}")
            print(f"图片文件: {short_image}")
            print(f"音频文件: {reference_audio}")
            print(f"文本内容: {text}")

            # 发送请求
            response = requests.post(
                self.generate_url,
                headers={'Content-Type': 'application/json'},
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    task_id = result.get('data', {}).get('taskId')
                    print(f"✅ 短视频生成任务创建成功: {task_id}")
                    return task_id
                else:
                    print(f"❌ 生成失败: {result.get('msg', '未知错误')}")
                    return None
            else:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None

        except Exception as e:
            print(f"❌ 生成短视频时发生异常: {str(e)}")
            return None

    def check_task_status(self, task_id: str) -> Optional[Dict]:
        """
        查询任务状态

        Args:
            task_id: 任务ID

        Returns:
            Optional[Dict]: 成功返回任务状态数据，失败返回None
        """
        try:
            data = {
                "apiKey": self.api_key,
                "taskId": task_id
            }

            response = requests.post(
                self.status_url,
                headers={'Content-Type': 'application/json'},
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    return result
                else:
                    # 返回包含错误信息的结果，让调用方处理
                    return result
            else:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ 查询任务状态时发生异常: {str(e)}")
            return None

    def download_video(self, file_url: str, output_path: str) -> bool:
        """
        下载视频文件

        Args:
            file_url: 视频文件URL
            output_path: 输出文件路径

        Returns:
            bool: 下载成功返回True，失败返回False
        """
        import time

        max_retries = 3
        retry_interval = 15  # 秒

        for attempt in range(max_retries):
            try:
                print(f"正在下载视频: {file_url}")
                if attempt > 0:
                    print(f"第 {attempt + 1} 次尝试下载...")

                response = requests.get(file_url, stream=True, timeout=30)

                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✅ 视频下载成功: {output_path}")
                    return True
                else:
                    print(f"❌ 下载失败，状态码: {response.status_code}")
                    if attempt < max_retries - 1:
                        print(f"⏳ {retry_interval}秒后重试...")
                        time.sleep(retry_interval)
                    continue

            except Exception as e:
                print(f"❌ 下载视频时发生异常: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"⏳ {retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                continue

        print(f"❌ 视频下载失败，已达到最大重试次数 ({max_retries})")
        return False

    def gen_slide_video(self, slide_num: int, digital_human: str = "man") -> bool:
        """
        生成幻灯片视频

        Args:
            slide_num: 幻灯片编号
            digital_human: 数字人子目录名称，默认为"man"

        Returns:
            bool: 生成成功返回True，失败返回False
        """
        import time

        print(f"\n{'='*50}")
        print(f"开始处理幻灯片: {slide_num}")
        print(f"使用数字人: {digital_human}")
        print('='*50)

        # 定义文件路径
        slide_image = f"slides/{slide_num}.png"
        slide_text_file = f"slides/{slide_num}.txt"
        task_file = f"slides/{slide_num}.task"
        output_video = f"slides/{slide_num}.mp4"

        # 检查必要文件是否存在
        if not os.path.exists(slide_image):
            print(f"❌ 幻灯片图片不存在: {slide_image}")
            return False

        # 读取文本内容
        if not os.path.exists(slide_text_file):
            print(f"❌ 幻灯片文本文件不存在: {slide_text_file}")
            return False

        try:
            with open(slide_text_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            if not text:
                print(f"⚠️ 幻灯片文本文件为空，跳过此幻灯片: {slide_text_file}")
                return "skip"

            # 检查是否是[full]开头的文本
            is_full_mode = text.startswith('[full]')
            if is_full_mode:
                # 移除[full]前缀
                text = text[5:].strip()
                print(f"📄 检测到[full]模式，使用landscape模式生成视频")
                # 修改输出路径为output/combine_{num}.mp4
                output_video = f"output/combine_{slide_num}.mp4"
                # 确保output目录存在
                os.makedirs("output", exist_ok=True)
                print(f"📁 输出路径: {output_video}")

            print(f"📄 已读取文本内容: {text[:50]}{'...' if len(text) > 50 else ''}")
        except Exception as e:
            print(f"❌ 读取文本文件失败: {str(e)}")
            return False

        # 获取数字人配置（在开始时就获取，避免重试时作用域问题）
        character_dir = f"characters/{digital_human}"
        character_config = self.load_reference_json(character_dir)
        if not character_config:
            print(f"❌ 未找到数字人配置: {character_dir}，请先上传数字人文件")
            return False

        # 检查是否已有任务文件（任务正在执行中）
        if os.path.exists(task_file):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    existing_task_id = f.read().strip()
                print(f"📋 发现已有任务ID: {existing_task_id}")
                print(f"将检查任务状态...")
                task_id = existing_task_id
            except Exception as e:
                print(f"❌ 读取任务文件失败: {str(e)}")
                return False
        else:
            # 根据模式选择合适的视频生成方式，直接使用配置文件中的ID
            if is_full_mode:
                print(f"使用landscape模式生成视频")
                task_id = self.gen_short_Video(
                    short_image=character_config['landscape_id'],
                    reference_audio=character_config['voice_id'],
                    text=text,
                    mode="landscape"
                )
            else:
                task_id = self.gen_short_Video(
                    short_image=character_config['short_id'],
                    reference_audio=character_config['voice_id'],
                    text=text,
                    mode="short"
                )

            if not task_id:
                print("❌ 生成短视频任务失败")
                return False

            # 保存任务ID到文件
            try:
                with open(task_file, 'w', encoding='utf-8') as f:
                    f.write(task_id)
                print(f"✅ 任务ID已保存: {task_file}")
            except Exception as e:
                print(f"❌ 保存任务ID失败: {str(e)}")
                return False

        # 轮询任务状态
        max_attempts = 300  # 最多等待3000秒（5分钟）
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            print(f"\n🔄 检查任务状态 (尝试 {retry_count + 1}/{max_retries})")

            for attempt in range(max_attempts):
                print(f"⏳ 等待任务完成... ({attempt + 1}/{max_attempts})")
                time.sleep(30)  # 等待10秒

                status_result = self.check_task_status(task_id)
                if not status_result:
                    print(f"❌ 查询任务状态失败，继续等待...")
                    continue

                code = status_result.get('code', -1)
                msg = status_result.get('msg', '')
                print(f"⏳  ({attempt + 1}/{max_attempts})，📊 任务状态: {msg}{code}")

                if code == 0 and msg == 'success':
                    # 任务成功，获取下载链接
                    data_list = status_result.get('data', [])
                    if data_list:
                        file_url = data_list[0].get('fileUrl', '')
                        if file_url:
                            print(f"🎬 视频生成成功，开始下载...")
                            success = self.download_video(file_url, output_video)
                            if success:
                                # 删除任务文件
                                try:
                                    os.remove(task_file)
                                    print(f"🗑️ 已删除任务文件: {task_file}")
                                except Exception as e:
                                    print(f"⚠️ 删除任务文件失败: {str(e)}")
                                print(f"✅ 幻灯片 {slide_num} 处理完成")
                                return True
                            else:
                                print(f"❌ 视频下载失败")
                                return False
                        else:
                            print(f"❌ 未找到下载链接")
                            return False
                    else:
                        print(f"❌ 响应数据为空")
                        return False

                elif msg in ['APIKEY_TASK_IS_RUNNING', 'APIKEY_TASK_IS_QUEUED']:
                    # 任务还在运行或排队，继续等待
                    print(f"🔄 任务{msg}，继续等待...")
                    continue

                else:
                    # 任务失败或其他错误
                    print(f"❌ 任务执行失败: {msg} (code: {code})")
                    break

            # 如果到这里说明任务超时或失败，尝试重新执行
            retry_count += 1
            if retry_count < max_retries:
                print(f"🔄 任务失败，重新尝试... ({retry_count}/{max_retries})")
                # 删除现有任务文件，重新生成任务
                try:
                    os.remove(task_file)
                except:
                    pass

                print(f"正在重新生成任务...")
                # 根据模式选择合适的视频生成方式，直接使用配置文件中的ID
                if is_full_mode:
                    task_id = self.gen_short_Video(
                        short_image=character_config['landscape_id'],
                        reference_audio=character_config['voice_id'],
                        text=text,
                        mode="landscape"
                    )
                else:
                    task_id = self.gen_short_Video(
                        short_image=character_config['short_id'],
                        reference_audio=character_config['voice_id'],
                        text=text,
                        mode="short"
                    )

                if task_id:
                    # 保存新的任务ID
                    try:
                        with open(task_file, 'w', encoding='utf-8') as f:
                            f.write(task_id)
                    except Exception as e:
                        print(f"❌ 保存新任务ID失败: {str(e)}")
                        return False
                else:
                    print(f"❌ 重新生成任务失败")
                    return False

        # 超过最大重试次数
        print(f"❌ 任务失败，已达到最大重试次数 ({max_retries})")
        return False


def get_webapp_id(mode: str) -> str:
    """
    从环境变量中获取指定模式的webappId

    Args:
        mode: 模式类型，可以是"short", "portrait", "landscape"

    Returns:
        str: 对应的webappId
    """
    env_key_map = {
        "short": "short_webappId",
        "portrait": "portrait_webappId",
        "landscape": "landscape_webappId"
    }

    if mode not in env_key_map:
        raise ValueError(f"不支持的mode: {mode}，支持的类型: {list(env_key_map.keys())}")

    env_key = env_key_map[mode]
    webapp_id = os.getenv(env_key)

    if not webapp_id:
        raise ValueError(f"未找到{env_key}，请在.env文件中配置")

    return webapp_id


def get_api_key() -> str:
    """
    从环境变量中获取API密钥

    Returns:
        str: API密钥
    """
    api_key = os.getenv('RUNNINGHUB_API_KEY')

    if not api_key:
        raise ValueError("未找到RUNNINGHUB_API_KEY，请在.env文件中配置")

    return api_key


def main():
    """主函数，用于单独测试"""
    if len(os.sys.argv) < 2:
        print("用法: python runninghub_api.py <数字人名称>")
        print("示例: python runninghub_api.py man")
        os.sys.exit(1)

    character_name = os.sys.argv[1]
    characters_dir = Path("characters")
    character_dir = characters_dir / character_name

    if not character_dir.exists():
        print(f"错误: 数字人目录 {character_dir} 不存在")
        os.sys.exit(1)

    try:
        api = RunningHubAPI()
        success = api.process_character_files(str(character_dir), character_name)
        os.sys.exit(0 if success else 1)

    except Exception as e:
        print(f"错误: {str(e)}")
        os.sys.exit(1)


if __name__ == "__main__":
    main()