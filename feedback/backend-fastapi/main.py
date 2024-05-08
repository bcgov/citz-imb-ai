from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from trulens_eval import Tru
from trulens_eval.tru_custom_app import instrument
from trulens_eval import TruCustomApp
import warnings
from typing import Annotated
warnings.filterwarnings("ignore")
import psycopg2
import os
import json
#from ragfromscratch import RAG_from_scratch

app = FastAPI()
kg = None
tru = None
APP_ID = 'TopK_Feedback_System_v2'
#rag = RAG_from_scratch()

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit/")
async def submit_question(prompt: str = Form(...)):
    # Implement your model_response and neo4j_vector_search functions here
    #responses = model_response(prompt)
    global kg
    if kg is None:
        kg = neo4j()
    print(kg)
    global tru
    rag = RAG_from_scratch()
    if tru is None:
        tru = connect_trulens()
    tru_rag = TruCustomApp(rag,
        app_id = APP_ID,
    )
    print(tru_rag)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    with tru_rag as recording:
        responses = rag.query(prompt, embeddings, kg)
    print(responses)
    record = recording.get()
    return {"responses": responses, "recording": record.record_id}


@app.post("/feedback/")
async def feedback(feedback: str = Form(...), index: str = Form(...),
                   recording_id: str =Form(...),
                   bulk: bool = Form(False)):
    global tru
    if tru is None:
        tru = connect_trulens()
    rows = process_feedback(index, feedback, recording_id, bulk)
    if rows:
        return {"status": True, "rows": rows}
    else:
        return {"status": False}
    

@app.get("/fetch_feedback/")
async def fetch_all_feedback():
    global tru
    if tru is None:
        tru = connect_trulens()
    rows = fetch_all_feedback()
    if rows:
        return {"status": True, "rows": rows}
    else:
        return {"status": False}    

def retrieval(query_str, embeddings, kg):
    return neo4j_vector_search(query_str, embeddings, kg)

def tru_connect():
    TRULENS_USER = os.getenv('TRULENS_USER')
    TRULENS_PASSWORD = os.getenv('TRULENS_PASSWORD')
    TRULENS_DB = os.getenv('TRULENS_DB')
    TRULENS_PORT = os.getenv('TRULENS_PORT')
    TRULENS_HOST = os.getenv('TRULENS_HOST')
    conn = psycopg2.connect(
        host= TRULENS_HOST,
        database=TRULENS_DB,
        user=TRULENS_USER,
        password=TRULENS_PASSWORD
    )
    return conn

def fetch_all_feedback():
    conn = tru_connect()
    cur = conn.cursor()  # creating a cursor
    cur.execute("""SELECT R.input, R.record_json as record_json, F.multi_result, F.result, R.app_id result FROM public.records R 
    LEFT Join feedbacks F ON F.record_id = R.record_id WHERE
    R.app_id = %s""",
    (APP_ID,))
    rows = cur.fetchall()
    return rows

def fetch_human_feedback(record_id):
    conn = tru_connect()
    cur = conn.cursor()  # creating a cursor
    cur.execute("""
    SELECT R.input, F.multi_result, F.result, R.app_id result FROM public.records R 
    LEFT Join feedbacks F ON F.record_id = R.record_id WHERE
    R.record_id= %s
    """,(record_id,))
    rows = cur.fetchall()
    return rows

def get_feedback_value(feedback):
    print(feedback)
    if feedback == "thumbs_up":
        return 1
    else:
        return -1

def process_feedback(index, feedback, record_id=None, bulk=False):
    if bulk:
        multi_result = {"bulk":[]}
        print(f"Feedback for Response: is {feedback} in bulk")
        feedback = feedback.split(",")
        for feedback_value in feedback:
            multi_result['bulk'].append(get_feedback_value(feedback_value))
        print(multi_result)    
        multi_result = json.dumps(multi_result)
    else:
        print(f"Feedback for Response {index}: is {feedback}")
        feedbackvalue = get_feedback_value(feedback)
        multi_result = json.dumps({index:[feedbackvalue]})

    print(multi_result)       

    tru_feedback = tru.add_feedback(
        name="Human Feedack",
        record_id=record_id,
        app_id=APP_ID,
        result=0,
        multi_result=multi_result,
    )
    print(record_id)
    print(tru_feedback)
    rows = fetch_human_feedback(record_id)
    if (rows):
        return rows
    else:
        return None

class RAG_from_scratch:
    @instrument
    def retrieve(self, query: str, embeddings, kg) -> list:
        """
        Retrieve relevant text from vector store.
        """
        return retrieval(query, embeddings, kg)    

    @instrument
    def query(self, query: str, embeddings, kg) -> str:
        context_str = self.retrieve(query, embeddings, kg)
        return context_str

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "*"
]

def neo4j_vector_search(question, embeddings, kg):
  """Search for similar nodes using the Neo4j vector index"""
  query_embedding = embeddings.embed_query(question)
  vector_search_query = """
    CALL db.index.vector.queryNodes($index_name, $top_k, $question) yield node, score
    RETURN score, node.ActId,  node.RegId as Regulations, node.sectionId, node.sectionName, node.url,  node.text AS text
  """
  similar = kg.query(vector_search_query, 
                     params={
                      'question': query_embedding, 
                      'index_name':'Acts_Updatedchunks', 
                      'top_k': 10})
  return similar

def neo4j():
    NEO4J_URI = 'bolt://neo4j:7687'
    kg = Neo4jGraph(
        url=NEO4J_URI, username='neo4j', password='neo4j', database='neo4j')
    return kg

def connect_trulens():
    TRULENS_USER = os.getenv('TRULENS_USER')
    TRULENS_PASSWORD = os.getenv('TRULENS_PASSWORD')
    TRULENS_DB = os.getenv('TRULENS_DB')
    TRULENS_PORT = os.getenv('TRULENS_PORT')
    TRULENS_HOST = os.getenv('TRULENS_HOST')
    TRULENS_CONNECTION_STRING = f'postgresql+psycopg2://{TRULENS_USER}:{TRULENS_PASSWORD}@{TRULENS_HOST}:{TRULENS_PORT}/{TRULENS_DB}'
    tru = Tru(database_url=TRULENS_CONNECTION_STRING)
    return tru

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def model_response(prompt):
    if prompt is None:
        return
    # Implement your model_response logic here
    responses = ["Answer 1", "Answer 2", "Answer 3", "Answer 4", "Answer 5"]
    return responses

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)