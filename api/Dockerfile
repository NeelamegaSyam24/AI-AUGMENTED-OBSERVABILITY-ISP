FROM python:3.10-slim-bookworm

WORKDIR /app

# Install curl for health checks and build tools for scikit-learn
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Create models directory
RUN mkdir -p /app/models

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Train models then start API
CMD ["sh", "-c", "python -m app.ml.train && python -m app.main"]
