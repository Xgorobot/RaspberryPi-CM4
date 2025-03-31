#! /bin/bash

###############################################################################
# ubuntu 20.04 
# add Additional startup programs
# start_DOGZILLA_app
# bash /home/pi/DOGZILLA/app_dogzilla/start_app.sh
# start app program
# 
###############################################################################

###############################################################################
# Raspbian
# add .config/autostart/start_app.desktop
# [Desktop Entry]
# Type=Application
# Exec=sh /home/pi/DOGZILLA/app_dogzilla/start_app.sh
###############################################################################



sleep 8

# ubuntu 20.04
gnome-terminal -- bash -c "python3 /home/pi/DOGZILLA/app_dogzilla/app_dogzilla.py;exec bash"


# Raspbian
# lxterminal -e bash -c 'python3 /home/pi/DOGZILLA/app_dogzilla/app_dogzilla.py;$SHELL'

wait
exit 0
