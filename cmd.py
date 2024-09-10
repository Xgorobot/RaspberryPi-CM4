import time
from xgolib import XGO
xgo=XGO(port='/dev/ttyAMA0',version="xgolite")
# 让机器狗坐下5秒钟
xgo.action(6)
time.sleep(5)
# 让机器狗停止坐下的动作
xgo.action(0)
# 让机器狗向前走10秒
xgo.move_x(15)
time.sleep(10)
# 让机器狗停止行走
xgo.move_x(0)
# 复位机器狗
xgo.reset()