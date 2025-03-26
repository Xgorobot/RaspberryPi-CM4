import os
import ast
from typing import List
from volcenginesdkarkruntime import Ark

API_KEY = '67e1719b-fc92-43b7-979d-3692135428a4'
MODEL_NAME = "doubao-1.5-pro-32k-250115"

ACTION_ORDER = [
    "Dance",        # 跳舞
    "Pushups",      # 俯卧撑
    "Pee",          # 撒尿
    "Stretch",      # 伸懒腰
    "Pray",         # 祈祷
    "Chickenhead",  # 鸡头
    "Lookforfood",  # 找食物
    "Grabdownwards",# 向下抓取
    "Wave",         # 波浪
    "Beg"           # 乞讨
]

def get_model_response(client: Ark, prompt: str) -> List[int]:
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    result = ast.literal_eval(completion.choices[0].message.content)
    print(f"模型返回结果: {result}, 类型: {type(result)}")
    return result

def model_output(content: str) -> List[int]:
    system_prompt = """
    请将以下描述转换为动作列表，格式为[跳舞,俯卧撑,撒尿,伸懒腰,祈祷,鸡头,找食物,向下抓取,波浪,乞讨]，
    执行动作为1，否则为0。
    """
    
    client = Ark(api_key=API_KEY)
    
    result = get_model_response(client, system_prompt + content)
    
    if len(result) != len(ACTION_ORDER):
        raise ValueError(f"返回结果长度不匹配，预期{len(ACTION_ORDER)}，实际{len(result)}")
    
    return result
