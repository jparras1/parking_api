#!/bin/bash

KAFKA_CONTAINER="kafka"
ZOOKEEPER_CONTAINER="zookeeper"
KAFKA_DATA_DIR="$(pwd)/data/kafka"

# Stop Kafka and ZooKeeper services
echo "Stopping Kafka and ZooKeeper..."
docker compose stop kafka
docker compose stop zookeeper

# find the meta.properties file
META_PROPERTIES_FILE=$(find "$KAFKA_DATA_DIR" -type f -name "meta.properties" 2>/dev/null)

# Remove the meta.properties file from Kafka's data directory
if [ -f "$META_PROPERTIES_FILE" ]; then
    echo "Removing meta.properties file from Kafka..."
    sudo rm -f "$META_PROPERTIES_FILE"
else
    echo "meta.properties file not found. Nothing to remove."
fi

# Restart ZooKeeper and Kafka services
echo "Starting ZooKeeper and Kafka services..."
docker compose start zookeeper
docker compose start kafka

# Verify that the containers are running
docker compose ps