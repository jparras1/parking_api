"""Reports data on availability of parking spaces"""
import os
import logging
import logging.config
import functools
import json
import time
from threading import Thread
import connexion
import yaml
from db import make_session
from models import ParkedCar, ReserveSpot
from sqlalchemy import select
from pykafka import KafkaClient
from pykafka.common import OffsetType
from pykafka.exceptions import KafkaException, SocketDisconnectedError

#####################################
#
# Configurations
#
#####################################

MAX_RETRIES = 10
RETRY_DELAY = 5

def use_db_session(func):
    """The decorator takes care of creating and closing sessions"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = make_session()
        try:
            return func(session, *args, **kwargs)
        finally:
            session.close()
    return wrapper

# load the configuration file for logging
with open("log_conf.yml", "r", encoding="utf-8") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger("basicLogger")

# load the configuration for environment variables
with open('app_conf.yml', 'r', encoding="utf-8") as f:
    app_config = yaml.safe_load(f.read())
    event_config = app_config['kafka']


#####################################
#
# Kafka process
#
#####################################

def setup_kafka_thread():
    """Run process_messages in the background"""
    t1_kafka = Thread(target=process_messages)
    t1_kafka.setDaemon(True)
    t1_kafka.start()

def process_messages():
    """ Process event messages """
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Attempt {attempt + 1} to connect to Kafka...")
            hostname = f"{event_config['hostname']}:{event_config['port']}"
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(event_config['topic'])]
            logger.debug("Connected to Kafka successfully!")
            break
        except (KafkaException, SocketDisconnectedError) as error_kafka:
            logger.warning(f"Kafka connection failed: {error_kafka}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached. Exiting.")
                raise  # Let the error propagate if all attempts fail


    # Create a consume on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).
    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                         reset_offset_on_start=False,
                                         auto_offset_reset=OffsetType.LATEST)

    # This is blocking - it will wait for a new message
    for msg in consumer:
        # Skip if there's no message
        if msg is None:
            logger.info("Waiting for messages from Kafka")
            continue

        logger.info("Message received from Kafka")

        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s", msg)

        payload = msg["payload"]

        if msg["type"] == app_config['event_type']['park_event']:
        # Store the event1 (i.e., the payload) to the DB
            report_parked_car(payload)
        elif msg["type"] == app_config['event_type']['reserve_event']:
        # Store the event2 (i.e., the payload) to the DB
            report_spot_reservation(payload)

        # Commit the new message as being read
        consumer.commit_offsets()


#####################################
#
# EVENT STORAGE
#
#####################################
@use_db_session
def report_parked_car(session, body):
    """send park report from kafka to db"""
    pc_report = ParkedCar(body['device_id'],
                   body['spot_id'],
                   body['timestamp'],
                   body['parking_duration'],
                   body['trace_id'])

    session.add(pc_report)
    session.commit()

    # log a message when an event is received
    logger.debug(f"Stored event parked_car with a trace id of {body['trace_id']}")

@use_db_session
def report_spot_reservation(session, body):
    """send reservation report from kafka to db"""
    sr_report = ReserveSpot(body['device_id'],
                     body['spot_id'],
                     body['timestamp'],
                     body['parking_time'],
                     body['trace_id'])

    session.add(sr_report)
    session.commit()

    logger.debug(f"Stored event spot_reservation with a trace id of {body['trace_id']}")


#####################################
#
# EVENT GET METHODS
#
#####################################
@use_db_session
def get_spots_occupied(session, start_timestamp, end_timestamp):
    """Gets the parking spots that are occupied"""
    statement = select(ParkedCar).where(
          (ParkedCar.date_created >= start_timestamp) &
          (ParkedCar.date_created < end_timestamp)
        )

    results = [
        result.to_dict()
        for result in session.execute(statement).scalars().all()
    ]
    logger.info(
        "Found %d spots occupied (start: %s, end: %s)",
        len(results),
        start_timestamp,
        end_timestamp
        )
    return results, 200

@use_db_session
def get_spots_reserved(session, start_timestamp, end_timestamp):
    """Gets the parking spots that are reserved"""
    statement = select(ReserveSpot).where(
          (ReserveSpot.date_created >= start_timestamp) &
          (ReserveSpot.date_created < end_timestamp)
        )

    results = [
        result.to_dict()
        for result in session.execute(statement).scalars().all()
    ]
    logger.info("Found %d spots reserved (start: %s, end: %s)",
                len(results), start_timestamp, end_timestamp)
    return results, 200

@use_db_session
def get_num_events(session):
    """Gets all events"""
    park_statement = select(ParkedCar)

    num_park_rows = [
        result.to_dict()
        for result in session.execute(park_statement).scalars().all()
    ]

    reserve_statement = select(ReserveSpot)

    num_reserve_rows = [
        result.to_dict()
        for result in session.execute(reserve_statement).scalars().all()
    ]

    results = {
        f"{app_config['event_type']['park_event']}" : len(num_park_rows),
        f"{app_config['event_type']['reserve_event']}" : len(num_reserve_rows)
    }

    return results, 200

@use_db_session
def get_park_event_list(session):
    """Gets the parking spots event id and trace id"""
    statement = select(ParkedCar.device_id, ParkedCar.trace_id)

    results = [
        {"device_id": device_id, "trace_id": trace_id}
        for device_id, trace_id in session.execute(statement).all()
    ]

    logger.debug(f"{results}")
    return results, 200

@use_db_session
def get_reserve_event_list(session):
    """Gets the parking spots event id and trace id"""
    statement = select(ReserveSpot.device_id, ReserveSpot.trace_id)

    results = [
        {"device_id": device_id, "trace_id": trace_id}
        for device_id, trace_id in session.execute(statement).all()
    ]
    return results, 200

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml",
            strict_validation=True,
            validate_responses=True)
if __name__ == "__main__":
    # Uncomment ONLY when dubugging
    # drop_tables()
    # create_tables()

    setup_kafka_thread()
    host = os.getenv("HOST")
    app.run(port=8090, host=host)
