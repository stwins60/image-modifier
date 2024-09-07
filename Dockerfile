FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM python:3.12-slim AS production

WORKDIR /app

COPY --from=base /app .
COPY --from=base /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

EXPOSE 8501
EXPOSE 8012

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["python3", "-m", "streamlit", "run", "app.py", "--server.enableCORS", "true", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats", "false"]