"""This module handles consistency checking"""
import os
import json
import logging
import logging.config
import yaml
import connexion
from connexion.middleware import MiddlewarePosition
from pykafka import KafkaClient
from starlette.middleware.cors import CORSMiddleware
from connexion import NoContent


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

def check_json_file(file):
    """checks if json file exists and contents"""
    if os.path.exists(file):
        with open(file, 'r', encoding="utf-8") as fp_file:
            try:
                data = json.load(fp_file)
            except json.JSONDecodeError:
                return False
            # check if the JSON content is empty
            if not data:
                return False
            return True
    return False


#####################################
#
# ENDPOINTS
#
#####################################
def update_anomalies():
    """find event with anomalies"""
    logger.info("Starting consistency checking...")
    
    hostname = f"{app_config['kafka']['hostname']}:{app_config['kafka']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[app_config["kafka"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)

    results = []
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if (data['type'] == app_config['event_type']['reserve_event']) and (data['payload']['spot_id'] > 100):
            event_payload = {
                "device_id" : data['payload']['device_id'],
                "trace_id" : data['payload']['trace_id'],
                "event_type" : app_config['event_type']['reserve_event'],
                "anomaly_type" : "Spot number exceeded",
                "description" : f"Detected: {data['payload']['spot_id']}; too high (threshold 100)"
            }
            results.append(event_payload)
        elif (data['type'] == app_config['event_type']['park_event']) and (data['payload']['parking_duration'] > 200):
            event_payload = {
                "device_id" : data['payload']['device_id'],
                "trace_id" : data['payload']['trace_id'],
                "event_type" : app_config['event_type']['reserve_event'],
                "anomaly_type" : "Parking duration exceeded",
                "description" : f"Detected: {data['payload']['parking_duration']}; too high (threshold 200)"
            }
            results.append(event_payload)

    # write all data to the JSON file
    with open(app_config["datastore"]["filename"], 'w', encoding="utf-8") as post_stats:
        json.dump(results, post_stats, indent=2)

    consumer.stop()
    return {"anomalies_count" : len(results)}, 201

def get_anomalies(event_type=None):
    # check if JSON file doesn't exists
    if not check_json_file(app_config["datastore"]["filename"]):
        logger.error("File does not exist")
        return "Anomaly datastore is missing or corrupted", 404
    
    with open(app_config["datastore"]["filename"], 'r', encoding="utf-8") as fp_file:
        data = json.load(fp_file)
    
    results = []
    if not event_type:
        return data, 204
    elif (event_type == app_config['event_type']['park_event']) or (event_type == app_config['event_type']['reserve_event']):
        for anomaly in data:
            if anomaly['event_type'] == event_type:
                results.append(anomaly)
        return results, 200    
    else:
        return "Invalid event type", 400

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

app.add_api("anomaly.yaml",
            base_path="/anomaly",
            strict_validation=True,
            validate_responses=True)
if __name__ == "__main__":
    host = os.getenv("HOST")
    app.run(port=8130, host=host)
