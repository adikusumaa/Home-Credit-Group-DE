from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'dag_gold_aggregation',
    default_args=default_args,
    description='Build Gold Layer from Silver tables',
    schedule_interval=None,
    catchup=False,
    tags=['gold'],
) as dag:
    gold_task = SparkSubmitOperator(
        task_id='gold_aggregation',
        application='jobs/pyspark/Application_g.py',  # sesuaikan path
        conn_id='spark_default',
        verbose=True,
        conf={'spark.sql.hive.convertMetastoreParquet': 'false'},
        name='Gold_Aggregation',
    )
    gold_task