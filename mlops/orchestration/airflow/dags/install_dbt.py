from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 16),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'setup_dbt_environment',
    default_args=default_args,
    description='A DAG to setup venv and install dbt Core',
    schedule_interval='@once',
    tags=['dbt', 'setup', 'venv', 'trulens'],
)

# Create virtual environment
create_venv = BashOperator(
    task_id='create_venv',
    bash_command='python3 -m venv /opt/airflow/dbt_venv',
    dag=dag,
)

# Activate venv and install dbt Core
install_dbt = BashOperator(
    task_id='install_dbt',
    bash_command='''
    source /opt/airflow/dbt_venv/bin/activate
    pip install dbt-core
    pip install dbt-postgres
    deactivate
    ''',
    dag=dag,
)

create_venv >> install_dbt