from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from datetime import datetime
import json

default_args = {
    'owner': 'data_team',
    'start_date': datetime(2024, 1, 1),
    'retries': 0,
}

with DAG(
    dag_id='dag_incident_response',
    default_args=default_args,
    description='CrewAI Incident Response via API',
    schedule_interval=None,
    catchup=False,
) as dag:

    call_crewai = SimpleHttpOperator(
        task_id='call_crewai_api',
        http_conn_id='crewai_api',
        endpoint='/run',
        method='POST',
        headers={"Content-Type": "application/json"},
        data=json.dumps({"dag_id": "{{ dag_run.conf['failed_dag_id'] }}"}),
        response_check=lambda response: response.status_code == 200,
        log_response=True,
    )