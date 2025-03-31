import uiutils
import os
la=uiutils.language()
if la=='cn':
    os.system('python3 ./demos/chatgpt_cn.py')
else:
    os.system('python3 ./demos/chatgpt_en.py')