#!/bin/bash

echo "Stopping all services..."

pkill -f a2a_server.py
pkill -f main.py
pkill -f http.server

echo "All services stopped."
