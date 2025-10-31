from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.route("/health")
def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return jsonify({"status": "healthy"})
