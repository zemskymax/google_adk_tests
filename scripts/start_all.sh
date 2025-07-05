#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p ../logs

# Start the personal_helper
echo "Starting personal_helper..."
python3 ../personal_helper/a2a_server.py > ../logs/personal_helper.log 2>&1 &

# Start the chinese restaurant bot
echo "Starting chinese restaurant bot..."
python3 ../chinese/a2a_server.py > ../logs/chinese.log 2>&1 &

# Start the pizza restaurant bot
echo "Starting pizza restaurant bot..."
python3 ../pizza_house_worker/a2a_server.py > ../logs/pizza_house_worker.log 2>&1 &

# Start the a2a_monitor backend
echo "Starting a2a_monitor backend..."
python3 ../a2a_monitor/main.py > ../logs/a2a_monitor.log 2>&1 &

# Start the a2a_monitor frontend
echo "Starting a2a_monitor frontend..."
python3 -m http.server 8088 --directory ../a2a_monitor/frontend > ../logs/monitor.log 2>&1 &

echo "All services started."
echo "You can view the A2A monitor at http://localhost:8088"
