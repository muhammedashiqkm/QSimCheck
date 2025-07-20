from flask import Flask, g, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
import uuid
import os
from dotenv import load_dotenv

from .models import db
from .config import configure_app
from .api import register_routes
from .services import setup_gemini
from .utils import setup_logging, log_request

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    loggers = setup_logging(app_name='flask-rag-app')
    app.logger = loggers['app_logger']
    
    @app.before_request
    def before_request():
        g.request_id = str(uuid.uuid4())
        log_request(request)
        
        if request.headers.get('Authorization', '').startswith('Bearer '):
            try:
                verify_jwt_in_request(optional=True)
                g.user_id = get_jwt_identity()
                if g.user_id:
                    app.logger.info(f"Request from authenticated user: {g.user_id}", 
                                extra={'user_id': g.user_id, 'request_id': g.request_id})
            except Exception:
                pass

    @app.after_request
    def add_security_headers(response):
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        status_code = response.status_code
        if status_code >= 400:
            loggers['access_logger'].warning(
                f"Response: status_code={status_code}",
                extra={
                    'request_id': getattr(g, 'request_id', 'unknown'),
                    'status_code': status_code
                }
            )
        else:
            loggers['access_logger'].info(
                f"Response: status_code={status_code}",
                extra={
                    'request_id': getattr(g, 'request_id', 'unknown'),
                    'status_code': status_code
                }
            )
        
        return response
    
    components = configure_app(app)
    
    setup_gemini(app)
    register_routes(app, components['limiter'])
    
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 error: {request.path} not found", 
                        extra={'request_id': getattr(g, 'request_id', 'unknown')})
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {str(error)}", 
                        extra={'request_id': getattr(g, 'request_id', 'unknown')})
        return jsonify({"error": "An internal server error occurred"}), 500

    @app.errorhandler(429)
    def ratelimit_error(error):
        app.logger.warning(f"429 error: Rate limit exceeded for {request.path}", 
                        extra={'request_id': getattr(g, 'request_id', 'unknown')})
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
    
    return app