#!/usr/bin/env python3
"""
视频生成项目主程序
整合PDF处理、PPT备注提取、视频生成和数字人上传功能
"""

import sys
import os
import shutil
import glob
import subprocess
from pathlib import Path
import argparse

# 添加lib目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "lib"))

from lib.logger import get_logger, execution_time_logger, step_logger

from lib.pdf_to_png import (
    create_directories,
    find_pdf_files,
    batch_process_pdfs
)
from lib.ppt_to_txt import extract_notes_from_pptx, find_pptx_file
from lib.runninghub_api import RunningHubAPI
from lib.slide_add_head_to_video import (
    check_and_create_directories,
    find_slide_pairs,
    process_slide_pairs,
    merge_videos
)
from lib.runninghub_api import get_api_key
from lib.gamma_api import generate_pptx_from_prompt
from lib.glm_api import talk_to_ai


@execution_time_logger("清空目录")
@step_logger("清空slides和output目录")
def clear_directories():
    """清空slides和output目录中的所有文件"""
    slides_dir = Path("slides")
    output_dir = Path("output")

    cleared_something = False

    # 清空slides目录
    if slides_dir.exists():
        files = list(slides_dir.glob("*"))
        if files:
            print(f"🗑️  清空slides目录中的 {len(files)} 个文件...")
            for file in files:
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file)
            cleared_something = True
        else:
            print("📁 slides目录已经是空的")
    else:
        print("📁 slides目录不存在，跳过")

    # 清空output目录
    if output_dir.exists():
        files = list(output_dir.glob("*"))
        if files:
            print(f"🗑️  清空output目录中的 {len(files)} 个文件...")
            for file in files:
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file)
            cleared_something = True
        else:
            print("📁 output目录已经是空的")
    else:
        print("📁 output目录不存在，跳过")

    if cleared_something:
        print("✅ 目录清空完成")

    return True


@execution_time_logger("处理PDF文件")
@step_logger("处理PDF文件")
def process_pdf():
    """处理input目录中的第一个PDF文件"""
    print("🔄 步骤2: 处理PDF文件")
    print("-" * 40)

    # 创建必要目录
    create_directories()

    # 查找PDF文件
    pdf_files = find_pdf_files()

    if not pdf_files:
        print("❌ 在input目录下没有找到PDF文件")
        return False

    # 只处理第一个PDF文件
    first_pdf = pdf_files[0]
    print(f"📋 处理PDF文件: {os.path.basename(first_pdf)}")

    # 处理这个PDF文件
    try:
        from lib.pdf_to_png import process_pdf_to_slides
        result_files = process_pdf_to_slides(first_pdf, target_size=(1920, 1080))

        if result_files:
            print(f"✅ PDF处理完成，生成了 {len(result_files)} 个PNG文件")
            return True
        else:
            print("❌ PDF处理失败，没有生成任何文件")
            return False
    except Exception as e:
        print(f"❌ PDF处理过程中发生错误: {str(e)}")
        return False


@execution_time_logger("处理PPT备注")
@step_logger("处理PPT备注提取")
def process_ppt():
    """处理PPT/PPTX文件的备注"""
    print("🔄 步骤3: 处理PPT备注提取")
    print("-" * 40)

    input_path = Path("input")
    pptx_file = None

    # 首先尝试查找与PDF同名的PPTX文件
    pdf_files = list(input_path.glob("*.pdf"))
    if pdf_files:
        base_name = pdf_files[0].stem
        print(f"📋 首先查找与PDF同名的PPT文件: {base_name}")
        pptx_file = find_pptx_file("input", base_name)

    # 如果没找到同名的PPTX文件，尝试查找生成的PPTX文件
    if not pptx_file:
        print("📋 未找到同名PPT文件，尝试查找生成的PPTX文件")
        generated_pptx = input_path / "generated.pptx"
        if generated_pptx.exists():
            pptx_file = str(generated_pptx)
            print(f"📄 找到生成的PPT文件: {generated_pptx.name}")

    # 如果仍然没找到，尝试查找任何PPTX文件
    if not pptx_file:
        print("📋 查找任何可用的PPTX文件")
        pptx_files = list(input_path.glob("*.pptx")) + list(input_path.glob("*.ppt"))
        if pptx_files:
            pptx_file = str(pptx_files[0])
            print(f"📄 找到PPT文件: {pptx_files[0].name}")

    if not pptx_file:
        print("❌ 在input目录下没有找到任何PPTX/PPT文件")
        return False

    print(f"📄 将使用PPT文件: {os.path.basename(pptx_file)}")

    # 处理PPT文件
    try:
        success = extract_notes_from_pptx(pptx_file, "slides")

        if success:
            print("✅ PPT备注提取完成")
            return True
        else:
            print("❌ PPT备注提取失败")
            return False
    except Exception as e:
        print(f"❌ PPT处理过程中发生错误: {str(e)}")
        return False


