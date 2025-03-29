"""creates models"""
import time
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String
# from sqlalchemy.sql.functions import now

class Base(DeclarativeBase):
    """base"""
    pass

class ParkedCar(Base):
    """ Parked Car """

    __tablename__ = "parked_car"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(250), nullable=False)
    spot_id = Column(Integer, nullable=False)
    timestamp = Column(String(100), nullable=False)
    parking_duration = Column(Integer, nullable=False)
    trace_id = Column(String(250), nullable=False)
    date_created = Column(Integer, nullable=False)

    def __init__(self, device_id, spot_id, timestamp, parking_duration, trace_id):
        """ Initialization """
        self.device_id = device_id
        self.spot_id = spot_id
        self.timestamp = timestamp
        self.parking_duration = parking_duration
        self.trace_id = trace_id
        self.date_created = int(time.time())

    def to_dict(self):
        """ Dictionary Representation of a parked car report """
        my_dict = {}
        my_dict['id'] = self.id
        my_dict['device_id'] = self.device_id
        my_dict['spot_id'] = self.spot_id
        my_dict['timestamp'] = self.timestamp
        my_dict['parking_duration'] = self.parking_duration
        my_dict['trace_id'] = self.trace_id
        my_dict['date_created'] = self.date_created

        return my_dict

class ReserveSpot(Base):
    """ Reserve Spot """

    __tablename__ = "reserve_spot"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(250), nullable=False)
    spot_id = Column(Integer, nullable=False)
    timestamp = Column(String(100), nullable=False)
    parking_time = Column(String(100), nullable=False)
    trace_id = Column(String(250), nullable=False)
    date_created = Column(Integer, nullable=False)

    def __init__(self, device_id, spot_id, timestamp, parking_time, trace_id):
        """ Initialization """
        self.device_id = device_id
        self.spot_id = spot_id
        self.timestamp = timestamp
        self.parking_time = parking_time
        self.trace_id = trace_id
        # self.date_created = dt.now(ZoneInfo("America/Vancouver"))
        self.date_created = int(time.time())

    def to_dict(self):
        """ Dictionary Representation of a Spot Reservation Report """
        my_dict = {}
        my_dict['id'] = self.id
        my_dict['device_id'] = self.device_id
        my_dict['spot_id'] = self.spot_id
        my_dict['timestamp'] = self.timestamp
        my_dict['parking_time'] = self.parking_time
        my_dict['trace_id'] = self.trace_id
        my_dict['date_created'] = self.date_created

        return my_dict
