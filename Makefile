.PHONY: setup run test clean docker-build docker-run docker-stop logs help

# Variables
PYTHON = python
PIP = pip
DOCKER_COMPOSE = docker-compose

help:
	@echo "Available commands:"
	@echo "  make setup         - Install dependencies"
	@echo "  make run           - Run the application locally"
	@echo "  make test          - Run tests"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run with Docker Compose"
	@echo "  make docker-stop   - Stop Docker containers"
	@echo "  make logs          - View application logs"

setup:
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) app.py

test:
	$(PYTHON) -m unittest discover -s tests

clean:
	$(PYTHON) -c "import shutil; import os; [shutil.rmtree(p, ignore_errors=True) for p in ['__pycache__', 'build', 'dist', '*.egg-info'] if os.path.exists(p)]"
	$(PYTHON) -c "import os; [os.remove(f) for f in [f for f in os.listdir('.') if f.endswith('.pyc')] if os.path.exists(f)]"

docker-build:
	$(DOCKER_COMPOSE) build

docker-run:
	$(DOCKER_COMPOSE) up -d

docker-stop:
	$(DOCKER_COMPOSE) down

logs:
	$(DOCKER_COMPOSE) logs -f app

.DEFAULT_GOAL := help