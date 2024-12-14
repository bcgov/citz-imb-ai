from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv("/vault/secrets/zuba-secret-dev")

# Retrieve environment variables
TRULENS_USER = os.getenv("TRULENS_USER")
TRULENS_PASSWORD = os.getenv("TRULENS_PASSWORD")
TRULENS_DB = os.getenv("TRULENS_DB")
TRULENS_PORT = os.getenv("TRULENS_PORT")
TRULENS_HOST = os.getenv("TRULENS_HOST")


# Define a function to print the loaded environment variables (for debugging or logging)
def print_env_variables():
    return f"Trulens environment variables loaded"


# Define the DAG
default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 8, 13),
    "retries": 1,
}

dag = DAG(
    "trulens_analytics_etl",
    default_args=default_args,
    description="A DAG to initialize DBT with Vault secrets",
    schedule_interval="0 0 * * *",
    catchup=False,
    tags=["dbt", "trulens", "bclaws", "bclaws_analytics"],
)

# Task to print the environment variables (optional for debugging)
retrieve_secrets = PythonOperator(
    task_id="retrieve_secrets_from_vault",
    python_callable=print_env_variables,
    dag=dag,
)

# Task to move the profiles.yml file to the /home/airflow/.dbt directory
move_profiles_yml = BashOperator(
    task_id="move_profiles_yml",
    bash_command="mkdir -p /home/airflow/.dbt && cp /opt/airflow/dbt/profiles.yml /home/airflow/.dbt/profiles.yml",
    dag=dag,
)

# Task to run the DBT command
run_dbt = BashOperator(
    task_id="run_dbt_command",
    bash_command="""
    source /opt/airflow/dbt_venv/bin/activate
    export HOME=/home/airflow
    dbt deps --project-dir /opt/airflow/dbt/analytics
    dbt run --profiles-dir /home/airflow/.dbt --project-dir /opt/airflow/dbt/analytics --select trulens
    deactivate
    """,
    env={
        "TRULENS_USER": TRULENS_USER if TRULENS_USER else "postgres",
        "TRULENS_PASSWORD": TRULENS_PASSWORD if TRULENS_PASSWORD else "root",
        "TRULENS_HOST": TRULENS_HOST if TRULENS_HOST else "trulens",
        "TRULENS_DB": TRULENS_DB if TRULENS_DB else "postgres",
    },
    dag=dag,
)

# Task to trigger the frontend analytics DAG upon successful completion of run_dbt
trigger_frontend_analytics_dag = TriggerDagRunOperator(
    task_id="trigger_frontend_analytics_etl",
    trigger_dag_id="frontend_analytics_etl",
    wait_for_completion=False,  # Don't wait for the triggered DAG to complete
    trigger_rule="all_success",  # Trigger the frontend DAG only if the current DAG completes successfully
    dag=dag,
)

# Set up task dependencies
retrieve_secrets >> move_profiles_yml >> run_dbt >> trigger_frontend_analytics_dag
