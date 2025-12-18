import time
from src.iot.thing import Thing, Parameter, ValueType
from xgolib import XGO
import logging


class MychanicalDog(Thing):
    def __init__(self):
        # 调用父类初始化方法，设置设备名称和描述
        # 第一个参数是设备ID(全局唯一)，第二个参数是对设备的描述文本
        super().__init__("MychanicalDog", "机械狗lulu")

        # 机械狗状态变量定义
        self.dog = XGO(port='/dev/ttyAMA0', version="xgomini")
        self.dog_type = 'M'
        self.init_dog()

        self.is_moving = False  # 定义机械狗是否正在移动，初始为False
        self.direction = 'stop'  # 定义机械狗的移动方向，初始为停止
        self.is_turn = False
        self.turn = 'stop' #定义狗的转向，初始为不转向
        self.gait_type = 'trot'  #定义xgo的步幅，初始为正常
        self.pace = 'normal'  #定义xgo的步频，初始为正常
        self.action = False   #xgo的自定义动作,初始为无动作
        self.perform = False  #xgo的表演模式
        self.move_time = 0 # 移动时间
        self.turn_time = 0 #转动时间
        self.speed = 0  # 定义机械狗的移动速度，初始为0
        self.turn_speed = 0 #转动速度
        self.last_update_time = 0  # 记录最后一次状态更新的时间戳
        self.claw = 0 #机械臂的夹爪开合
        # 三轴旋转参数
        self.is_attitude = False
        self.attitude_r = 0
        self.attitude_p = 0
        self.attitude_y = 0
        # 三轴平移参数
        self.is_translation = False
        self.translation_x = 0
        self.translation_y = 0
        self.translation_z = 75
        # 机械臂参数
        self.is_arm = False
        self.arm_x = 0
        self.arm_z = 0

        # 腿的参数
        self.leg_1 = False
        self.leg_2 = False
        self.leg_3 = False
        self.leg_4 = False

        # 舵机的参数
        self.motor_11 = False
        self.motor_12 = False
        self.motor_13 = False
        self.motor_21 = False
        self.motor_22 = False
        self.motor_23 = False
        self.motor_31 = False
        self.motor_32 = False
        self.motor_33 = False
        self.motor_41 = False
        self.motor_42 = False
        self.motor_43 = False
        self.motor_51 = False
        self.motor_52 = False
        self.motor_53 = False

        # =========================
        # 注册设备属性（状态值）
        # =========================
        self.add_property("is_moving", "机械狗是否正在移动(True为移动，False为停止)",
                          lambda: self.is_moving)
        self.add_property("direction", "机械狗的移动方向(stop, forward, backward, left, right)",
                          lambda: self.direction)
        self.add_property("speed", "机械狗的移动速度可以是前后移动速度也可以是左右平移速度",
                          lambda: self.speed)
        self.add_property("last_update_time", "最后一次状态更新时间",
                          lambda: self.last_update_time)
        self.add_property("turn_speed", "机械狗的转动速度",
                          lambda: self.turn_speed)
        self.add_property("action", "机械狗的预设动作",
                          lambda: self.action)
        self.add_property("pace_mode", "机械狗的迈步频率",
                          lambda: self.pace)
        self.add_property("claw", "机械狗的机械臂夹爪开合程度,0对应完全张开，255对应完全闭合",
                          lambda: self.claw)
        self.add_property("gait", "机械狗的步态设置",
                          lambda: self.gait_type)
        self.add_property("perform", "机械狗的表演模式是否开启",
                          lambda: self.perform)
        self.add_property("is_turn", "机械狗是否正在转动(True为转动，False为停止)",
                          lambda: self.is_turn)
        self.add_property("turn", "机械狗的转动方向(stop, left, right)",
                          lambda: self.turn)
        self.add_property("move_time", "机械狗的移动的时间",
                          lambda: self.move_time)
        self.add_property("turn", "机械狗的转动时间",
                          lambda: self.turn_time)

        self.add_property("is_translation", "机械狗的位姿是否平移",
                          lambda: self.is_translation)
        self.add_property("translation_x", "机械狗的前后平移距离",
                          lambda: self.translation_x)
        self.add_property("translation_y", "机械狗的左右平移距离",
                          lambda: self.translation_y)
        self.add_property("translation_z", "机械狗的上下平移距离",
                          lambda: self.translation_z)
        self.add_property("is_attitude", "机械狗的位姿是否调整",
                          lambda: self.is_attitude)
        self.add_property("attitude_r", "机械狗的滚轮角",
                          lambda: self.attitude_r)
        self.add_property("attitude_p", "机械狗的俯仰角",
                          lambda: self.attitude_p)
        self.add_property("attitude_y", "机械狗的偏航角",
                          lambda: self.attitude_y)
        self.add_property("is_arm", "机械狗的机械臂是否调整",
                          lambda: self.is_arm)
        self.add_property("arm_x", "机械狗的机械臂相对于机械臂的基座的x坐标",
                          lambda: self.arm_x)
        self.add_property("arm_z", "机械狗的机械臂相对于机械臂的基座的z坐标",
                          lambda: self.arm_z)

        self.add_property("leg_1", "机械狗的左前腿是否移动",
                          lambda: self.leg_1)
        self.add_property("leg_2", "机械狗的右前腿是否移动",
                          lambda: self.leg_2)
        self.add_property("leg_3", "机械狗的右后腿是否移动",
                          lambda: self.leg_3)
        self.add_property("leg_4", "机械狗的左后腿是否移动",
                          lambda: self.leg_4)

        self.add_property("motor_11", "机械狗的11号舵机是否移动，位置在机械狗的左前腿的下面",
                          lambda: self.motor_11)
        self.add_property("motor_12", "机械狗的12号舵机是否移动，位置在机械狗的左前腿的中间",
                          lambda: self.motor_12)
        self.add_property("motor_13", "机械狗的13号舵机是否移动，位置在机械狗的左前腿的上面",
                          lambda: self.motor_13)

        self.add_property("motor_21", "机械狗的21号舵机是否移动，位置在机械狗的右前腿的下面",
                          lambda: self.motor_21)
        self.add_property("motor_22", "机械狗的22号舵机是否移动，位置在机械狗的右前腿的中间",
                          lambda: self.motor_22)
        self.add_property("motor_23", "机械狗的23号舵机是否移动，位置在机械狗的右前腿的上面",
                          lambda: self.motor_23)

        self.add_property("motor_31", "机械狗的31号舵机是否移动，位置在机械狗的右后腿的下面",
                          lambda: self.motor_31)
        self.add_property("motor_32", "机械狗的32号舵机是否移动，位置在机械狗的右后腿的中间",
                          lambda: self.motor_32)
        self.add_property("motor_33", "机械狗的33号舵机是否移动，位置在机械狗的右后腿的上面",
                          lambda: self.motor_33)

        self.add_property("motor_41", "机械狗的41号舵机是否移动，位置在机械狗的左后腿的下面",
                          lambda: self.motor_41)
        self.add_property("motor_42", "机械狗的42号舵机是否移动，位置在机械狗的左后腿的中间",
                          lambda: self.motor_42)
        self.add_property("motor_43", "机械狗的43号舵机是否移动，位置在机械狗的左后腿的上面",
                          lambda: self.motor_43)

        self.add_property("motor_51", "机械狗的51号舵机是否移动，位置在机械臂夹爪",
                          lambda: self.motor_51)
        self.add_property("motor_52", "机械狗的52号舵机是否移动，位置在机械臂小臂",
                          lambda: self.motor_52)
        self.add_property("motor_53", "机械狗的53号舵机是否移动，位置在机械臂大臂",
                          lambda: self.motor_53)





        # =========================
        # 注册设备方法（可执行的操作）
        # =========================

        self.add_method(
            "MoveForward",
            "让机械狗向前移动",
            [
                Parameter("speed", "机械狗向前移动的速度(0-25之间的数字)", ValueType.NUMBER, True),
                Parameter("move_time", "机械狗向前移动的时间单位秒", ValueType.NUMBER, True)
            ],
            lambda params: self._move_forward(params["speed"].get_value(), params['move_time'].get_value())
        )

        self.add_method(
            "MoveBackward",
            "让机械狗向后移动",
            [
                Parameter("speed", "机械狗向后移动的速度(0-25之间的数字)", ValueType.NUMBER, True),
                Parameter("move_time", "机械狗向后移动的时间单位秒", ValueType.NUMBER, True)
            ],
            lambda params: self._move_backward(params["speed"].get_value(), params['move_time'].get_value())
        )

        self.add_method(
            "MoveLeft",
            "让机械狗向左平移",
            [
                Parameter("speed", "机械狗向左移动的速度(0-18之间的数字)", ValueType.NUMBER, True),
                Parameter("move_time", "机械狗向左移动的时间单位秒", ValueType.NUMBER, True)
            ],
            lambda params: self._move_left(params["speed"].get_value(), params['move_time'].get_value())
        )

        self.add_method(
            "MoveRight",
            "让机械狗向右平移",
            [
                Parameter("speed", "机械狗向右移动速度(0-18之间的数字)", ValueType.NUMBER, True),
                Parameter("move_time", "机械狗向右移动的时间单位秒", ValueType.NUMBER, True)
            ],
            lambda params: self._move_right(params["speed"].get_value(), params['move_time'].get_value())
        )

        self.add_method(
            "Stop",
            "让机械狗停止移动",
            [],
            lambda params: self._stop()
        )

        self.add_method(
            "Turnright",
            "让机械狗右转",
            [
                Parameter('turn_speed', "机械狗向右转动的速度(0-30之间的数字)单位度/秒", ValueType.NUMBER, True),
                Parameter("turn_time", "机械狗向右转动的时间单位秒", ValueType.NUMBER, True)
            ],
            lambda params: self._turn_right(params["turn_speed"].get_value(), params["turn_time"].get_value())
        )

        self.add_method(
            "Turnleft",
            "让机械狗左转",
            [
                Parameter('turn_speed', "机械狗向左转动的速度(0-30之间的数字)单位度/秒", ValueType.NUMBER, True),
                Parameter("turn_time", "机械狗向左转动的时间单位秒", ValueType.NUMBER, True)
            ],
            lambda params: self._turn_left(params["turn_speed"].get_value(), params["turn_time"].get_value())
        )

        self.add_method(
            "pace",
            "改变机械狗的迈步频率",
            [
                Parameter('pace_mode', "模式选择(1,2,3之间的一个),1表示慢速,2表示正常,3表示高速", ValueType.NUMBER, True)
            ],
            lambda params: self._pace_mode(params["pace_mode"].get_value())
        )

        self.add_method(
            "claw",
            "机械狗的机械臂夹爪开合",
            [
                Parameter('claw', '夹爪开合(0-255之间的数字),0表示夹爪完全张开，255表示夹爪完全闭合', ValueType.NUMBER, True)
            ],
            lambda params: self._claw(params["claw"].get_value())
        )

        self.add_method(
            "action_1",
            "机械狗执行第一组预设动作，尤其注意动作对应的id",
            [
                Parameter('action',
             '取值范围为1-6，趴下的id为1,站起的id是2,匍匐前进的id是3,转圈的id是4,原地踏步的id是5,蹲起的id是6',
             ValueType.NUMBER,
             True)
            ],
            lambda params: self._action_1(params["action"].get_value())

        )
        self.add_method(
            "action_2",
            "机械狗执行第二组预设动作,尤其注意动作对应的id",
            [
                Parameter('action',
                          '取值范围为7-12，沿x转动的id为7，沿y转动的id是8，沿z转动的id为9，三轴转动的id为10,撒尿的id为11,坐下的id为12',
                          ValueType.NUMBER,
                          True)
            ],
            lambda params: self._action_2(params["action"].get_value())

        )
        self.add_method(
            "action_3",
            "机械狗执行第三组预设动作,尤其注意动作对应的id",
            [
                Parameter('action',
                          '取值范围为13-18，招手的id为13，伸懒腰的id为14,波浪运动的id为15,波浪运动的id为16，求食的id为17，找食物的id为18',
                          ValueType.NUMBER,
                          True)
            ],
            lambda params: self._action_3(params["action"].get_value())

        )
        self.add_method(
            "action_4",
            "机械狗执行第四组预设动作,尤其注意动作对应的id",
            [
                Parameter('action',
                          '取值范围为19-24，握手的id为19,展示机械臂的id为20，俯卧撑的id为21，张望的id为22,跳舞的id为23，调皮的id为24',
                          ValueType.NUMBER,
                          True)
            ],
            lambda params: self._action_4(params["action"].get_value())

        )
        self.add_method(
            "action_5",
            "机械狗执行第五组预设动作,尤其注意动作对应的id",
            [
                Parameter('action',
                          '取值范围为128-130，向上抓取对应128，向中抓取对应129，向下抓取对应130',
                          ValueType.NUMBER,
                          True)
            ],
            lambda params: self._action_5(params["action"].get_value())

        )
        self.add_method(
            "gait",
            "机械狗的步态设置",
            [
                Parameter('gait', '模式选择(1,2,3,4之间的一个),1表示trot,2表示walk,3表示high_walk,4表示slow_trot,默认为1', ValueType.NUMBER, True)
            ],
            lambda params: self._gait(params["gait"].get_value())
        )

        self.add_method(
            "perform",
            "机械狗的表演模式,如果未明确给出表演指令，请不要轻易进入表演模式，可以多去看看预设动作",
            [
                Parameter('perform', '0代表关闭、1代表开启', ValueType.NUMBER, True)
            ],
            lambda params: self._perform(params["perform"].get_value())
        )

        self.add_method(
            "translation",
            "机械狗的机身位置平移",
            [
                Parameter('translation_x', '机械狗的机身位置前后平移(-35和35之间的数字)单位mm', ValueType.NUMBER, True),
                Parameter('translation_y', '机械狗的机身位置左右平移(-18和18之间的数字)单位mm', ValueType.NUMBER, True),
                Parameter('translation_z', '机械狗的机身位置上下平移(75和115之间的数字)单位mm', ValueType.NUMBER, True)
            ],
            lambda params: self._translation(params["translation_x"].get_value(), params["translation_y"].get_value(), params["translation_z"].get_value())
        )

        self.add_method(
            "attitude",
            "机械狗的机身姿态调整(角度调整)",
            [
                Parameter('attitude_r', '机械狗的机身滚转角(-20和20之间的数字)单位度', ValueType.NUMBER, True),
                Parameter('attitude_p', '机械狗的机身俯仰角(-15和15之间的数字)单位度', ValueType.NUMBER, True),
                Parameter('attitude_y', '机械狗的机身偏航角(-11和11之间的数字)单位度', ValueType.NUMBER, True)
            ],
            lambda params: self._attitude(params["attitude_r"].get_value(), params["attitude_p"].get_value(),
                                             params["attitude_y"].get_value())
        )

        self.add_method(
            "arm",
            "机械狗的机械臂末端位置",
            [
                Parameter('arm_x', '机械狗的机械臂相对于机械臂的基座的x坐标(-80和155之间的数组)单位mm', ValueType.NUMBER, True),
                Parameter('arm_z', '机械狗的机械臂相对于机械臂的基座的z坐标(-95和155之间的数组)单位mm', ValueType.NUMBER, True)
            ],
            lambda params: self._arm(params["arm_x"].get_value(), params["arm_z"].get_value())
        )

        self.add_method(
            "leg_1",
            "机械狗的左前腿末端位置",
            [
                Parameter('data_x', '机械狗的左前腿足端位置的x坐标,x的范围是[-35,35]', ValueType.NUMBER, True),
                Parameter('data_y', '机械狗的左前腿足端位置的y坐标,y的范围是[-18,18]', ValueType.NUMBER, True),
                Parameter('data_z', '机械狗的左前腿足端位置的z坐标,z的范围是[75，155]', ValueType.NUMBER, True)
            ],
            lambda params: self._leg_1(params["data_x"].get_value(), params["data_y"].get_value(), params["data_z"].get_value())
        )

        self.add_method(
            "leg_2",
            "机械狗的右前腿末端位置",
            [
                Parameter('data_x', '机械狗的右前腿足端位置的x坐标,x的范围是[-35,35]', ValueType.NUMBER, True),
                Parameter('data_y', '机械狗的右前腿足端位置的y坐标,y的范围是[-18,18]', ValueType.NUMBER, True),
                Parameter('data_z', '机械狗的右前腿足端位置的z坐标,z的范围是[75，155]', ValueType.NUMBER, True)
            ],
            lambda params: self._leg_2(params["data_x"].get_value(), params["data_y"].get_value(), params["data_z"].get_value())
        )

        self.add_method(
            "leg_3",
            "机械狗的右后腿末端位置",
            [
                Parameter('data_x', '机械狗的右后腿足端位置的x坐标,x的范围是[-35,35]', ValueType.NUMBER, True),
                Parameter('data_y', '机械狗的右后腿足端位置的y坐标,y的范围是[-18,18]', ValueType.NUMBER, True),
                Parameter('data_z', '机械狗的右后腿足端位置的z坐标,z的范围是[75，155]', ValueType.NUMBER, True)
            ],
            lambda params: self._leg_3(params["data_x"].get_value(), params["data_y"].get_value(), params["data_z"].get_value())
        )

        self.add_method(
            "leg_4",
            "机械狗的左后腿末端位置",
            [
                Parameter('data_x', '机械狗的左后腿足端位置的x坐标,x的范围是[-35,35]', ValueType.NUMBER, True),
                Parameter('data_y', '机械狗的左后腿足端位置的y坐标,y的范围是[-18,18]', ValueType.NUMBER, True),
                Parameter('data_z', '机械狗的左后腿足端位置的z坐标,z的范围是[75，155]', ValueType.NUMBER, True)
            ],
            lambda params: self._leg_4(params["data_x"].get_value(), params["data_y"].get_value(), params["data_z"].get_value())
        )

        self.add_method(
            "motor_11",
            "机械狗的左前腿下面的舵机",
            [
                Parameter('data', '机械狗的左前腿下面的舵机角度,取值范围是[-73,57]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_11(params["data"].get_value())
        )
        self.add_method(
            "motor_12",
            "机械狗的左前腿中间的舵机",
            [
                Parameter('data', '机械狗的左前腿中间的舵机角度,取值范围是[-66,93]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_12(params["data"].get_value())
        )
        self.add_method(
            "motor_13",
            "机械狗的左前腿上面的舵机",
            [
                Parameter('data', '机械狗的左前腿上面的舵机角度,取值范围是[-31,31]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_13(params["data"].get_value())
        )

        self.add_method(
            "motor_21",
            "机械狗的右前腿下面的舵机",
            [
                Parameter('data', '机械狗的右前腿下面的舵机角度,取值范围是[-73,57]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_21(params["data"].get_value())
        )
        self.add_method(
            "motor_22",
            "机械狗的右前腿中间的舵机",
            [
                Parameter('data', '机械狗的右前腿中间的舵机角度,取值范围是[-66,93]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_22(params["data"].get_value())
        )
        self.add_method(
            "motor_23",
            "机械狗的右前腿上面的舵机",
            [
                Parameter('data', '机械狗的右前腿上面的舵机角度,取值范围是[-31,31]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_23(params["data"].get_value())
        )

        self.add_method(
            "motor_31",
            "机械狗的右后腿下面的舵机",
            [
                Parameter('data', '机械狗的右后腿下面的舵机角度,取值范围是[-73,57]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_31(params["data"].get_value())
        )
        self.add_method(
            "motor_32",
            "机械狗的右前腿中间的舵机",
            [
                Parameter('data', '机械狗的右后腿中间的舵机角度,取值范围是[-66,93]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_32(params["data"].get_value())
        )
        self.add_method(
            "motor_33",
            "机械狗的右前腿上面的舵机",
            [
                Parameter('data', '机械狗的右后腿上面的舵机角度,取值范围是[-31,31]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_33(params["data"].get_value())
        )

        self.add_method(
            "motor_41",
            "机械狗的左后腿下面的舵机",
            [
                Parameter('data', '机械狗的左后腿下面的舵机角度,取值范围是[-73,57]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_31(params["data"].get_value())
        )
        self.add_method(
            "motor_42",
            "机械狗的左前腿中间的舵机",
            [
                Parameter('data', '机械狗的左后腿中间的舵机角度,取值范围是[-66,93]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_32(params["data"].get_value())
        )
        self.add_method(
            "motor_43",
            "机械狗的左前腿上面的舵机",
            [
                Parameter('data', '机械狗的左后腿上面的舵机角度,取值范围是[-31,31]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_33(params["data"].get_value())
        )


        self.add_method(
            "motor_51",
            "机械狗的机械臂夹爪的舵机",
            [
                Parameter('data', '机械狗的机械臂夹爪的舵机角度,取值范围是[-65,65]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_51(params["data"].get_value())
        )
        self.add_method(
            "motor_52",
            "机械狗的机械臂小臂的舵机",
            [
                Parameter('data', '机械狗的机械臂小臂的舵机角度,取值范围是[-85,50]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_52(params["data"].get_value())
        )
        self.add_method(
            "motor_53",
            "机械狗的机械臂大臂的舵机",
            [
                Parameter('data', '机械狗的机械臂大臂的舵机角度,取值范围是[-75,90]', ValueType.NUMBER, True)
            ],
            lambda params: self._motor_53(params["data"].get_value())
        )

    # =========================
    # 确定狗的型号
    # =========================
    def init_dog(self):
        fm = self.dog.read_firmware()
        if fm[0] == 'M':
            print('XGO-MINI')
            self.dog = XGO(port='/dev/ttyAMA0', version="xgomini")
            self.dog_type = 'M'
        else:
            print('XGO-LITE')
            self.dog = XGO(port='/dev/ttyAMA0', version="xgolite")
            self.dog_type = 'L'

    def stop(self):
        self.is_moving = False
        self.direction = "stop"
        self.speed = 0
        self.last_update_time = int(time.time())
        self.is_turn = False
        self.turn = 'stop'
        self.turn_speed = 0
        self.dog.stop()
        print("开始下一个动作前，停止其他动作")
    # =========================
    # 内部方法实现（实际功能）
    # =========================

    def _move_forward(self, speed, move_time):
        self.stop()
        self.is_moving = True
        self.speed = speed
        self.last_update_time = int(time.time())
        self.direction = 'forward'
        self.dog.move('x', self.speed)
        self.move_time = move_time
        time.sleep(move_time)
        self.stop()

        return {
            "status": "success",
            "message": f"机械狗以速度 {self.speed} 向前移动{self.move_time}秒"
        }
    def _move_backward(self, speed, move_time):
        self.stop()
        self.is_moving = True
        self.speed = speed
        self.last_update_time = int(time.time())
        self.direction = 'backward'
        self.dog.move('x', -self.speed)
        self.move_time = move_time
        time.sleep(move_time)
        self.stop()
        print(f"[IoT设备] 机械狗以速度 {self.speed} 向后移动{self.move_time}秒")

        return {
            "status": "success",
            "message": f"机械狗以速度 {self.speed} 向后移动{self.move_time}秒"
        }
    def _move_left(self, speed, move_time):
        self.stop()
        self.is_moving = True
        self.speed = speed
        self.last_update_time = int(time.time())
        self.direction = 'left'
        self.dog.move('y', self.speed)
        self.move_time = move_time
        time.sleep(move_time)
        self.stop()

        print(f"[IoT设备] 机械狗正在以速度 {self.speed} 向左平移")

        return {
            "status": "success",
            "message": f"机械狗以速度 {self.speed} 向左平移{self.move_time}秒"
        }
    def _move_right(self, speed, move_time):
        self.stop()
        self.is_moving = True
        self.speed = speed
        self.last_update_time = int(time.time())
        self.direction = 'right'
        self.dog.move('y', -self.speed)
        self.move_time = move_time
        time.sleep(move_time)
        self.stop()
        print(f"[IoT设备] 机械狗正在以速度 {self.speed} 向右平移")

        return {
            "status": "success",
            "message": f"机械狗以速度 {self.speed} 向右平移{self.move_time}秒"
        }
    def _stop(self):
        self.is_moving = False
        self.direction = "stop"
        self.speed = 0
        self.last_update_time = int(time.time())
        self.is_turn = False
        self.turn = 'stop'
        self.turn_speed = 0
        self.dog.stop()

        print("[IoT设备] 机械狗已停止移动")
        return {
            "status": "success",
            "message": "机械狗已停止移动"
        }
    def _turn_right(self, turn_speed, turn_time):
        self.stop()
        self.is_turn = True
        self.turn = 'right'
        self.turn_speed = turn_speed
        self.last_update_time = int(time.time())
        self.dog.turn(-1.5 * self.turn_speed)
        self.turn_time = turn_time
        time.sleep(turn_time)
        self.stop()

        print("[IoT设备] 机械狗已经开始右转")
        return {
            "status": "success",
            "message": f"机械狗以速度 {turn_speed} 向右转{self.turn_time}秒"
        }
    def _turn_left(self, turn_speed, turn_time):
        self.stop()
        self.is_turn = True
        self.turn = 'left'
        self.turn_speed = turn_speed
        self.last_update_time = int(time.time())
        self.dog.turn(1.5 * self.turn_speed)
        self.turn_time = turn_time
        time.sleep(turn_time)
        self.stop()

        print("[IoT设备] 机械狗已经开始左转")
        return {
            "status": "success",
            "message": f"机械狗以速度 {turn_speed} 向左转{self.turn_time}秒"
        }
    def _pace_mode(self, pace_mode):
        self.stop()
        # 1表示慢速,2表示正常,3表示高速
        pace_list = ['slow', 'normal', 'high']
        self.last_update_time = int(time.time())
        self.pace = pace_list[pace_mode-1]
        self.dog.pace(self.pace)

        print("[IoT设备] 机械狗改变迈步频率")
        return {
            "status": "success",
            "message": f"机械狗的迈步频率为:{self.pace} "
        }
    def _claw(self, claw):
        self.stop()
        self.claw = claw
        self.last_update_time = int(time.time())
        self.dog.claw(self.claw)

        print("[IoT设备] 机械狗已改变机械臂开合")
        return {
            "status": "success",
            "message": f"机械狗现在的机械臂开合为{self.claw}"
        }
    def _action_1(self, action):
        self.stop()
        self.last_update_time = int(time.time())
        time_list = [0] * 131  
        time_list[1:25] = [3.5, 3.5, 5.5, 5.5, 4.5, 4.5, 4.5, 4.5, 4.5, 7.5, 7.5, 5.5, 7.5, 10.5, 6.5, 6.5, 6.5, 6.5, 10.5, 9.5, 8.5, 8.5, 6.5, 7.5]
        time_list[128:131] = [10.5, 10.5, 10.5]
        action_list = ['趴下', '站起', '匍匐前进', '转圈', '原地踏步', '蹲起', '沿x转动', '沿y转动', '沿z转动', '三轴转动', '撒尿', '坐下', '招手', '伸懒腰', '波浪运动', '摇摆运动', '求食', '找食物', '握手', '展示机械臂', '俯卧撑', '张望', '跳舞', '调皮','向上抓取','向中抓取','向下抓取']
        if  1 <= action <= 24:
            self.action = action_list[action-1]
            self.dog.action(action)
            time.sleep(time_list[action-1])
        else :
            self.action =action_list[action-104]
            self.dog.action(action)
        logging.warning(f"[IoT设备] 机械狗正在完成预设动作{self.action}")
        return {
            "status": "success",
            "message": f"机械狗已经完成预设动作{self.action},并且停止"
        }
    def _action_2(self, action):
        self.stop()
        self.last_update_time = int(time.time())
        time_list = [0] * 131
        time_list[1:25] = [3.5, 3.5, 5.5, 5.5, 4.5, 4.5, 4.5, 4.5, 4.5, 7.5, 7.5, 5.5, 7.5, 10.5, 6.5, 6.5, 6.5, 6.5, 10.5, 9.5, 8.5, 8.5, 6.5, 7.5]
        time_list[128:131] = [10.5, 10.5, 10.5]
        action_list = ['趴下', '站起', '匍匐前进', '转圈', '原地踏步', '蹲起', '沿x转动', '沿y转动', '沿z转动', '三轴转动', '撒尿', '坐下', '招手', '伸懒腰', '波浪运动', '摇摆运动', '求食', '找食物', '握手', '展示机械臂', '俯卧撑', '张望', '跳舞', '调皮','向上抓取','向中抓取','向下抓取']
        if  1 <= action <= 24:
            self.action = action_list[action-1]
            self.dog.action(action)
            time.sleep(time_list[action-1])
        else :
            self.action =action_list[action-104]
            self.dog.action(action)
        logging.warning(f"[IoT设备] 机械狗正在完成预设动作{self.action}")
        return {
            "status": "success",
            "message": f"机械狗已经完成预设动作{self.action},并且停止"
        }
    def _action_3(self, action):
        self.stop()
        self.last_update_time = int(time.time())
        time_list = [0] * 131
        time_list[1:25] = [3.5, 3.5, 5.5, 5.5, 4.5, 4.5, 4.5, 4.5, 4.5, 7.5, 7.5, 5.5, 7.5, 10.5, 6.5, 6.5, 6.5, 6.5, 10.5, 9.5, 8.5, 8.5, 6.5, 7.5]
        time_list[128:131] = [10.5, 10.5, 10.5]
        action_list = ['趴下', '站起', '匍匐前进', '转圈', '原地踏步', '蹲起', '沿x转动', '沿y转动', '沿z转动', '三轴转动', '撒尿', '坐下', '招手', '伸懒腰', '波浪运动', '摇摆运动', '求食', '找食物', '握手', '展示机械臂', '俯卧撑', '张望', '跳舞', '调皮','向上抓取','向中抓取','向下抓取']
        if  1 <= action <= 24:
            self.action = action_list[action-1]
            self.dog.action(action)
            time.sleep(time_list[action-1])
        else :
            self.action =action_list[action-104]
            self.dog.action(action)
        logging.warning(f"[IoT设备] 机械狗正在完成预设动作{self.action}")
        return {
            "status": "success",
            "message": f"机械狗已经完成预设动作{self.action},并且停止"
        }
    def _action_4(self, action):
        self.stop()
        self.last_update_time = int(time.time())
        time_list = [0] * 131
        time_list[1:25] = [3.5, 3.5, 5.5, 5.5, 4.5, 4.5, 4.5, 4.5, 4.5, 7.5, 7.5, 5.5, 7.5, 10.5, 6.5, 6.5, 6.5, 6.5, 10.5, 9.5, 8.5, 8.5, 6.5, 7.5]
        time_list[128:131] = [10.5, 10.5, 10.5]
        action_list = ['趴下', '站起', '匍匐前进', '转圈', '原地踏步', '蹲起', '沿x转动', '沿y转动', '沿z转动', '三轴转动', '撒尿', '坐下', '招手', '伸懒腰', '波浪运动', '摇摆运动', '求食', '找食物', '握手', '展示机械臂', '俯卧撑', '张望', '跳舞', '调皮','向上抓取','向中抓取','向下抓取']
        if  1 <= action <= 24:
            self.action = action_list[action-1]
            self.dog.action(action)
            time.sleep(time_list[action-1])
        else :
            self.action =action_list[action-104]
            self.dog.action(action)
        logging.warning(f"[IoT设备] 机械狗正在完成预设动作{self.action}")
        return {
            "status": "success",
            "message": f"机械狗已经完成预设动作{self.action},并且停止"
        }
    def _action_5(self, action):
        self.stop()
        self.last_update_time = int(time.time())
        time_list = [0] * 131
        time_list[1:25] = [3.5, 3.5, 5.5, 5.5, 4.5, 4.5, 4.5, 4.5, 4.5, 7.5, 7.5, 5.5, 7.5, 10.5, 6.5, 6.5, 6.5, 6.5, 10.5, 9.5, 8.5, 8.5, 6.5, 7.5]
        time_list[128:131] = [10.5, 10.5, 10.5]
        action_list = ['趴下', '站起', '匍匐前进', '转圈', '原地踏步', '蹲起', '沿x转动', '沿y转动', '沿z转动', '三轴转动', '撒尿', '坐下', '招手', '伸懒腰', '波浪运动', '摇摆运动', '求食', '找食物', '握手', '展示机械臂', '俯卧撑', '张望', '跳舞', '调皮','向上抓取','向中抓取','向下抓取']
        if  1 <= action <= 24:
            self.action = action_list[action-1]
            self.dog.action(action)
            time.sleep(time_list[action-1])
        else :
            self.action =action_list[action-104]
            self.dog.action(action)
        logging.warning(f"[IoT设备] 机械狗正在完成预设动作{self.action}")
        return {
            "status": "success",
            "message": f"机械狗已经完成预设动作{self.action},并且停止"
        }
    def _gait(self, gait_mode):
        self.stop()
        gait_list = ['trot', 'walk', 'high_walk', 'slow_trot']
        self.gait_type = gait_list[gait_mode-1]

        print("[IoT设备] 机械狗的步态已经调整")
        return {
            "status": "success",
            "message": f"机械狗的步态已经调整为{self.gait_type}"
        }

    def _perform(self, perform):
        self.stop()
        perform_list = [False, True]
        self.perform = perform_list[perform]
        self.dog.perform(perform)
        time.sleep(10)
        self.dog.stop()

        logging.warning("[IoT设备] 机械狗已经完成表演")
        return {
            "status": "success",
            "message": "机械狗已经完成表演"
        }

    def _attitude(self, r, p, y):
        if r== 0 and p== 0 and y == 0:
            self.is_attitude = False
        else:
            self.is_attitude = True
        self.attitude_r = r
        self.attitude_y = y
        self.attitude_p = p
        self.dog.attitude(['r', 'p', 'y'],[self.attitude_r, self.attitude_p, self.attitude_y])

        return {
            "status": "success",
            "message": "机械狗已经完成位姿调整"
        }

    def _translation(self, x, y, z):
        self.is_translation = True
        self.translation_x = x
        self.translation_y = y
        self.translation_z = z
        self.dog.attitude(['x', 'y', 'z'],[self.translation_x, self.translation_y, self.translation_z])

        return {
            "status": "success",
            "message": "机械狗已经完成机身平移调整"
        }

    def _arm(self, arm_x, arm_z):
        self.is_arm = True
        self.arm_x = arm_x
        self.arm_z = arm_z
        self.dog.arm(self.arm_x, self.arm_z)

        return {
            "status": "success",
            "message": "机械狗已经完成机械臂调整"
        }

    def _leg_1(self, x, y, z):
        data = [x, y, z]
        if data == [0, 0, 0]:
            self.leg_1 = False
        else:
            self.leg_1 = True
        self.dog.leg(1, data)

        return {
            "status": "success",
            "message": "机械狗已经完成左前腿的调整"
        }

    def _leg_2(self, x, y, z):
        data = [x, y, z]
        if data == [0, 0, 0]:
            self.leg_2 = False
        else:
            self.leg_2 = True
        self.dog.leg(2, data)

        return {
            "status": "success",
            "message": "机械狗已经完成右前腿的调整"
        }

    def _leg_3(self, x, y, z):
        data = [x, y, z]
        if data == [0, 0, 0]:
            self.leg_3 = False
        else:
            self.leg_3 = True
        self.dog.leg(3, data)

        return {
            "status": "success",
            "message": "机械狗已经完成右后腿的调整"
        }

    def _leg_4(self, x, y, z):
        data = [x, y, z]
        if data == [0, 0, 0]:
            self.leg_4 = False
        else:
            self.leg_4 = True
        self.dog.leg(4, data)

        return {
            "status": "success",
            "message": "机械狗已经完成左后腿的调整"
        }
    def _motor_11(self, data):
        self.motor_11 = True
        self.dog.motor(11, data)
        return {
            "status": "success",
            "message": "机械狗已经完成左前腿下面舵机的调整"
        }
    def _motor_12(self, data):
        self.motor_12 = True
        self.dog.motor(12, data)
        return {
            "status": "success",
            "message": "机械狗已经完成左前腿中间舵机的调整"
        }
    def _motor_13(self, data):
        self.motor_13 = True
        self.dog.motor(13, data)
        return {
            "status": "success",
            "message": "机械狗已经完成左前腿上面舵机的调整"
        }

    def _motor_21(self, data):
        self.motor_21 = True
        self.dog.motor(21, data)
        return {
            "status": "success",
            "message": "机械狗已经完成右前腿下面舵机的调整"
        }
    def _motor_22(self, data):
        self.motor_22 = True
        self.dog.motor(22, data)
        return {
            "status": "success",
            "message": "机械狗已经完成右前腿中间舵机的调整"
        }
    def _motor_23(self, data):
        self.motor_23 = True
        self.dog.motor(23, data)
        return {
            "status": "success",
            "message": "机械狗已经完成右前腿上面舵机的调整"
        }

    def _motor_31(self, data):
        self.motor_31 = True
        self.dog.motor(31, data)
        return {
            "status": "success",
            "message": "机械狗已经完成右后腿下面舵机的调整"
        }
    def _motor_32(self, data):
        self.motor_32 = True
        self.dog.motor(32, data)
        return {
            "status": "success",
            "message": "机械狗已经完成右后腿中间舵机的调整"
        }
    def _motor_33(self, data):
        self.motor_33 = True
        self.dog.motor(33, data)
        return {
            "status": "success",
            "message": "机械狗已经完成右后腿上面舵机的调整"
        }

    def _motor_41(self, data):
        self.motor_41 = True
        self.dog.motor(41, data)
        return {
            "status": "success",
            "message": "机械狗已经完成左后腿下面舵机的调整"
        }
    def _motor_42(self, data):
        self.motor_42 = True
        self.dog.motor(42, data)
        return {
            "status": "success",
            "message": "机械狗已经完成左后腿中间舵机的调整"
        }
    def _motor_43(self, data):
        self.motor_43 = True
        self.dog.motor(43, data)
        return {
            "status": "success",
            "message": "机械狗已经完成左后腿上面舵机的调整"
        }

    def _motor_51(self, data):
        self.motor_51 = True
        self.dog.motor(51, data)
        return {
            "status": "success",
            "message": "机械狗已经完成机械臂夹爪舵机的调整"
        }
    def _motor_52(self, data):
        self.motor_52 = True
        self.dog.motor(52, data)
        return {
            "status": "success",
            "message": "机械狗已经完成机械臂小臂舵机的调整"
        }
    def _motor_53(self, data):
        self.motor_53 = True
        self.dog.motor(53, data)
        return {
            "status": "success",
            "message": "机械狗已经完成机械臂大臂舵机的调整"
        }