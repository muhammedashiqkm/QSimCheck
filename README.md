# Question Similarity Checker

A Flask application that uses Gemini AI and vector embeddings to check for semantically similar questions.

## Features

- Simple single-user authentication with JWT
- Question similarity checking using vector embeddings and Gemini AI
- Group similar questions
- Comprehensive logging
- Rate limiting
- Security headers
- Docker support

## Project Structure

```
.
├── app.py                  # Main application entry point
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker build configuration
├── Makefile                # Build automation
├── requirements.txt        # Python dependencies
├── src/                    # Application source code
│   ├── api/                # API routes
│   ├── config/             # Application configuration
│   ├── models/             # Database models
│   ├── services/           # External services integration
│   └── utils/              # Utility functions
└── tests/                  # Test suite
```

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your configuration values
3. Install dependencies:

```bash
make setup
```

4. Run the application:

```bash
make run
```

## Docker

To run with Docker:

```bash
make docker-build
make docker-run
```

## API Endpoints

- `POST /login` - Login with admin credentials and get JWT tokens
- `POST /refresh` - Refresh access token
- `POST /check-question` - Check if a question is similar to existing ones
- `POST /group_similar_questions` - Group similar questions
- `GET /health` - Health check endpoint

## Testing

Run tests with:

```bash
make test
```