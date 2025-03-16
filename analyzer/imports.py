import json
import httpx
import yaml
import logging
import logging.config
import connexion
from connexion import NoContent
import time
from pykafka import KafkaClient
from pykafka.common import OffsetType