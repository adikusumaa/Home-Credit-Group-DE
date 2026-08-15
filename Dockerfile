FROM apache/airflow:2.9.0-python3.11

USER root

RUN apt-get update && apt-get install -y git && apt-get clean

# Hanya install library yang benar-benar dibutuhkan Airflow
RUN python -m pip install --no-cache-dir hdfs requests elasticsearch gitpython pydantic pyyaml

USER airflow