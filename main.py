#!/usr/bin/env python3
"""
视频生成项目主程序
整合PDF处理、PPT备注提取、视频生成和数字人上传功能
"""

import sys
import os
import shutil
import glob
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
    """处理与PDF同名的PPT/PPTX文件"""
    print("🔄 步骤3: 处理PPT备注提取")
    print("-" * 40)

    # 查找PDF文件获取基础名称
    input_path = Path("input")
    pdf_files = list(input_path.glob("*.pdf"))

    if not pdf_files:
        print("❌ 在input目录下没有找到PDF文件")
        return False

    # 使用第一个PDF的基础名称
    base_name = pdf_files[0].stem
    print(f"📋 查找与 {base_name} 同名的PPT文件")

    # 查找对应的PPTX/PPT文件
    pptx_file = find_pptx_file("input", base_name)

    if not pptx_file:
        print(f"❌ 未找到与 {base_name} 对应的PPTX/PPT文件")
        return False

    print(f"📄 找到匹配的PPT文件: {os.path.basename(pptx_file)}")

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


def generate_pptx(num_cards: int = 6):
    """根据提示词文件生成PPTX文件"""
    print("🔄 生成PPTX文件")
    print("-" * 40)

    try:
        # 检查提示词文件是否存在
        prompt_file = "input/prompt.txt"
        if not Path(prompt_file).exists():
            print(f"❌ 提示词文件不存在: {prompt_file}")
            print("请在input目录下创建prompt.txt文件并添加您要生成PPT的提示词内容")
            return False

        print(f"📖 读取提示词文件: {prompt_file}")
        print(f"📄 设置幻灯片数量: {num_cards}")

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
                "style": "现代简约"
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
  %(prog)s --clear                  # 仅清空slides和output目录
  %(prog)s --pdf                    # 仅处理PDF文件
  %(prog)s --ppt                    # 仅处理PPT备注提取
  %(prog)s --generate               # 仅生成slide视频
  %(prog)s --generate --digital-human woman  # 仅生成slide视频（使用 woman 数字人）
  %(prog)s --batch                  # 仅批量处理slides
  %(prog)s --upload man             # 上传指定数字人
  %(prog)s --upload all             # 批量上传所有数字人
  %(prog)s --create-ppt             # 生成PPTX（默认6张幻灯片）
  %(prog)s --create-ppt 8           # 生成PPTX（8张幻灯片）
        """
    )

    parser.add_argument("--clear", action="store_true", help="清空slides和output目录")
    parser.add_argument("--pdf", action="store_true", help="仅处理PDF文件")
    parser.add_argument("--ppt", action="store_true", help="仅处理PPT备注提取")
    parser.add_argument("--generate", action="store_true", help="仅生成slide视频")
    parser.add_argument("--batch", action="store_true", help="仅批量处理slides")
    parser.add_argument("--upload", metavar="NAME", help="上传指定数字人 (如: man, woman, all)")
    parser.add_argument("--digital-human", metavar="NAME", default="man",
                       help="指定使用的数字人 (默认: man)")
    parser.add_argument("--create-ppt", nargs='?', const=6, type=int, metavar="NUM_CARDS",
                       help="根据提示词文件生成PPTX (默认生成6张幻灯片，可指定数量)")

    args = parser.parse_args()

    # 根据参数执行相应功能
    if args.clear:
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
    elif args.create_ppt is not None:
        # args.create_ppt 默认为6，用户可以指定数值
        return generate_pptx(args.create_ppt)
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