@execution_time_logger("生成slide视频")
@step_logger("生成slide视频")
def generate_slide_videos(digital_human: str = "man"):
    """生成每个slide的视频"""
    print("🔄 步骤4: 生成slide视频")
    print("-" * 40)

    try:
        # 创建API客户端
        api = RunningHubAPI()
        print("✅ 成功创建API客户端")

        # 数字人选择
        print(f"🎭 使用数字人: {digital_human}")

        success_count = 0
        skip_count = 0
        fail_count = 0

        # 查找所有slide文本文件
        slides_dir = Path("slides")
        txt_files = sorted(slides_dir.glob("*.txt"), key=lambda x: int(x.stem) if x.stem.isdigit() else 0)

        if not txt_files:
            print("❌ 在slides目录中没有找到文本文件")
            return False

        print(f"📋 找到 {len(txt_files)} 个文本文件")

        for txt_file in txt_files:
            slide_num = txt_file.stem
            print(f"\n🎬 处理幻灯片 {slide_num}")

            # 检查是否为full模式
            is_full_mode = False
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    text = f.read().strip()
                is_full_mode = text.startswith('[full]')
            except Exception as e:
                print(f"⚠️ 读取文本文件失败: {str(e)}")

            # 检查对应视频文件是否已存在
            if is_full_mode:
                mp4_file_path = f"output/combine_{slide_num}.mp4"
            else:
                mp4_file_path = f"slides/{slide_num}.mp4"

            if os.path.exists(mp4_file_path):
                print(f"⏭️ 视频文件已存在，跳过: {mp4_file_path}")
                skip_count += 1
                continue

            # 调用API生成视频
            try:
                slide_num_int = int(slide_num)
                result = api.gen_slide_video(slide_num_int, digital_human)

                if result is True:
                    print(f"✅ 幻灯片 {slide_num} 处理成功")
                    success_count += 1
                elif result == "skip":
                    print(f"⏭️ 幻灯片 {slide_num} 文本为空，已跳过")
                    skip_count += 1
                else:
                    print(f"❌ 幻灯片 {slide_num} 处理失败")
                    fail_count += 1
            except ValueError:
                print(f"❌ 无效的幻灯片编号: {slide_num}")
                fail_count += 1
            except Exception as e:
                print(f"❌ 处理幻灯片 {slide_num} 时发生错误: {str(e)}")
                fail_count += 1

        # 统计结果
        print(f"\n📊 视频生成完成！统计结果:")
        print(f"✅ 成功: {success_count} 个")
        print(f"⏭️ 跳过: {skip_count} 个")
        print(f"❌ 失败: {fail_count} 个")

        if fail_count == 0:
            print("🎉 所有幻灯片视频生成成功！")
            return True
        else:
            print("⚠️ 部分幻灯片视频生成失败")
            return False

    except Exception as e:
        print(f"❌ 视频生成过程中发生错误: {str(e)}")
        return False


@execution_time_logger("批量处理slides")
@step_logger("批量处理slides文件")
def batch_process_slides():
    """批量处理slides目录中的文件"""
    print("🔄 步骤5: 批量处理slides文件")
    print("-" * 40)

    try:
        # 检查并创建目录
        check_and_create_directories()

        # 查找slide对
        pairs = find_slide_pairs()

        if not pairs:
            print("❌ 没有找到任何有效的图片-视频对")
            return False

        print(f"📁 找到 {len(pairs)} 个有效的图片-视频对")

        # 批量处理slide对
        processed_files = process_slide_pairs(pairs)

        if not processed_files:
            print("❌ 没有成功处理任何文件")
            return False

        print(f"✅ 成功处理 {len(processed_files)} 个文件")

        # 合并所有结果
        print("🔄 开始合并最终结果...")
        success = merge_videos(processed_files)

        if success:
            print("✅ 批量处理完成！")
            print(f"📹 最终输出文件: output/result.mp4")
            return True
        else:
            print("❌ 最终合并失败")
            return False

    except Exception as e:
        print(f"❌ 批量处理过程中发生错误: {str(e)}")
        return False


