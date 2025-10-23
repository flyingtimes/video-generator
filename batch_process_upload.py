"""
数字人文件批量上传工具
批量处理characters目录下的数字人文件上传
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lib.runninghub_api import RunningHubAPI, get_api_key


def process_single_character(character_name: str) -> bool:
    """
    处理单个数字人的文件上传

    Args:
        character_name: 数字人名称

    Returns:
        bool: 处理成功返回True，失败返回False
    """
    characters_dir = Path("characters")
    character_dir = characters_dir / character_name

    if not character_dir.exists():
        print(f"❌ 数字人目录不存在: {character_dir}")
        return False

    try:
        api_key = get_api_key()
        api = RunningHubAPI(api_key)
        return api.process_character_files(str(character_dir), character_name)

    except Exception as e:
        print(f"❌ 处理数字人 {character_name} 时发生错误: {str(e)}")
        return False


def batch_process_characters() -> bool:
    """
    批量处理所有数字人目录

    Returns:
        bool: 全部处理成功返回True，否则返回False
    """
    characters_dir = Path("characters")

    if not characters_dir.exists():
        print(f"❌ characters目录不存在: {characters_dir}")
        return False

    # 获取所有子目录
    character_dirs = [d for d in characters_dir.iterdir() if d.is_dir()]

    if not character_dirs:
        print(f"❌ 在characters目录中未找到任何数字人子目录")
        return False

    print(f"发现 {len(character_dirs)} 个数字人目录:")
    for char_dir in character_dirs:
        print(f"  - {char_dir.name}")

    print("\n开始批量处理...")

    success_count = 0
    fail_count = 0

    for character_dir in character_dirs:
        character_name = character_dir.name
        print(f"\n{'-'*60}")

        try:
            api_key = get_api_key()
            api = RunningHubAPI(api_key)
            success = api.process_character_files(str(character_dir), character_name)

            if success:
                success_count += 1
                print(f"✅ {character_name} 处理成功")
            else:
                fail_count += 1
                print(f"❌ {character_name} 处理失败")

        except Exception as e:
            fail_count += 1
            print(f"❌ 处理 {character_name} 时发生异常: {str(e)}")

    # 输出总结
    print(f"\n{'='*60}")
    print("批量处理完成!")
    print(f"总数字人数: {len(character_dirs)}")
    print(f"成功处理: {success_count}")
    print(f"失败数量: {fail_count}")

    if fail_count == 0:
        print("✅ 所有数字人处理成功!")
        return True
    else:
        print("❌ 部分数字人处理失败")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("数字人文件批量上传工具")
        print("="*50)
        print("用法:")
        print("  python batch_process_upload.py <数字人名称>    # 处理指定数字人")
        print("  python batch_process_upload.py all            # 批量处理所有数字人")
        print("  python batch_process_upload.py                # 默认处理man数字人")
        print("\n示例:")
        print("  python batch_process_upload.py man")
        print("  python batch_process_upload.py all")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "all":
        # 批量处理所有数字人
        success = batch_process_characters()
        sys.exit(0 if success else 1)

    else:
        # 处理指定数字人
        character_name = command
        print(f"数字人文件上传工具")
        print("="*50)
        print(f"处理数字人: {character_name}")

        success = process_single_character(character_name)

        if success:
            print(f"\n✅ 数字人 {character_name} 处理完成!")
            sys.exit(0)
        else:
            print(f"\n❌ 数字人 {character_name} 处理失败!")
            sys.exit(1)


if __name__ == "__main__":
    main()