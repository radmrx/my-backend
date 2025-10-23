FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg build-essential libsndfile1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/
COPY intro.mp4 /app/intro.mp4
COPY outro.mp4 /app/outro.mp4

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
