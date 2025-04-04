"""Reports data on availability of parking spaces"""
import os
import uuid
import logging
import logging.config
import datetime
import json
import time
import yaml
import connexion
from pykafka import KafkaClient
from pykafka.exceptions import KafkaException, SocketDisconnectedError
from connexion import NoContent


#####################################
#
# Configurations
#
#####################################

MAX_RETRIES = 10
RETRY_DELAY = 5

# load the configuration file to replace hardcoded URLs
with open('app_conf.yml', 'r', encoding="utf-8") as f:
    app_config = yaml.safe_load(f.read())
    event_config = app_config['kafka']

# load the configuration file for logging
with open("log_conf.yml", "r", encoding="utf-8") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger("basicLogger")


#####################################
#
# Kafka process
#
#####################################
def connect_to_kafka(kafka_config):
    """this function connects service to kafka"""
    for attempt in range(MAX_RETRIES):
        try:
            logger.info("Attempt %d to connect to Kafka...", attempt + 1)
            kafka_client = KafkaClient(hosts=f"{kafka_config['hostname']}:{kafka_config['port']}")
            kafka_topic = kafka_client.topics[str.encode(f"{kafka_config['topic']}")]
            kafka_producer = kafka_topic.get_sync_producer()
            logger.debug("Connected to Kafka successfully!")
            return kafka_client, kafka_topic, kafka_producer  # Return objects if successful
        except (KafkaException, SocketDisconnectedError) as error_kafka:
            logger.warning("Kafka connection failed: %s", error_kafka)
            if attempt < MAX_RETRIES - 1:
                logger.info("Retrying in %s seconds...", RETRY_DELAY)
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached. Exiting.")
                raise

# Usage:
client, topic, producer = connect_to_kafka(event_config)

def send_to_kafka(event_type, payload):
    """send to kafka service"""
    # add a trace_id to the JSON payload
    payload["trace_id"] = str(uuid.uuid4())

    # log a message when an event is received
    logger.info(f"Received event {event_type} with a trace id of {payload['trace_id']}")

    msg = { "type": event_type,
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "payload": payload
           }

    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    # log the response of the storage service
    logger.info(
        f"Response for event {event_type} (id: {payload['trace_id']}) has status 201"
        )

    # return HTTP status code from storage
    return NoContent, 201


#####################################
#
# EVENTS
#
#####################################
def report_parked_car(body):
    """Adds a new parked car report to the system"""
    event_type = app_config['event_type']['park_event']
    return send_to_kafka(event_type, body)

def report_spot_reservation(body):
    """Adds a new parking spot reservation report to the system"""
    event_type = app_config['event_type']['reserve_event']
    return send_to_kafka(event_type, body)


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml",
            base_path="/receiver",
            strict_validation=True,
            validate_responses=True)
if __name__ == "__main__":
    host = os.getenv("HOST")
    app.run(port=8080, host=host)
