#!/bin/bash
# Sync files first (assuming run from local machine, but this script is for the Pi info-only or remote execution)
echo "Restarting dog_app service..."
sudo systemctl restart dog_app.service
echo "Service restarted. Logs:"
tail -n 10 /home/jinliang/dog_app/startup.log
