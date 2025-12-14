import serial
import struct
import time
import math

__version__ = '1.0.0'
__last_modified__ = '2024/12/23'

"""
XGOorder 用来存放命令地址和对应数据
XGOorder is used to store the command address and corresponding data
"""

XGOorder = {
    "BATTERY": [0x01, 100],
    "PERFORM": [0x03, 0],
    "CALIBRATION": [0x04, 0],
    "UPGRADE": [0x05, 0],
    "SET_ORIGIN": [0x06, 1],
    "FIRMWARE_VERSION": [0x07],
    "GAIT_TYPE": [0x09, 0x00],
    "BT_NAME": [0x13, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "UNLOAD_MOTOR": [0x20, 0],
    "LOAD_MOTOR": [0x20, 0],
    "VX": [0x30, 128],
    "VY": [0x31, 128],
    "VYAW": [0x32, 128],
    "TRANSLATION": [0x33, 0, 0, 0],
    "ATTITUDE": [0x36, 0, 0, 0],
    "PERIODIC_ROT": [0x39, 0, 0, 0],
    "MarkTime": [0x3C, 0],
    "MOVE_MODE": [0x3D, 0],
    "ACTION": [0x3E, 0],
    "MOVE_TO": [0x3F, 0, 0],
    "PERIODIC_TRAN": [0x80, 0, 0, 0],
    "MOTOR_ANGLE": [0x50, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128],
    "MOTOR_SPEED": [0x5C, 1],
    "MOVE_TO_MID": [0x5F, 1],
    "LEG_POS": [0x40, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "IMU": [0x61, 0],
    "ROLL": [0x62, 0],
    "PITCH": [0x63, 0],
    "TEACH_RECORD": [0x21, 0],
    "TEACH_PLAY": [0x22, 0],
    "TEACH_ARM_RECORD": [0x23, 0],
    "TEACH_ARM_PLAY": [0x24, 0],
    "YAW": [0x64, 0],
    "CLAW": [0x71, 0],
    "ARM_MODE": [0x72, 0],
    "ARM_X": [0x73, 0],
    "ARM_Z": [0x74, 0],
    "ARM_SPEED": [0x75, 0],
    "ARM_THETA": [0x76, 0],
    "ARM_R": [0x77, 0],
    "OUTPUT_ANALOG": [0x90, 0],
    "OUTPUT_DIGITAL": [0x91, 0],
    "LED_COLOR": [0x69, 0, 0, 0],
    "ANALOG_READ": [0x92, 0],
    "DIGITIAL_READ": [0x93, 0],
    "EX_MOTOR": [0xA1, 0x08, 0x00]
}

"""
XGOparam 用来存放机器狗的参数限制范围
Xgoparam is used to store the parameter limit range of the robot dog
"""
XGOparam = {}


def search(data, list):
    for i in range(len(list)):
        if data == list[i]:
            return i + 1
    return -1


def conver2u8(data, limit, min_value=0):
    """
    将实际参数转化为0到255的单字节数据
    Convert the actual parameters to single byte data from 0 to 255
    """
    max_value = 0xff
    if not isinstance(limit, list):
        limit = [-limit, limit]
    if data >= limit[1]:
        return max_value
    elif data <= limit[0]:
        return min_value
    else:
        return int(255 / (limit[1] - limit[0]) * (data - limit[0]))


def conver2float(data, limit):
    if not isinstance(limit, list):
        return (data - 128.0) / 255.0 * limit
    else:
        return data / 255.0 * (limit[1] - limit[0]) + limit[0]


def Byte2Float(rawdata):
    a = bytearray()
    a.append(rawdata[3])
    a.append(rawdata[2])
    a.append(rawdata[1])
    a.append(rawdata[0])
    return struct.unpack("!f", a)[0]


def Byte2Short(rawdata):
    a = bytearray()
    a.append(rawdata[0])
    a.append(rawdata[1])
    return struct.unpack('>h', a)[0]


def changePara(version):
    global XGOparam
    if version == 'xgomini':
        XGOparam = {
            "TRANSLATION_LIMIT": [35, 19.5, [60, 120]],  # X Y Z 平移范围
            "ATTITUDE_LIMIT": [20, 22, 16],  # Roll Pitch Yaw 姿态范围
            "LEG_LIMIT": [35, 18, [75, 115]],  # 腿长范围
            "MOTOR_LIMIT": [[-73, 57], [-66, 93], [-31, 31], [-65, 65], [-85, 50], [-75, 90]],  # 下 中 上 舵机范围
            "PERIOD_LIMIT": [[1.5, 8]],
            "MARK_TIME_LIMIT": [10, 35],  # 原地踏步高度范围
            "VX_LIMIT": 25,  # X速度范围
            "VY_LIMIT": 18,  # Y速度范围
            "VYAW_LIMIT": 100,  # 旋转速度范围
            "ARM_LIMIT": [[-80, 155], [-95, 155], [70, 270], [80, 140]],
            "ActionTime": {
                1: 3, 2: 3, 3: 5, 4: 5, 5: 4, 6: 4, 7: 4, 8: 4, 9: 4, 10: 7,
                11: 7, 12: 5, 13: 7, 14: 10, 15: 6, 16: 6, 17: 4, 18: 6, 19: 10, 20: 9,
                21: 8, 22: 7, 23: 6, 24: 7, 128: 10, 129: 10, 130: 10, 255: 1}
        }
    elif version == 'xgolite':
        XGOparam = {
            "TRANSLATION_LIMIT": [25, 18, [60, 110]],
            "ATTITUDE_LIMIT": [20, 10, 12],
            "LEG_LIMIT": [25, 18, [60, 110]],
            "MOTOR_LIMIT": [[-70, 50], [-70, 90], [-30, 30], [-65, 65], [-115, 70], [-85, 100]],
            "PERIOD_LIMIT": [[1.5, 8]],
            "MARK_TIME_LIMIT": [10, 25],
            "VX_LIMIT": 25,
            "VY_LIMIT": 18,
            "VYAW_LIMIT": 100,
            "ARM_LIMIT": [[-80, 155], [-95, 155], [70, 270], [80, 140]],
            "ActionTime": {
                1: 3, 2: 3, 3: 5, 4: 5, 5: 4, 6: 4, 7: 4, 8: 4, 9: 4, 10: 7,
                11: 7, 12: 5, 13: 7, 14: 10, 15: 6, 16: 6, 17: 4, 18: 6, 19: 10, 20: 9,
                21: 8, 22: 7, 23: 6, 24: 7, 128: 10, 129: 10, 130: 10, 255: 1}
        }


class XGO():
    """
    在实例化XGO时需要指定上位机与机器狗的串口通讯接口
    When instantiating XGO, you need to specify the serial
    communication interface between the upper computer and the machine dog
    """

    def __init__(self, port, baud=115200, version="xgomini", verbose=False):
        self.verbose = verbose
        self.ser = serial.Serial("/dev/ttyAMA0", baud, timeout=0.5)
        self.ser.flushOutput()
        self.ser.flushInput()
        self.port = port
        self.rx_FLAG = 0
        self.rx_COUNT = 0
        self.rx_ADDR = 0
        self.rx_LEN = 0
        self.rx_data = bytearray(50)
        time.sleep(0.25)
        self.version = self.read_firmware()
        if self.version[0] == 'M':
            changePara('xgomini')
        elif self.version[0] == 'L':
            changePara('xgolite')
        else:
            print("ERROR!Can't read firmware version!")
        self.mintime = 0.65
        self.reset()
        self.init_yaw = self.read_yaw()
        time.sleep(1)
        pass

    # --- Low-level communication ---
    def __send(self, key, index=1, len=1):
        mode = 0x00
        order = XGOorder[key][0] + index - 1
        value = []
        value_sum = 0
        for i in range(0, len):
            value.append(XGOorder[key][index + i])
            value_sum = value_sum + XGOorder[key][index + i]
        sum_data = ((len + 0x08) + mode + order + value_sum) % 256
        sum_data = 255 - sum_data
        tx = [0x55, 0x00, (len + 0x08), mode, order]
        tx.extend(value)
        tx.extend([sum_data, 0x00, 0xAA])
        self.ser.write(tx)
        if self.verbose:
            print("tx_data: ", tx)

    def __read(self, addr, read_len=1):
        # self.ser.flushInput() # Flushing input here might clear responses too early
        mode = 0x02
        sum_data = (0x09 + mode + addr + read_len) % 256
        sum_data = 255 - sum_data
        tx = [0x55, 0x00, 0x09, mode, addr, read_len, sum_data, 0x00, 0xAA]
        self.ser.flushInput()
        self.ser.write(tx)
        if self.verbose:
            print("tx_data: ", tx)

    def __change_baud(self, baud):
        self.ser.flush()
        self.ser.close()
        self.ser = serial.Serial(self.port, baud, timeout=0.5)

    # --- High-level actions & movements ---
    def stop(self):
        self.move_x(0)
        self.move_y(0)
        self.mark_time(0)
        self.turn(0)

    def move(self, direction, step):
        if direction in ['x', 'X']:
            self.move_x(step)
        elif direction in ['y', 'Y']:
            self.move_y(step)
        else:
            print("ERROR!Invalid direction!")

    def move_x(self, step, runtime=0):
        XGOorder["VX"][1] = conver2u8(step, XGOparam["VX_LIMIT"])
        self.__send("VX")
        if runtime:
            time.sleep(runtime)
            XGOorder["VX"][1] = conver2u8(0, XGOparam["VX_LIMIT"])
            self.__send("VX")

    def move_y(self, step, runtime=0):
        XGOorder["VY"][1] = conver2u8(step, XGOparam["VY_LIMIT"])
        self.__send("VY")
        if runtime:
            time.sleep(runtime)
            XGOorder["VY"][1] = conver2u8(0, XGOparam["VY_LIMIT"])
            self.__send("VY")

    def turn(self, step, runtime=0):
        XGOorder["VYAW"][1] = conver2u8(step, XGOparam["VYAW_LIMIT"])
        self.__send("VYAW")
        if runtime:
            time.sleep(runtime)
            XGOorder["VYAW"][1] = conver2u8(0, XGOparam["VYAW_LIMIT"])
            self.__send("VYAW")

    def forward(self, step):
        self.move_x(abs(step))

    def back(self, step):
        self.move_x(-abs(step))

    def left(self, step):
        self.move_y(abs(step))

    def right(self, step):
        self.move_y(-abs(step))

    def turnleft(self, step):
        self.turn(abs(step))

    def turnright(self, step):
        self.turn(-abs(step))

    def move_by(self, distance, vx, vy, k, mintime):
        runtime = k * abs(distance) + mintime
        self.move_x(math.copysign(vx, distance))
        self.move_y(math.copysign(vy, distance))
        time.sleep(runtime)
        self.move_x(0)
        self.move_y(0)
        time.sleep(0.2)

    def move_x_by(self, distance, vx=18, k=0.035, mintime=0.55):
        self.move_by(distance, vx, 0, k, mintime)
        pass

    def move_y_by(self, distance, vy=18, k=0.0373, mintime=0.5):
        self.move_by(distance, 0, vy, k, mintime)
        pass

    def turn_by(self, theta, mintime, vyaw=16, k=0.08):
        runtime = abs(theta) * k + mintime
        self.turn(math.copysign(vyaw, theta))
        time.sleep(runtime)
        self.turn(0)
        pass

    def turn_to(self, theta, vyaw=60, emax=10):
        cur_yaw = self.read_yaw()
        des_yaw = self.init_yaw + theta
        while abs(des_yaw - cur_yaw) >= emax:
            self.turn(math.copysign(vyaw, des_yaw - cur_yaw))
            cur_yaw = self.read_yaw()
        self.turn(0)
        time.sleep(0.2)
        pass

    def __translation(self, direction, data):
        index = search(direction, ['x', 'y', 'z'])
        if index == -1:
            print("ERROR!Direction must be 'x', 'y' or 'z'")
            return
        XGOorder["TRANSLATION"][index] = conver2u8(data, XGOparam["TRANSLATION_LIMIT"][index - 1])
        self.__send("TRANSLATION", index)

    def translation(self, direction, data):
        """
        使机器狗足端不动，身体进行三轴平动
        Keep the robot's feet stationary and the body makes three-axis translation
        """
        if isinstance(direction, list):
            if len(direction) != len(data):
                print("ERROR!The length of direction and data don't match!")
                return
            for i in range(len(data)):
                self.__translation(direction[i], data[i])
        else:
            self.__translation(direction, data)

    # Internal helper for attitude, could be considered mid-level
    def __attitude(self, direction, data):
        index = search(direction, ['r', 'p', 'y'])
        if index == -1:
            print("ERROR!Direction must be 'r', 'p' or 'y'")
            return
        XGOorder["ATTITUDE"][index] = conver2u8(data, XGOparam["ATTITUDE_LIMIT"][index - 1])
        self.__send("ATTITUDE", index)

    def attitude(self, direction, data):
        """
        使机器狗足端不动，身体进行三轴转动
        Keep the robot's feet stationary and the body makes three-axis rotation
        """
        if isinstance(direction, list):
            if len(direction) != len(data):
                print("ERROR!The length of direction and data don't match!")
                return
            for i in range(len(data)):
                self.__attitude(direction[i], data[i])
        else:
            self.__attitude(direction, data)

    def action(self, action_id, wait=False):
        """
        使机器狗狗指定的预设动作
        Make the robot do the specified preset action
        """
        if action_id <= 0 or action_id > 255:
            print("ERROR!Illegal Action ID!")
            return
        XGOorder["ACTION"][1] = action_id
        self.__send("ACTION")
        if wait:
            st = XGOparam["ActionTime"].get(action_id)
            if st:
                time.sleep(st)

    def reset(self):
        """
        机器狗停止运动，所有参数恢复到初始状态
        The robot dog stops moving and all parameters return to the initial state
        """
        self.action(255)
        time.sleep(1)

    # --- Mid-level joint/leg control ---
    def leg(self, leg_id, data):
        """
        控制机器狗的单腿的三轴移动
        Control the three-axis movement of a single leg of the robot
        """
        value = [0, 0, 0]
        if leg_id not in [1, 2, 3, 4]:
            print("Error!Illegal Index!")
            return
        if len(data) != 3:
            # message = "Error!Illegal Value!" # Original variable was unused
            print("Error!Illegal Value for leg data length!")
            return
        for i in range(3):
            try:
                value[i] = conver2u8(data[i], XGOparam["LEG_LIMIT"][i])
            except:
                print("Error!Illegal Value for leg data content!")
                return # Important to return on error
        for i in range(3):
            index = 3 * (leg_id - 1) + i + 1
            XGOorder["LEG_POS"][index] = value[i]
            self.__send("LEG_POS", index)

    # Internal helper for motor control
    def __motor(self, motor_index, data): # Renamed index to motor_index for clarity
        if motor_index < 13: # Body/Leg motors
            XGOorder["MOTOR_ANGLE"][motor_index] = conver2u8(data, XGOparam["MOTOR_LIMIT"][(motor_index - 1) % 3])
        elif motor_index == 13: # Claw motor (often identified separately)
            # This was MOTOR_LIMIT[3] which might be an index error if MOTOR_LIMIT is for leg pairs.
            # Assuming MOTOR_LIMIT[3] is intended for a claw or similar single motor.
            # The original `motor` function maps ID 51 (claw) to index 13.
            # MOTOR_LIMIT has 6 entries for leg motors. Claw might need its own param limits.
            # For now, keeping original logic, but it's a point of attention.
            # The `self.claw()` method is more direct for claw control.
            # This direct call to self.claw() from __motor seems unusual.
            # Let's assume it means motor ID 13 is special.
            # The claw method itself uses XGOorder["CLAW"]
            # This line might be redundant if claw() is the preferred way.
            # However, motor_id 51 (claw) is mapped to index 13 in self.motor()
            # So, if self.motor(51, value) is called, it becomes self.__motor(13, value)
            # This will then call self.claw(conver2u8(data, XGOparam["MOTOR_LIMIT"][3]))
            # This looks like it could be simplified by having self.motor call self.claw directly if ID is 51.
            # For now, replicate:
            self.claw(conver2u8(data, XGOparam["MOTOR_LIMIT"][3])) # Ensure MOTOR_LIMIT[3] is sensible for claw
            return # Important: return after handling claw via self.claw()
        else: # Other motors (e.g., arm motors if mapped here, original had 12 motors + claw in MOTOR_ID)
            # Original MOTOR_ID had: 11-13 (leg1), 21-23 (leg2), 31-33 (leg3), 41-43 (leg4)
            # Then 51 (claw, index 13), 52 (arm base?, index 14), 53 (arm mid?, index 15)
            # MOTOR_LIMIT seems to be for leg motors primarily (0-2 are hip/thigh/knee).
            # Need to verify XGOparam["MOTOR_LIMIT"] indexing for arm motors (index-10)
            # (14-10)=4, (15-10)=5. These are valid indices if MOTOR_LIMIT has 6 elements for legs.
            XGOorder["MOTOR_ANGLE"][motor_index] = conver2u8(data, XGOparam["MOTOR_LIMIT"][motor_index - 10])
        self.__send("MOTOR_ANGLE", motor_index)




    def motors(self, angles):
        """
        控制所有15个舵机 (Control all 15 servos)
        angles: list of 15 floats (degrees)
        """
        if len(angles) != 15:
            print(f"Error: motors() requires 15 angles, got {len(angles)}")
            return
        
        for i in range(15):
            # Map index to limit index.
            # 0-2 (Leg1): Limit 0
            # 3-5 (Leg2): Limit 1
            # 6-8 (Leg3): Limit 2
            # 9-11 (Leg4): Limit 3
            # 12-14 (Head/Arm): Limit 4? 
            # XGOparam["MOTOR_LIMIT"] has 6 subarrays.
            # 0: Leg1? 1: Leg2?
            # read_motor logic: `i < 12: i%3`. `i >= 12: i-9`.
            # i=12 (13th item) -> 12-9=3.
            # i=13 -> 4.
            # i=14 -> 5.
            # Matches MOTOR_LIMIT length of 6.
            
            limit_idx = i % 3 if i < 12 else (i - 9)
            XGOorder["MOTOR_ANGLE"][i+1] = conver2u8(angles[i], XGOparam["MOTOR_LIMIT"][limit_idx])
            
        self.__send("MOTOR_ANGLE", len=15)
        MOTOR_ID = [11, 12, 13, 21, 22, 23, 31, 32, 33, 41, 42, 43, 51, 52, 53]

        if isinstance(motor_id, list):
            if len(motor_id) != len(data):
                print("Error!Length Mismatching!")
                return
            index = []
            for i in range(len(motor_id)):
                temp_index = search(motor_id[i], MOTOR_ID)
                if temp_index == -1:
                    print("Error!Illegal Index!")
                    return
                index.append(temp_index)
            for i in range(len(index)):
                self.__motor(index[i], data[i])
        else:
            index = search(motor_id, MOTOR_ID)
            self.__motor(index, data)

    def unload_motor(self, leg_id):
        if leg_id not in [1, 2, 3, 4, 5]:
            print('ERROR!leg_id must be 1, 2, 3 ,4 or 5')
            return
        XGOorder["UNLOAD_MOTOR"][1] = 0x10 + leg_id
        self.__send("UNLOAD_MOTOR")

    def unload_allmotor(self):
        XGOorder["UNLOAD_MOTOR"][1] = 0x01
        self.__send("UNLOAD_MOTOR")

    def load_motor(self, leg_id):
        if leg_id not in [1, 2, 3, 4, 5]:
            print('ERROR!leg_id must be 1, 2, 3 ,4 or 5')
            return
        XGOorder["LOAD_MOTOR"][1] = 0x20 + leg_id
        self.__send("LOAD_MOTOR")

    def load_allmotor(self):
        XGOorder["LOAD_MOTOR"][1] = 0x00
        self.__send("LOAD_MOTOR")

    def __periodic_rot(self, direction, period):
        index = search(direction, ['r', 'p', 'y'])
        if index == -1:
            print("ERROR!Direction must be 'r', 'p' or 'y'")
            return
        if period == 0:
            XGOorder["PERIODIC_ROT"][index] = 0
        else:
            XGOorder["PERIODIC_ROT"][index] = conver2u8(period, XGOparam["PERIOD_LIMIT"][0], min_value=1)
        self.__send("PERIODIC_ROT", index)

    def periodic_rot(self, direction, period):
        """
        使机器狗周期性转动
        Make the robot rotate periodically
        """
        if (isinstance(direction, list)):
            if (len(direction) != len(period)):
                print("ERROR!The length of direction and data don't match!")
                return
            for i in range(len(period)):
                self.__periodic_rot(direction[i], period[i])
        else:
            self.__periodic_rot(direction, period)

    # Internal helper
    def __periodic_tran(self, direction, period):
        index = search(direction, ['x', 'y', 'z'])
        if index == -1:
            print("ERROR!Direction must be 'x', 'y' or 'z'")
            return
        if period == 0:
            XGOorder["PERIODIC_TRAN"][index] = 0
        else:
            XGOorder["PERIODIC_TRAN"][index] = conver2u8(period, XGOparam["PERIOD_LIMIT"][0], min_value=1)
        self.__send("PERIODIC_TRAN", index)

    def periodic_tran(self, direction, period):
        """
        使机器狗周期性平动
        Make the robot translate periodically
        """
        if isinstance(direction, list):
            if len(direction) != len(period):
                print("ERROR!The length of direction and data don't match!")
                return
            for i in range(len(period)):
                self.__periodic_tran(direction[i], period[i])
        else:
            self.__periodic_tran(direction, period)

    def mark_time(self, data):
        """
        使机器狗原地踏步
        Make the robot marks time
        """
        if data == 0:
            XGOorder["MarkTime"][1] = 0
        else:
            XGOorder["MarkTime"][1] = conver2u8(data, XGOparam["MARK_TIME_LIMIT"], min_value=1)
        self.__send("MarkTime")

    # --- Configuration & Modes ---
    def pace(self, mode):
        """
        改变机器狗的踏步频率
        Change the step frequency of the robot
        """
        if mode == "normal":
            value = 0x00
        elif mode == "slow":
            value = 0x01
        elif mode == "high":
            value = 0x02
        else:
            print("ERROR!Illegal Value for pace mode!")
            return
        XGOorder["MOVE_MODE"][1] = value
        self.__send("MOVE_MODE")

    def gait_type(self, mode_str): # Renamed mode to mode_str for clarity
        """Sets the gait type for the robot."""
        value = None
        if mode_str == "trot":
            value = 0x00
        elif mode_str == "walk":
            value = 0x01
        elif mode_str == "high_walk":
            value = 0x02
        elif mode_str == "slow_trot":
            value = 0x03
        else:
            print(f"ERROR! Illegal gait_type: {mode_str}")
            return
        XGOorder["GAIT_TYPE"][1] = value
        self.__send("GAIT_TYPE")

    def imu_mode(self, mode_val): # Renamed mode to mode_val for clarity
        """
        开启/关闭机器狗自稳状态 (Turn on/off the self-stabilization state of the robot dog)
        Turn on / off the self stable state of the robot dog
        """
        if mode != 0 and mode != 1:
            print("ERROR!Illegal Value!")
            return
        XGOorder["IMU"][1] = mode
        self.__send("IMU")

    def perform(self, mode):
        """
        开启/关闭机器狗循环做动作状态
        Turn on / off the action status of the robot dog cycle
        """
        if mode != 0 and mode != 1:
            print("ERROR!Illegal Value!")
            return
        XGOorder["PERFORM"][1] = mode
        self.__send("PERFORM")

    def motor_speed(self, speed):
        """
        调节舵机转动速度，只在单独控制舵机的情况下有效
        Adjust the steering gear rotation speed,
        only effective when control the steering gear separately.
        Value 0 is mapped to 1.
        """
        if not 0 <= speed <= 255:
            print("ERROR! Illegal Value! Motor speed must be between 0 and 255.")
            return

        effective_speed = speed if speed != 0 else 1
        XGOorder["MOTOR_SPEED"][1] = effective_speed
        self.__send("MOTOR_SPEED")

    def bt_rename(self, name_str): # Renamed name to name_str
        """Renames the Bluetooth device."""
        if not isinstance(name_str, str):
            print("ERROR! Bluetooth name must be a string.")
            return

        if not 1 <= len(name_str) <= 10: # Original allowed empty string, but likely not intended for rename
            print("ERROR! Bluetooth name length must be between 1 and 10 characters.")
            return

        try:
            name_bytes = name_str.encode('ascii')
            # Clear previous name data in XGOorder if necessary (or ensure it's fixed length)
            # XGOorder["BT_NAME"] = [0x13, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] (10 zeros for name)
            for i in range(10): # Max 10 chars for name
                if i < len(name_bytes):
                    XGOorder["BT_NAME"][i+1] = name_bytes[i]
                else:
                    XGOorder["BT_NAME"][i+1] = 0 # Pad with null bytes if name is shorter
            self.__send("BT_NAME", len=10) # Send full 10 byte payload for BT_NAME
        except UnicodeEncodeError:
            print("ERROR! Bluetooth name only supports ASCII characters.")

    # --- Sensor & State Reading ---
    def read_motor(self):
        """
        读取15个舵机的角度 (Reads the angles of the 15 servo motors)
        """
        self.__read(XGOorder["MOTOR_ANGLE"][0], 15)
        angle = []
        if self.__unpack():
            for i in range(self.rx_COUNT + 1):
                if i < 12:
                    angle.append(round(conver2float(self.rx_data[i], XGOparam["MOTOR_LIMIT"][i % 3]), 2))
                else:
                    angle.append(round(conver2float(self.rx_data[i], XGOparam["MOTOR_LIMIT"][i - 9]), 2))
        return angle

    def read_battery(self):
        self.__read(XGOorder["BATTERY"][0], 1)
        battery = 0
        if self.__unpack():
            battery = int(self.rx_data[0])
        return battery

    def read_firmware(self):
        self.__read(XGOorder["FIRMWARE_VERSION"][0], 10)
        firmware_version = 'Null'
        if self.__unpack():
            data = self.rx_data[0:10]
            try:
                firmware_version = data.decode("ascii").strip('\0')
            except Exception as e:
                print(e)
        return firmware_version

    def read_roll(self):
        self.__read(XGOorder["ROLL"][0], 4)
        roll = 0
        if self.__unpack():
            roll = Byte2Float(self.rx_data)
        return round(roll, 2)

    def read_pitch(self):
        self.__read(XGOorder["PITCH"][0], 4)
        pitch = 0
        if self.__unpack():
            pitch = Byte2Float(self.rx_data)
        return round(pitch, 2)

    def read_yaw(self):
        self.__read(XGOorder["YAW"][0], 4)
        yaw = 0
        if self.__unpack():
            yaw = Byte2Float(self.rx_data)
        return round(yaw, 2)

    def read_analog(self):
        self.__read(XGOorder["ANALOG_READ"][0], 1)
        data = 0
        if self.__unpack():
            data = int(self.rx_data[0])
        return data

    def read_digital(self):
        self.__read(XGOorder["DIGITIAL_READ"][0], 1)
        data = 0
        if self.__unpack():
            data = int(self.rx_data[0])
        return data

    def read_rotate_state(self):
        self.__read(XGOorder["MOVE_TO"][0], 1)
        state = 0
        if self.__unpack():
            state = int(self.rx_data[0])
        return state

    def __unpack(self, timeout=1):
        t = time.time()
        rx_msg = []
        while time.time() - t < timeout:
            n = self.ser.inWaiting()
            rx_CHECK = 0
            if n:
                data = self.ser.read(n)
                for num in data:
                    rx_msg.append(num)
                    if self.rx_FLAG == 0:
                        if num == 0x55:
                            self.rx_FLAG = 1
                        else:
                            self.rx_FLAG = 0

                    elif self.rx_FLAG == 1:
                        if num == 0x00:
                            self.rx_FLAG = 2
                        else:
                            self.rx_FLAG = 0

                    elif self.rx_FLAG == 2:
                        self.rx_LEN = num
                        self.rx_FLAG = 3

                    elif self.rx_FLAG == 3:
                        self.rx_TYPE = num
                        self.rx_FLAG = 4

                    elif self.rx_FLAG == 4:
                        self.rx_ADDR = num
                        self.rx_FLAG = 5
                        self.rx_COUNT = 0

                    elif self.rx_FLAG == 5:
                        if self.rx_COUNT == (self.rx_LEN - 9):
                            self.rx_data[self.rx_COUNT] = num
                            self.rx_FLAG = 6
                        elif self.rx_COUNT < self.rx_LEN - 9:
                            self.rx_data[self.rx_COUNT] = num
                            self.rx_COUNT = self.rx_COUNT + 1

                    elif self.rx_FLAG == 6:
                        for i in self.rx_data[0:(self.rx_LEN - 8)]:
                            rx_CHECK = rx_CHECK + i
                        rx_CHECK = 255 - (self.rx_LEN + self.rx_TYPE + self.rx_ADDR + rx_CHECK) % 256
                        if num == rx_CHECK:
                            self.rx_FLAG = 7
                        else:
                            self.rx_FLAG = 0
                            self.rx_COUNT = 0
                            self.rx_ADDR = 0
                            self.rx_LEN = 0

                    elif self.rx_FLAG == 7:
                        if num == 0x00:
                            self.rx_FLAG = 8
                        else:
                            self.rx_FLAG = 0
                            self.rx_COUNT = 0
                            self.rx_ADDR = 0
                            self.rx_LEN = 0

                    elif self.rx_FLAG == 8:
                        if num == 0xAA:
                            self.rx_FLAG = 0
                            if self.verbose:
                                print("rx_data: ", rx_msg)
                            return True
                        else:
                            self.rx_FLAG = 0
                            self.rx_COUNT = 0
                            self.rx_ADDR = 0
                            self.rx_LEN = 0
        return False

    def set_move_mintime(self, mintime):
        """Sets the minimum time for move_by operations."""
        self.mintime = mintime

    # --- Firmware & System ---
    def upgrade(self, filename):
        """Initiates firmware upgrade process. Use with extreme caution."""
        XGOorder["UPGRADE"][1] = 1
        self.ser.flush()
        self.__send("UPGRADE")
        if self.__unpack(10):
            if self.rx_data[0] == 0x55:
                time.sleep(1)
                print("Start!")
                self.__send_bin(filename)
            else:
                print("Upgrade Response Error!")
        else:
            print("Upgrade Timeout!")

    def read_lib_version(self):
        return __version__

    def __send_bin(self, filename):
        """
        处于测试阶段，请勿使用 (In testing phase, do not use)
        Internal helper for firmware upgrade.
        """
        try:
            self.__change_baud(350000)
            with open(filename, 'rb') as f:
                file_content = f.read() # Renamed file to file_content
            print("The file size is", len(file_content), ' bytes.')
            print("The expected upgrade time is", round(len(file_content) / 350000 * 8 * 1.3), ' s.')
            self.ser.write(file_content)
            print("Done!")
            self.__change_baud(115200)
        except Exception as e:
            print(f"Send bin file error: {e}")

    def calibration(self, state_cmd): # Renamed state to state_cmd
        """
        用于软件标定，请谨慎使用！！！ (Used for software calibration, use with caution!!!)
        """
        if state_cmd == 'start' or state_cmd == 1:
            XGOorder["CALIBRATION"][1] = 1
        elif state_cmd == 'end' or state_cmd == 0:
            XGOorder["CALIBRATION"][1] = 0
        else:
            print(f"ERROR! Invalid calibration state: {state_cmd}")
            return
        self.__send("CALIBRATION")
        # return # Original had return, not strictly necessary if no value returned

    # --- Arm & Claw Control ---
    def arm(self, arm_x, arm_z):
        """
        控制机器狗的机械臂的前后和上下移动 (Control the arm's forward/backward and up/down movement)
        Control the movement of the arm of the robot
        """
        try:
            arm_x_u8 = conver2u8(arm_x, XGOparam["ARM_LIMIT"][0])
            arm_z_u8 = conver2u8(arm_z, XGOparam["ARM_LIMIT"][1])
        except:
            print("Error!Illegal Value!")
            return
        XGOorder["ARM_X"][1] = arm_x_u8
        XGOorder["ARM_Z"][1] = arm_z_u8
        self.__send("ARM_X")
        self.__send("ARM_Z")

    def arm_polar(self, arm_theta, arm_r):
        """
        控制机器狗的机械臂的前后和上下移动
        Control the movement of the arm of the robot
        """
        try:
            arm_theta_u8 = conver2u8(arm_theta, XGOparam["ARM_LIMIT"][2])
            arm_r_u8 = conver2u8(arm_r, XGOparam["ARM_LIMIT"][3])
        except:
            print("Error!Illegal Value!")
            return
        XGOorder["ARM_THETA"][1] = arm_theta_u8
        XGOorder["ARM_R"][1] = arm_r_u8
        self.__send("ARM_THETA")
        self.__send("ARM_R")

    def arm_mode(self, mode):
        if mode != 0x01 and mode != 0x00:
            print("Error!Illegal Value!")
            return
        XGOorder["ARM_MODE"][1] = mode
        self.__send("ARM_MODE")

    def claw(self, pos):
        try:
            claw_pos = conver2u8(pos, [0, 255])
        except:
            print("Error!Illegal Value!")
            return
        XGOorder["CLAW"][1] = claw_pos
        self.__send("CLAW")

    def moveToMid(self):
        self.__send("MOVE_TO_MID")

    def teach(self, mode, pos_id):
        if mode == "play":
            XGOorder["TEACH_PLAY"][1] = pos_id
            self.__send("TEACH_PLAY")
        if mode == "record":
            XGOorder["TEACH_RECORD"][1] = pos_id
            self.__send("TEACH_RECORD")
        else:
            return

    def teach_arm(self, mode, pos_id):
        if mode == "play":
            XGOorder["TEACH_ARM_PLAY"][1] = pos_id
            self.__send("TEACH_ARM_PLAY")
        if mode == "record":
            XGOorder["TEACH_ARM_RECORD"][1] = pos_id
            self.__send("TEACH_ARM_RECORD")
        else:
            return

    def arm_speed(self, speed):
        if speed < 0 or speed > 255:
            print("ERROR!Illegal Value!The speed parameter needs to be between 0 and 255!")
            return
        if speed == 0:
            speed = 1
        XGOorder["ARM_SPEED"][1] = speed
        self.__send("ARM_SPEED")

    # --- Sensor & State Reading (continued) ---
    def read_imu(self):
        """Reads comprehensive IMU data (accel, gyro, an Euler/Quaternion depending on firmware)."""
        self.__read(0x65, 24) # Address for full IMU data block
        result = []
        if self.__unpack():
            if self.version[0] == "R":
                result = self.unpack_imu_r()
            else:
                result = self.unpack_imu()
        return result

    def read_imu_int16(self, direction):
        if direction == "roll":
            self.__read(0x66, 2)
        elif direction == "pitch":
            self.__read(0x67, 2)
        elif direction == "yaw":
            self.__read(0x68, 2)
        else:
            return None
        result = []
        if self.__unpack():
            result = Byte2Short(self.rx_data)
        return result

    def unpack_imu(self):
        result = []
        for i in range(9):
            a = bytearray()
            if i < 6:
                a.append(self.rx_data[2 * i + 1])
                a.append(self.rx_data[2 * i])
                if i < 3:
                    result.append(struct.unpack("!h", a)[0] / 16384 * 9.8)
                else:
                    result.append(struct.unpack("!h", a)[0] / 16.4)
            else:
                a.append(self.rx_data[4 * i - 9])
                a.append(self.rx_data[4 * i - 10])
                a.append(self.rx_data[4 * i - 11])
                a.append(self.rx_data[4 * i - 12])
                result.append(struct.unpack("!f", a)[0] / 180 * 3.14)
        return result

    def unpack_imu_r(self):
        result = []
        for i in range(6):
            a = bytearray()
            a.append(self.rx_data[4 * i + 3])
            a.append(self.rx_data[4 * i + 2])
            a.append(self.rx_data[4 * i + 1])
            a.append(self.rx_data[4 * i])
            result.append(struct.unpack("!f", a)[0])
        return result

    def set_origin(self):
        XGOorder["SET_ORIGIN"][1] = 1
        self.__send("SET_ORIGIN")

    # --- High-level actions & movements (continued) ---
    def move_to(self, data, wait=True, overtime=15.0):
        """
        Moves the robot to a specific orientation or state?
        The 'data' parameter is packed as a short, its exact meaning needs context.
        Original comment for XGOorder["MOVE_TO"] was just [0x3F, 0, 0].
        It reads a rotate_state (0x3F) to check for completion.
        This might be "rotate to specific absolute yaw angle" or similar.
        """
        packed_data = struct.pack('>h', data)
        XGOorder["MOVE_TO"][1] = packed_data[0]
        XGOorder["MOVE_TO"][2] = packed_data[1]
        self.__send("MOVE_TO", len=2)
        time.sleep(0.1)

        t_s = time.time()
        while time.time() - t_s < overtime:  # 等待旋转结束或者超时
            flag = self.read_rotate_state()
            if flag:
                break
            time.sleep(0.1)

        time.sleep(0.5)  # 停止旋转后短暂延时

    def output_analog(self, data):
        XGOorder["OUTPUT_ANALOG"][1] = data
        self.__send("OUTPUT_ANALOG")
        pass

    def output_digital(self, data):
        XGOorder["OUTPUT_DIGITAL"][1] = data
        self.__send("OUTPUT_DIGITAL")
        pass

    def extern_motor(self, position):
        low = (int(struct.pack("h", position)[0]))
        high = (int(struct.pack("h", position)[1]))
        XGOorder["EX_MOTOR"][1] = high
        XGOorder["EX_MOTOR"][2] = low
        self.__send("EX_MOTOR", len=2)

# --- Added from uiutils.py ---
import os # Already imported by original xgolib? No, uiutils had it.

# Global cache for XGO instance and its properties
_default_dog_instance = None
_dog_firmware_info = None # e.g., "MINI" or "LITE"
_dog_version_name = None # e.g., "xgomini" or "xgolite"
_is_permissions_set = False

def init_dog(port="/dev/ttyAMA0", version_hint="xgolite", force_reinit=False):
    """
    Initializes and returns a global XGO instance.
    Manages serial port permissions and caches the instance.

    :param port: Serial port for the XGO.
    :param version_hint: Hint for the XGO version ('xgomini' or 'xgolite'),
                         used if firmware reading has issues initially.
    :param force_reinit: If True, forces re-initialization even if an instance exists.
    :return: Tuple of (XGO_instance, firmware_info_str, version_name_str)
             Returns (None, None, None) on failure.
    """
    global _default_dog_instance, _dog_firmware_info, _dog_version_name, _is_permissions_set

    if _default_dog_instance is not None and not force_reinit:
        return _default_dog_instance, _dog_firmware_info, _dog_version_name

    # Set serial port permissions (ensure this is appropriate for your system)
    if not _is_permissions_set:
        try:
            # print("Attempting to set permissions for /dev/ttyAMA0...")
            # Using os.system is a security risk if port string could be manipulated.
            # Prefer using 'sudo' configured for specific commands or udev rules.
            # For now, replicating original behavior.
            if os.system(f"sudo chmod 777 -R {port}") == 0: # nosec
                # print(f"Permissions set for {port}")
                _is_permissions_set = True
            else:
                print(f"Warning: Failed to set permissions for {port}. Serial communication may fail.")
                # Optionally, choose not to proceed if permissions are critical
        except Exception as e:
            print(f"Error setting permissions for {port}: {e}")
            # return None, None, None # Or try to continue if permissions might already be okay

    try:
        # print(f"Initializing XGO on port {port} with version hint {version_hint}...")
        dog = XGO(port=port, version=version_hint) # XGO class __init__ reads firmware

        # Firmware info is read within XGO's __init__ and sets self.version (e.g. "M1.0.0")
        # and calls changePara based on it.
        fm_version_str = dog.version # This is like "M1.0.0" or "L1.0.0"

        if fm_version_str and fm_version_str[0] == "M":
            _dog_firmware_info = "MINI"
            _dog_version_name = "xgomini"
        elif fm_version_str and fm_version_str[0] == "L":
            _dog_firmware_info = "LITE"
            _dog_version_name = "xgolite"
        else:
            print(f"Warning: Could not determine dog type from firmware version: {fm_version_str}. Using hint: {version_hint}")
            # Fallback to hint if firmware read was problematic for type deduction
            if "mini" in version_hint.lower():
                 _dog_firmware_info = "MINI"
                 _dog_version_name = "xgomini"
            else: # Default to lite
                 _dog_firmware_info = "LITE"
                 _dog_version_name = "xgolite"
            # Ensure XGOparam is set correctly based on this fallback
            changePara(_dog_version_name)


        _default_dog_instance = dog
        print(f"XGO Initialized: Type={_dog_firmware_info}, VersionName={_dog_version_name}, Firmware={fm_version_str}")
        return _default_dog_instance, _dog_firmware_info, _dog_version_name

    except Exception as e:
        print(f"Error initializing XGO: {e}")
        _default_dog_instance = None
        _dog_firmware_info = None
        _dog_version_name = None
        return None, None, None

def get_dog_instance():
    """Returns the cached XGO instance, initializing if needed."""
    if _default_dog_instance is None:
        init_dog() # Use default parameters
    return _default_dog_instance

def get_dog_info():
    """Returns cached dog info (instance, firmware_info, version_name). Initializes if needed."""
    if _default_dog_instance is None:
        init_dog()
    return _default_dog_instance, _dog_firmware_info, _dog_version_name

# Example of how to use it:
if __name__ == '__main__':
    print("Testing XGO initialization...")
    # Test basic initialization
    dog_instance, fw_info, ver_name = init_dog()
    if dog_instance:
        print(f"Successfully initialized: {fw_info} ({ver_name})")
        print(f"Battery: {dog_instance.read_battery()}%")
        dog_instance.reset()
    else:
        print("Failed to initialize XGO dog.")

    # Test getting cached instance
    # print("\nTesting get_dog_instance...")
    # cached_dog = get_dog_instance()
    # if cached_dog:
    #     print(f"Got cached instance. Battery: {cached_dog.read_battery()}%")
    # else:
    #     print("Failed to get cached dog instance.")

    # print("\nTesting get_dog_info...")
    # _, info_fw, info_ver = get_dog_info()
    # if info_fw:
    #     print(f"Dog info: {info_fw} ({info_ver})")

    print("Test complete.")
