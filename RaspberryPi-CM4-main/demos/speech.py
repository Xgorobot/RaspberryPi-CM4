import uiutils
import os
la=uiutils.language()
if la=='cn':
    os.system('python3 ./demos/speech_cn.py')
else:
    os.system('python3 ./demos/speech_en.py')
