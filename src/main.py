import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.repairs import repairs_bp
from src.routes.admin import admin_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
import os
from datetime import timedelta
from flask_cors import CORS

# Clé secrète depuis l'environnement (Render)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')

# Autoriser le front Netlify à envoyer/recevoir le cookie de session
NETLIFY_ORIGIN = "https://reparetout.netlify.app"   # ← remplace si ton URL Netlify est différente
CORS(app,
     supports_credentials=True,
     resources={r"/api/*": {"origins": [NETLIFY_ORIGIN]}})

# Cookies de session compatibles cross-site (Netlify → Render)
app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)


# Configuration CORS
CORS(app, supports_credentials=True)

# Enregistrement des blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(repairs_bp, url_prefix='/api/repairs')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    
    # Créer un utilisateur admin par défaut
    from src.models.user import User
    admin_user = User.query.filter_by(email='admin@reparetout.com').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@reparetout.com',
            role='admin',
            city='Paris',
            bio='Administrateur de la plateforme RépareTout'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