def count_pages_from_scripts():
    """从scripts.txt文件中计算页数"""
    scripts_file = Path("input/scripts.txt")

    if not scripts_file.exists():
        print(f"❌ 讲稿文件不存在: {scripts_file}")
        print("请先使用 --prepare 参数生成讲稿文件")
        return 0

    try:
        with open(scripts_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            print(f"❌ 讲稿文件为空: {scripts_file}")
            return 0

        # 使用"---"分隔符计算页数
        pages = content.split('---')
        # 过滤掉空页面
        pages = [page.strip() for page in pages if page.strip()]
        page_count = len(pages)

        print(f"📄 从讲稿文件中计算出页数: {page_count} 页")
        return page_count

    except Exception as e:
        print(f"❌ 读取讲稿文件时发生错误: {str(e)}")
        return 0


def generate_pptx():
    """根据提示词文件生成PPTX文件"""
    print("🔄 生成PPTX文件")
    print("-" * 40)

    try:
        # 从scripts.txt文件计算页数
        num_cards = count_pages_from_scripts()

        if num_cards == 0:
            print("❌ 无法获取页数，请先运行 --prepare 生成讲稿文件")
            return False

        # 检查提示词文件是否存在
        prompt_file = "input/prompt.txt"
        if not Path(prompt_file).exists():
            print(f"❌ 提示词文件不存在: {prompt_file}")
            print("请先使用 --prepare 参数生成提示词文件")
            return False

        print(f"📖 读取提示词文件: {prompt_file}")
        print(f"📄 自动计算幻灯片数量: {num_cards}")

        # 生成PPTX
        result = generate_pptx_from_prompt(
            prompt_file=prompt_file,
            output_dir="input",
            themeName="企业汇报模版",
            numCards=num_cards,
            additionalInstructions="创建一个专业的演示文稿，包含清晰的标题和结构化的内容",
            textOptions={
                "amount": "brief",
                "tone": "professional",
                "audience": "general",
                "language": "zh-cn"
            },
            imageOptions={
                "source": "aiGenerated",
                "model": "imagen-3-pro",
                "style": "现实风格"
            },
            cardOptions={"dimensions": "16x9"}
        )

        if result:
            print(f"✅ PPTX文件生成成功: {result}")
            return True
        else:
            print("❌ PPTX文件生成失败")
            return False

    except Exception as e:
        print(f"❌ PPTX生成过程中发生错误: {str(e)}")
        return False




@execution_time_logger("准备标题、封面和内容")
@step_logger("准备标题、封面和内容")
def prepare_title_and_cover_and_content():
    """准备标题、封面和内容：生成标题、创建封面图片、拆分内容并生成讲稿"""
    print("🔄 准备标题、封面和内容")
    print("-" * 40)

    try:
        # 检查必要文件是否存在
        essay_file = Path("input/essay.txt")
        prompt_file = Path("assets/gen_title_prompt.prompt")

        if not essay_file.exists():
            print(f"❌ 文章文件不存在: {essay_file}")
            print("请在input目录下创建essay.txt文件并添加文章内容")
            return False

        if not prompt_file.exists():
            print(f"❌ 提示词文件不存在: {prompt_file}")
            return False

        # 读取文章内容
        print(f"📖 读取文章文件: {essay_file}")
        with open(essay_file, 'r', encoding='utf-8') as f:
            essay_content = f.read().strip()

        if not essay_content:
            print(f"❌ 文章文件为空: {essay_file}")
            return False

        print(f"📄 文章内容长度: {len(essay_content)} 字符")

        # 计算中文字符数量并确定页数
        import re
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', essay_content)
        chinese_char_count = len(chinese_chars)

        # 根据中文字符数计算页数（每500字一页，向上取整）
        import math
        page = math.ceil(chinese_char_count / 400) if chinese_char_count > 0 else 1

        print(f"📊 中文字符数量: {chinese_char_count} 个")
        print(f"📄 自动计算页数: {page} 页")

        # 调用GLM API生成标题
        print("🤖 正在生成标题...")
        try:
            title = talk_to_ai(str(prompt_file), essay_content)

            if not title:
                print("❌ 标题生成失败，返回空内容")
                return False

            # 清理标题内容（去除多余的空白字符）
            title = title.strip()
            print(f"✅ 标题生成成功: {title}")

        except Exception as e:
            print(f"❌ 调用GLM API生成标题时发生错误: {str(e)}")
            return False

        # 保存标题到文件
        title_file = Path("input/title.txt")
        try:
            with open(title_file, 'w', encoding='utf-8') as f:
                f.write(title)
            print(f"✅ 标题已保存到: {title_file}")
        except Exception as e:
            print(f"❌ 保存标题文件时发生错误: {str(e)}")
            return False

        # 更新 biliconfig.yaml 文件中的 title 和 desc 字段
        print("🔄 正在更新 biliconfig.yaml 配置文件...")
        try:
            config_file = Path("assets/biliconfig.yaml")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_content = f.read()

                # 简单的字符串替换来更新 title 和 desc 字段
                lines = config_content.split('\n')
                updated_lines = []

                for line in lines:
                    if line.startswith('title:'):
                        updated_lines.append(f'title: {title}')
                    elif line.startswith('desc:'):
                        updated_lines.append(f'desc: {title}')
                    else:
                        updated_lines.append(line)

                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(updated_lines))

                print(f"✅ biliconfig.yaml 文件已更新，标题: {title}")
            else:
                print(f"⚠️ biliconfig.yaml 文件不存在: {config_file}")
        except Exception as e:
            print(f"⚠️ 更新 biliconfig.yaml 文件时发生错误: {str(e)}")
            # 不返回 False，因为这不是关键错误

        # 创建封面图片
        cover_path = Path("input/cover.jpg")
        if cover_path.exists():
            print("✅ 封面图片已存在，跳过创建")
            print(f"📁 使用现有封面: {cover_path}")
        else:
            print("🎨 正在创建封面图片...")
            try:
                api = RunningHubAPI()
                cover_success = api.create_cover(title)

                if not cover_success:
                    print("❌ 封面创建失败")
                    return False

                print("✅ 封面创建成功")
            except Exception as e:
                print(f"❌ 创建封面时发生错误: {str(e)}")
                return False

        # 第3步：拆分内容
        print(f"📝 正在拆分内容为 {page} 页...")
        try:
            split_prompt_file = Path("assets/split_content.prompt")
            if not split_prompt_file.exists():
                print(f"❌ 内容拆分提示词文件不存在: {split_prompt_file}")
                return False

            # 读取拆分提示词并替换页数参数
            with open(split_prompt_file, 'r', encoding='utf-8') as f:
                split_prompt = f.read().strip()

            # 将页数参数填入提示词
            split_prompt = split_prompt.replace("{page}", str(page))
            # 调用GLM API拆分内容
            split_content = talk_to_ai(split_prompt, essay_content, model="GLM-4.5-Flash", is_content=True)

            if not split_content:
                print("❌ 内容拆分失败，返回空内容")
                return False

            split_content = split_content.strip()
            print(f"✅ 内容拆分成功，长度: {len(split_content)} 字符")

        except Exception as e:
            print(f"❌ 拆分内容时发生错误: {str(e)}")
            return False

        # 保存拆分后的内容
        prompt_file = Path("input/prompt.txt")
        try:
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(split_content)
            print(f"✅ 拆分内容已保存到: {prompt_file}")
        except Exception as e:
            print(f"❌ 保存拆分内容时发生错误: {str(e)}")
            return False

        # 第4步：生成讲稿
        print("📜 正在生成讲稿（使用GLM-4.6模型）...")
        try:
            scripts_prompt_file = Path("assets/gen_scripts.prompt")
            if not scripts_prompt_file.exists():
                print(f"❌ 讲稿生成提示词文件不存在: {scripts_prompt_file}")
                return False

            # 使用GLM-4.6模型生成讲稿
            scripts_content = talk_to_ai(str(scripts_prompt_file), split_content, model="GLM-4.6")

            if not scripts_content:
                print("❌ 讲稿生成失败，返回空内容")
                return False

            scripts_content = scripts_content.strip()
            print(f"✅ 讲稿生成成功，长度: {len(scripts_content)} 字符")

        except Exception as e:
            print(f"❌ 生成讲稿时发生错误: {str(e)}")
            return False

        # 保存讲稿内容
        scripts_file = Path("input/scripts.txt")
        try:
            with open(scripts_file, 'w', encoding='utf-8') as f:
                f.write(scripts_content)
            print(f"✅ 讲稿已保存到: {scripts_file}")
        except Exception as e:
            print(f"❌ 保存讲稿时发生错误: {str(e)}")
            return False

        print("🎉 所有任务完成！")
        print("📋 已生成：标题、封面、拆分内容和讲稿")
        return True

    except Exception as e:
        print(f"❌ 准备过程中发生错误: {str(e)}")
        return False


