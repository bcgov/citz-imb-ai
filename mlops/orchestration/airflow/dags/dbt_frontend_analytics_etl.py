from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
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
            "INSERT INTO frontend.raw_frontend_analytics (data) VALUES (%s)",
            (Json(item),)
        )

    conn.commit()
    cur.close()
    conn.close()

# Define a task to create the schema
create_schema = PostgresOperator(
    task_id='create_schema',
    postgres_conn_id='trulens_db',
    sql="CREATE SCHEMA IF NOT EXISTS frontend;",
    dag=dag,
)

# Define a task to create the raw table
create_raw_table = PostgresOperator(
    task_id='create_raw_table',
    postgres_conn_id='trulens_db',
    sql="""
    CREATE TABLE IF NOT EXISTS frontend.raw_frontend_analytics (
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

# Task to move the profiles.yml file to the /home/airflow/.dbt directory
move_profiles_yml = BashOperator(
    task_id='move_profiles_yml',
    bash_command='mkdir -p /home/airflow/.dbt && cp /opt/airflow/dbt/profiles.yml /home/airflow/.dbt/profiles.yml',
    dag=dag,
)

# Task to run the DBT command
run_dbt = BashOperator(
    task_id='run_dbt_command',
    bash_command='''
    source /opt/airflow/dbt_venv/bin/activate
    export HOME=/home/airflow
    dbt run --profiles-dir /home/airflow/.dbt --project-dir /opt/airflow/dbt/analytics
    deactivate
    ''',
    env={
        'TRULENS_USER': TRULENS_USER if TRULENS_USER else 'postgres',
        'TRULENS_PASSWORD': TRULENS_PASSWORD if TRULENS_PASSWORD else 'root',
        'TRULENS_HOST': TRULENS_HOST if TRULENS_HOST else 'trulens',
        'TRULENS_DB': TRULENS_DB if TRULENS_DB else 'postgres',
        'TRULENS_PORT': TRULENS_PORT if TRULENS_PORT else '5432',
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
    cur.execute("SELECT data->>'sessionId' FROM frontend.raw_frontend_analytics")
    processed_sessions = set(row[0] for row in cur.fetchall())

    original_file = '/opt/airflow/analytics_data/all_analytics.json'
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        # Lock the temporary file
        fcntl.flock(temp_file.fileno(), fcntl.LOCK_EX)
        
        # Read from original file
        with open(original_file, 'r') as f:
            original_data = json.load(f)
        
        # Filter out processed data
        filtered_data = [item for item in original_data if item['sessionId'] not in processed_sessions]
        
        # Re-read the original file to get any new data that might have been added
        with open(original_file, 'r') as f:
            new_data = json.load(f)
        
        # Merge filtered data with any new data
        merged_data = filtered_data + [item for item in new_data if item not in original_data]
        
        # Write merged data to temp file
        json.dump(merged_data, temp_file)
        
        # Ensure all data is written to disk
        temp_file.flush()
        os.fsync(temp_file.fileno())
    
    # Replace the original file with the temporary file
    shutil.move(temp_file.name, original_file)

    cur.close()
    conn.close()

cleanup_task = PythonOperator(
    task_id='cleanup_source_file',
    python_callable=cleanup_source_file,
    dag=dag,
)

# Define the DAG tasks
create_schema >> create_raw_table >> load_data >> move_profiles_yml >> run_dbt >> cleanup_task
