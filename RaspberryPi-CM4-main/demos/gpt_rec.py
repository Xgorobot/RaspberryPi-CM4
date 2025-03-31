import uiutils
import os
la=uiutils.language()
if la=='cn':
    os.system('python3 ./demos/gpt_rec_cn.py')
else:
    os.system('python3 ./demos/gpt_rec_en.py')