#! /bin/bash

len1=` ps -ef|grep oled_dogzilla.py |grep -v grep| wc -l`
echo "Number of processes="$len1

if [ $len1 -eq 0 ] 
then
    echo "oled_dogzilla.py is not running "
else
    # ps -ef| grep oled_dogzilla.py| grep -v grep| awk '{print $2}'| xargs kill -9  
    pid_number=` ps -ef| grep oled_dogzilla.py| grep -v grep| awk '{print $2}'`
    kill -9 $pid_number
    echo "oled_dogzilla.py killed, PID:"
    echo $pid_number
    
    # Clear OLED
    python3 /home/pi/DOGZILLA/app_dogzilla/oled_dogzilla.py clear
fi
sleep .01
