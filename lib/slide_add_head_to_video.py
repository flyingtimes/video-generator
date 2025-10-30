#!/usr/bin/env python3
"""
视频合成工具 - 使用 FFmpeg 将幻灯片图片和视频文件合成为新视频
支持单个文件处理和批量处理功能
"""

import os
import glob
import ffmpeg
from pathlib import Path
from typing import Optional, List, Tuple


def compose_slide_with_video(
    slide_image: str,
    video_file: str,
    mask_path: str,
    output_file: str,
    bg_size: tuple = (1920, 1080),
    fg_size: tuple = (280, 280),
    overlay_position: tuple = (1600, 720),
    crf: int = 23,
    preset: str = "fast"
) -> str:
    """
    将幻灯片图片和视频文件合成为一个新的视频文件

    Args:
        slide_image: 幻灯片图片路径
        video_file: 视频文件路径
        mask_path: 遮罩图片路径
        output_file: 输出视频文件路径
        bg_size: 背景图片尺寸 (width, height)
        fg_size: 前景视频尺寸 (width, height)
        overlay_position: 前景视频在背景上的位置 (x, y)
        crf: 视频质量控制因子 (0-51, 数值越小质量越高)
        preset: 编码速度预设 ('ultrafast', 'superfast', 'veryfast', 'faster', 'fast',
                'medium', 'slow', 'slower', 'veryslow')

    Returns:
        str: 输出文件路径

    Raises:
        FileNotFoundError: 当输入文件不存在时
        ffmpeg.Error: 当 FFmpeg 处理失败时
    """

    # 检查输入文件是否存在
    input_files = [slide_image, video_file, mask_path]
    for file_path in input_files:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"输入文件不存在: {file_path}")

    try:
        # 确保使用绝对路径和正确的路径格式
        slide_image = str(Path(slide_image).absolute())
        video_file = str(Path(video_file).absolute())
        mask_path = str(Path(mask_path).absolute())
        output_file = str(Path(output_file).absolute())

        # 使用ffmpeg-python构建流水线，对应命令行参数：
        # '-i', slide_image,
        # '-i', video_file,
        # '-i', str(mask_path),
        # '-filter_complex',
        # '[0:v]scale=1920:1080,format=rgba,colorchannelmixer=aa=1.0[bg];[1:v]scale=280:280[fg];[2:v]alphaextract[mask];[fg][mask]alphamerge[masked_fg];[bg][masked_fg]overlay=1600:720:format=auto,format=yuv420p',
        input_bg = ffmpeg.input(slide_image)
        input_fg = ffmpeg.input(video_file)
        input_mask = ffmpeg.input(mask_path)

        # 构建滤镜链，对应：[0:v]scale=1920:1080,format=rgba,colorchannelmixer=aa=1.0[bg]
        bg = input_bg.filter('scale', bg_size[0], bg_size[1]).filter('format', 'rgba').filter('colorchannelmixer', aa=1.0)

        # 对应：[1:v]scale=280:280[fg]
        fg = input_fg.filter('scale', fg_size[0], fg_size[1])

        # 对应：[2:v]alphaextract[mask]
        mask = input_mask.filter('alphaextract')

        # 对应：[fg][mask]alphamerge[masked_fg]
        masked_fg = ffmpeg.filter([fg, mask], 'alphamerge')

        # 对应：[bg][masked_fg]overlay=1600:720:format=auto,format=yuv420p
        overlay = ffmpeg.filter([bg, masked_fg], 'overlay', overlay_position[0], overlay_position[1], format='auto').filter('format', 'yuv420p')

        # 获取视频的音频流
        audio_stream = input_fg.audio if hasattr(input_fg, 'audio') else None

        if audio_stream is not None:
            # 如果视频有音频，保留音频
            out = ffmpeg.output(overlay, audio_stream, output_file,
                               vcodec='libx264',
                               preset=preset,
                               crf=crf,
                               acodec='copy')
        else:
            # 如果视频没有音频，只输出视频
            out = ffmpeg.output(overlay, output_file,
                               vcodec='libx264',
                               preset=preset,
                               crf=crf)

        # 运行
        ffmpeg.run(out, overwrite_output=True, capture_stdout=True, capture_stderr=True)

        print(f"视频合成完成: {output_file}")
        return output_file

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        raise RuntimeError(f"FFmpeg 处理失败: {error_msg}")


