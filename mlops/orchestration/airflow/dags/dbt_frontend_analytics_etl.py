from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import Connection
from airflow import settings
from airflow.operators.python import BranchPythonOperator
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
import tempfile
import shutil
import fcntl

# Load environment variables from the .env file
load_dotenv("/vault/secrets/zuba-secret-dev")

# Retrieve environment variables
TRULENS_USER = os.getenv('TRULENS_USER')
TRULENS_PASSWORD = os.getenv('TRULENS_PASSWORD')
TRULENS_DB = os.getenv('TRULENS_DB')
TRULENS_HOST = os.getenv('TRULENS_HOST')
TRULENS_PORT = os.getenv('TRULENS_PORT')

# Define the Postgres connection ID
POSTGRES_CONN_ID = 'trulens_postgres'

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 22),
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
    schedule_interval='@daily',
    tags=['dbt', 'bclaws', 'bclaws_analytics', 'trulens'],
)

# Function to create the Postgres connection if it doesn't exist
def create_postgres_connection():
    session = settings.Session()
    conn = session.query(Connection).filter(Connection.conn_id == POSTGRES_CONN_ID).first()
    if not conn:
        new_conn = Connection(
            conn_id=POSTGRES_CONN_ID,
            conn_type='postgres',
            host=TRULENS_HOST,
            schema=TRULENS_DB,
            login=TRULENS_USER,
            password=TRULENS_PASSWORD,
            port=TRULENS_PORT
        )
        session.add(new_conn)
        session.commit()
    session.close()

# Create the Postgres connection
create_postgres_connection()

# Function to get PostgresHook
def get_postgres_hook():
    return PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

# Function to print environment variables (for debugging)
def print_env_variables():
    return f'Trulens environment variables loaded'

# Function to check if json data exists and has valid sessionIds
def check_json_data():
    json_file_path = '/opt/airflow/analytics_data/all_analytics.json'
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        valid_data = [item for item in data if item.get('sessionId')]
        
        if valid_data:
            return 'load_json_to_postgres'
        else:
            return 'skip_processing'
    except (FileNotFoundError, json.JSONDecodeError):
        return 'skip_processing'

# Function to load JSON data to Postgres
def load_json_to_postgres():
    pg_hook = get_postgres_hook()
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    with open('/opt/airflow/analytics_data/all_analytics.json', 'r') as f:
        data = json.load(f)

    for item in data:
        if item.get('sessionId'):  # Only insert items with a sessionId
            cur.execute(
                "INSERT INTO frontend.raw_frontend_analytics (data) VALUES (%s)",
                (json.dumps(item),)
            )

    conn.commit()
    cur.close()
    conn.close()

# Function to cleanup the source file
def cleanup_source_file():
    pg_hook = get_postgres_hook()
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    # Get processed session IDs
    cur.execute("SELECT data->>'sessionId' FROM frontend.raw_frontend_analytics")
    processed_sessions = set(row[0] for row in cur.fetchall())

    original_file = '/opt/airflow/analytics_data/all_analytics.json'
    
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        fcntl.flock(temp_file.fileno(), fcntl.LOCK_EX)
        
        with open(original_file, 'r') as f:
            original_data = json.load(f)
        
        filtered_data = [item for item in original_data if item.get('sessionId') not in processed_sessions]
        
        json.dump(filtered_data, temp_file)
        temp_file.flush()
        os.fsync(temp_file.fileno())
    
    shutil.move(temp_file.name, original_file)

    cur.close()
    conn.close()

# Task definitions
retrieve_secrets = PythonOperator(
    task_id='retrieve_secrets_from_vault',
    python_callable=print_env_variables,
    dag=dag,
)

create_schema = PostgresOperator(
    task_id='create_schema',
    sql="CREATE SCHEMA IF NOT EXISTS frontend;",
    postgres_conn_id=POSTGRES_CONN_ID,
    dag=dag,
)

create_raw_table = PostgresOperator(
    task_id='create_raw_table',
    sql="""
    CREATE TABLE IF NOT EXISTS frontend.raw_frontend_analytics (
        id SERIAL PRIMARY KEY,
        data JSONB NOT NULL
    );
    """,
    postgres_conn_id=POSTGRES_CONN_ID,
    dag=dag,
)

check_data = BranchPythonOperator(
    task_id='check_data',
    python_callable=check_json_data,
    dag=dag,
)

load_data = PythonOperator(
    task_id='load_json_to_postgres',
    python_callable=load_json_to_postgres,
    dag=dag,
)

move_profiles_yml = BashOperator(
    task_id='move_profiles_yml',
    bash_command='mkdir -p /home/airflow/.dbt && cp /opt/airflow/dbt/profiles.yml /home/airflow/.dbt/profiles.yml',
    dag=dag,
)

run_dbt = BashOperator(
    task_id='run_dbt',
    bash_command='''
    source /opt/airflow/dbt_venv/bin/activate
    export HOME=/home/airflow
    dbt deps --project-dir /opt/airflow/dbt/analytics
    dbt run --profiles-dir /home/airflow/.dbt --project-dir /opt/airflow/dbt/analytics --select frontend
    deactivate
    ''',
    env={
        'TRULENS_USER': TRULENS_USER,
        'TRULENS_PASSWORD': TRULENS_PASSWORD,
        'TRULENS_HOST': TRULENS_HOST,
        'TRULENS_DB': TRULENS_DB,
    },
    dag=dag,
)

# Define the DAG tasks
skip_processing = DummyOperator(
    task_id='skip_processing',
    dag=dag,
)

end_task = DummyOperator(
    task_id='end_task',
    trigger_rule='none_failed_or_skipped',
    dag=dag,
)

cleanup_task = PythonOperator(
    task_id='cleanup_source_file',
    python_callable=cleanup_source_file,
    dag=dag,
)

# Define the task dependencies
retrieve_secrets >> create_schema >> create_raw_table >> check_data
check_data >> [load_data, skip_processing]
load_data >> move_profiles_yml >> run_dbt >> cleanup_task
[cleanup_task, skip_processing] >> end_task
