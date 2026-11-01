FROM python:3.10-slim-bookworm

WORKDIR /app

COPY api/requirements.txt /app/api-requirements.txt
COPY simulator/requirements.txt /app/simulator-requirements.txt
RUN pip install --no-cache-dir -r /app/api-requirements.txt -r /app/simulator-requirements.txt

COPY api/app/ /app/api/app/
COPY simulator/app/ /app/simulator/app/
COPY deploy/run_services.py /app/deploy/run_services.py

ENV PYTHONUNBUFFERED=1
ENV ML_MODEL_DIR=/app/api/app/models

EXPOSE 10000

CMD ["python", "/app/deploy/run_services.py"]
