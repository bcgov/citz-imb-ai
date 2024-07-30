from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

from langchain_community.embeddings import HuggingFaceEmbeddings

def downlaod_sentence_transformer():
    HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

with DAG(
    'download_sentence_transformer',
    default_args=default_args,
    description='A simple tutorial DAG',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
) as dag:

    task_download_sentence_transformer = PythonOperator(
        task_id='task_download_sentence_transformer',
        python_callable=downlaod_sentence_transformer,
        execution_timeout=timedelta(hours=1),
    )

    task_download_sentence_transformer