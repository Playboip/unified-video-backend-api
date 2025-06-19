from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.subscription import SubscriptionPlan, Transaction
from src.main import db

subscriptions_bp = Blueprint("subscriptions", __name__)

@subscriptions_bp.route("/subscription_plans", methods=["GET"])
def get_subscription_plans():
    plans = SubscriptionPlan.query.all()
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "price_monthly": p.price_monthly,
            "price_yearly": p.price_yearly,
            "features": p.features,
            "max_projects": p.max_projects,
            "max_storage_gb": p.max_storage_gb,
            "max_video_length": p.max_video_length,
            "max_resolution": p.max_resolution,
            "allows_white_labeling": p.allows_white_labeling
        } for p in plans
    ]), 200

@subscriptions_bp.route("/subscribe", methods=["POST"])
@jwt_required()
def subscribe():
    user_id = get_jwt_identity()
    data = request.get_json()
    plan_id = data.get("plan_id")
    amount = data.get("amount")
    transaction_id = data.get("transaction_id")

    if not all([plan_id, amount, transaction_id]):
        return jsonify({"msg": "Missing required subscription data"}), 400

    plan = SubscriptionPlan.query.get(plan_id)
    if not plan:
        return jsonify({"msg": "Subscription plan not found"}), 404

    new_transaction = Transaction(
        user_id=user_id,
        subscription_plan_id=plan_id,
        amount=amount,
        transaction_id=transaction_id,
        status="completed" # Assuming successful payment for now
    )
    db.session.add(new_transaction)
    db.session.commit()

    # Here you would typically update the user's subscription status in the User model

    return jsonify({"msg": "Subscription successful", "transaction_id": new_transaction.id}), 201

@subscriptions_bp.route("/transactions", methods=["GET"])
@jwt_required()
def get_transactions():
    user_id = get_jwt_identity()
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    return jsonify([
        {
            "id": t.id,
            "plan_name": t.subscription_plan.display_name,
            "amount": t.amount,
            "transaction_date": t.transaction_date.isoformat(),
            "status": t.status
        } for t in transactions
    ]), 200
