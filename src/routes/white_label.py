from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.white_label import WhiteLabelConfig
from src.main import db

white_label_bp = Blueprint("white_label", __name__)

@white_label_bp.route("/white_label_config", methods=["POST"])
@jwt_required()
def create_white_label_config():
    user_id = get_jwt_identity()
    data = request.get_json()
    custom_domain = data.get("custom_domain")

    if not custom_domain:
        return jsonify({"msg": "Missing custom domain"}), 400

    if WhiteLabelConfig.query.filter_by(user_id=user_id).first():
        return jsonify({"msg": "White label config already exists for this user"}), 409

    new_config = WhiteLabelConfig(
        user_id=user_id,
        custom_domain=custom_domain,
        logo_url=data.get("logo_url"),
        favicon_url=data.get("favicon_url"),
        primary_color=data.get("primary_color"),
        secondary_color=data.get("secondary_color"),
        contact_email=data.get("contact_email")
    )
    db.session.add(new_config)
    db.session.commit()

    return jsonify({"msg": "White label config created successfully"}), 201

@white_label_bp.route("/white_label_config", methods=["GET"])
@jwt_required()
def get_white_label_config():
    user_id = get_jwt_identity()
    config = WhiteLabelConfig.query.filter_by(user_id=user_id).first()

    if not config:
        return jsonify({"msg": "White label config not found"}), 404

    return jsonify({
        "id": config.id,
        "user_id": config.user_id,
        "custom_domain": config.custom_domain,
        "domain_verified": config.domain_verified,
        "logo_url": config.logo_url,
        "favicon_url": config.favicon_url,
        "primary_color": config.primary_color,
        "secondary_color": config.secondary_color,
        "contact_email": config.contact_email,
        "created_at": config.created_at.isoformat()
    }), 200

@white_label_bp.route("/white_label_config", methods=["PUT"])
@jwt_required()
def update_white_label_config():
    user_id = get_jwt_identity()
    config = WhiteLabelConfig.query.filter_by(user_id=user_id).first()

    if not config:
        return jsonify({"msg": "White label config not found"}), 404

    data = request.get_json()
    config.custom_domain = data.get("custom_domain", config.custom_domain)
    config.logo_url = data.get("logo_url", config.logo_url)
    config.favicon_url = data.get("favicon_url", config.favicon_url)
    config.primary_color = data.get("primary_color", config.primary_color)
    config.secondary_color = data.get("secondary_color", config.secondary_color)
    config.contact_email = data.get("contact_email", config.contact_email)
    config.domain_verified = data.get("domain_verified", config.domain_verified)

    db.session.commit()

    return jsonify({"msg": "White label config updated successfully"}), 200

@white_label_bp.route("/white_label_config", methods=["DELETE"])
@jwt_required()
def delete_white_label_config():
    user_id = get_jwt_identity()
    config = WhiteLabelConfig.query.filter_by(user_id=user_id).first()

    if not config:
        return jsonify({"msg": "White label config not found"}), 404

    db.session.delete(config)
    db.session.commit()

    return jsonify({"msg": "White label config deleted successfully"}), 200
