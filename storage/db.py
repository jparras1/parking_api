import time
import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

# Set up an engine
# engine = create_engine("sqlite:///parking.db")

# load the configuration file for the database
with open('app_conf.yml', 'r') as f:
    db_config = yaml.safe_load(f.read())
    datastore = db_config['datastore']
''' 
1) pip install pymysql - to use SQLAlchemy with MySQL
2) pip install cryptography - to handle secure authentication methods in mysql
3) mysql+pymysql://<username>:<password>@<host>:<port>/<database>

'''

def wait_for_db(retries=10, delay=5):
    """Waits for the database to be ready before proceeding."""
    for attempt in range(retries):
        try:
            # Try to create an engine and test the connection
            engine = create_engine(
                f"mysql+pymysql://{datastore['user']}:"
                f"{datastore['password']}@{datastore['hostname']}:{datastore['port']}/"
                f"{datastore['db']}"
                )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))  # Simple query to check DB readiness
            print("Database is ready!")
            return engine  # Return the working engine
        except OperationalError:
            print(f"Database not ready, retrying in {delay} seconds... ({attempt + 1}/{retries})")
            time.sleep(delay)
    
    print("Database failed to start, exiting.")
    exit(1)

# Wait for the database before proceeding
engine = wait_for_db()


# Factory function to get a session bound to the DB engine
def make_session():
    return sessionmaker(bind=engine)()

# test the connection to database here
# with engine.connect() as connection:
#     result = connection.execute(text("SELECT DATABASE()"))
#     print(result.fetchone())