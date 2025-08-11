# RépareTout - Guide de Déploiement

## 📋 Description
RépareTout est une plateforme full-stack de mise en relation entre particuliers et réparateurs d'objets. L'application permet aux clients de publier des demandes de réparation et aux réparateurs de proposer leurs services.

## 🏗️ Architecture
- **Frontend**: React avec Tailwind CSS et shadcn/ui
- **Backend**: Flask avec SQLAlchemy
- **Base de données**: SQLite (développement) / PostgreSQL (production recommandée)
- **Notifications**: Service d'email intégré

## 🚀 Déploiement

### Option 1: Déploiement Full-Stack sur Railway/Render
1. **Créer un compte sur Railway.app ou Render.com**
2. **Connecter votre repository GitHub**
3. **Configurer les variables d'environnement**:
   - `EMAIL_PASSWORD`: Mot de passe d'application Gmail pour haknprestige@gmail.com
   - `FLASK_ENV`: production
4. **Railway détectera automatiquement le Dockerfile ou utilisera le requirements.txt**

### Option 2: Déploiement séparé Frontend/Backend

#### Frontend (Netlify)
1. **Build du frontend**:
   ```bash
   cd reparetout
   npm run build
   ```
2. **Déployer le dossier `dist/` sur Netlify**
3. **Configurer les redirections** (fichier `_redirects` dans `dist/`):
   ```
   /api/* https://votre-backend-url.com/api/:splat 200
   /* /index.html 200
   ```

#### Backend (Railway/Render/Heroku)
1. **Déployer le dossier `reparetout-backend/`**
2. **Configurer les variables d'environnement**
3. **Mettre à jour l'URL du backend dans le frontend**

## 🔧 Configuration Email

### Configuration Gmail
1. **Activer l'authentification à 2 facteurs** sur haknprestige@gmail.com
2. **Générer un mot de passe d'application**:
   - Aller dans Paramètres Google > Sécurité
   - Mots de passe d'application
   - Créer un nouveau mot de passe pour "RépareTout"
3. **Utiliser ce mot de passe dans la variable d'environnement `EMAIL_PASSWORD`**

## 📧 Notifications Email Configurées

### Inscriptions
- Email de bienvenue automatique aux nouveaux utilisateurs
- Notification à l'admin (haknprestige@gmail.com) pour chaque inscription

### Demandes de réparation
- Notification aux réparateurs pertinents lors de nouvelles demandes
- Notification à l'admin pour chaque nouvelle demande

### Devis
- Notification au client lors de la réception d'un devis
- Notification à l'admin pour chaque devis envoyé
- Notifications lors de l'acceptation d'un devis (client + réparateur + admin)

## 🗄️ Base de Données

### Modèles principaux
- **User**: Utilisateurs (clients, réparateurs, admin)
- **RepairRequest**: Demandes de réparation
- **Quote**: Devis des réparateurs
- **RepairImage**: Images des objets à réparer

### Compte Admin par défaut
- Email: admin@reparetout.com
- Mot de passe: admin123
- **⚠️ À changer en production !**

## 🎨 Fonctionnalités

### Pour les Clients
- Inscription et connexion sécurisées
- Création de demandes de réparation avec photos
- Réception et comparaison de devis
- Suivi des réparations
- Profil utilisateur complet

### Pour les Réparateurs
- Inscription avec vérification
- Consultation des demandes par catégorie/localisation
- Envoi de devis détaillés
- Gestion des interventions

### Pour les Administrateurs
- Tableau de bord complet avec statistiques
- Gestion des utilisateurs et vérifications
- Modération des demandes
- Suivi des activités
- Notifications email automatiques

## 🔒 Sécurité
- Mots de passe hachés avec Werkzeug
- Sessions sécurisées
- Validation des données côté serveur
- Protection CORS configurée

## 📱 Interface
- Design responsive (mobile-first)
- Couleurs: Beige (#F5F5DC) et Vert foncé (#2D5016)
- Interface intuitive avec animations
- Accessibilité optimisée

## 🛠️ Développement Local

### Prérequis
- Python 3.11+
- Node.js 20+
- npm/yarn

### Installation
1. **Backend**:
   ```bash
   cd reparetout-backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   python src/main.py
   ```

2. **Frontend**:
   ```bash
   cd reparetout
   npm install
   npm run dev
   ```

## 📞 Support
Pour toute question technique, contacter haknprestige@gmail.com

## 📄 Licence
Propriétaire - Tous droits réservés

