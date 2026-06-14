# IMPORTANTE: construir desde la RAIZ del repo (necesita el paquete dtos/):
#   docker build -f data_processor/Dockerfile -t onlooker-data-processor .
FROM python:3-slim
WORKDIR /app

COPY data_processor/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# dtos/ es compartido (data CRUDA + entidades de comportamiento) -> se copia.
COPY dtos/ ./dtos/
COPY data_processor/ ./data_processor/

ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Transporte LLM por defecto dentro del contenedor (override por env).
ENV LLM_TRANSPORT=auto

CMD ["python", "-m", "data_processor"]
