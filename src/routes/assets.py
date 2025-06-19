from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.asset import Asset
from src.main import db

assets_bp = Blueprint("assets", __name__)

@assets_bp.route("/assets", methods=["POST"])
@jwt_required()
def upload_asset():
    user_id = get_jwt_identity()
    # In a real application, you would handle file uploads here
    # For now, we'll simulate by taking a file_path and asset_name
    data = request.get_json()
    asset_name = data.get("asset_name")
    asset_type = data.get("asset_type")
    storage_provider = data.get("storage_provider")
    file_path = data.get("file_path")
    project_id = data.get("project_id")

    if not all([asset_name, asset_type, storage_provider, file_path]):
        return jsonify({"msg": "Missing required asset data"}), 400

    new_asset = Asset(
        user_id=user_id,
        project_id=project_id,
        asset_name=asset_name,
        asset_type=asset_type,
        storage_provider=storage_provider,
        file_path=file_path,
        asset_metadata={}
    )
    db.session.add(new_asset)
    db.session.commit()

    return jsonify({"msg": "Asset uploaded successfully", "asset_id": new_asset.id}), 201

@assets_bp.route("/assets", methods=["GET"])
@jwt_required()
def get_assets():
    user_id = get_jwt_identity()
    assets = Asset.query.filter_by(user_id=user_id).all()
    return jsonify([
        {
            "id": a.id,
            "asset_name": a.asset_name,
            "asset_type": a.asset_type,
            "file_path": a.file_path,
            "created_at": a.created_at.isoformat()
        } for a in assets
    ]), 200

@assets_bp.route("/assets/<int:asset_id>", methods=["GET"])
@jwt_required()
def get_asset(asset_id):
    user_id = get_jwt_identity()
    asset = Asset.query.filter_by(id=asset_id, user_id=user_id).first()

    if not asset:
        return jsonify({"msg": "Asset not found"}), 404

    return jsonify({
        "id": asset.id,
        "asset_name": asset.asset_name,
        "asset_type": asset.asset_type,
        "storage_provider": asset.storage_provider,
        "file_path": asset.file_path,
        "asset_metadata": asset.asset_metadata,
        "created_at": asset.created_at.isoformat()
    }), 200

@assets_bp.route("/assets/<int:asset_id>", methods=["PUT"])
@jwt_required()
def update_asset(asset_id):
    user_id = get_jwt_identity()
    asset = Asset.query.filter_by(id=asset_id, user_id=user_id).first()

    if not asset:
        return jsonify({"msg": "Asset not found"}), 404

    data = request.get_json()
    asset.asset_name = data.get("asset_name", asset.asset_name)
    asset.asset_type = data.get("asset_type", asset.asset_type)
    asset.storage_provider = data.get("storage_provider", asset.storage_provider)
    asset.file_path = data.get("file_path", asset.file_path)
    asset.asset_metadata = data.get("asset_metadata", asset.asset_metadata)

    db.session.commit()

    return jsonify({"msg": "Asset updated successfully"}), 200

@assets_bp.route("/assets/<int:asset_id>", methods=["DELETE"])
@jwt_required()
def delete_asset(asset_id):
    user_id = get_jwt_identity()
    asset = Asset.query.filter_by(id=asset_id, user_id=user_id).first()

    if not asset:
        return jsonify({"msg": "Asset not found"}), 404

    db.session.delete(asset)
    db.session.commit()

    return jsonify({"msg": "Asset deleted successfully"}), 200
