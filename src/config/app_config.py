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

    # Initialize database only if using database authentication
    if os.getenv("USE_DATABASE_AUTH", "false").lower() == "true":
        from src.models import db
        
        # Use SQLite for development if MySQL credentials are not provided
        db_user = os.getenv("DB_USER")
        if db_user:
            db_password = os.getenv("DB_PASSWORD")
            db_host = os.getenv("DB_HOST")
            db_name = os.getenv("DB_NAME")
            app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
        else:
            # Use SQLite for development
            app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        
        db.init_app(app)

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