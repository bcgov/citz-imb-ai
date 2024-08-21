from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv("/vault/secrets/zuba-secret-dev")

# Retrieve environment variables
TRULENS_USER = os.getenv('TRULENS_USER')
TRULENS_PASSWORD = os.getenv('TRULENS_PASSWORD')
TRULENS_DB = os.getenv('TRULENS_DB')
TRULENS_HOST = os.getenv('TRULENS_HOST')
TRULENS_PORT = os.getenv('TRULENS_PORT')

# Define a function to print the loaded environment variables (for debugging or logging)
def print_env_variables():
    return f'Trulens environment variables loaded'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 21),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'frontend_analytics_etl',
    default_args=default_args,
    description='ETL process for frontend analytics',
    schedule_interval=timedelta(days=1),
)

def load_json_to_postgres():
    import psycopg2
    from psycopg2.extras import Json

    conn = psycopg2.connect(
        dbname=TRULENS_DB,
        user=TRULENS_USER,
        password=TRULENS_PASSWORD,
        host=TRULENS_HOST,
        port=TRULENS_PORT
    )
    cur = conn.cursor()

    with open('/opt/airflow/analytics_data/all_analytics.json', 'r') as f:
        data = json.load(f)

    for item in data:
        cur.execute(
            "INSERT INTO frontend_analytics.raw_frontend_analytics (data) VALUES (%s)",
            (Json(item),)
        )

    conn.commit()
    cur.close()
    conn.close()

create_schema = PostgresOperator(
    task_id='create_schema',
    postgres_conn_id='trulens_db',
    sql="CREATE SCHEMA IF NOT EXISTS frontend_analytics;",
    dag=dag,
)

create_raw_table = PostgresOperator(
    task_id='create_raw_table',
    postgres_conn_id='trulens_db',
    sql="""
    CREATE TABLE IF NOT EXISTS frontend_analytics.raw_frontend_analytics (
        id SERIAL PRIMARY KEY,
        data JSONB NOT NULL
    );
    """,
    dag=dag,
)

load_data = PythonOperator(
    task_id='load_json_to_postgres',
    python_callable=load_json_to_postgres,
    dag=dag,
)

run_dbt = BashOperator(
    task_id='run_dbt',
    bash_command='cd /opt/airflow/dbt/frontend_analytics && dbt run',
    env={
        'DBT_PROFILES_DIR': '/opt/airflow/dbt',
    },
    dag=dag,
)

create_schema >> create_raw_table >> load_data >> run_dbt