def clear_input_directory_except_essay():
    """清空input目录中除essay.txt外的所有文件"""
    input_dir = Path("input")
    if not input_dir.exists():
        print("📁 input目录不存在，跳过")
        return True

    files_to_keep = {"essay.txt"}
    files_found = list(input_dir.glob("*"))

    if not files_found:
        print("📁 input目录已经是空的")
        return True

    files_to_delete = [f for f in files_found if f.name not in files_to_keep]

    if not files_to_delete:
        print("📁 input目录中没有需要删除的文件")
        return True

    print(f"🗑️  准备删除input目录中的 {len(files_to_delete)} 个文件（保留essay.txt）...")

    for file in files_to_delete:
        try:
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                shutil.rmtree(file)
        except Exception as e:
            print(f"⚠️ 删除文件失败: {file} - {str(e)}")

    print("✅ input目录清理完成")
    return True


def check_os_and_pdf_status():
    """检查操作系统和PDF文件状态"""
    import platform
    current_os = platform.system().lower()

    print(f"🖥️ 当前操作系统: {current_os}")

    if current_os == "darwin":  # macOS
        print("🍎 检测到macOS系统")

        # 检查是否已有PDF文件
        input_dir = Path("input")
        pdf_files = list(input_dir.glob("*.pdf")) if input_dir.exists() else []

        if pdf_files:
            print(f"📄 发现PDF文件: {', '.join([f.name for f in pdf_files])}")
            return True, current_os
        else:
            print("❓ 未发现PDF文件")
            while True:
                try:
                    answer = input("你是否已经手动创建了PDF文件? (y/n): ").lower().strip()
                    if answer in ['y', 'yes', '是']:
                        return True, current_os
                    elif answer in ['n', 'no', '否']:
                        return False, current_os
                    else:
                        print("请输入 y/yes/是 或 n/no/否")
                except KeyboardInterrupt:
                    print("\n\n操作已取消")
                    return False, current_os
    else:
        print(f"💻 检测到 {current_os} 系统")
        return True, current_os


