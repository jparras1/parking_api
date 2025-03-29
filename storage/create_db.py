"""creates database"""
import sys
from models import Base
from db import engine

def create_tables():
    """create db tables"""
    Base.metadata.create_all(engine)

def drop_tables():
    """delete db tables"""
    Base.metadata.drop_all(engine)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_tables()
    create_tables()


# In the terminal, you can now use:
# python create_db.py => creates all tables
# python create_db.py drop => drops all tables
