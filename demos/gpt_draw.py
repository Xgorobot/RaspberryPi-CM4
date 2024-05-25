import uiutils
import os
la=uiutils.language()
if la=='cn':
    os.system('python3 ./demos/gpt_draw_cn.py')
else:
    os.system('python3 ./demos/gpt_draw_en.py')