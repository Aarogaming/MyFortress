FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOMEGATEWAY_HOST=0.0.0.0 \
    HOMEGATEWAY_PORT=8100

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY gateway ./gateway

EXPOSE 8100

CMD ["uvicorn", "gateway.api.server:app", "--host", "0.0.0.0", "--port", "8100", "--log-level", "info"]
