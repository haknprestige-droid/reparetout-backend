from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, RepairRequest, Quote
from src.services.email_service import email_service
from datetime import datetime

repairs_bp = Blueprint('repairs', __name__)

@repairs_bp.route('/requests', methods=['GET'])
def get_repair_requests():
    try:
        # Paramètres de filtrage
        category = request.args.get('category')
        city = request.args.get('city')
        status = request.args.get('status', 'open')
        search = request.args.get('search', '')
        
        query = RepairRequest.query
        
        # Filtres
        if category and category != 'all':
            query = query.filter(RepairRequest.category == category)
        
        if city:
            query = query.filter(RepairRequest.city.ilike(f'%{city}%'))
        
        if status != 'all':
            query = query.filter(RepairRequest.status == status)
        
        if search:
            query = query.filter(
                db.or_(
                    RepairRequest.title.ilike(f'%{search}%'),
                    RepairRequest.description.ilike(f'%{search}%')
                )
            )
        
        # Ordre par date de création (plus récent en premier)
        requests = query.order_by(RepairRequest.created_at.desc()).all()
        
        return jsonify({
            'requests': [req.to_dict() for req in requests],
            'total': len(requests)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des demandes'}), 500

@repairs_bp.route('/requests', methods=['POST'])
def create_repair_request():
    if 'user_id' not in session:
        return jsonify({'error': 'Connexion requise'}), 401
    
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['title', 'description', 'category', 'city']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Le champ {field} est obligatoire'}), 400
        
        # Créer la demande
        repair_request = RepairRequest(
            title=data['title'],
            description=data['description'],
            category=data['category'],
            subcategory=data.get('subcategory'),
            city=data['city'],
            address=data.get('address'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            budget_min=data.get('budget_min'),
            budget_max=data.get('budget_max'),
            visibility=data.get('visibility', 'public'),
            client_id=session['user_id']
        )
        
        db.session.add(repair_request)
        db.session.commit()
        
        # Notifier les réparateurs pertinents
        try:
            repairers = User.query.filter_by(role='repairer', status='active').all()
            if repairers:
                email_service.send_new_request_notification(repair_request, repairers)
        except Exception as e:
            print(f"Erreur envoi notification réparateurs: {e}")
        
        # Notifier l'admin
        try:
            email_service.send_admin_alert(
                "Nouvelle demande de réparation",
                f"Nouvelle demande créée par {repair_request.client.username}: {repair_request.title}"
            )
        except Exception as e:
            print(f"Erreur notification admin: {e}")
        
        return jsonify({
            'message': 'Demande créée avec succès',
            'request': repair_request.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la création de la demande'}), 500

@repairs_bp.route('/requests/<int:request_id>', methods=['GET'])
def get_repair_request(request_id):
    try:
        repair_request = RepairRequest.query.get_or_404(request_id)
        return jsonify({'request': repair_request.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': 'Demande introuvable'}), 404

@repairs_bp.route('/requests/<int:request_id>/quotes', methods=['POST'])
def create_quote(request_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Connexion requise'}), 401
    
    try:
        # Vérifier que l'utilisateur est un réparateur
        user = User.query.get(session['user_id'])
        if user.role not in ['repairer', 'admin']:
            return jsonify({'error': 'Seuls les réparateurs peuvent faire des devis'}), 403
        
        repair_request = RepairRequest.query.get_or_404(request_id)
        
        if repair_request.status != 'open':
            return jsonify({'error': 'Cette demande n\'accepte plus de devis'}), 400
        
        data = request.get_json()
        
        # Validation
        if not data.get('price') or not data.get('estimated_duration'):
            return jsonify({'error': 'Prix et durée estimée sont obligatoires'}), 400
        
        # Créer le devis
        quote = Quote(
            repair_request_id=request_id,
            repairer_id=session['user_id'],
            price=int(data['price'] * 100),  # Convertir en centimes
            estimated_duration=data['estimated_duration'],
            conditions=data.get('conditions', ''),
            location_type=data.get('location_type', 'domicile')
        )
        
        db.session.add(quote)
        
        # Mettre à jour le statut de la demande
        if repair_request.status == 'open':
            repair_request.status = 'quoted'
        
        db.session.commit()
        
        # Notifier le client du nouveau devis
        try:
            email_service.send_quote_notification(quote)
        except Exception as e:
            print(f"Erreur envoi notification devis: {e}")
        
        return jsonify({
            'message': 'Devis envoyé avec succès',
            'quote': quote.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de l\'envoi du devis'}), 500

@repairs_bp.route('/quotes/<int:quote_id>/accept', methods=['POST'])
def accept_quote(quote_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Connexion requise'}), 401
    
    try:
        quote = Quote.query.get_or_404(quote_id)
        repair_request = quote.repair_request
        
        # Vérifier que l'utilisateur est le client de la demande
        if repair_request.client_id != session['user_id']:
            return jsonify({'error': 'Non autorisé'}), 403
        
        # Accepter le devis
        quote.status = 'accepted'
        repair_request.accepted_quote_id = quote_id
        repair_request.status = 'accepted'
        
        # Rejeter les autres devis
        other_quotes = Quote.query.filter_by(repair_request_id=repair_request.id).filter(Quote.id != quote_id).all()
        for other_quote in other_quotes:
            other_quote.status = 'rejected'
        
        db.session.commit()
        
        # Notifier les parties concernées
        try:
            email_service.send_quote_accepted_notification(quote)
        except Exception as e:
            print(f"Erreur envoi notification acceptation: {e}")
        
        return jsonify({
            'message': 'Devis accepté',
            'quote': quote.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de l\'acceptation du devis'}), 500

@repairs_bp.route('/my-requests', methods=['GET'])
def get_my_requests():
    if 'user_id' not in session:
        return jsonify({'error': 'Connexion requise'}), 401
    
    try:
        requests = RepairRequest.query.filter_by(client_id=session['user_id']).order_by(RepairRequest.created_at.desc()).all()
        return jsonify({
            'requests': [req.to_dict() for req in requests]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des demandes'}), 500

@repairs_bp.route('/my-quotes', methods=['GET'])
def get_my_quotes():
    if 'user_id' not in session:
        return jsonify({'error': 'Connexion requise'}), 401
    
    try:
        quotes = Quote.query.filter_by(repairer_id=session['user_id']).order_by(Quote.created_at.desc()).all()
        return jsonify({
            'quotes': [quote.to_dict() for quote in quotes]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des devis'}), 500

