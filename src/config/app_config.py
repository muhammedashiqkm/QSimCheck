import os
from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def configure_app(app):
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_IDENTITY_CLAIM"] = "sub"
    app.config['SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")

    
    frontend_origins_str = os.getenv("FRONTEND_ORIGINS", "*")
    frontend_origins = [origin.strip() for origin in frontend_origins_str.split(',')]

    CORS(app, resources={r"/*": {"origins": frontend_origins, "supports_credentials": True}})
    
    jwt = JWTManager(app)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    return {
        'jwt': jwt,
        'limiter': limiter
    }