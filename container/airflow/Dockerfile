FROM apache/airflow:2.9.3

# Install system libraries required by PyHive (dbt-spark thrift driver)
USER root
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        libsasl2-dev \
        libsasl2-modules \
        libsasl2-modules-gssapi-mit \
        gcc \
        build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow

# dbt-spark (PyHive transport = Spark Thrift Server JDBC)
# astro-cosmos = optional dbt-native task graph in Airflow UI
COPY requirements.txt /tmp/airflow-requirements.txt
RUN pip install --no-cache-dir -r /tmp/airflow-requirements.txt
