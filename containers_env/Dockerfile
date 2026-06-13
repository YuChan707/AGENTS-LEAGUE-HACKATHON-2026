# Backend container for the OnLooker FastAPI app.
# Scaffold: builds from the repo root context (see docker-compose.yml).

FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY backend ./backend
COPY dtos ./dtos
COPY data_processor ./data_processor
COPY data_ingestor ./data_ingestor

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
