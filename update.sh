#!/bin/bash

#! Exit immediately if any command fails
set -e

# Function to display a warning and ask for user confirmation
confirm_continue() {
    while true; do
        echo "WARNING! Files will be overwritten with files from GitHub."
        read -p "Do you want to continue? (Y/N): " yn
        case $yn in
            [Yy]* ) echo "Continuing..."; break;;  # Continue the script if user presses Y or y
            [Nn]* ) echo "Exiting script."; exit 1;;  # Exit the script if user presses N or n
            * ) echo "Please answer Y or N.";;  # Prompt again if input is not Y or N
        esac
    done
}

#! Define the repository URL and target directory
repo_url="https://github.com/Xgorobot/RaspberryPi-CM4.git"
target_dir="/home/pi"  # The target directory is /home/pi
repo_dir="$target_dir"  # Directory where the repo is cloned (now directly in /home/pi)
rc_local_file="/etc/rc.local"
startup_command="su pi -c 'bash /home/pi/start1.sh'"
startup_file="/home/pi/start1.sh"

# Define the new files and directories to check in the /home/pi directory
required_files=("start1.sh" "README.md")
required_dirs=("xgoMusic" "xgoPictures" "xgoVideo")

# Call the confirmation prompt before starting
confirm_continue

# Function to ensure directories are tracked (add .gitkeep if empty)
ensure_dirs_tracked() {
    for dir in "${required_dirs[@]}"; do
        # Only create .gitkeep if directory is empty
        if [ -d "$target_dir/$dir" ] && [ ! "$(ls -A "$target_dir/$dir")" ]; then
            echo "Adding .gitkeep to track empty directory: $dir"
            touch "$target_dir/$dir/.gitkeep"  # Add a .gitkeep file to track empty directories
        fi
    done
}

# Step 1: Ensure directories are tracked (by adding .gitkeep if the directory is empty)
ensure_dirs_tracked

# Step 2: Check if the startup command is in /etc/rc.local, and add it if it's not
if ! grep -qF "$startup_command" "$rc_local_file"; then
    sudo sed -i "/^exit 0/i $startup_command" "$rc_local_file"
fi

# Step 3: Check and create the startup file if it doesn't exist
if [ ! -f "$startup_file" ]; then
    echo "$startup_file"
    echo "cd /home/pi/" > "$startup_file"
    echo "sudo python3 main.py" >> "$startup_file"
fi

# Git configuration
echo "Configuring Git..."
git config --global init.defaultBranch main
git config --global user.email "xgo@update.com"
git config --global user.name "No One"

if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install Git and try again."
    exit 1
fi

# Step 4: Check if the repository exists and is initialized as a git repository
if [ ! -d "$repo_dir/.git" ]; then
    echo "Git repository not found in $repo_dir. Initializing Git repository."
    git -C "$repo_dir" init  # Initialize the Git repo if it doesn't exist
    git -C "$repo_dir" remote add origin "$repo_url"  # Add the remote repository
else
    echo "Git repository already exists in $repo_dir."
fi

# Step 5: Add or update the required files in the repo directory (Pi directory)
for file in "${required_files[@]}"; do
    if [ -f "$target_dir/$file" ] && ! git -C "$repo_dir" ls-files --error-unmatch "$file" &>/dev/null; then
        echo "Adding new or modified file to Git: $file"
        git -C "$repo_dir" add "$target_dir/$file"
    else
        echo "File $file already exists and is already tracked by Git, skipping add."
    fi
done

# Add directories (only if they exist, are not empty, and are not already tracked)
for dir in "${required_dirs[@]}"; do
    if [ -d "$target_dir/$dir" ] && [ "$(ls -A "$target_dir/$dir")" ] && ! git -C "$repo_dir" ls-files --error-unmatch "$dir" &>/dev/null; then
        echo "Adding new or modified directory to Git: $dir"
        git -C "$repo_dir" add "$target_dir/$dir"
    fi
done

# Commit the changes (if any)
if git -C "$repo_dir" diff --cached --quiet; then
    echo "No changes to commit."
else
    git -C "$repo_dir" commit -m "Adding new or modified files and directories"
fi

# Step 6: Ensure that the local repository is reset to the latest from the remote repository (force pull)
echo "Resetting and pulling from the remote repository..."
git -C "$repo_dir" fetch origin
git -C "$repo_dir" reset --hard origin/main  # Reset the local repository to match the remote (this will overwrite local changes)

# Step 7: Install the Python library
sudo pip install --upgrade xgo-pythonlib

echo "Repository pulled successfully, and new files have been added!"
