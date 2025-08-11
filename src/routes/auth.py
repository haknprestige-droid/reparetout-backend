from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.services.email_service import email_service
from werkzeug.security import check_password_hash
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validation des données
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Tous les champs sont obligatoires'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'error': 'Format d\'email invalide'}), 400
        
        if len(data['password']) < 6:
            return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caractères'}), 400
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Un compte avec cet email existe déjà'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Ce nom d\'utilisateur est déjà pris'}), 400
        
        # Créer le nouvel utilisateur
        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'client'),
            city=data.get('city', ''),
            bio=data.get('bio', ''),
            phone=data.get('phone', '')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Envoyer l'email de bienvenue
        try:
            email_service.send_welcome_email(user)
        except Exception as e:
            print(f"Erreur envoi email de bienvenue: {e}")
        
        # Connecter automatiquement l'utilisateur
        session['user_id'] = user.id
        session['user_role'] = user.role
        
        return jsonify({
            'message': 'Inscription réussie ! Un email de bienvenue vous a été envoyé.',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de l\'inscription'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email et mot de passe requis'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
        
        if user.status == 'suspended':
            return jsonify({'error': 'Compte suspendu'}), 403
        
        session['user_id'] = user.id
        session['user_role'] = user.role
        
        return jsonify({
            'message': 'Connexion réussie',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la connexion'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Déconnexion réussie'}), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Non connecté'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'error': 'Utilisateur introuvable'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Non connecté'}), 401
    
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Utilisateur introuvable'}), 404
        
        data = request.get_json()
        
        # Mise à jour des champs autorisés
        if 'username' in data:
            # Vérifier l'unicité
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.id != user.id:
                return jsonify({'error': 'Ce nom d\'utilisateur est déjà pris'}), 400
            user.username = data['username']
        
        if 'city' in data:
            user.city = data['city']
        if 'bio' in data:
            user.bio = data['bio']
        if 'phone' in data:
            user.phone = data['phone']
        if 'role' in data and data['role'] in ['client', 'repairer']:
            user.role = data['role']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profil mis à jour',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la mise à jour'}), 500

