from trulens_eval import Tru
import os
from trulens_eval import Feedback
from trulens_eval import Huggingface
from trulens_eval import TruChain
import numpy as np

TRULENS_USER = os.getenv('TRULENS_USER')
TRULENS_PASSWORD = os.getenv('TRULENS_PASSWORD')
TRULENS_DB = os.getenv('TRULENS_DB')
TRULENS_PORT = os.getenv('TRULENS_PORT')
TRULENS_HOST = os.getenv('TRULENS_HOST')

TRULENS_CONNECTION_STRING = f'postgresql+psycopg2://{TRULENS_USER}:{TRULENS_PASSWORD}@{TRULENS_HOST}:{TRULENS_PORT}/{TRULENS_DB}'

########################################################################
tru = Tru(database_url=TRULENS_CONNECTION_STRING)
tru.reset_database()


hugs = Huggingface()

# Create a feedback function from a provider:
f_qa_relevance = Feedback(
    hugs.language_match, # the implementation,
    name = 'Answer Relevance' # the name of the feedback function
).on_input_output() # selectors shorthand


context_selection = TruChain.select_context().node.text

f_qs_relevance = (
    Feedback(
            hugs.language_match, # the implementation,
             name="Context Relevance")
    .on_input()
    .on(context_selection)
    .aggregate(np.mean)
)


