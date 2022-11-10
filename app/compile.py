#!/usr/bin/env python3
# coding=utf-8
"""
# file=input name cfile=output name
# python3 compile.py xxx
"""

import py_compile
import os
import sys
import time

File_Name = ''
if len(sys.argv) > 1:
    File_Name = str(sys.argv[1]) + '.py'
else:
    print("Please Input File Name")
    print("-----Compile Failed!-----")
    sys.exit(0)
print("File Name:", File_Name)

# PATH_APP_DIR = "/home/pi/DOGZILLA/app_dogzilla/"
PATH_APP_DIR = ""
PATH_FILE = PATH_APP_DIR + File_Name
print("File PATH:", PATH_FILE)

TARGET_FILE = PATH_FILE + "c"
print("Target File:", TARGET_FILE)

if os.path.exists(PATH_FILE):
    print("Succeed to Read File")
else:
    print("File Name Error or File Does Not Exist")
    print("-----Compile Failed!-----")
    sys.exit(0)


if os.path.exists(TARGET_FILE):
    os.system('rm ' + TARGET_FILE)
    print(TARGET_FILE, "Cleared")
    time.sleep(.1)

print("Start Compile:", PATH_FILE)
py_compile.compile(file=PATH_FILE, cfile=TARGET_FILE, optimize=-1)
print("Succeed to Generate:", TARGET_FILE)
os.system("chmod +x " + TARGET_FILE)
print("-----Compiled OK!-----")
