"""
批量处理PPT文件备注提取的测试脚本
扫描input目录下的PDF文件，查找对应的PPTX/PPT文件，并提取备注到slides目录
"""

import os
import sys
from pathlib import Path

# 添加lib目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from ppt_to_txt import extract_notes_from_pptx, find_pptx_file


def scan_and_process_ppt_files(input_dir: str = "input", output_dir: str = "slides"):
    """
    扫描输入目录下的PDF文件，查找对应的PPTX/PPT文件并处理

    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"错误: 输入目录 {input_dir} 不存在")
        return False

    # 扫描PDF文件
    pdf_files = list(input_path.glob("*.pdf"))

    if not pdf_files:
        print(f"在 {input_dir} 目录中没有找到PDF文件")
        return False

    print(f"在 {input_dir} 目录中找到 {len(pdf_files)} 个PDF文件")
    print("=" * 50)

    success_count = 0
    total_count = 0

    for pdf_file in pdf_files:
        total_count += 1
        base_name = pdf_file.stem  # 获取不含扩展名的文件名

        print(f"\n处理文件 {total_count}/{len(pdf_files)}: {pdf_file.name}")
        print("-" * 30)

        # 查找对应的PPTX/PPT文件
        pptx_file = find_pptx_file(input_dir, base_name)

        if not pptx_file:
            print(f"未找到与 {pdf_file.name} 对应的PPTX/PPT文件")
            continue

        print(f"找到匹配的PPT文件: {os.path.basename(pptx_file)}")

        # 处理PPT文件
        success = extract_notes_from_pptx(pptx_file, output_dir)

        if success:
            success_count += 1
            print(f"✅ 成功处理 {base_name}")
        else:
            print(f"❌ 处理 {base_name} 失败")

    print("\n" + "=" * 50)
    print(f"批量处理完成!")
    print(f"总文件数: {total_count}")
    print(f"成功处理: {success_count}")
    print(f"失败数量: {total_count - success_count}")

    return success_count > 0


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="批量处理PPT文件备注提取")
    parser.add_argument(
        "--input-dir", "-i",
        default="input",
        help="输入目录路径 (默认: input)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="slides",
        help="输出目录路径 (默认: slides)"
    )

    args = parser.parse_args()

    print("PPT文件备注批量提取工具")
    print("=" * 50)
    print(f"输入目录: {args.input_dir}")
    print(f"输出目录: {args.output_dir}")
    print()

    success = scan_and_process_ppt_files(args.input_dir, args.output_dir)

    if not success:
        print("\n❌ 批量处理失败")
        sys.exit(1)
    else:
        print("\n✅ 批量处理成功完成")
        sys.exit(0)


if __name__ == "__main__":
    main()