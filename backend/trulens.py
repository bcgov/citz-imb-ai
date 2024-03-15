from trulens_eval import Tru
import os

TRULENS_USER = os.getenv('TRULENS_USER')
TRULENS_PASSWORD = os.getenv('TRULENS_PASSWORD')
TRULENS_DB = os.getenv('TRULENS_DB')
TRULENS_PORT = os.getenv('TRULENS_PORT')
TRULENS_HOST = os.getenv('TRULENS_HOST')

CONNECTION_STRING = f'postgresql+psycopg2://{TRULENS_USER}:{TRULENS_PASSWORD}@{TRULENS_HOST}:{TRULENS_PORT}/{TRULENS_DB}'

########################################################################
tru = Tru(database_url=CONNECTION_STRING)
tru.reset_database()


