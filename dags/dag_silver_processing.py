from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {'owner': 'airflow', 'start_date': datetime(2026, 8, 10), 'retries': 1}

dag = DAG(
    'dag_silver_processing',
    default_args=default_args,
    description='Silver Layer via spark-submit (BashOperator)',
    schedule_interval=None,
    catchup=False,
)

# Daftar script PySpark (4 task ETL)
scripts = [
    'application_profile.py',
    'bureau_credit_history.py',
    'loan_and_payment_behavior.py',
    'final_application_features.py'
]

tasks = []
for script in scripts:
    task = BashOperator(
        task_id=script.replace('.py', ''),
        bash_command=f'docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --deploy-mode client --conf spark.driver.memory=1g --conf spark.executor.memory=1g --conf spark.sql.shuffle.partitions=20 /opt/jobs/pyspark/{script}',
        dag=dag,
    )
    tasks.append(task)

# ============================================
# TASK TAMBAHAN: VALIDASI GREAT EXPECTATIONS
# ============================================
validate_task = BashOperator(
    task_id='validate_silver_data',
    bash_command='docker exec spark-master /opt/spark/bin/spark-submit /opt/jobs/pyspark/generate_report.py',
    dag=dag,
)

# ============================================
# URUTAN EKSEKUSI (4 ETL dulu, BARU Validasi)
# ============================================
tasks[0] >> tasks[1] >> tasks[2] >> tasks[3] >> validate_task