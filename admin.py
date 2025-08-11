from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, RepairRequest, Quote
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def require_admin():
    if 'user_id' not in session:
        return jsonify({'error': 'Connexion requise'}), 401
    
    user = User.query.get(session['user_id'])
    if not user or user.role != 'admin':
        return jsonify({'error': 'Accès administrateur requis'}), 403
    
    return None

@admin_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    
    try:
        # Statistiques générales
        total_users = User.query.count()
        total_requests = RepairRequest.query.count()
        total_quotes = Quote.query.count()
        
        # Demandes par statut
        requests_by_status = {}
        statuses = ['open', 'quoted', 'accepted', 'in_progress', 'done', 'closed']
        for status in statuses:
            count = RepairRequest.query.filter_by(status=status).count()
            requests_by_status[status] = count
        
        # Utilisateurs par rôle
        users_by_role = {}
        roles = ['client', 'repairer', 'admin']
        for role in roles:
            count = User.query.filter_by(role=role).count()
            users_by_role[role] = count
        
        # Activité récente (7 derniers jours)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_users = User.query.filter(User.created_at >= week_ago).count()
        recent_requests = RepairRequest.query.filter(RepairRequest.created_at >= week_ago).count()
        recent_quotes = Quote.query.filter(Quote.created_at >= week_ago).count()
        
        return jsonify({
            'stats': {
                'total_users': total_users,
                'total_requests': total_requests,
                'total_quotes': total_quotes,
                'requests_by_status': requests_by_status,
                'users_by_role': users_by_role,
                'recent_activity': {
                    'new_users': recent_users,
                    'new_requests': recent_requests,
                    'new_quotes': recent_quotes
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des statistiques'}), 500

@admin_bp.route('/users', methods=['GET'])
def get_all_users():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        role_filter = request.args.get('role')
        status_filter = request.args.get('status')
        
        query = User.query
        
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        if status_filter:
            query = query.filter(User.status == status_filter)
        
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des utilisateurs'}), 500

@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
def update_user_status(user_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'error': 'Statut requis'}), 400
        
        if data['status'] not in ['active', 'suspended', 'pending_verification']:
            return jsonify({'error': 'Statut invalide'}), 400
        
        user.status = data['status']
        
        if data['status'] == 'active' and not user.verified_at:
            user.verified_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Statut utilisateur mis à jour',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la mise à jour du statut'}), 500

@admin_bp.route('/requests', methods=['GET'])
def get_all_requests():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        category_filter = request.args.get('category')
        
        query = RepairRequest.query
        
        if status_filter:
            query = query.filter(RepairRequest.status == status_filter)
        
        if category_filter:
            query = query.filter(RepairRequest.category == category_filter)
        
        requests = query.order_by(RepairRequest.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'requests': [req.to_dict() for req in requests.items],
            'total': requests.total,
            'pages': requests.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des demandes'}), 500

@admin_bp.route('/requests/<int:request_id>/status', methods=['PUT'])
def update_request_status(request_id):
    auth_error = require_admin()
    if auth_error:
        return auth_error
    
    try:
        repair_request = RepairRequest.query.get_or_404(request_id)
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'error': 'Statut requis'}), 400
        
        valid_statuses = ['open', 'quoted', 'accepted', 'in_progress', 'done', 'rated', 'closed']
        if data['status'] not in valid_statuses:
            return jsonify({'error': 'Statut invalide'}), 400
        
        repair_request.status = data['status']
        repair_request.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Statut de la demande mis à jour',
            'request': repair_request.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la mise à jour du statut'}), 500

@admin_bp.route('/quotes', methods=['GET'])
def get_all_quotes():
    auth_error = require_admin()
    if auth_error:
        return auth_error
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        
        query = Quote.query
        
        if status_filter:
            query = query.filter(Quote.status == status_filter)
        
        quotes = query.order_by(Quote.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'quotes': [quote.to_dict() for quote in quotes.items],
            'total': quotes.total,
            'pages': quotes.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erreur lors de la récupération des devis'}), 500

