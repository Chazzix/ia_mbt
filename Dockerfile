FROM python:3.13-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && pip install --no-cache-dir -r requirements.txt

CMD ["python", "app/main.py"]