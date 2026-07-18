FROM python:3.12-slim

WORKDIR /feature_store

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl default-jre-headless procps \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV PYSPARK_SUBMIT_ARGS="--packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.apache.iceberg:iceberg-aws-bundle:1.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 pyspark-shell"

RUN pip install --no-cache-dir "feast[spark,redis,aws]==0.40.0" "pyspark==3.5.1"

COPY data_platform/feature_store/ /feature_store/

EXPOSE 6566

CMD ["feast", "-c", "/feature_store", "serve", "--host", "0.0.0.0", "--port", "6566"]
