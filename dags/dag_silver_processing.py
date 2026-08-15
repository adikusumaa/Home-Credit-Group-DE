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
    'owner': 'airflow',
    'start_date': datetime(2026, 8, 10),
    'retries': 0,
}

dag = DAG(
    'dag_silver_processing',
    default_args=default_args,
    description='Silver Layer via spark-submit (BashOperator) - 3 scripts',
    schedule_interval='@daily',
    catchup=False,
    on_failure_callback=trigger_ai_on_failure
)


scripts = [
    'application_s.py',
    'bureau_s.py',
    'previous_s.py'
]

tasks = []
for script in scripts:
    task = BashOperator(
        task_id=script.replace('.py', ''),
        bash_command=f'docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --deploy-mode client --conf spark.driver.memory=1g --conf spark.executor.memory=1g --conf spark.sql.shuffle.partitions=20 /opt/jobs/pyspark/{script}',
        dag=dag,
    )
    tasks.append(task)

# Tugas validasi (opsional – jika Anda masih punya generate_report.py)
validate_task = BashOperator(
    task_id='validate_silver_data',
    bash_command=(
        'docker exec spark-master /opt/spark/bin/spark-submit '
        '--driver-memory 512m '
        '--executor-memory 512m '
        '--conf spark.driver.maxResultSize=200m '
        '--conf spark.sql.shuffle.partitions=4 '
        '/opt/jobs/pyspark/generate_report.py'
    ),
    dag=dag,
)

# Tugas copy laporan GE (opsional)
copy_report_task = BashOperator(
    task_id='copy_ge_report',
    bash_command='docker cp spark-master:/opt/jobs/pyspark/great_expectations /opt/airflow/ge_report/',
    dag=dag,
)

# Dependencies: application -> bureau -> previous -> validate -> copy_report
tasks[0] >> tasks[1] >> tasks[2] >> validate_task >> copy_report_task 