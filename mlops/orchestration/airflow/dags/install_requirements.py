from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 7, 23),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'install_requirements',
    default_args=default_args,
    description='A simple DAG to install requirements from requirements.txt',
    schedule_interval='@once',
    tags=['requirements'],
)

# Define the task to install requirements
install_requirements = BashOperator(
    task_id='install_requirements',
    bash_command='pip install -r /opt/airflow/dags/requirements.txt',
    dag=dag,
)

# Set the task in the DAG
install_requirements
