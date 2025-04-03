"""This module handles consistency checking"""
import os
import json
import httpx
import logging
import logging.config
import yaml
import time
import connexion
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

CHECK_FLAG = False

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
    eventstores = app_config['eventstores']

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
# PROCESS DATA
#
#####################################

def format_count_object(event1, event2):
    formatted = {
        f"{app_config['event_type']['park_event']}" : event1,
        f"{app_config['event_type']['reserve_event']}" : event2
    }
    return formatted

def compare_data(event, db_source, queue_source):
    """Compares two lists of dictionaries and returns the ones missing in the other"""
    
    # Convert lists of dictionaries to sets of tuples to perform set operations
    set_db_source = {tuple(data.items()) for data in db_source}
    set_queue_source = {tuple(data.items()) for data in queue_source}
    
    # Find the dictionaries that are in db_source but not in queue_source
    missing_in_queue = [
        {**dict(tuple_item), 'type': event} for tuple_item in set_db_source - set_queue_source
        ]
    
    # Find the dictionaries that are in set_queue_source but not in set_db_source
    missing_in_db = [
        {**dict(tuple_item), 'type': event} for tuple_item in set_queue_source - set_db_source
        ]
    
    return missing_in_db, missing_in_queue


#####################################
#
# ENDPOINTS
#
#####################################
def run_consistency_checks():
    """Runs the consistency checks and updates the JSON datastore"""
    logger.info("Starting consistency checking...")
    start = int(time.time() * 1000)

    results = {"last_updated" : "",
               "counts" : {},
               "missing_in_db" : [],
               "missing_in_queue" : []
               }
    
    # connect to processing
    processing_stats = httpx.get(eventstores['processing_stats']['stats_url'])
    # get the counts for each event using the new endpoint
    ps_pc_count = processing_stats.json().get("num_pc_reports", 0)
    ps_sr_count = processing_stats.json().get("num_sr_reports", 0)
    # store to results
    results['counts']['processing'] = format_count_object(ps_pc_count, ps_sr_count)

    # connect to analyzer (analyzer gets its stats from kafka queue)
    analyzer_stats = httpx.get(eventstores['analyzer_stats']['stats_url'])
    # get the counts
    as_pc_count = analyzer_stats.json().get(f"num_{app_config['event_type']['park_event']}", 0)
    as_sr_count = analyzer_stats.json().get(f"num_{app_config['event_type']['reserve_event']}", 0)
    # store to results
    results['counts']['queue'] = format_count_object(as_pc_count, as_sr_count)
    # get the ids
    analyzer_pc_id = httpx.get(eventstores['analyzer_stats']['park_ids_url'])
    analyzer_sr_id = httpx.get(eventstores['analyzer_stats']['reserve_ids_url'])

    # connect to storage and get the count
    storage_stats = httpx.get(eventstores['storage_stats']['stats_url'])
    # store to results
    results['counts']['db'] = storage_stats.json()
    # get the ids
    storage_pc_id = httpx.get(eventstores['storage_stats']['park_ids_url'])
    storage_sr_id = httpx.get(eventstores['storage_stats']['reserve_ids_url'])

    # compare the parking events between queue and storage
    pc_events_missing_in_db, pc_events_missing_in_queue = compare_data(
                                        app_config['event_type']['park_event'],
                                        storage_pc_id.json(),
                                        analyzer_pc_id.json()
                                        )
    # store the missing data to results
    results['missing_in_db'] = pc_events_missing_in_db
    results['missing_in_queue'] = pc_events_missing_in_queue

    # compare the parking events between queue and storage
    sr_events_missing_in_db, sr_events_missing_in_queue = compare_data(
                                        app_config['event_type']['reserve_event'],
                                        storage_sr_id.json(),
                                        analyzer_sr_id.json()
                                        )
    # append the missing data to results
    results['missing_in_db'] += sr_events_missing_in_db
    results['missing_in_queue'] += sr_events_missing_in_queue

    # get the current datetime and change it to proper format
    results['last_updated'] = int(time.time())

    # write all data to the JSON file
    with open(app_config["datastore"]["filename"], 'w', encoding="utf-8") as post_stats:
        json.dump(results, post_stats, indent=2)

    global CHECK_FLAG
    CHECK_FLAG = True

    end = int(time.time() * 1000)
    processing_time_ms = end - start
    logger.info(
        f"Consistency checking completed | "
        f"processing_time_ms={processing_time_ms} | "
        f"missing_in_db={len(results['missing_in_db'])} | "
        f"missing_in_queue={len(results['missing_in_queue'])}"
    )

    return {"processing_time_ms" : processing_time_ms}, 200

def get_checks():
    if not CHECK_FLAG or not check_json_file(app_config["datastore"]["filename"]):
        return {"message": "No checks have been run yet!"}, 404
    
    with open(app_config["datastore"]["filename"], 'r', encoding="utf-8") as fp_file:
        data = json.load(fp_file)
    
    return data, 200

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
            base_path="/consistency",
            strict_validation=True,
            validate_responses=True)
if __name__ == "__main__":
    host = os.getenv("HOST")
    app.run(port=8120, host=host)