def upload_video_to_bilibili():
    """上传视频到B站，如果失败则尝试renew后重试"""
    print("📺 开始上传视频到B站")
    print("-" * 40)

    try:
        import platform
        current_os = platform.system().lower()

        # 根据操作系统选择biliup可执行文件
        if current_os == "windows":
            biliup_exe = Path("biliup/biliup_win.exe")
        elif current_os == "darwin":
            biliup_exe = Path("biliup/biliup_macos")
        else:
            print(f"❌ 不支持的操作系统: {current_os}")
            return False

        config_file = Path("assets/biliconfig.yaml")

        if not biliup_exe.exists():
            print(f"❌ biliup可执行文件不存在: {biliup_exe}")
            return False

        if not config_file.exists():
            print(f"❌ biliup配置文件不存在: {config_file}")
            return False

        # 尝试上传的函数
        def attempt_upload():
            upload_cmd = [str(biliup_exe), "upload", "-c", str(config_file)]
            print(f"🚀 执行上传命令: {' '.join(upload_cmd)}")
            print("⏳ 上传过程可能需要较长时间，请耐心等待...")

            result = subprocess.run(upload_cmd, cwd=project_root, capture_output=True, text=True)
            return result

        # 第一次尝试上传
        result = attempt_upload()

        if result.returncode == 0:
            print("✅ 视频上传成功！")
            if result.stdout:
                print("📋 上传输出:")
                print(result.stdout)
            return True
        else:
            print("❌ 视频上传失败")
            if result.stderr:
                print("❌ 错误信息:")
                print(result.stderr)

            # 检查错误信息是否包含登录相关的错误
            error_output = (result.stderr or "").lower() + (result.stdout or "").lower()
            login_error_keywords = ["登录", "login", "认证", "auth", "cookie", "session", "token", "过期", "expire"]

            if any(keyword in error_output for keyword in login_error_keywords):
                print("🔄 检测到可能的登录问题，尝试执行renew刷新登录信息...")

                # 执行renew命令
                renew_cmd = [str(biliup_exe), "renew", "-c", str(config_file)]
                print(f"🔄 执行renew命令: {' '.join(renew_cmd)}")

                renew_result = subprocess.run(renew_cmd, cwd=project_root, capture_output=True, text=True)

                if renew_result.returncode == 0:
                    print("✅ renew执行成功，登录信息已刷新")
                    if renew_result.stdout:
                        print("📋 renew输出:")
                        print(renew_result.stdout)

                    # renew成功后重新尝试上传
                    print("🔄 重新尝试上传视频...")
                    retry_result = attempt_upload()

                    if retry_result.returncode == 0:
                        print("✅ renew后视频上传成功！")
                        if retry_result.stdout:
                            print("📋 重试上传输出:")
                            print(retry_result.stdout)
                        return True
                    else:
                        print("❌ renew后重新上传仍然失败")
                        if retry_result.stderr:
                            print("❌ 重试错误信息:")
                            print(retry_result.stderr)
                        return False
                else:
                    print("❌ renew执行失败")
                    if renew_result.stderr:
                        print("❌ renew错误信息:")
                        print(renew_result.stderr)
                    return False
            else:
                print("❌ 未检测到登录相关错误，不执行renew")
                return False

    except Exception as e:
        print(f"❌ 上传过程中发生错误: {str(e)}")
        return False


