#!/usr/bin/env python3
"""
测试gen_slide_video函数
"""

import sys
import os

# 添加lib目录到路径
sys.path.insert(0, 'lib')

from runninghub_api import RunningHubAPI

def test_gen_slide_video():
    """测试gen_slide_video函数"""
    try:
        # 创建API客户端（会自动从环境变量读取API密钥）
        api = RunningHubAPI()
        print(f"✅ 成功创建API客户端")

        # 测试参数：digital_human="man"
        digital_human = "man"

        print(f"\n🧪 开始测试gen_slide_video函数")
        print(f"数字人: '{digital_human}'")

        success_count = 0
        skip_count = 0
        fail_count = 0

        # 测试幻灯片2-4
        for i in range(2, 5):
            print(f"\n{'='*60}")
            print(f"处理幻灯片 {i}")
            print('='*60)

            # 调用函数
            result = api.gen_slide_video(i, digital_human)

            if result is True:
                print(f"✅ 幻灯片 {i} 处理成功")
                success_count += 1
            elif result == "skip":
                print(f"⏭️ 幻灯片 {i} 文本为空，已跳过")
                skip_count += 1
            else:
                print(f"❌ 幻灯片 {i} 处理失败")
                fail_count += 1

        # 打印统计结果
        print(f"\n{'='*60}")
        print(f"测试完成！统计结果:")
        print(f"✅ 成功: {success_count} 个")
        print(f"⏭️ 跳过: {skip_count} 个")
        print(f"❌ 失败: {fail_count} 个")
        print('='*60)

        if fail_count == 0:
            print(f"\n🎉 测试成功！所有幻灯片都已处理完成")
        else:
            print(f"\n⚠️ 部分幻灯片处理失败，请检查错误信息")

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gen_slide_video()