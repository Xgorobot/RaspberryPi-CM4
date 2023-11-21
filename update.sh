# scirpt needs to be run from home/pi

#!/bin/bash

#! Exit immediately if any command fails
set -e

#! Define the repository URL and target directory
repo_url="https://github.com/Xgorobot/RaspberryPi-CM4.git"
target_dir="/home/pi/RaspberryPi-CM4-main"
rc_local_file="/etc/rc.local"
startup_command="su pi -c 'bash /home/pi/start1.sh'"
startup_file="/home/pi/start1.sh"

#! Check if the startup command is in /etc/rc.local, and add it if it's not
if ! grep -qF "$startup_command" "$rc_local_file"; then
    sudo sed -i "/^exit 0/i $startup_command" "$rc_local_file"
fi

if [ ! -f "$startup_file" ]; then
    echo "$startup_file"
    echo "cd /home/pi/RaspberryPi-CM4-main/" > "$startup_file"
    echo "sudo python3 main.py" >> "$startup_file"
fi

git config --global init.defaultBranch main
git config --global user.email "xgo@update.com"

if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install Git and try again."
    exit 1
fi

#! Check if the target directory exists
if [ ! -d "$target_dir" ]; then
    # If it doesn't exist, clone the repository
    git clone "$repo_url" "$target_dir"
    sudo chown -R pi:pi RaspberryPi-CM4-main/
    elif [ ! -d "$target_dir/.git" ]; then
    # if the directory exist but not a git clone
    cd "$target_dir"
    echo "init"
    git init
    git checkout -b temp-branch
    git add .
    git commit -m 'importing local files'
    git remote add main https://github.com/Xgorobot/RaspberryPi-CM4.git
    git fetch main --depth 1
    git checkout main
    git branch -D temp-branch
else
    # If it does exist, go into the directory, reset it, and then pull to update
    cd "$target_dir"
    git reset --hard main
    git clean -f -d # Remove untracked files and directories
    git config pull.rebase false
    git pull
fi

sudo pip install --upgrade xgo-pythonlib
