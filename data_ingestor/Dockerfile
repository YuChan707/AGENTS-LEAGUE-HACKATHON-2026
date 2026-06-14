FROM python:3-slim
WORKDIR /app
COPY . .
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]