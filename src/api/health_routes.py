import uuid
import os
from flask import jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import db

def register_health_routes(app, limiter):
    @app.route("/health", methods=["GET"])
    @jwt_required()
    @limiter.limit("1/second")
    def health_check():
        request_id = getattr(g, 'request_id', str(uuid.uuid4()))
        current_user = get_jwt_identity()
        app.logger.info("Health check requested", 
                    extra={'user_id': current_user, 'request_id': request_id})    
        llm = app.config.get('llm')
        gemini_status = "available" if llm else "unavailable"
        
        app.logger.info(f"Health check results: Gemini={gemini_status}", 
                    extra={'user_id': current_user, 'request_id': request_id})
        
        return jsonify({
            "status": "healthy",
            "gemini_api": gemini_status,
            "timestamp": str(uuid.uuid1().time)
        })