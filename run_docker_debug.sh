#!/bin/bash

# This script runs the debug tool inside the Docker container

echo "=== Running Notification System Debug Tool ==="
echo "This tool will help identify issues with the notification system in Docker"

# Get container ID (adjust this if your Docker container has a specific name)
CONTAINER_ID=$(docker ps | grep "takecare" | awk '{print $1}')

if [ -z "$CONTAINER_ID" ]; then
  echo "❌ No running TakeCare Docker container found!"
  echo "Please make sure your Docker container is running."
  exit 1
fi

echo "Found container: $CONTAINER_ID"

# Copy the debug script to the container
echo "Copying debug script to container..."
docker cp /Users/macbook/Projects/university/se2/TakeCare/docker_debug_notifications.py $CONTAINER_ID:/app/

# Set execute permissions
echo "Setting execute permissions..."
docker exec $CONTAINER_ID chmod +x /app/docker_debug_notifications.py

# Run the debug script
echo "Running debug script..."
docker exec $CONTAINER_ID python /app/docker_debug_notifications.py

# Check result
if [ $? -eq 0 ]; then
  echo "✅ Debug completed successfully. Notification system is working!"
else
  echo "❌ Debug found issues with the notification system."
  echo ""
  echo "Recommendations:"
  echo "1. Check that signals.py is being properly loaded in apps.py"
  echo "2. Verify model field names match between signals and models"
  echo "3. Check Docker logs for any Django errors"
  echo "4. Try restarting the Docker container"
fi
