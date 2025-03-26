import os
import ast

from volcenginesdkarkruntime import Ark

def model_output(content):

    api_key = '67e1719b-fc92-43b7-979d-3692135428a4'

    model = "doubao-1.5-pro-32k-250115"

    # 初始化Ark客户端
    client = Ark(api_key = api_key)
    client = Ark(api_key = api_key)
    prompt = '''
    我接下来会给你一段话，请依据特定要求对其进行处理，并以指定的列表形式返回结果。列表的格式为  [
    前进,
    后退,
    ]，
    各元素含义如下：
    Dance:该值为 1；否则该值为 0
    PushUp:该值为 1；否则该值为 0
    Pee:该值为 1；否则该值为 0
    Strech:该值为 1；否则该值为 0
    Pray:该值为 1；否则该值为 0
    Beg:该值为 1；否则该值为 0
    LookingForFood:该值为 1；否则该值为 0
    GrabDown:该值为 1；否则该值为 0
    Wave:该值为 1；否则该值为 0
    ChickenHead:该值为 1；否则该值为 0
    '''
    prompt = prompt + content
    # 创建一个对话请求
    completion = client.chat.completions.create(
        model = model,
        messages = [
            {"role": "user", "content": prompt},
        ],
    )
    result = completion.choices[0].message.content
    result = ast.literal_eval(result)
    print(result)
    print(type(result))
    Dance,Pushups,Pee,Stretch,Pray,Chickenhead,Lookforfood,Grabdownwards,Wave,Beg= result[0], result[1],result[2],result[3],result[4],result[5],result[6],result[7],result[8],result[9]
    return Dance,Pushups,Pee,Stretch,Pray,Chickenhead,Lookforfood,Grabdownwards,Wave,Beg
