import uuid
import os
from flask import request, jsonify, g
from flask_jwt_extended import (
    create_access_token, jwt_required,
    get_jwt_identity
)
from src.utils import log_security_event

def register_auth_routes(app, limiter):
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")
    
    @app.route("/login", methods=["POST"])
    @limiter.limit("20 per minute")
    def login():
        request_id = getattr(g, 'request_id', str(uuid.uuid4()))
        app.logger.info("Processing login request", extra={'request_id': request_id})
        
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            app.logger.warning("Login failed: missing username or password", 
                            extra={'request_id': request_id})
            return jsonify({"error": "Username and password are required"}), 400

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            user_agent = request.headers.get('User-Agent', '')
            ip_address = request.remote_addr
            fingerprint = f"{user_agent}|{ip_address}"
            
            access_token = create_access_token(
                identity=username,
                additional_claims={"fingerprint": fingerprint}
            )
            
            log_security_event(
                event_type="user_login",
                details=f"User '{username}' logged in successfully",
                user_id=username,
                ip_address=ip_address
            )
            
            app.logger.info(f"User '{username}' logged in successfully", 
                        extra={'user_id': username, 'request_id': request_id})
            return jsonify(access_token=access_token)

        log_security_event(
            event_type="failed_login",
            details=f"Failed login attempt for user '{username}'",
            ip_address=request.remote_addr
        )
        
        app.logger.warning(f"Failed login attempt for user '{username}'", 
                        extra={'request_id': request_id})
        return jsonify({"error": "Invalid credentials"}), 401