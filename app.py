import os
from src import create_app

app = create_app()

if __name__ == "__main__":
    app.logger.info("Starting Flask application")
    app.run(host="0.0.0.0", port=5000)