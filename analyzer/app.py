"""This module handles audit info of the api"""
import os
import json
import logging
import logging.config
import yaml
import connexion
from connexion.middleware import MiddlewarePosition
from pykafka import KafkaClient
from starlette.middleware.cors import CORSMiddleware

#####################################
#
# Configurations
#
#####################################
# load the configuration file for logging
with open("log_conf.yml", "r", encoding="utf-8") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger("basicLogger")

# load the configuration file to replace hardcoded URLs
with open('app_conf.yml', 'r', encoding="utf-8") as f:
    app_config = yaml.safe_load(f.read())

#####################################
#
# KAFKA
#
#####################################
def retrieve_message(index, event):
    """this function retrieves event from kafka"""
    hostname = f"{app_config['kafka']['hostname']}:{app_config['kafka']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[app_config["kafka"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)

    counter = 0
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        # Look for the index requested and return the payload with 200 status code
        if data['type'] == event:
            if counter == index:
                # return the payload if the event_message at the index is found
                return data['payload']
            counter += 1

    consumer.stop()
    # if the event_message at index is not found, return False
    return False


#####################################
#
# ENDPOINTS
#
#####################################
def get_spots_occupied(index):
    """this function Gets occupied parking spots from history"""
    logger.info(
        f"Request for {app_config['event_type']['park_event']} at index #{index} received"
    )
    result = retrieve_message(index, app_config['event_type']['park_event'])

    if result:
        return result, 200
    return { "message": f"No message at index {index}!"}, 404

def get_spots_reserved(index):
    """this function Gets reserved parking spots from history"""
    logger.info(
        f"Request for {app_config['event_type']['reserve_event']} at index #{index} received"
    )
    result = retrieve_message(index, app_config['event_type']['reserve_event'])

    if result:
        return result, 200
    return { "message": f"No message at index {index}!"}, 404

def get_stats():
    """Gets the count of each event currently in the queue"""
    hostname = f"{app_config['kafka']['hostname']}:{app_config['kafka']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[app_config["kafka"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)

    stats = {}
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        event = f"num_{data['type']}"
        if event in stats:
            stats[event] += 1
        else:
            stats[event] = 1

    consumer.stop()
    return stats, 200

def get_park_event_list():
    """Gets the parking spots event id and trace id"""
    hostname = f"{app_config['kafka']['hostname']}:{app_config['kafka']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[app_config["kafka"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)

    results = []
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if data['type'] == app_config['event_type']['park_event']:
            event_payload = {
                "device_id" : data['payload']['device_id'],
                "trace_id" : data['payload']['trace_id']
            }
            results.append(event_payload)

    consumer.stop()
    return results, 200

def get_reserve_event_list():
    """Gets the reserve spots event id and trace id"""
    hostname = f"{app_config['kafka']['hostname']}:{app_config['kafka']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[app_config["kafka"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)

    results = []
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if data['type'] == app_config['event_type']['reserve_event']:
            event_payload = {
                "device_id" : data['payload']['device_id'],
                "trace_id" : data['payload']['trace_id']
            }
            results.append(event_payload)

    consumer.stop()
    return results, 200


app = connexion.FlaskApp(__name__, specification_dir='')

if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    # Set up '*' CORS headers when `CORS_ALLOW_ALL` is 'yes
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_api("openapi.yaml",
            base_path="/analyzer",
            strict_validation=True,
            validate_responses=True)
if __name__ == "__main__":
    host = os.getenv("HOST")
    app.run(port=8110, host=host)
