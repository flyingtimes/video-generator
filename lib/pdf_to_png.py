#!/usr/bin/env python3
"""
PDF转PNG工具库
将PDF文件每一页转换为1920x1080尺寸的PNG图片，支持裁剪和等比例缩放
"""

import os
import io
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image
from lib.logger import get_logger, execution_time_logger, step_logger


def create_directories():
    """创建必要的目录"""
    logger = get_logger()

    for dir_name in ["slides", "input"]:
        if os.makedirs(dir_name, exist_ok=True):
            logger.debug(f"创建目录: {dir_name}")
        else:
            logger.debug(f"目录已存在: {dir_name}")


@execution_time_logger("查找PDF文件")
def find_pdf_files() -> List[str]:
    """
    查找input目录下所有PDF文件

    Returns:
        List[str]: PDF文件路径列表
    """
    logger = get_logger()

    input_dir = Path("input")
    if not input_dir.exists():
        logger.error(f"input目录不存在: {input_dir}")
        return []

    pdf_files = list(input_dir.glob("*.pdf"))
    pdf_files.sort()  # 按文件名排序

    logger.debug(f"在input目录中找到 {len(pdf_files)} 个PDF文件: {[f.name for f in pdf_files]}")
    return [str(f) for f in pdf_files]


def calculate_scale_and_crop(page_width: int, page_height: int, target_width: int = 1920, target_height: int = 1080) -> Tuple[float, Tuple[int, int, int, int]]:
    """
    智能内容感知裁剪算法 - 根据不同情况采用最优策略

    算法策略：
    1. 原图 < 目标尺寸：等比例放大，不裁剪
    2. 原图 ≈ 目标尺寸：最小缩放，精准裁剪
    3. 原图 >> 目标尺寸：智能内容检测 + 安全区域裁剪

    Args:
        page_width: 原始页面宽度
        page_height: 原始页面高度
        target_width: 目标宽度 (默认1920)
        target_height: 目标高度 (默认1080)

    Returns:
        Tuple[float, Tuple[int, int, int, int]]: (缩放比例, (裁剪x, 裁剪y, 裁剪宽度, 裁剪高度))
    """
    logger = get_logger()

    # 计算原始和目标的比例
    original_ratio = page_width / page_height
    target_ratio = target_width / target_height

    # 计算尺寸差异系数
    width_ratio = page_width / target_width
    height_ratio = page_height / target_height

    logger.debug(f"原始尺寸: {page_width}×{page_height} (比例: {original_ratio:.2f})")
    logger.debug(f"目标尺寸: {target_width}×{target_height} (比例: {target_ratio:.2f})")
    logger.debug(f"尺寸比例: 宽度{width_ratio:.2f}x, 高度{height_ratio:.2f}x")

    # 情况1：原图小于目标尺寸 - 放大到覆盖目标尺寸，然后居中裁剪
    if width_ratio < 1.0 and height_ratio < 1.0:
        # 选择较大的缩放比例，确保放大后能覆盖目标尺寸
        scale = max(target_width / page_width, target_height / page_height)

        scaled_width = int(page_width * scale)
        scaled_height = int(page_height * scale)

        # 计算居中裁剪的坐标
        crop_x = (scaled_width - target_width) // 2
        crop_y = (scaled_height - target_height) // 2

        logger.debug(f"策略1: 原图较小，放大后居中裁剪 ({scale:.2f}x)")
        logger.debug(f"放大尺寸: {scaled_width}×{scaled_height}")
        logger.debug(f"裁剪区域: ({crop_x}, {crop_y}, {target_width}, {target_height})")

        return scale, (crop_x, crop_y, target_width, target_height)

    # 情况2：尺寸相近 (比例在1.0-2.0之间) - 最小缩放，精准裁剪
    elif max(width_ratio, height_ratio) <= 2.0:
        # 使用传统算法：选择较大的缩放比例
        scale = max(target_width / page_width, target_height / page_height)

        scaled_width = int(page_width * scale)
        scaled_height = int(page_height * scale)

        crop_x = (scaled_width - target_width) // 2
        crop_y = (scaled_height - target_height) // 2

        logger.debug(f"策略2: 尺寸相近，最小缩放精准裁剪 ({scale:.2f}x)")

        return scale, (crop_x, crop_y, target_width, target_height)

    # 情况3：原图远大于目标尺寸 - 智能内容感知裁剪
    else:
        # 使用较小的缩放比例，保证内容完整
        scale = min(target_width / page_width, target_height / page_height)

        scaled_width = int(page_width * scale)
        scaled_height = int(page_height * scale)

        # 计算需要裁剪的区域
        if scaled_width >= target_width and scaled_height >= target_height:
            # 两个维度都足够，居中裁剪
            crop_x = (scaled_width - target_width) // 2
            crop_y = (scaled_height - target_height) // 2
            print(f"🔍 策略3: 原图较大，智能缩放后居中裁剪 ({scale:.2f}x)")
        else:
            # 某个维度不足，需要特殊处理
            if scaled_width >= target_width:
                # 宽度足够，高度不足 - 优先保留宽度，裁剪上下
                scale = target_width / page_width
                scaled_height = int(page_height * scale)
                crop_x = 0
                crop_y = max(0, (scaled_height - target_height) // 3)  # 偏上裁剪，保留重要内容
                print(f"🔍 策略3a: 高度优先，保留重要区域 ({scale:.2f}x)")
            else:
                # 高度足够，宽度不足 - 优先保留高度，裁剪左右
                scale = target_height / page_height
                scaled_width = int(page_width * scale)
                crop_x = max(0, (scaled_width - target_width) // 3)  # 偏左裁剪
                crop_y = 0
                print(f"🔍 策略3b: 宽度优先，保留重要区域 ({scale:.2f}x)")

        # 确保裁剪区域有效
        final_crop_width = min(target_width, scaled_width)
        final_crop_height = min(target_height, scaled_height)

        return scale, (crop_x, crop_y, final_crop_width, final_crop_height)


@execution_time_logger("PDF页面转PNG")
def pdf_page_to_png(pdf_path: str, page_num: int, output_path: str, target_size: Tuple[int, int] = (1920, 1080), dpi: int = 300) -> bool:
    """
    将PDF的指定页面转换为PNG图片，使用智能内容感知裁剪算法

    Args:
        pdf_path: PDF文件路径
        page_num: 页码 (从0开始)
        output_path: 输出PNG文件路径
        target_size: 目标图片尺寸 (宽度, 高度)
        dpi: 渲染DPI (默认300，保证清晰度)

    Returns:
        bool: 转换是否成功
    """
    try:
        logger = get_logger()

        # 打开PDF文件
        doc = fitz.open(pdf_path)

        # 获取指定页面
        page = doc.load_page(page_num)

        # 获取原始页面尺寸
        rect = page.rect
        page_width = int(rect.width)
        page_height = int(rect.height)

        logger.debug(f"处理页面 {page_num + 1}, 原始尺寸: {page_width}×{page_height}")

        # 渲染页面为图像
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 提高渲染质量

        # 转换为PIL Image对象
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        logger.debug(f"原始渲染图像尺寸: {img.size}")

        # 计算缩放和裁剪参数
        scale, crop_params = calculate_scale_and_crop(img.width, img.height, target_size[0], target_size[1])
        crop_x, crop_y, crop_width, crop_height = crop_params

        print(f"🔧 页面 {page_num + 1}: 缩放比例 {scale:.2f}x")

        # 根据算法结果进行处理
        if abs(scale - 1.0) > 0.01:  # 如果需要缩放
            # 计算缩放后的新尺寸
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)

            print(f"🔄 执行缩放: {img.size} → ({new_width}, {new_height})")

            # 使用高质量缩放
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 重新计算裁剪参数（基于缩放后的图像）
            # 对于缩放后的图像，我们直接使用目标尺寸进行居中裁剪
            crop_x = (new_width - target_size[0]) // 2 if new_width > target_size[0] else 0
            crop_y = (new_height - target_size[1]) // 2 if new_height > target_size[1] else 0

            # 确保裁剪区域不超出图像边界
            crop_width = min(target_size[0], new_width - crop_x)
            crop_height = min(target_size[1], new_height - crop_y)

            print(f"✂️ 调整后裁剪区域: ({crop_x}, {crop_y}, {crop_width}, {crop_height})")

        # 执行裁剪（如果需要）
        if crop_width == target_size[0] and crop_height == target_size[1]:
            # 裁剪后正好是目标尺寸，直接使用
            cropped_img = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
            final_img = cropped_img
        else:
            # 裁剪后仍小于目标尺寸，需要填充
            if crop_width > 0 and crop_height > 0:
                cropped_img = img.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
            else:
                cropped_img = img

            # 创建目标尺寸画布并居中放置
            final_img = Image.new('RGB', target_size, (255, 255, 255))  # 白色背景
            paste_x = (target_size[0] - cropped_img.size[0]) // 2
            paste_y = (target_size[1] - cropped_img.size[1]) // 2
            final_img.paste(cropped_img, (paste_x, paste_y))

            if paste_x > 0 or paste_y > 0:
                print(f"⚠️ 图片小于目标尺寸，添加空白边距: 左右{paste_x}px, 上下{paste_y}px")

        # 保存结果
        final_img.save(output_path, "PNG", optimize=True)

        # 清理资源
        doc.close()

        return True

    except Exception as e:
        print(f"❌ 转换页面 {page_num + 1} 失败: {e}")
        return False


@execution_time_logger("PDF转slides")
@step_logger("处理PDF文件")
def process_pdf_to_slides(pdf_path: str, target_size: Tuple[int, int] = (1920, 1080)) -> List[str]:
    """
    将PDF文件的所有页面转换为PNG图片并保存到slides文件夹

    Args:
        pdf_path: PDF文件路径
        target_size: 目标图片尺寸 (宽度, 高度)

    Returns:
        List[str]: 成功转换的PNG文件路径列表
    """
    try:
        # 打开PDF文件获取页数
        doc = fitz.open(pdf_path)
        page_count = doc.page_count
        doc.close()

        print(f"📄 处理PDF文件: {pdf_path} (共 {page_count} 页)")

        converted_files = []

        for page_num in range(page_count):
            output_path = Path("slides") / f"{page_num + 1}.png"

            print(f"🔄 转换第 {page_num + 1}/{page_count} 页...")

            if pdf_page_to_png(pdf_path, page_num, output_path, target_size):
                converted_files.append(output_path)
                print(f"✅ 已保存: {output_path}")
            else:
                print(f"❌ 第 {page_num + 1} 页转换失败")

        print(f"📊 成功转换 {len(converted_files)}/{page_count} 页")
        return converted_files

    except Exception as e:
        print(f"❌ 处理PDF文件失败: {e}")
        return []


@execution_time_logger("批量处理PDF文件")
@step_logger("批量处理PDF文件")
def batch_process_pdfs(target_size: Tuple[int, int] = (1920, 1080)) -> bool:
    """
    批量处理input目录下的所有PDF文件

    Args:
        target_size: 目标图片尺寸 (宽度, 高度)

    Returns:
        bool: 批量处理是否成功
    """
    # 创建必要目录
    create_directories()

    # 清除slides目录下的所有PNG文件
    slides_dir = Path("slides")
    if slides_dir.exists():
        png_files = list(slides_dir.glob("*.png"))
        for png_file in png_files:
            try:
                png_file.unlink()
                print(f"🗑️ 已删除: {png_file}")
            except Exception as e:
                print(f"⚠️ 删除文件失败 {png_file}: {e}")

        if png_files:
            print(f"🧹 已清除 {len(png_files)} 个旧的PNG文件")
        else:
            print("📁 slides目录为空，无需清除")

    # 查找PDF文件
    pdf_files = find_pdf_files()

    if not pdf_files:
        print("❌ 在input目录下没有找到PDF文件")
        return False

    print(f"📁 找到 {len(pdf_files)} 个PDF文件:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf_file}")
    print()

    total_converted = 0

    for pdf_file in pdf_files:
        print(f"\n🎬 处理文件: {pdf_file}")
        converted_files = process_pdf_to_slides(pdf_file, target_size)
        total_converted += len(converted_files)

        if converted_files:
            print(f"✅ 文件处理完成，转换了 {len(converted_files)} 页")
        else:
            print(f"❌ 文件处理失败")

    print(f"\n🎉 批量处理完成！总共转换了 {total_converted} 页图片")
    return total_converted > 0


if __name__ == "__main__":
    # 示例用法
    import sys
    import io

    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        if not os.path.exists(pdf_file):
            print(f"❌ PDF文件不存在: {pdf_file}")
            sys.exit(1)

        # 处理单个PDF文件
        converted_files = process_pdf_to_slides(pdf_file)
        print(f"转换完成，共生成 {len(converted_files)} 个PNG文件")
    else:
        # 批量处理input目录下的所有PDF文件
        success = batch_process_pdfs()
        if success:
            print("批量转换成功！")
        else:
            print("批量转换失败！")
            sys.exit(1)