FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    streamlit==1.38.0 \
    httpx==0.28.1

COPY ai_systems/webui/streamlit_app.py /app/streamlit_app.py

EXPOSE 8501

CMD ["streamlit", "run", "/app/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
