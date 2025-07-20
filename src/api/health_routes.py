import uuid
import os
from flask import jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import db

def register_health_routes(app, limiter):
    @app.route("/health", methods=["GET"])
    @jwt_required()
    def health_check():
        request_id = getattr(g, 'request_id', str(uuid.uuid4()))
        current_user = get_jwt_identity()
        app.logger.info("Health check requested", 
                    extra={'user_id': current_user, 'request_id': request_id})
        
        # Check if we're using database authentication
        if os.getenv("USE_DATABASE_AUTH", "false").lower() == "true":
            db_status = "error"
            try:
                db.session.execute("SELECT 1")
                db_status = "connected"
            except Exception as e:
                app.logger.error(f"Database health check failed: {str(e)}", 
                                extra={'user_id': current_user, 'request_id': request_id})
        else:
            db_status = "not_used"
        
        llm = app.config.get('llm')
        gemini_status = "available" if llm else "unavailable"
        
        app.logger.info(f"Health check results: DB={db_status}, Gemini={gemini_status}", 
                    extra={'user_id': current_user, 'request_id': request_id})
        
        return jsonify({
            "status": "healthy",
            "database": db_status,
            "gemini_api": gemini_status,
            "timestamp": str(uuid.uuid1().time)
        })