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
TRULENS_USER = os.getenv('TRULENS_USER', 'postgres')
TRULENS_PASSWORD = os.getenv('TRULENS_PASSWORD', 'rppt')
TRULENS_DB = 'trulens' 
TRULENS_HOST = os.getenv('TRULENS_HOST', 'trulens')
TRULENS_PORT = os.getenv('TRULENS_PORT', '5432')

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

def print_env_variables():
    print(f"TRULENS_HOST: {TRULENS_HOST}")
    print(f"TRULENS_PORT: {TRULENS_PORT}")
    print(f"TRULENS_DB: {TRULENS_DB}")
    print(f"TRULENS_USER: {TRULENS_USER}")
    # Don't print the password for security reasons
    return f'Trulens environment variables loaded'


# Define the DAG
dag = DAG(
    'trulens_frontend_unified_etl',
    default_args=default_args,
    description='Unified ETL process for Trulens and frontend analytics',
    schedule_interval='0 0 * * *',
    catchup=False,
    tags=['dbt', 'bclaws', 'bclaws_analytics', 'trulens'],
)

def create_postgres_connection():
    session = settings.Session()
    conn = session.query(Connection).filter(Connection.conn_id == POSTGRES_CONN_ID).first()
    
    # Print connection values for debugging
    print(f"Connection values: host={TRULENS_HOST}, port={TRULENS_PORT}, db={TRULENS_DB}")
    
    # Remove existing connection if it exists
    if conn:
        session.delete(conn)
        session.commit()
    
    # Create new connection with explicit values
    new_conn = Connection(
        conn_id=POSTGRES_CONN_ID,
        conn_type='postgres',
        host=TRULENS_HOST if TRULENS_HOST else 'postgres',  # Use explicit default
        schema=TRULENS_DB if TRULENS_DB else 'trulens',     # Use explicit default
        login=TRULENS_USER if TRULENS_USER else 'postgres', # Use explicit default
        password=TRULENS_PASSWORD if TRULENS_PASSWORD else 'postgres',
        port=int(TRULENS_PORT) if TRULENS_PORT else 5432    # Convert to int and use default
    )
    
    session.add(new_conn)
    session.commit()
    
    # Verify the connection was created correctly
    verify_conn = session.query(Connection).filter(Connection.conn_id == POSTGRES_CONN_ID).first()
    print(f"Verified connection: host={verify_conn.host}, port={verify_conn.port}, db={verify_conn.schema}")
    
    session.close()

# Create the Postgres connection
create_postgres_connection()

# Function to get PostgresHook
def get_postgres_hook():
    return PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

# Function to print environment variables (for debugging)
def print_env_variables():
    return f'Trulens environment variables loaded'

# Function to create a snapshot of the frontend analytics
def create_frontend_snapshot():
    original_file = '/opt/airflow/analytics_data/all_analytics.json'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    snapshot_dir = '/opt/airflow/analytics_data/snapshots'
    snapshot_file = f'{snapshot_dir}/frontend_analytics_{timestamp}.json'
    
    # Create snapshots directory if it doesn't exist
    if not os.path.exists(snapshot_dir):
        os.makedirs(snapshot_dir, exist_ok=True)
    
    # Skip if the original file doesn't exist
    if not os.path.exists(original_file):
        return None
    
    try:
        # Create temp file in the same directory as the destination
        # instead of using the default /tmp location
        with open(original_file, 'r') as src:
            data = json.load(src)
        
        # Write directly to the destination instead of using move
        with open(snapshot_file, 'w') as dest:
            json.dump(data, dest)
        
        # Store the snapshot path for other tasks to use
        with open(f"{snapshot_dir}/latest_snapshot.txt", "w") as f:
            f.write(snapshot_file)
            
        return snapshot_file
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
        print(f"Error creating snapshot: {str(e)}")
        return None

# Function to check if json data exists and has valid sessionIds
def check_frontend_data():
    snapshot_path_file = '/opt/airflow/analytics_data/snapshots/latest_snapshot.txt'
    
    # Check if we have a snapshot file path
    if os.path.exists(snapshot_path_file):
        with open(snapshot_path_file, 'r') as f:
            snapshot_file = f.read().strip()
        
        # If snapshot exists and has valid data, process it
        if snapshot_file and os.path.exists(snapshot_file):
            try:
                with open(snapshot_file, 'r') as f:
                    data = json.load(f)
                
                valid_data = [item for item in data if item.get('sessionId')]
                
                if valid_data:
                    return 'load_frontend_data'
            except (json.JSONDecodeError, FileNotFoundError):
                pass
    
    return 'skip_frontend_processing'

