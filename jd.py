from xgolib import XGO
dog = XGO(port='/dev/ttyAMA0',version="xgolite")
#print(dog.read_battery())
dog.action(3)
 