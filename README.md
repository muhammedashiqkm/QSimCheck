

-----

# Semantic Question Analysis API

This Flask application provides a set of API endpoints to analyze and compare academic questions using Google's Gemini AI. It can find semantically similar questions and group identical ones from a given source URL.

## Features

  * **Semantic Search**: Checks if a new question is semantically identical to any in an existing list.
  * **Question Grouping**: Identifies and groups all semantically identical questions within a list.
  * **Secure**: Uses JWT for authentication and an allowlist for source URLs.
  * **Health Check**: An endpoint to monitor the status of the application and its connection to the Gemini API.

-----

## Setup and Installation

### 1\. Prerequisites

  * Python 3.8+
  * A Google Gemini API Key

### 2\. Installation

First, clone the repository and navigate into the project directory.

```bash
git clone <your-repository-url>
cd <your-project-directory>
```

Next, create a virtual environment and install the required dependencies.

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
# venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3\. Environment Configuration

Create a `.env` file in the root of your project directory. This file will store all your secret keys and configuration variables.

```env
# .env file

# --- Application Security ---
# A strong, random secret key for signing JWTs.
JWT_SECRET_KEY=your_super_secret_random_key_here

# --- Admin Credentials ---
# Login details for the application's admin user.
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_strong_password_here

# --- Google Gemini API ---
# Your API key from Google AI Studio.
GEMINI_API_KEY=your_gemini_api_key_here

# --- Allowed Domains (for backend requests) ---
# Comma-separated list of domains the app is allowed to fetch questions from.
ALLOWED_DOMAINS=beta.onlinetcsv5.meshilogic.co.in

# --- Allowed Frontend Origins (for CORS) ---
# The URL of your frontend application. For multiple, separate with a comma.
FRONTEND_ORIGINS=http://localhost:3000,http://your-production-frontend.com
```

### 4\. Running the Application

You can run the application using a production-ready server like Gunicorn:

```bash
gunicorn --bind 0.0.0.0:8000 app:app
```

-----

## API Endpoints

All protected endpoints require a Bearer Token in the `Authorization` header: `Authorization: Bearer <your_access_token>`.

### Authentication

#### `POST /login`

Authenticates the user and returns a JWT access token.

  * **Request Body**:
    ```json
    {
        "username": "admin",
        "password": "your_strong_password_here"
    }
    ```
  * **Successful Response (200)**:
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
  * **Error Response (401)**:
    ```json
    {
        "error": "Invalid credentials"
    }
    ```

### Health Check

#### `GET /health`

Checks the application status and Gemini API connectivity. **(Authentication Required)**

  * **Successful Response (200)**:
    ```json
    {
        "status": "healthy",
        "gemini_api": "available",
        "timestamp": "12749453716834111"
    }
    ```

### Question Analysis

#### `POST /check-question`

Compares a new question against a list from a URL to find semantic matches. **(Authentication Required)**

  * **Request Body**:
    ```json
    {
        "questions_url": "https://beta.onlinetcsv5.meshilogic.co.in/website/ReadCourseQuestionDetails?PaperNameID=94",
        "question": "Explain the role of loops in Python."
    }
    ```
  * **Successful Response (Match Found)**:
    ```json
    {
        "response": "yes",
        "matched_questions": [
            {
                "Question": "<p>What are loops in python? explain with example</p>",
                "Answer": "...",
                "QuestionID": 123
            }
        ]
    }
    ```
  * **Successful Response (No Match Found)**:
    ```json
    {
        "response": "no"
    }
    ```

#### `POST /group_similar_questions`

Analyzes a list of questions from a URL and groups the ones that are semantically identical. **(Authentication Required)**

  * **Request Body**:
    ```json
    {
        "questions_url": "https://beta.onlinetcsv5.meshilogic.co.in/website/ReadCourseQuestionDetails?PaperNameID=94"
    }
    ```
  * **Successful Response (Groups Found)**:
    ```json
    {
        "response": "yes",
        "matched_groups": [
            [
                { "QuestionID": 101, "Question": "<p>What is a variable?</p>", "Answer": "..." },
                { "QuestionID": 105, "Question": "<p>Define variable.</p>", "Answer": "..." }
            ],
            [
                { "QuestionID": 210, "Question": "<p>Explain for loops.</p>", "Answer": "..." },
                { "QuestionID": 212, "Question": "<p>Describe the use of a for loop.</p>", "Answer": "..." }
            ]
        ]
    }
    ```
  * **Successful Response (No Groups Found)**:
    ```json
    {
        "response": "no"
    }
    ```