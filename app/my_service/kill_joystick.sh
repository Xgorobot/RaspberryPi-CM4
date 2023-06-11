#! /bin/bash

len1=` ps -ef|grep joystick_dogzilla.py |grep -v grep| wc -l`
echo "Number of processes="$len1

if [ $len1 -eq 0 ] 
then
    echo "joystick_dogzilla.py is not running "
else
    # ps -ef| grep joystick_dogzilla.py| grep -v grep| awk '{print $2}'| xargs kill -9  
    pid_number=` ps -ef| grep joystick_dogzilla.py| grep -v grep| awk '{print $2}'`
    kill -9 $pid_number
    echo "joystick_dogzilla.py killed, PID:"
    echo $pid_number
fi
sleep .1
