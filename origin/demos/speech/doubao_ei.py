import ast
from typing import List
from volcenginesdkarkruntime import Ark

API_KEY = '67e1719b-fc92-43b7-979d-3692135428a4'
MODEL_NAME = "doubao-1.5-pro-32k-250115"

#version=2.0

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
            我接下来会给你一段话，如果有退出，停止等意思，请返回字符'退出'，如果指令存在不符合下面要求或无法理解请返回'重试',请根据以下规则对其进行处理，并以列表形式返回结果。列表格式为：
            `[['x', step], ['y', -step], ['turn', yaw], ...]`，列表中元素都是成对出现的，各元素的含义如下：
            1. name:'x'：表示前后移动。
               - `step` 为正时，表示向前移动的距离。
               - `step` 为负时，表示向后移动的距离。
            2. name:'y'：表示左右移动。
               - `step` 为正时，表示向左平移的距离。
               - `step` 为负时，表示向右平移的距离。
            3. name:'turn'：表示转向。
               - 'yaw'：为正时，表示向左转动的角度
               - 'yaw'：为负时，表示向右转动的角度
            4. name:action
               - id:趴下,站起,匍匐前进,转圈,原地踏步,蹲起,沿x转动,沿y转动,沿z转动,三轴转动,撒尿,坐下,招手,伸懒腰,波浪运动,摇摆运动,求食,找食物,握手,展示机械臂,俯卧撑，张望，跳舞，调皮，向上抓取，向中抓取，向下抓取，严格按照前面给的词语给出
            5. name:pace
               - mode, 取值为slow, normal, high,分别对应慢速，正常，高速
            6. name:translation
               - [direction,data], direction取值为'x','y','z' ,data的单位是毫米，沿X轴正方向平移为正数，0表示回到初始位置，沿着X负方向平移为负数，取值范围是[-35,35]mm，y轴和z轴同理。
            7. name:attitude
               - [direction,data], direction取值为'r','p','y' ,data的单位是度，沿X轴正时针旋转为正数，0表示回到初始位置，沿着X逆时针旋转为负数，取值范围是[-20,20]mm，y轴和z轴旋转运动同理。
            8. name:arm
               - [arm_x, arm_z],arm_x取值范围是[-80,155]和arm_z的取值范围是[-95，155]，是机械臂的相关动作，arm_x是机械狗的机械臂相对于机械臂的基座的x坐标，arm_z机械狗的机械臂相对于机械臂的基座的z坐标
            9. name:claw
               - pos,取值是0-255，其中0表示夹爪完全张开，255表示夹爪完全闭合。
            10. name:imu
               - mode,取值为0或者1，0代表关闭自稳定模式，1表示打开自稳定模式。
            11. name:perform
               - mode, 取值为0或者1，0代表关闭表演模式，1表示打开表演模式。
            12. name:reset
               - mode,取值为0,表示让机器狗复位
            13. name:motor
               - [motor_id, data],motor_id的取值范围是 [11,12,13,21,22,23,31,32,33,41,42,43,51,52,53]，第一位数字代表舵机所在的腿1,2,3,4,分别代表左前腿、右前腿、右后腿、左后腿，第二位数字代表在该腿上的位置，从下到上依次是1，2，3；51、52、53分别是夹爪、小臂、大臂舵机，data表示舵机角度，腿下面舵机的取值范围[-70, 50],腿中间舵机的取值范围[-66, 93],腿上面舵机的取值范围是[-31, 31] 51号舵机的取值范围是[-65, 65]52号舵机的取值范围是[-115, 70]53号舵机的取值范围是[-85, 100]。
            14. name:battery
               - mode,取值为0,读取当前电池电量
            15. name:leg
              - [leg_id, [x, y, z]], leg_id的取值是1,2,3,4,分别代表左前腿、右前腿、右后腿、左后腿.[x,y,z]代表足端位置，单位为mm,其中x的取值范围是[-35,35],y的取值范围是[-18,18],z的取值范围是[75,115]
           **默认值规则**：
            - 如果未指定移动距离，默认移动距离为 `30`。
            - 如果未指定转动角度，默认转动角度为 `90`。
            - 如某些命令未给出参数，可自行随机生成，但必须有参数。
            - 招手为打招呼动作。
            - 机械b 就是机械臂
            - 眼外周运动、歪轴运动、外轴运动等类近音文字，都是沿y轴运动。
            - 厘米是毫米的10倍,分米是毫米的100倍，米是毫米的1000倍。
            - 注意给的内容是语音转文字，可能存在谐音，标点位置错位等情况
           name是指方法名字，后面是需要传入的参数以及参数规则,多个参数时需要以列表形式给出
           返回结果以'['作为开始，以']'作为结束,下面我将给出几个例子
           前进30，跳个舞，打个招呼然后退出应返回[['x', 30], [action, '跳舞'], [action, '招手'], ['退出']]
            退出退出退出应返回[['退出']]
            什么前进请说左转应返回[['重试']], ['x', 30], ['重试'],['turn', 90]]
            沿x轴旋转，沿x轴运动都应返回['action','沿x转动']
            沿y轴旋转，沿y轴运动都应返回['action','沿y转动']
            沿z轴旋转，沿z轴运动都应返回['action','沿z转动']
            调整机械臂x为80，可以返回['arm',[80,100]]
            请严格按照上述规则处理输入内容，并返回结果列表。
    """
    
    client = Ark(api_key=API_KEY)
    
    result = get_model_response(client, system_prompt + content)

    return result
