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

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 23),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'frontend_analytics_etl',
    default_args=default_args,
    description='ETL process for frontend analytics',
    schedule_interval=timedelta(days=1),
    tags=['dbt', 'bclaws', 'bclaws_analytics', 'trulens'],
)

# Define a function to load JSON data to Postgres
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

# Define a task to create the schema
create_schema = PostgresOperator(
    task_id='create_schema',
    postgres_conn_id='trulens_db',
    sql="CREATE SCHEMA IF NOT EXISTS frontend_analytics;",
    dag=dag,
)

# Define a task to create the raw table
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

# Define a task to run the DBT command
run_dbt = BashOperator(
    task_id='run_dbt',
    bash_command='cd /opt/airflow/dbt/frontend_analytics && dbt run',
    env={
        'DBT_PROFILES_DIR': '/opt/airflow/dbt',
    },
    dag=dag,
)

# Define a function to cleanup the source file
def cleanup_source_file():
    import psycopg2
    import json

    conn = psycopg2.connect(
        dbname=TRULENS_DB,
        user=TRULENS_USER,
        password=TRULENS_PASSWORD,
        host=TRULENS_HOST,    
        port=TRULENS_PORT
    )
    cur = conn.cursor()

    # Get processed session IDs
    cur.execute("SELECT data->>'sessionId' FROM frontend_analytics.raw_frontend_analytics")
    processed_sessions = set(row[0] for row in cur.fetchall())

    # Read and filter JSON file
    with open('/opt/airflow/analytics_data/all_analytics.json', 'r') as f:
        data = json.load(f)

    filtered_data = [item for item in data if item['sessionId'] not in processed_sessions]

    # Write filtered data back to file
    with open('/opt/airflow/analytics_data/all_analytics.json', 'w') as f:
        json.dump(filtered_data, f)

    cur.close()
    conn.close()

cleanup_task = PythonOperator(
    task_id='cleanup_source_file',
    python_callable=cleanup_source_file,
    dag=dag,
)

# Define the DAG tasks
create_schema >> create_raw_table >> load_data >> run_dbt >> cleanup_task
