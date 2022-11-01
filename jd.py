from xgolib import XGO
import time
XGO_lite = XGO(port='/dev/ttyAMA0',version="xgolite")
#XGO_lite.unload_allmotor()
#XGO_lite.load_allmotor()

#XGO_lite.claw(255)
#time.sleep(1)
print(XGO_lite.read_motor())
time.sleep(1)
#print(XGO_lite.action(1))


  
 