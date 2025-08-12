import os
import sys
from datetime import timedelta
from pathlib import Path

# Pour importer src.*
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS

# Modèles & routes
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.repairs import repairs_bp
from src.routes.admin import admin_bp

# ------------------------------------------------------------------------------
# App
# ------------------------------------------------------------------------------
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))

# ------------------------------------------------------------------------------
# Sécurité sessions (cookies cross-site Netlify → Render)
# ------------------------------------------------------------------------------
NETLIFY_ORIGIN = os.environ.get("NETLIFY_ORIGIN", "https://reparetout.netlify.app")

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
app.config.update(
    SESSION_COOKIE_SAMESITE="None",   # obligatoire si front sur autre domaine
    SESSION_COOKIE_SECURE=True,       # cookies envoyés seulement en HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

# ------------------------------------------------------------------------------
# CORS : autoriser Netlify à appeler /api/* avec les cookies
# (⚠️ Une seule initialisation CORS — ne pas la dupliquer)
# ------------------------------------------------------------------------------
ALLOWED_ORIGINS = [NETLIFY_ORIGIN]

CORS(
    app,
    supports_credentials=True,
    origins=ALLOWED_ORIGINS,
    resources={r"/api/*": {"origins": ALLOWED_ORIGINS}},
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"]
)

# ------------------------------------------------------------------------------
# Dossier d'upload d'images (utilisé par /api/repairs)
# ------------------------------------------------------------------------------
UPLOAD_DIR = Path(os.path.join(os.path.dirname(__file__), "static", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.config["UPLOAD_DIR"] = str(UPLOAD_DIR)

# ------------------------------------------------------------------------------
# Base de données
# ------------------------------------------------------------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

    # Admin par défaut (si non existant)
    from src.models.user import User
    admin_user = User.query.filter_by(email="admin@reparetout.com").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@reparetout.com",
            role="admin",
            city="Paris",
            bio="Administrateur de la plateforme RépareTout",
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.commit()

# ------------------------------------------------------------------------------
# Blueprints API
# ------------------------------------------------------------------------------
app.register_blueprint(user_bp,    url_prefix="/api/users")
app.register_blueprint(auth_bp,    url_prefix="/api/auth")
app.register_blueprint(repairs_bp, url_prefix="/api/repairs")
app.register_blueprint(admin_bp,   url_prefix="/api/admin")

# Petit endpoint de santé pour tester vite fait
@app.get("/api/health")
def health():
    return {"status": "ok", "origin": NETLIFY_ORIGIN}, 200

# ------------------------------------------------------------------------------
# Fallback statique (rarement utilisé ici, le front est servi par Netlify)
# ------------------------------------------------------------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    static_folder_path = app.static_folder
    if not static_folder_path or not os.path.exists(static_folder_path):
        index_fallback = os.path.join(os.path.dirname(__file__), "static", "index.html")
        if os.path.exists(index_fallback):
            return send_from_directory(os.path.dirname(index_fallback), "index.html")
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, "index.html")
        return "index.html not found", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
