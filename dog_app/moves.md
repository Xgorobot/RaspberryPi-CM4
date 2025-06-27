机器狗动作功能与代码索引
本文档详细梳理了机器狗的各项动作指令、功能及其对应的源代码位置。所有底层动作的实现都集中在核心控制库 xgolib.py 中，其他应用和演示脚本均通过调用该库来控制机器狗。

核心控制库
所有物理动作的最终实现都封装在此文件中。

|

| 文件路径 | 类名 | 描述 |
| dog_app/control/xgolib.py | XGO | 包含了控制机器狗所有硬件（舵机、IMU、机械臂等）的底层指令和通信协议。 |

1. 基础运动 (Basic Movement)
控制机器狗在平面上移动和转向的基础指令。

| 动作 | 描述 | 核心代码位置 (xgolib.py) | 调用示例 |
| 前进/后退 | 沿 X 轴向前或向后移动。 | move_x(step), forward(step), back(step) | dog_Joystick.py, web_server.py |
| 左/右平移 | 沿 Y 轴向左或向右横向移动。 | move_y(step), left(step), right(step) | dog_Joystick.py, web_server.py |
| 左/右转 | 原地向左或向右旋转。 | turn(step), turnleft(step), turnright(step) | dog_Joystick.py, web_server.py |
| 停止 | 停止所有运动。 | stop() | dog_Joystick.py |
| 原地踏步 | 在原地保持踏步动作。 | mark_time(data) | dog_test.py |
| 按距离/角度移动 | 精确移动指定距离或旋转指定角度。 | move_x_by(distance), move_y_by(distance), turn_by(angle) | follow_line.py |

2. 预设动作 (Pre-set Actions)
机器狗固化了一系列特定编号的组合动作，可通过单个指令调用。

核心调用函数: xgolib.py -> action(action_id)

| 动作ID | 动作名称 | 动作ID | 动作名称 |
| 1 | 趴下 (Lie down) | 15 | 波浪运动 (Wave) |
| 2 | 站起 (Stand up) | 16 | 摇摆 (Sway) |
| 3 | 匍匐前进 (Crawl) | 17 | 求食 (Beg for food) |
| 4 | 转圈 (Circle) | 18 | 找食物 (Look for food) |
| 5 | 原地踏步 (Mark time) | 19 | 握手 (Shake hands) |
| 6 | 蹲起 (Squat) | 20 | 展示机械臂/鸡头 (Chicken head) |
| 7 | 沿X轴转动 (Roll) | 21 | 俯卧撑 (Push-ups) |
| 8 | 沿Y轴转动 (Pitch) | 22 | 张望 (Look around) |
| 9 | 沿Z轴转动 (Yaw) | 23 | 跳舞 (Dance) |
| 10 | 三轴转动 (3-axis rotation) | 24 | 调皮 (Naughty) |
| 11 | 撒尿 (Pee) | 128 | 向上抓取 (Catch from top) |
| 12 | 坐下 (Sit down) | 129 | 向中抓取 (Catch from middle) |
| 13 | 招手 (Wave hands) | 130 | 向下抓取 (Catch from bottom) |
| 14 | 伸懒腰 (Stretch) | 255 | 复位 (Reset) |

调用示例:

手势识别: demos/hands.py - 根据不同的手势（如 "one", "OK"）调用 dog.action(id)。

语音控制: demos/speech/ei.py, demos/xiaozhi_test/src/iot/things/dog_test.py - 解析语音指令（如“转个圈”）来执行对应动作。

Web遥控: dog_app/remote/web_server.py - 接收前端按钮事件来调用 dog.action(id)。

3. 姿态控制 (Pose & Attitude Control)
独立调整身体的姿态和位置，而不移动足端。

| 动作 | 描述 | 核心代码位置 (xgolib.py) | 调用示例 |
| 身体平移 | 身体在X, Y, Z三个轴向上整体平移。 | translation(direction, data) | pose_dog.py - 模仿人下蹲。 |
| 身体旋转 | 身体进行翻滚(roll)、俯仰(pitch)、偏航(yaw)。 | attitude(direction, data) | face_decetion.py - 跟随人脸。 |
| 周期性姿态 | 身体周期性地进行平移或旋转。 | periodic_tran(direction), periodic_rot(direction) | dog_test.py |
| 单腿控制 | 控制单条腿的末端在三维空间中的位置。 | leg(leg_id, data) | - |
| 舵机控制 | 直接控制单个舵机（关节）转动到指定角度。 | motor(motor_id, data) | - |

4. 机械臂与爪子控制 (Arm & Claw Control)
| 动作 | 描述 | 核心代码位置 (xgolib.py) | 调用示例 |
| 机械臂移动 | 通过直角坐标或极坐标控制机械臂末端的位置。 | arm(x, z), arm_polar(theta, r) | demos/ball.py - 用于抓取小球。 |
| 爪子开合 | 控制爪子的张开和闭合。 | claw(pos) | demos/ball.py |

5. 模式与参数设置 (Modes & Parameters)
| 动作 | 描述 | 核心代码位置 (xgolib.py) |
| 步态设置 | 切换不同的行走步态，如 trot, walk。 | gait_type(mode_str) |
| 步频设置 | 调整步行的频率 (slow, normal, high)。 | pace(mode) |
| 自稳定模式 | 开启或关闭IMU自稳定功能。 | imu_mode(mode_val) |
| 循环表演 | 让机器狗循环执行预设的表演动作。 | perform(mode) |

6. 屏幕表情显示 (Screen Expressions)
在机器狗胸前的LCD屏幕上显示视觉反馈。

| 动作 | 描述 | 核心代码位置 | 调用示例 |
| 显示表情 | 显示预设的动图表情，如高兴、悲伤、惊讶等。 | dog_app/emotion/emotion_manager.py | dog_app/main_app.py, demos/dog_show.py |
