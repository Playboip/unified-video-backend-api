from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.project import Project
from src.main import db

projects_bp = Blueprint("projects", __name__)

@projects_bp.route("/projects", methods=["POST"])
@jwt_required()
def create_project():
    user_id = get_jwt_identity()
    data = request.get_json()
    project_name = data.get("project_name")
    project_type = data.get("project_type")

    if not project_name or not project_type:
        return jsonify({"msg": "Missing project name or type"}), 400

    new_project = Project(
        user_id=user_id,
        project_name=project_name,
        project_type=project_type,
        project_data={}
    )
    db.session.add(new_project)
    db.session.commit()

    return jsonify({"msg": "Project created successfully", "project_id": new_project.id}), 201

@projects_bp.route("/projects", methods=["GET"])
@jwt_required()
def get_projects():
    user_id = get_jwt_identity()
    projects = Project.query.filter_by(user_id=user_id).all()
    return jsonify([
        {
            "id": p.id,
            "project_name": p.project_name,
            "project_type": p.project_type,
            "created_at": p.created_at.isoformat()
        } for p in projects
    ]), 200

@projects_bp.route("/projects/<int:project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()

    if not project:
        return jsonify({"msg": "Project not found"}), 404

    return jsonify({
        "id": project.id,
        "project_name": project.project_name,
        "project_type": project.project_type,
        "project_data": project.project_data,
        "created_at": project.created_at.isoformat()
    }), 200

@projects_bp.route("/projects/<int:project_id>", methods=["PUT"])
@jwt_required()
def update_project(project_id):
    user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()

    if not project:
        return jsonify({"msg": "Project not found"}), 404

    data = request.get_json()
    project.project_name = data.get("project_name", project.project_name)
    project.project_type = data.get("project_type", project.project_type)
    project.project_data = data.get("project_data", project.project_data)

    db.session.commit()

    return jsonify({"msg": "Project updated successfully"}), 200

@projects_bp.route("/projects/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()

    if not project:
        return jsonify({"msg": "Project not found"}), 404

    db.session.delete(project)
    db.session.commit()

    return jsonify({"msg": "Project deleted successfully"}), 200
