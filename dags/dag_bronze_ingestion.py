from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
from hdfs import InsecureClient

from airflow.operators.trigger_dagrun import TriggerDagRunOperator

def trigger_ai_on_failure(context):
    TriggerDagRunOperator(
        task_id="trigger_ai",
        trigger_dag_id="dag_incident_response",
        conf={"failed_dag_id": context['dag'].dag_id}
    ).execute(context=context)

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2026, 8, 9),
    'retries': 1,
}

ENV = "dev" 

def create_hdfs_directory(**context):
    client = InsecureClient('http://namenode:9870', user='root')
    path = f'/data/{ENV}/bronze/home_credit/raw/'
    if not client.status(path, strict=False):
        client.makedirs(path)
        print(f"[INGESTION] Directory {path} has been created successfully.")
    else:
        print(f"[INGESTION] Directory {path} already exists.")

def upload_to_hdfs(file_name, **context):
    client = InsecureClient('http://namenode:9870', user='root')
    local_path = f"/opt/airflow/data/{file_name}"
    hdfs_path = f"/data/{ENV}/bronze/home_credit/raw/{file_name}"
    
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"[INGESTION] File not found in local path: {local_path}")

    client.upload(hdfs_path, local_path, overwrite=True, n_threads=1)
    print(f"[INGESTION] File {file_name} uploaded to HDFS successfully.")

def verify_hdfs_files(**context):
    client = InsecureClient('http://namenode:9870', user='root')
    path = f'/data/{ENV}/bronze/home_credit/raw/'
    files = client.list(path, status=True)
    print(f"[INGESTION] Total files found in HDFS: {len(files)}")
    
    for f in files:
        try:
            if isinstance(f, tuple):
                name = f[0]
                if hasattr(f[1], 'length'):
                    size = f[1].length
                elif hasattr(f[1], 'size'):
                    size = f[1].size
                elif isinstance(f[1], dict) and 'length' in f[1]:
                    size = f[1]['length']
                else:
                    size = f[1] if isinstance(f[1], (int, float)) else 0
            else:
                name = f.get('name', 'unknown')
                size = f.get('length', f.get('size', 0))
        except Exception as e:
            print(f"[INGESTION] WARNING: Failed to parse file metadata {f}. Error: {e}")
            continue
        print(f"[INGESTION] File: {name} - Size: {size} bytes")
        
    if len(files) != 10:
        raise Exception(f"[INGESTION] File count validation failed. Found {len(files)} files, expected 10 files.")

CSV_FILES = [
    'application_train.csv',
    'application_test.csv',
    'bureau.csv',
    'bureau_balance.csv',
    'credit_card_balance.csv',
    'installments_payments.csv',
    'POS_CASH_balance.csv',
    'previous_application.csv',
    'sample_submission.csv',
    'HomeCredit_columns_description.csv'
]

dag = DAG(
    'dag_bronze_ingestion',
    default_args=default_args,
    description='Upload CSV to HDFS Bronze via hdfs library',
    schedule='@daily',
    catchup=False,
    on_failure_callback=trigger_ai_on_failure
)

create_dir_task = PythonOperator(
    task_id='create_hdfs_directory',
    python_callable=create_hdfs_directory,
    dag=dag,
)

upload_tasks = []
for f in CSV_FILES:
    task = PythonOperator(
        task_id=f'upload_{f.replace(".", "_")}',
        python_callable=upload_to_hdfs,
        op_kwargs={'file_name': f},
        dag=dag,
    )
    upload_tasks.append(task)

verify_task = PythonOperator(
    task_id='verify_hdfs_files',
    python_callable=verify_hdfs_files,
    dag=dag,
)

create_dir_task >> upload_tasks >> verify_task