def create_mask_image(mask_path: str, size: tuple = (280, 280)) -> str:
    """
    创建一个带有过度效果边缘的圆形遮罩图片（RGBA格式，包含alpha通道）

    Args:
        mask_path: 遮罩图片保存路径
        size: 遮罩尺寸 (width, height)

    Returns:
        str: 遮罩图片路径
    """
    try:
        import numpy as np
        from PIL import Image, ImageDraw

        # 使用正方形尺寸，保证圆形效果
        mask_size = max(size)
        # 创建RGBA图像（支持透明度）
        mask = Image.new('RGBA', (mask_size, mask_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(mask)

        # 绘制多层圆形，实现边缘柔和过渡
        center = mask_size // 2
        max_radius = mask_size // 2

        # 外层到内层的渐变
        for i in range(10):
            radius = max_radius - i * 2
            alpha = int(255 - i * 15)  # 渐变透明度
            if alpha > 0 and radius > 0:
                draw.ellipse([center - radius, center - radius, center + radius, center + radius],
                            fill=(255, 255, 255, alpha))

        # 中心完全不透明
        if max_radius > 20:
            center_radius = max_radius - 20
            draw.ellipse([center - center_radius, center - center_radius, center + center_radius, center + center_radius],
                        fill=(255, 255, 255, 255))

        # 直接保存为PNG格式，保留alpha通道
        mask.save(mask_path, 'PNG')
        print(f"✅ 遮罩图片创建完成: {mask_path}")
        return mask_path

    except ImportError:
        raise ImportError("需要安装 Pillow 和 numpy 库来创建遮罩图片: uv add Pillow numpy")


# ==================== 批量处理相关函数 ====================

def check_and_create_directories():
    """创建必要的目录"""
    os.makedirs("output", exist_ok=True)
    os.makedirs("assets", exist_ok=True)


def find_slide_pairs() -> List[Tuple[int, str, str]]:
    """
    查找slides目录下所有有效的图片-视频对
    如果存在png文件但缺少mp4文件，会检查output目录是否已有combine_{num}.mp4

    Returns:
        List[Tuple[int, str, str]]: 包含(编号, png文件, mp4文件)的列表
    """
    slides_dir = Path("slides")
    if not slides_dir.exists():
        print(f"❌ slides目录不存在: {slides_dir}")
        return []

    # 获取所有png文件
    png_files = glob.glob("slides/*.png")
    pairs = []

    for png_file in png_files:
        # 提取数字编号
        base_name = Path(png_file).stem
        if base_name.isdigit():
            num = int(base_name)
            mp4_file = Path("slides") / f"{num}.mp4"
            output_file = Path("output") / f"combine_{num}.mp4"

            # 检查对应的mp4文件是否存在
            if Path(mp4_file).exists():
                pairs.append((num, png_file, mp4_file))
            else:
                # 如果mp4文件不存在，检查output目录是否已有combine_{num}.mp4
                if Path(output_file).exists():
                    print(f"✅ {base_name}.png: 缺少对应的 {base_name}.mp4 文件，但已存在合并结果 {output_file}")
                    pairs.append((num, png_file, mp4_file))
                else:
                    print(f"⚠️  跳过 {base_name}.png: 缺少对应的 {base_name}.mp4 文件，且未找到合并结果")

    # 按数字排序
    pairs.sort(key=lambda x: x[0])
    return pairs


def process_slide_pairs(pairs: List[Tuple[int, str, str]]) -> List[str]:
    """
    处理指定的slide对，合成视频文件

    Args:
        pairs: 包含(编号, png文件, mp4文件)的列表

    Returns:
        List[str]: 成功处理的视频文件路径列表
    """
    if not pairs:
        print("❌ 没有找到有效的图片-视频对")
        return []

    # 创建遮罩文件
    mask_path = "assets/mask.png"
    if not Path(mask_path).exists():
        create_mask_image(mask_path)

    processed_files = []

    for num, png_file, mp4_file in pairs:
        output_file = Path("output") / f"combine_{num}.mp4"

        # 检查输出文件是否已存在
        if Path(output_file).exists():
            print(f"⏭️  combine_{num}.mp4 已存在，跳过")
            processed_files.append(output_file)
            continue

        # 检查对应的mp4文件是否存在
        if not Path(mp4_file).exists():
            print(f"⚠️  跳过第 {num} 组: 缺少对应的 {num}.mp4 文件")
            continue

        print(f"🎬 处理第 {num} 组: {png_file} + {mp4_file}")

        try:
            # 合成视频
            result_path = compose_slide_with_video(
                slide_image=png_file,
                video_file=mp4_file,
                mask_path=mask_path,
                output_file=output_file,
                bg_size=(1920, 1080),
                fg_size=(280, 280),
                overlay_position=(1600, 720),
                crf=23,
                preset="fast"
            )
            processed_files.append(result_path)
            print(f"✅ 合成完成: {result_path}")

        except Exception as e:
            print(f"❌ 处理 {num} 组失败: {e}")

    return processed_files


def merge_videos(video_files: List[str], output_path: str = "output/result.mp4") -> bool:
    """
    将所有视频合并为一个文件，支持智能音频处理，确保音画同步

    Args:
        video_files: 要合并的视频文件列表
        output_path: 输出文件路径

    Returns:
        bool: 合并是否成功
    """
    if not video_files:
        print("❌ 没有视频文件需要合并")
        return False

    print(f"🔄 开始合并 {len(video_files)} 个视频文件...")

    try:
        # 创建输入流
        inputs = [ffmpeg.input(file) for file in video_files]

        # 检查视频文件是否包含音频，并获取详细信息
        has_audio = []
        for i, file in enumerate(video_files):
            try:
                probe = ffmpeg.probe(file)
                audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
                has_audio.append(len(audio_streams) > 0)

                if len(audio_streams) > 0:
                    print(f"📹 视频 {i+1} ({Path(file).name}): 包含音频流")
                else:
                    print(f"📹 视频 {i+1} ({Path(file).name}): 无音频流")

            except Exception as e:
                print(f"⚠️  无法检测视频 {i+1} 的音频信息: {e}")
                has_audio.append(False)

        # 如果所有视频都没有音频，合并时只处理视频
        if not any(has_audio):
            print("ℹ️  检测到所有视频都没有音频，将创建无声视频")
            (
                ffmpeg
                .concat(*inputs)
                .output(output_path, vcodec='libx264', preset='medium', crf=23)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        else:
            # 使用改进的同步合并方法
            print("ℹ️  检测到视频包含音频，将使用音画同步合并")

            # 使用分离式处理，但对每个有音频的视频保持音画同步
            # 这种方法更可靠，能正确处理部分视频有音频的情况

            # 构建输入流列表
            input_streams = []
            for i, input_file in enumerate(inputs):
                input_streams.append(input_file.video)  # 视频流
                if has_audio[i]:
                    input_streams.append(input_file.audio)  # 音频流（如果有）

            # 计算需要处理的视频和音频流数量
            video_count = len(inputs)
            audio_count = sum(has_audio)

            if audio_count == 0:
                # 所有视频都没有音频
                concat = ffmpeg.concat(*inputs)
                out = ffmpeg.output(concat, output_path, vcodec='libx264', preset='medium', crf=23)
            else:
                # 使用分离式合并，但保持音画同步
                # 创建临时文件列表
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                    temp_list_path = temp_file.name
                    for file in video_files:
                        temp_file.write(f"file '{Path(file).absolute()}'\n")

                # 使用ffmpeg的concat demuxer进行合并，这是最可靠的音画同步方法
                import subprocess
                cmd = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', temp_list_path,
                    '-c', 'copy',  # 直接复制流，避免重新编码导致的问题
                    '-y',          # 覆盖输出文件
                    output_path
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)
                Path(temp_list_path).unlink()  # 删除临时文件

                if result.returncode != 0:
                    raise RuntimeError(f"FFmpeg concat failed: {result.stderr}")

        print(f"✅ 合并完成: {output_path}")

        # 验证合并后的音画同步
        try:
            probe = ffmpeg.probe(output_path)
            video_streams = [s for s in probe['streams'] if s['codec_type'] == 'video']
            audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']

            if len(video_streams) > 0 and len(audio_streams) > 0:
                video_duration = float(video_streams[0].get('duration', 0))
                audio_duration = float(audio_streams[0].get('duration', 0))

                if abs(video_duration - audio_duration) > 0.1:
                    print(f"⚠️  警告: 合并后的视频存在音画时长差异 - 视频: {video_duration:.2f}s, 音频: {audio_duration:.2f}s")
                else:
                    print("✅ 音画同步检查通过")

        except Exception as e:
            print(f"⚠️  无法验证音画同步: {e}")

        return True

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"❌ 合并失败: {error_msg}")
        return False
    except Exception as e:
        print(f"❌ 合并过程中出错: {e}")
        return False
