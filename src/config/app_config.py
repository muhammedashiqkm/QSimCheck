import os
from datetime import timedelta
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

def configure_app(app):
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=10)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    app.config["JWT_IDENTITY_CLAIM"] = "sub"
    app.config['SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")

    CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})
    csrf = CSRFProtect(app)
    jwt = JWTManager(app)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    return {
        'jwt': jwt,
        'csrf': csrf,
        'limiter': limiter
    }