@execution_time_logger("完整自动化流程")
@step_logger("完整自动化流程")
def run_full_workflow(digital_human: str = "man"):
    """运行完整的自动化流程"""
    print("🚀 开始完整自动化流程")
    print("=" * 60)

    # 步骤1: 检查必要文件
    print("🔄 步骤1: 检查必要文件")
    print("-" * 40)

    essay_file = Path("input/essay.txt")
    if not essay_file.exists():
        print("❌ 未找到input/essay.txt文件")
        print("💡 请先在input目录下创建essay.txt文件并添加文章内容")
        return False

    print(f"✅ 找到文章文件: {essay_file}")
    print(f"📄 文章大小: {essay_file.stat().st_size} 字节")
    print("✅ 步骤1完成\n")

    # 步骤2: 清理目录（保留essay.txt）
    print("🔄 步骤2: 清理目录")
    print("-" * 40)

    while True:
        try:
            answer = input("是否需要清空input目录（保留essay.txt）、slides和output目录中的所有文件? (y/n): ").lower().strip()
            if answer in ['y', 'yes', '是']:
                # 清理input目录（保留essay.txt）
                clear_input_directory_except_essay()
                # 清理slides和output目录
                clear_directories()
                break
            elif answer in ['n', 'no', '否']:
                print("跳过清理目录操作")
                break
            else:
                print("请输入 y/yes/是 或 n/no/否")
        except KeyboardInterrupt:
            print("\n\n操作已取消")
            return False

    print("✅ 步骤2完成\n")

    # 步骤3: 准备内容（prepare）
    print("🔄 步骤3: 准备标题、封面和内容")
    print("-" * 40)
    success = prepare_title_and_cover_and_content()
    if not success:
        print("❌ 步骤3失败，工作流程终止")
        return False
    print("✅ 步骤3完成\n")

    # 步骤4: 生成PPT（create-ppt）
    print("🔄 步骤4: 生成PPTX文件")
    print("-" * 40)
    success = generate_pptx()
    if not success:
        print("❌ 步骤4失败，工作流程终止")
        return False
    print("✅ 步骤4完成\n")

    # 步骤5: 检查操作系统和PDF状态
    print("🔄 步骤5: 检查PDF文件状态")
    print("-" * 40)
    has_pdf, current_os = check_os_and_pdf_status()
    if not has_pdf:
        print("❌ 未检测到PDF文件，工作流程终止")
        print("💡 请先创建PDF文件后重新运行")
        return False
    print("✅ 步骤5完成\n")

    # 步骤6-9: 执行视频生成流程
    print("🔄 步骤6-9: 执行视频生成流程")
    print("-" * 40)

    # 执行标准流程
    steps = [
        ("处理PDF文件", process_pdf),
        ("处理PPT备注", process_ppt),
        ("生成slide视频", lambda: generate_slide_videos(digital_human)),
        ("批量处理slides", batch_process_slides)
    ]

    for i, (step_name, step_func) in enumerate(steps, 6):
        print(f"🔄 步骤{i}: {step_name}")
        print("-" * 40)

        success = step_func()

        if not success:
            print(f"❌ 步骤{i}失败，工作流程终止")
            return False

        print(f"✅ 步骤{i}完成\n")

    # 步骤10: 上传视频到B站（publish）
    print("🔄 步骤10: 上传视频到B站")
    print("-" * 40)

    while True:
        try:
            answer = input("是否需要上传视频到B站? (y/n): ").lower().strip()
            if answer in ['y', 'yes', '是']:
                upload_success = upload_video_to_bilibili()
                if not upload_success:
                    print("⚠️ 视频上传失败，但视频文件已生成在output/result.mp4")
                break
            elif answer in ['n', 'no', '否']:
                print("跳过视频上传操作")
                break
            else:
                print("请输入 y/yes/是 或 n/no/否")
        except KeyboardInterrupt:
            print("\n\n操作已取消")
            return False

    print("🎉 完整自动化流程执行完成！")
    print(f"📹 最终输出文件: output/result.mp4")
    return True


