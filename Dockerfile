FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# On donne les droits de lecture/exécution sur les fichiers de bibliothèque
RUN chmod +x libraries/*.so 2>/dev/null || true

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860
CMD ["python", "main.py"]