# Function to load frontend data with focus on unique record_ids and click counts
def load_frontend_data():
    snapshot_path_file = '/opt/airflow/analytics_data/snapshots/latest_snapshot.txt'
    
    if not os.path.exists(snapshot_path_file):
        return
    
    with open(snapshot_path_file, 'r') as f:
        snapshot_file = f.read().strip()
    
    if not snapshot_file or not os.path.exists(snapshot_file):
        return
    
    pg_hook = get_postgres_hook()
    conn = pg_hook.get_conn()
    cur = conn.cursor()
    
    # Create a table specifically for record_id analytics
    cur.execute("""
        CREATE TABLE IF NOT EXISTS frontend.record_id_clicks (
            record_id VARCHAR PRIMARY KEY,
            total_clicks INTEGER,
            source_clicks JSONB,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    with open(snapshot_file, 'r') as f:
        data = json.load(f)
    
    # Process data to collect unique record_ids and click counts
    record_data = {}
    
    for item in data:
        for chat in item.get('chats', []):
            record_id = chat.get('recording_id')
            
            if not record_id:
                continue
                
            # Initialize if this is a new record_id
            if record_id not in record_data:
                record_data[record_id] = {
                    'total_clicks': 0,
                    'source_clicks': {}
                }
            
            # Add total clicks
            clicks = int(chat.get('llmResponseInteraction', {}).get('clicks', 0))
            record_data[record_id]['total_clicks'] += clicks
            
            # Process source-specific clicks
            for source in chat.get('sources', []):
                source_key = str(source.get('sourceKey', ''))
                source_clicks = int(source.get('clicks', 0))
                
                if source_clicks > 0:
                    current = record_data[record_id]['source_clicks'].get(source_key, 0)
                    record_data[record_id]['source_clicks'][source_key] = current + source_clicks
    
    # Insert or update the data
    for record_id, data in record_data.items():
        cur.execute("""
            INSERT INTO frontend.record_id_clicks 
                (record_id, total_clicks, source_clicks)
            VALUES (%s, %s, %s)
            ON CONFLICT (record_id) 
            DO UPDATE SET
                total_clicks = frontend.record_id_clicks.total_clicks + EXCLUDED.total_clicks,
                source_clicks = frontend.record_id_clicks.source_clicks || EXCLUDED.source_clicks,
                last_updated = CURRENT_TIMESTAMP
        """, (
            record_id,
            data['total_clicks'],
            json.dumps(data['source_clicks'])
        ))
    
    # Create a view for top 10 clicked records
    cur.execute("""
        CREATE OR REPLACE VIEW frontend.top_10_clicked_records AS
        SELECT 
            record_id, 
            total_clicks,
            source_clicks
        FROM 
            frontend.record_id_clicks
        ORDER BY 
            total_clicks DESC
        LIMIT 10
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    
    return f"Processed {len(record_data)} unique record_ids"

# Function to cleanup the source file
def cleanup_frontend_file():
    pg_hook = get_postgres_hook()
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    # Get processed session IDs
    cur.execute("SELECT data->>'sessionId' FROM frontend.raw_frontend_analytics")
    processed_sessions = set(row[0] for row in cur.fetchall() if row[0])

    original_file = '/opt/airflow/analytics_data/all_analytics.json'
    
    if os.path.exists(original_file):
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

def test_connection():
    from airflow.hooks.base import BaseHook
    import psycopg2

    print_env_variables() 
    conn_info = BaseHook.get_connection("trulens_postgres")
    print(f"Host: {conn_info.host}")
    print(f"Port: {conn_info.port}")
    print(f"Schema: {conn_info.schema}")
    print(f"Login: {conn_info.login}")
    
    # Try to connect
    try:
        conn = psycopg2.connect(
            host=conn_info.host,
            port=conn_info.port,
            dbname=conn_info.schema,
            user=conn_info.login,
            password=conn_info.password,
        )
        print("Connection successful!")
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return False

test_connection_task = PythonOperator(
    task_id='test_connection_task',
    python_callable=test_connection,
    dag=dag,
)

# Task definitions
retrieve_secrets = PythonOperator(
    task_id='retrieve_secrets_from_vault',
    python_callable=print_env_variables,
    dag=dag,
)

# Create snapshot of frontend data - first step
create_snapshot = PythonOperator(
    task_id='create_frontend_snapshot',
    python_callable=create_frontend_snapshot,
    dag=dag,
)

# Create schemas for both data sources
create_frontend_schema = PostgresOperator(
    task_id='create_frontend_schema',
    sql="CREATE SCHEMA IF NOT EXISTS frontend;",
    postgres_conn_id=POSTGRES_CONN_ID,
    dag=dag,
)

create_frontend_table = PostgresOperator(
    task_id='create_frontend_table',
    sql="""
    CREATE TABLE IF NOT EXISTS frontend.raw_frontend_analytics (
        id SERIAL PRIMARY KEY,
        data JSONB NOT NULL,
        snapshot_source TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    postgres_conn_id=POSTGRES_CONN_ID,
    dag=dag,
)

# Check whether to process frontend data
check_frontend = BranchPythonOperator(
    task_id='check_frontend_data',
    python_callable=check_frontend_data,
    dag=dag,
)

# Load frontend data to postgres
load_frontend = PythonOperator(
    task_id='load_frontend_data',
    python_callable=load_frontend_data,
    dag=dag,
)

# Move profiles.yml for dbt
move_profiles_yml = BashOperator(
    task_id='move_profiles_yml',
    bash_command='mkdir -p /home/airflow/.dbt && cp /opt/airflow/dbt/profiles.yml /home/airflow/.dbt/profiles.yml',
    dag=dag,
)

# Run dbt for Trulens analytics
run_trulens_dbt = BashOperator(
    task_id='run_trulens_dbt',
    bash_command='''
    source /opt/airflow/dbt_venv/bin/activate
    export HOME=/home/airflow
    dbt deps --project-dir /opt/airflow/dbt/analytics
    dbt run --profiles-dir /home/airflow/.dbt --project-dir /opt/airflow/dbt/analytics --select trulens_1_4_7 --profile analytics_v2
    deactivate
    ''',
    env={
        'TRULENS_USER': TRULENS_USER if TRULENS_USER else 'postgres',
        'TRULENS_PASSWORD': TRULENS_PASSWORD if TRULENS_PASSWORD else 'root',
        'TRULENS_HOST': TRULENS_HOST if TRULENS_HOST else 'trulens',
        'TRULENS_DB': TRULENS_DB if TRULENS_DB else 'trulenss',
    },
    execution_timeout=timedelta(minutes=30),
    dag=dag,
)

# After the existing run_frontend_dbt task, add a new task for the unified model
run_unified_dbt = BashOperator(
    task_id='run_unified_dbt',
    bash_command='''
    source /opt/airflow/dbt_venv/bin/activate
    export HOME=/home/airflow
    dbt deps --project-dir /opt/airflow/dbt/analytics
    dbt run --profiles-dir /home/airflow/.dbt --project-dir /opt/airflow/dbt/analytics --select trulens_1_4_7_frontend_unified --profile analytics_v2
    deactivate
    ''',
    env={
        'TRULENS_USER': TRULENS_USER if TRULENS_USER else 'postgres',
        'TRULENS_PASSWORD': TRULENS_PASSWORD if TRULENS_PASSWORD else 'root',
        'TRULENS_HOST': TRULENS_HOST if TRULENS_HOST else 'trulens',
        'TRULENS_DB': TRULENS_DB if TRULENS_DB else 'trulens',
    },
    execution_timeout=timedelta(minutes=30),
    dag=dag,
)

# Final task to indicate completion
end_task = DummyOperator(
    task_id='end_task',
    trigger_rule='none_failed_or_skipped',
    dag=dag,
)

# Set up the DAG dependencies
retrieve_secrets >> create_snapshot >> [test_connection_task, move_profiles_yml]
test_connection_task >> create_frontend_schema >> create_frontend_table >> check_frontend
check_frontend >> load_frontend
move_profiles_yml >> run_trulens_dbt

# Only run frontend dbt and cleanup if we processed frontend data
load_frontend >> run_unified_dbt

# Modify the DAG dependencies to include the unified model
run_trulens_dbt >> run_unified_dbt

# Final paths to completion (update this section)
run_unified_dbt >> end_task