def upload_digital_human(character_name: str = "man"):
    """上传数字人文件"""
    print(f"🔄 数字人上传: {character_name}")
    print("-" * 40)

    try:
        api_key = get_api_key()
        api = RunningHubAPI(api_key)

        # 检查数字人目录是否存在
        character_dir = Path("characters") / character_name
        if not character_dir.exists():
            print(f"❌ 数字人目录不存在: {character_dir}")
            return False

        print(f"📂 处理数字人目录: {character_dir}")

        success = api.process_character_files(str(character_dir), character_name)

        if success:
            print(f"✅ 数字人 {character_name} 上传成功")
            return True
        else:
            print(f"❌ 数字人 {character_name} 上传失败")
            return False

    except Exception as e:
        print(f"❌ 数字人上传过程中发生错误: {str(e)}")
        return False


@execution_time_logger("完整工作流程")
@step_logger("完整视频生成工作流程")
def run_complete_workflow(digital_human: str = "man"):
    """运行完整的工作流程"""
    print("🚀 开始完整视频生成工作流程")
    print("=" * 60)

    # 步骤1: 询问是否清空目录
    print("🔄 步骤1: 清空slides和output目录")
    print("-" * 40)

    while True:
        try:
            answer = input("是否需要清空slides和output中的所有文件? (y/n): ").lower().strip()
            if answer in ['y', 'yes', '是']:
                clear_directories()
                break
            elif answer in ['n', 'no', '否']:
                print("跳过清空目录操作")
                break
            else:
                print("请输入 y/yes/是 或 n/no/否")
        except KeyboardInterrupt:
            print("\n\n操作已取消")
            return False

    print()

    # 步骤2-5: 执行完整流程
    steps = [
        ("处理PDF文件", process_pdf),
        ("处理PPT备注", process_ppt),
        ("生成slide视频", lambda: generate_slide_videos(digital_human)),
        ("批量处理slides", batch_process_slides)
    ]

    for i, (step_name, step_func) in enumerate(steps, 2):
        print(f"🔄 步骤{i}: {step_name}")
        print("-" * 40)

        success = step_func()

        if not success:
            print(f"❌ 步骤{i}失败，工作流程终止")
            return False

        print(f"✅ 步骤{i}完成\n")

    print("🎉 完整工作流程执行完成！")
    print(f"📹 最终输出文件: output/result.mp4")
    return True


