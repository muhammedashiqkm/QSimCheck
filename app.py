import os
from src import create_app

app = create_app()

if __name__ == "__main__":
    if os.getenv("USE_DATABASE_AUTH", "false").lower() == "true":
        with app.app_context():
            from src.models import db
            db.create_all()
    
    app.logger.info("Starting Flask application")
    app.run(host="0.0.0.0", port=5000)