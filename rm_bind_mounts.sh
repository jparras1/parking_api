#!/bin/bash

# Confirm with the user before proceeding
echo "WARNING: This script will remove the following:"
echo "- All files in the 'database' and 'kafka' directories"
echo "- Contents of 'processing.json'"
echo "- All logs in the 'logs' directory"
echo "- Unmount Docker desktop bind mounts"
echo "Are you sure you want to continue? (y/n)"
read -r CONFIRMATION

if [[ "$CONFIRMATION" != "y" && "$CONFIRMATION" != "Y" ]]; then
    echo "Operation canceled. No files were removed."
    exit 0
fi

CURRENT_DIRECTORY=$(pwd)
LOGS="$CURRENT_DIRECTORY/logs"

# Remove database files
if sudo find "$CURRENT_DIRECTORY/data/database" -mindepth 1 -delete; then
    echo "Database files removed successfully."
else
    echo "Failed to remove database files."
fi

# Remove Kafka files
if sudo find "$CURRENT_DIRECTORY/data/kafka" -mindepth 1 -delete; then
    echo "Kafka files removed successfully."
else
    echo "Failed to remove Kafka files."
fi

# Remove the contents of the processing JSON file
if > "$CURRENT_DIRECTORY/data/processing/processing.json"; then
    echo "Contents of processing.json cleared successfully."
else
    echo "Failed to clear contents of processing.json."
fi

# Remove all the contents of the service logs
if > "$LOGS/analyzer.log" && > "$LOGS/processing.log" && > "$LOGS/receiver.log" && > "$LOGS/storage.log"; then
    echo "Service logs cleared successfully."
else
    echo "Failed to clear service logs."
fi
