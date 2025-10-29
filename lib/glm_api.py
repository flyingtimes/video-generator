from openai import OpenAI
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

def talk_to_ai(prompt_file_or_content, user_input, model="GLM-4.5-Flash", is_content=False):
    """
    基于提示词文件或内容调用GLM大模型

    Args:
        prompt_file_or_content (str): 提示词文件路径或直接的内容字符串
        user_input (str): 用户输入内容
        model (str): 使用的模型名称，默认为GLM-4.5-Flash
        is_content (bool): 如果为True，第一个参数被视为直接内容而非文件路径

    Returns:
        str: 大模型返回的结果
    """
    client = OpenAI(
        api_key=os.getenv("GLM_API_KEY"),
        base_url="https://open.bigmodel.cn/api/paas/v4/"
    )

    # 获取提示词内容
    if is_content:
        content = prompt_file_or_content.strip()
    else:
        file_path = Path(prompt_file_or_content)
        if not file_path.exists():
            raise FileNotFoundError(f"提示词文件不存在: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except Exception as e:
            raise Exception(f"读取提示词文件时发生错误: {str(e)}")

    if not content:
        raise ValueError("提示词内容为空")

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": content},
                {"role": "user", "content": user_input}
            ],
            top_p=0.7,
            temperature=0.9
        )

        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"调用GLM API时发生错误: {str(e)}")