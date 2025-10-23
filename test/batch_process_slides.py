#!/usr/bin/env python3
"""
批量处理slides目录下的图片和视频文件的主程序
将每组图片和视频合成为新视频，最后合并所有结果
"""

from lib.slide_add_head_to_video import (
    check_and_create_directories,
    find_slide_pairs,
    process_slide_pairs,
    merge_videos
)


def main():
    """主函数 - 控制整个批量处理流程"""
    print("🚀 批量处理slides目录")
    print("=" * 50)

    # 1. 初始化环境
    check_and_create_directories()

    # 2. 查找并显示所有slide对
    pairs = find_slide_pairs()
    if not pairs:
        print("❌ 没有找到任何有效的图片-视频对")
        return

    print(f"📁 找到 {len(pairs)} 个有效的图片-视频对:")
    for num, png_file, mp4_file in pairs:
        print(f"   {num}: {png_file} + {mp4_file}")
    print()

    # 3. 批量处理slide对
    print("🎬 开始批量处理...")
    processed_files = process_slide_pairs(pairs)

    if not processed_files:
        print("❌ 没有成功处理任何文件")
        return

    print(f"\n📊 成功处理 {len(processed_files)} 个文件")

    # 4. 合并所有结果
    print("\n🔄 开始合并最终结果...")
    success = merge_videos(processed_files)

    # 5. 显示最终结果
    if success:
        print("\n🎉 批量处理完成!")
        print("📹 最终输出文件: output/result.mp4")
        print("\n📋 输出文件列表:")
        for i, file in enumerate(processed_files, 1):
            print(f"   {i}. {file}")
    else:
        print("\n❌ 最终合并失败")


if __name__ == "__main__":
    main()