FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config/ config/
COPY schemas/ schemas/
COPY providers/ providers/
COPY main.py .

RUN mkdir -p /app/audio_cache

EXPOSE 8103

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8103"]
