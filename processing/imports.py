import os
import json
import httpx
from pathlib import Path
import yaml
import logging
import logging.config
import connexion
from connexion import NoContent
from apscheduler.schedulers.background import BackgroundScheduler
import time
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware