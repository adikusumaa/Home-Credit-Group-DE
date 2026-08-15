from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

from airflow.operators.trigger_dagrun import TriggerDagRunOperator

def trigger_ai_on_failure(context):
    TriggerDagRunOperator(
        task_id="trigger_ai",
        trigger_dag_id="dag_incident_response",
        conf={"failed_dag_id": context['dag'].dag_id}
    ).execute(context=context)

default_args = {
    'owner': 'data_team',
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='dag_gold_final',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['gold'],
    on_failure_callback=trigger_ai_on_failure
) as dag:

    gold_task = BashOperator(
    task_id='gold_aggregation',
    bash_command=(
        'docker exec spark-master /opt/spark/bin/spark-submit '
        '--master spark://spark-master:7077 '
        '--deploy-mode client '
        '--conf spark.hive.metastore.uris=thrift://hive-metastore:9083 ' 
        '--conf spark.driver.memory=1g '
        '--conf spark.executor.memory=1g '
        '--conf spark.sql.shuffle.partitions=20 '
        '/opt/jobs/pyspark/Application_g.py'
    ),
)