@execution_time_logger("主程序执行")
def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="视频生成项目主程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                          # 运行完整工作流程（使用默认数字人 man）
  %(prog)s --digital-human woman    # 运行完整工作流程（使用 woman 数字人）
  %(prog)s --full                   # 运行完整自动化流程（从essay.txt到B站上传）
  %(prog)s --full --digital-human woman  # 运行完整自动化流程（使用 woman 数字人）
  %(prog)s --clear                  # 仅清空slides和output目录
  %(prog)s --pdf                    # 仅处理PDF文件
  %(prog)s --ppt                    # 仅处理PPT备注提取
  %(prog)s --generate               # 仅生成slide视频
  %(prog)s --generate --digital-human woman  # 仅生成slide视频（使用 woman 数字人）
  %(prog)s --batch                  # 仅批量处理slides
  %(prog)s --upload man             # 上传指定数字人
  %(prog)s --upload all             # 批量上传所有数字人
  %(prog)s --create-ppt             # 生成PPTX（自动从scripts.txt文件计算页数）
  %(prog)s --prepare                # 准备标题和封面（基于essay.txt生成标题并创建封面，自动根据中文长度计算页数）
  %(prog)s --publish                # 上传视频到B站（需要output/result.mp4文件存在）
        """
    )

    parser.add_argument("--full", action="store_true", help="运行完整自动化流程（从essay.txt到B站上传）")
    parser.add_argument("--clear", action="store_true", help="清空slides和output目录")
    parser.add_argument("--pdf", action="store_true", help="仅处理PDF文件")
    parser.add_argument("--ppt", action="store_true", help="仅处理PPT备注提取")
    parser.add_argument("--generate", action="store_true", help="仅生成slide视频")
    parser.add_argument("--batch", action="store_true", help="仅批量处理slides")
    parser.add_argument("--upload", metavar="NAME", help="上传指定数字人 (如: man, woman, all)")
    parser.add_argument("--digital-human", metavar="NAME", default="man",
                       help="指定使用的数字人 (默认: man)")
    parser.add_argument("--create-ppt", action="store_true",
                       help="根据提示词文件生成PPTX (自动从scripts.txt文件计算页数)")
    parser.add_argument("--prepare", action="store_true",
                       help="准备标题和封面（基于essay.txt生成标题并创建封面，自动根据中文长度计算页数）")
    parser.add_argument("--publish", action="store_true",
                       help="上传视频到B站（需要output/result.mp4文件存在）")

    args = parser.parse_args()

    # 根据参数执行相应功能
    if args.full:
        return run_full_workflow(args.digital_human)
    elif args.clear:
        return clear_directories()
    elif args.pdf:
        return process_pdf()
    elif args.ppt:
        return process_ppt()
    elif args.generate:
        return generate_slide_videos(args.digital_human)
    elif args.batch:
        return batch_process_slides()
    elif args.upload is not None:
        if args.upload.lower() == "all":
            # 批量上传所有数字人
            characters_dir = Path("characters")
            if characters_dir.exists():
                character_dirs = [d for d in characters_dir.iterdir() if d.is_dir()]
                if not character_dirs:
                    print("❌ 在characters目录中未找到任何数字人子目录")
                    return False

                success_count = 0
                for char_dir in character_dirs:
                    if upload_digital_human(char_dir.name):
                        success_count += 1

                print(f"\n📊 上传完成！成功: {success_count}/{len(character_dirs)}")
                return success_count == len(character_dirs)
            else:
                print("❌ characters目录不存在")
                return False
        else:
            return upload_digital_human(args.upload)
    elif args.create_ppt:
        return generate_pptx()
    elif args.prepare:
        return prepare_title_and_cover_and_content()
    elif args.publish:
        return upload_video_to_bilibili()
    else:
        # 没有指定参数，运行完整工作流程
        return run_complete_workflow(args.digital_human)


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序执行过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)