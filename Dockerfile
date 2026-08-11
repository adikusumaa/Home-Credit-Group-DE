# Gunakan base image Airflow resmi
FROM apache/airflow:2.9.0-python3.11

# Pindah ke user root untuk instalasi package
USER root

# Install package yang diperlukan
RUN python -m pip install --no-cache-dir hdfs requests

# Kembali ke user airflow (opsional, untuk keamanan)
USER airflow