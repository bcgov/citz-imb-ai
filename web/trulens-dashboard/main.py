import psycopg2
import os
from trulens_eval import Tru
from dotenv import load_dotenv
import logging
import time


# Load environment variables from .env file
load_dotenv("/vault/secrets/zuba-secret-dev") # need to find soltion to load test and prod files in respective envs.

TRULENS_USER = os.getenv('TRULENS_USER')
TRULENS_PASSWORD = os.getenv('TRULENS_PASSWORD')
TRULENS_DB = os.getenv('TRULENS_DB')
TRULENS_PORT = os.getenv('TRULENS_PORT')
TRULENS_HOST = os.getenv('TRULENS_HOST')

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def connect_to_database(connection_string, retries=5, delay=5):
    for attempt in range(retries):
        try:
            tru = Tru(connection_string)
            logging.debug("Successfully connected to the database.")
            return tru
        except OperationalError as e:
            logging.warning(f"Attempt {attempt + 1}: Database connection failed. Retrying in {delay} seconds...")
            time.sleep(delay)
    logging.error("Failed to connect to the database after multiple attempts.")
    raise Exception("Database connection failed.")

def main():
    logging.debug("Starting main.py")
    
    try:
        TRULENS_CONNECTION_STRING = f'postgresql+psycopg2://{TRULENS_USER}:{TRULENS_PASSWORD}@{TRULENS_HOST}:{TRULENS_PORT}/{TRULENS_DB}'
        tru = connect_to_database(TRULENS_CONNECTION_STRING)
        
        logging.log
        records, feedback = tru.get_records_and_feedback(app_ids=[])

        tru.run_dashboard(port=14000)
    
            
        # Further processing of records and feedback
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()


