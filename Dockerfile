FROM python:3.13-slim

WORKDIR /app

# Copie uniquement requirements.txt d'abord pour tirer parti du cache Docker
COPY "requirements.txt" ./requirements.txt

# Installation des dépendances système nécessaires uniquement
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste de l'application
COPY . .

CMD ["python", "main.py"]
