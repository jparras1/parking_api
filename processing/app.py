from imports import *


# load the configuration file for logging
with open("log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger("basicLogger")

# load the configuration file to replace hardcoded URLs
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# checks if json file exists and contents
def check_json_file(file):
    if os.path.exists(file):
        with open(file, 'r') as fp:
            try:
                data = json.load(fp)
            except json.JSONDecodeError:
                return False
            else:
                # check if the JSON content is empty
                if not data:
                    return False
                return True
    return False

# calculate minimum parking duration value
def min_duration(prev_min, current_entry):
    values = [v for v in (prev_min, current_entry) if v != 0]  # Exclude 0 values
    return min(values) if values else 0  # Return min if values exist, else 0

# calculate maximum parking duration value
def max_duration(prev_max, current_entry):
    values = [v for v in (prev_max, current_entry) if v != 0]
    return max(values) if values else 0

def populate_stats():
    logger.info("Processing started")

    # get stats
    data, status = get_stats()

    # if the get_stats function can't retrieve the info in json file
    if status != 200:
        data = {"num_pc_reports" : 0,
                "min_parking_duration" : 0,
                "max_parking_duration" : 0,
                "num_sr_reports" : 0,
                "last_updated" : 1735718400} # 01-01-2025

    # latest timestamp on the json file
    start = data["last_updated"]

    # get the current datetime and change it to proper format
    end = int(time.time())

    # Query the timestamps to the storage service using the GET methods
    params = {
        "start_timestamp" : start,
        "end_timestamp" : end
    }
    parking_res = httpx.get(app_config['eventstores']['park']['url'], params=params)
    if parking_res.status_code == 200:
        logger.info(f"{len(parking_res.json())} reports found for occupied parking spots")
    else:
        logger.error("Failed to retrieve parking events from database")

    reserve_res = httpx.get(app_config['eventstores']['reserve']['url'], params=params)
    if reserve_res.status_code == 200:
        logger.info(f"{len(reserve_res.json())} reports found for spot reservation")
    else:
        logger.error("Failed to retrieve reservation events from database")

    # calculate minimum value
    for entry in parking_res.json():
        data["min_parking_duration"] = min_duration(
            data["min_parking_duration"], entry["parking_duration"]
            )
        data["max_parking_duration"] = max_duration(
            data["max_parking_duration"], entry["parking_duration"]
            )

    # add the number of entries
    data["num_pc_reports"] += len(parking_res.json())
    data["num_sr_reports"] += len(reserve_res.json())

    # update the latest processing timestamp
    data["last_updated"] = end
    logger.debug(f"{app_config['datastore']['filename']} updated with new values")

    # write all data to the JSON file
    with open(app_config["datastore"]["filename"], 'w') as post_stats:
        json.dump(data, post_stats, indent=2)

    logger.info("Processing completed")


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
                  'interval',
                  seconds=app_config['scheduler']['interval'])
                
    sched.start()


# EVENTS
def get_stats():
    logger.info("Request to retrieve stats received")

    # check if JSON file doesn't exists
    if not check_json_file(app_config["datastore"]["filename"]):
        logger.error("File does not exist")
        return "Statistics do not exist", 404
    
    with open(app_config["datastore"]["filename"], 'r') as fp:
        data = json.load(fp)
    logger.debug(f"Contents of the stats file: {data}")

    logger.info("Request completed")
    return data, 200


app = connexion.FlaskApp(__name__, specification_dir='')

app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_api("openapi.yaml",
            strict_validation=True,
            validate_responses=True)
if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")
