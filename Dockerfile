FROM apache/airflow:2.9.0-python3.11
USER root
RUN python -m pip install --no-cache-dir hdfs requests
USER airflow