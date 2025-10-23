#!/usr/bin/env python3
"""
批量处理PDF文件的主程序
将input目录下的PDF文件转换为1920x1080的PNG图片，保存到slides目录
"""

from lib.pdf_to_png import (
    create_directories,
    find_pdf_files,
    batch_process_pdfs
)


def main():
    """主函数 - 控制整个PDF转换流程"""
    print("🚀 批量处理PDF文件转换为PNG图片")
    print("=" * 60)

    # 1. 初始化环境
    print("📁 初始化环境...")
    create_directories()

    # 2. 查找PDF文件
    print("\n🔍 查找PDF文件...")
    pdf_files = find_pdf_files()

    if not pdf_files:
        print("❌ 在input目录下没有找到PDF文件")
        print("💡 请确保input目录下存在PDF文件")
        return

    print(f"📋 找到 {len(pdf_files)} 个PDF文件:")
    for i, pdf_file in enumerate(pdf_files, 1):
        # 显示文件大小信息
        file_path = pdf_file
        file_size = ""
        try:
            import os
            size = os.path.getsize(file_path)
            if size < 1024:
                file_size = f"{size} B"
            elif size < 1024 * 1024:
                file_size = f"{size / 1024:.1f} KB"
            else:
                file_size = f"{size / (1024 * 1024):.1f} MB"
        except:
            pass

        filename = file_path.split('/')[-1]
        print(f"   {i}. {filename} ({file_size})")

    print()

    # 3. 确认处理
    print("🎯 目标设置:")
    print("   • 输出格式: PNG图片")
    print("   • 输出尺寸: 1920 × 1080 像素")
    print("   • 输出目录: slides/")
    print("   • 处理方式: 等比例缩放 + 居中裁剪")
    print()

    # 4. 批量处理
    print("🎬 开始批量转换...")
    success = batch_process_pdfs(target_size=(1920, 1080))

    # 5. 显示结果
    if success:
        print("\n🎉 批量转换完成!")
        print("📋 生成的PNG文件:")

        # 显示生成的文件列表
        try:
            import os
            import glob

            png_files = sorted(glob.glob("slides/*.png"),
                              key=lambda x: int(os.path.basename(x).split('.')[0]))

            if png_files:
                for i, png_file in enumerate(png_files, 1):
                    filename = os.path.basename(png_file)
                    try:
                        size = os.path.getsize(png_file)
                        if size < 1024:
                            file_size = f"{size} B"
                        elif size < 1024 * 1024:
                            file_size = f"{size / 1024:.1f} KB"
                        else:
                            file_size = f"{size / (1024 * 1024):.1f} MB"
                        print(f"   {i:2d}. {filename} ({file_size})")
                    except:
                        print(f"   {i:2d}. {filename}")

                print(f"\n📊 总共生成了 {len(png_files)} 个PNG文件")
                print("💡 现在可以使用 batch_process_slides.py 进行视频合成")
            else:
                print("   (没有找到生成的PNG文件)")
        except Exception as e:
            print(f"   (无法列出生成的文件: {e})")
    else:
        print("\n❌ 批量转换失败!")
        print("💡 请检查PDF文件是否有效，或查看错误信息")


if __name__ == "__main__":
    main()