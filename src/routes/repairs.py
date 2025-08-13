import os
from uuid import uuid4
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename

from src.models.user import db, User, RepairRequest  # + Quote si besoin (pas ici)

repairs_bp = Blueprint("repairs", __name__)

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}
MAX_BYTES = 3 * 1024 * 1024  # ~3 Mo

def _ensure_upload_dir():
    updir = current_app.config.get("UPLOAD_DIR")
    if not updir:
        # dossier fallback si non configuré dans main.py
        updir = os.path.join(os.path.dirname(current_app.root_path), "static", "uploads")
        os.makedirs(updir, exist_ok=True)
        current_app.config["UPLOAD_DIR"] = updir
    return updir

def _parse_budget(value: str) -> float:
    if not value:
        return 0.0
    v = str(value).strip().replace("€", "").replace(" ", "").replace(",", ".")
    try:
        return round(float(v), 2)
    except Exception:
        return 0.0

def _require_login():
    if "user_id" not in session:
        return jsonify({"error": "Connexion requise"}), 401
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 401
    return user

# ---------------------------------------------------------------------
# POST /api/repairs/requests : créer une demande avec photo (FormData)
# ---------------------------------------------------------------------

@repairs_bp.route("/requests", methods=["POST"])
def create_request():
    user = _require_login()
    if not isinstance(user, User):
        return user  # (json, status) de _require_login

    try:
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        category = (request.form.get("category") or "").strip()  # ex: "electronics"
        city = (request.form.get("city") or "").strip()
        budget = _parse_budget(request.form.get("budget"))

        # validations simples
        if not title or not description or not category or not city:
            return jsonify({"error": "Champs manquants"}), 400

        # fichier
        file = request.files.get("photo")
        if not file or file.filename == "":
            return jsonify({"error": "Photo obligatoire"}), 400

        filename = secure_filename(file.filename)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXT:
            return jsonify({"error": "Format image non supporté (jpg, jpeg, png, webp)"}), 415

        # limite taille (si l’en-tête est présent) — le backend Render coupe parfois, donc on garde souple
        clen = request.content_length or 0
        if clen and clen > MAX_BYTES + 512_000:  # petite marge
            return jsonify({"error": "Image trop volumineuse (> 3 Mo)"}), 413

        # enregistrer le fichier
        updir = _ensure_upload_dir()
        unique = f"{uuid4().hex}.{ext}"
        dst = os.path.join(updir, unique)
        file.save(dst)

        # chemin public (servi par /static/uploads/... sur Netlify ou Render)
        public_path = f"/static/uploads/{unique}"

        # créer l’objet SQLAlchemy
        rr = RepairRequest(
            title=title,
            description=description,
            category=category,
            city=city,
            status="open",
            user_id=user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # budget unique → on remplit ce qui existe dans le modèle
        if hasattr(RepairRequest, "budget"):
            rr.budget = budget
        if hasattr(RepairRequest, "budget_min"):
            rr.budget_min = budget
        if hasattr(RepairRequest, "budget_max"):
            rr.budget_max = budget

        # image/chemin (selon nom de colonne)
        if hasattr(RepairRequest, "image"):
            rr.image = public_path
        elif hasattr(RepairRequest, "photo_url"):
            rr.photo_url = public_path
        elif hasattr(RepairRequest, "image_url"):
            rr.image_url = public_path

        db.session.add(rr)
        db.session.commit()

        # to_dict() si dispo, sinon JSON minimal
        if hasattr(rr, "to_dict"):
            payload = rr.to_dict()
        else:
            payload = {
                "id": rr.id,
                "title": rr.title,
                "description": rr.description,
                "category": rr.category,
                "city": rr.city,
                "budget": getattr(rr, "budget", None),
                "budget_min": getattr(rr, "budget_min", None),
                "budget_max": getattr(rr, "budget_max", None),
                "image": getattr(rr, "image", None) or getattr(rr, "photo_url", None) or getattr(rr, "image_url", None),
                "status": rr.status,
                "user_id": rr.user_id,
                "created_at": rr.created_at.isoformat() if rr.created_at else None,
            }

        return jsonify({"message": "Demande créée", "request": payload}), 201

    except Exception as e:
        current_app.logger.exception("Erreur création demande")
        db.session.rollback()
        # 500 → fera apparaître un 502 côté proxy si l’erreur n’est pas catchée.
        return jsonify({"error": "Erreur serveur pendant la création"}), 500


# ---------------------------------------------------------------------
# GET /api/repairs/requests/mine : lister mes demandes
# ---------------------------------------------------------------------
@repairs_bp.route("/requests/mine", methods=["GET"])
def my_requests():
    user = _require_login()
    if not isinstance(user, User):
        return user

    q = RepairRequest.query.filter_by(user_id=user.id).order_by(RepairRequest.created_at.desc())
    items = []
    for r in q.all():
        if hasattr(r, "to_dict"):
            items.append(r.to_dict())
        else:
            items.append({
                "id": r.id,
                "title": r.title,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "image": getattr(r, "image", None) or getattr(r, "photo_url", None) or getattr(r, "image_url", None),
            })
    return jsonify({"items": items}), 200
