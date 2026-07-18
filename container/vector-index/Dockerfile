FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    qdrant-client==1.9.0 \
    sentence-transformers==2.7.0 \
    pyhive==0.7.0 \
    thrift-sasl==0.4.3 \
    pure-sasl==0.6.2 \
    thrift==0.20.0

COPY data_platform/vector_index/indexer.py /app/indexer.py

CMD ["python", "/app/indexer.py"]
