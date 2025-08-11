FROM python:3.11-slim

WORKDIR /app

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer le dossier de base de données
RUN mkdir -p src/database

# Exposer le port
EXPOSE 5000

# Variables d'environnement
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Commande de démarrage
CMD ["python", "src/main.py"]

