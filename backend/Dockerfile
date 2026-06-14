# IMPORTANTE: construir desde la RAIZ del repo (backend es un paquete + usa dtos/):
#   docker build -f backend/Dockerfile -t onlooker-backend .
FROM python:3-slim
WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY dtos/ ./dtos/
COPY backend/ ./backend/

ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
