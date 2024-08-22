from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
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
TRULENS_USER = os.getenv('TRULENS_USER', 'postgres')
TRULENS_PASSWORD = os.getenv('TRULENS_PASSWORD', 'root')
TRULENS_DB = os.getenv('TRULENS_DB', 'postgres')
TRULENS_HOST = os.getenv('TRULENS_HOST', 'trulens')
TRULENS_PORT = os.getenv('TRULENS_PORT', '5432')

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
    schedule_interval=timedelta(days=1),
    tags=['dbt', 'bclaws', 'bclaws_analytics', 'trulens'],
)

# Function to get PostgresHook
def get_postgres_hook():
    return PostgresHook(
        host=TRULENS_HOST,
        database=TRULENS_DB,
        user=TRULENS_USER,
        password=TRULENS_PASSWORD,
        port=int(TRULENS_PORT)
    )

# Function to print environment variables (for debugging)
def print_env_variables():
    return f'Trulens environment variables loaded'

# Function to load JSON data to Postgres
def load_json_to_postgres():
    pg_hook = get_postgres_hook()
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    with open('/opt/airflow/analytics_data/all_analytics.json', 'r') as f:
        data = json.load(f)

    for item in data:
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
        
        filtered_data = [item for item in original_data if item['sessionId'] not in processed_sessions]
        
        with open(original_file, 'r') as f:
            new_data = json.load(f)
        
        merged_data = filtered_data + [item for item in new_data if item not in original_data]
        
        json.dump(merged_data, temp_file)
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
    postgres_hook=get_postgres_hook(),
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
    postgres_hook=get_postgres_hook(),
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
    task_id='run_dbt_command',
    bash_command='''
    source /opt/airflow/dbt_venv/bin/activate
    export HOME=/home/airflow
    dbt run --profiles-dir /home/airflow/.dbt --project-dir /opt/airflow/dbt/analytics
    deactivate
    ''',
    env={
        'TRULENS_USER': TRULENS_USER,
        'TRULENS_PASSWORD': TRULENS_PASSWORD,
        'TRULENS_HOST': TRULENS_HOST,
        'TRULENS_DB': TRULENS_DB,
        'TRULENS_PORT': TRULENS_PORT,
    },
    dag=dag,
)

cleanup_task = PythonOperator(
    task_id='cleanup_source_file',
    python_callable=cleanup_source_file,
    dag=dag,
)

# Define the DAG tasks
retrieve_secrets >> create_schema >> create_raw_table >> load_data >> move_profiles_yml >> run_dbt >> cleanup_task
