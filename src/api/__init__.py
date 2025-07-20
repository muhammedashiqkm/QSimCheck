from .auth_routes import register_auth_routes
from .question_routes import register_question_routes
from .health_routes import register_health_routes

def register_routes(app, limiter):
    register_auth_routes(app, limiter)
    register_question_routes(app, limiter)
    register_health_routes(app, limiter)

__all__ = ['register_routes']