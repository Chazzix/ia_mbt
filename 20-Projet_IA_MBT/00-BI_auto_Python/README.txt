# Projet Dockerisé Gradio + PostgreSQL

Ce projet permet de générer des documents PDF à partir d’un template Word, d’envoyer des e-mails via Outlook, et d’enregistrer les données dans une base PostgreSQL, le tout via une interface web Gradio.

## 📁 Structure du projet

- `app/main.py` : Script principal avec l’interface Gradio.
- `app/.env` : Variables d’environnement pour la connexion à la base.
- `app/init.sql` : Script d’initialisation de la base PostgreSQL.
- `template_bon-intervention.docx` : Modèle Word utilisé pour générer les bons d’intervention.
- `Dockerfile` : Image Docker de l’application.
- `docker-compose.yml` : Lancement des services (PostgreSQL, pgAdmin, application).
- `requirements.txt` : Dépendances Python.

## ⚙️ Prérequis

- Docker
- Docker Compose

## 🚀 Lancement du projet

1. Clonez ou téléchargez ce projet :
   ```bash
   git clone <url-du-projet>
   cd mon-app
   ```