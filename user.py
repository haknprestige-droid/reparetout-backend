from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='client')  # client, repairer, admin
    status = db.Column(db.String(20), nullable=False, default='active')  # active, suspended, pending_verification
    city = db.Column(db.String(100))
    bio = db.Column(db.Text)
    phone = db.Column(db.String(20))
    avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    
    # Relations
    repair_requests = db.relationship('RepairRequest', backref='client', lazy=True, foreign_keys='RepairRequest.client_id')
    quotes = db.relationship('Quote', backref='repairer', lazy=True, foreign_keys='Quote.repairer_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'city': self.city,
            'bio': self.bio,
            'phone': self.phone,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None
        }

class RepairRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50))
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    budget_min = db.Column(db.Integer)
    budget_max = db.Column(db.Integer)
    status = db.Column(db.String(20), nullable=False, default='open')  # draft, open, quoted, accepted, in_progress, done, rated, closed
    visibility = db.Column(db.String(20), nullable=False, default='public')  # public, private
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    accepted_quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    quotes = db.relationship('Quote', backref='repair_request', lazy=True, foreign_keys='Quote.repair_request_id')
    images = db.relationship('RepairImage', backref='repair_request', lazy=True)

    def __repr__(self):
        return f'<RepairRequest {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'subcategory': self.subcategory,
            'city': self.city,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'budget_min': self.budget_min,
            'budget_max': self.budget_max,
            'status': self.status,
            'visibility': self.visibility,
            'client_id': self.client_id,
            'accepted_quote_id': self.accepted_quote_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'quotes_count': len(self.quotes),
            'client': self.client.to_dict() if self.client else None
        }

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repair_request_id = db.Column(db.Integer, db.ForeignKey('repair_request.id'), nullable=False)
    repairer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    price = db.Column(db.Integer, nullable=False)  # en centimes
    estimated_duration = db.Column(db.String(100))
    conditions = db.Column(db.Text)
    location_type = db.Column(db.String(20), nullable=False, default='domicile')  # domicile, atelier
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Quote {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'repair_request_id': self.repair_request_id,
            'repairer_id': self.repairer_id,
            'price': self.price,
            'estimated_duration': self.estimated_duration,
            'conditions': self.conditions,
            'location_type': self.location_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'repairer': self.repairer.to_dict() if self.repairer else None
        }

class RepairImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repair_request_id = db.Column(db.Integer, db.ForeignKey('repair_request.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'repair_request_id': self.repair_request_id,
            'filename': self.filename,
            'url': self.url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

