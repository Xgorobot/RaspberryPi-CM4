import time
from xgolib import XGO
from xgoedu import XGOEDU
xgo = XGO(port='/dev/ttyAMA0', version="xgolite")
XGO_edu = XGOEDU()

# 前进三秒钟
xgo.move_x(15)
time.sleep(3)

# 坐下
xgo.action(4)
time.sleep(180)

# 过三分钟之后再站起来
time.sleep(180)
xgo.reset()