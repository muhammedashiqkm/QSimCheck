# Semantic Question Matcher API

## Project Overview

This project is a Flask-based API that determines if a new question is semantically similar to any question in an existing list. It uses a powerful combination of sentence embeddings, a high-speed vector search index, and a Large Language Model (LLM) to provide accurate semantic matching.

The API is designed to be flexible, allowing the list of existing questions to be provided dynamically with each request via a URL. This makes it ideal for use cases where the source of questions can change frequently.

## Key Features

* **Dynamic Question Sets**: Compares a new question against a list of questions fetched from a URL provided in the API request.
* **High-Speed Similarity Search**: Uses `sentence-transformers` to generate vector embeddings and `FAISS` to find the most similar questions with minimal latency.
* **LLM-Powered Validation**: Employs Google's Gemini model to perform a final validation on the top matches, ensuring high accuracy in identifying semantically identical questions.
* **Production-Ready**: The application is containerized with Docker and deployed using a Gunicorn WSGI server for robust, parallel request handling.

## Technology Stack

* **Backend**: Flask
* **WSGI Server**: Gunicorn
* **AI/ML**:
    * **LLM**: Google Gemini (`gemini-1.5-flash`)
    * **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2` model)
    * **Vector Search**: `faiss-cpu` (Facebook AI Similarity Search)
* **Deployment**: Docker
* **Other Libraries**: Requests, python-dotenv, BeautifulSoup4

---

## API Endpoint Details

### Check for Similar Questions

This endpoint takes a new question and a URL pointing to a JSON list of existing questions, and it returns any matches that are semantically the same.

* **URL**: `/check-question`
* **Method**: `POST`
* **Headers**:
    * `Content-Type: application/json`

#### Request Body (JSON)

| Key             | Type   | Description                                                                              | Required |
| --------------- | ------ | ---------------------------------------------------------------------------------------- | -------- |
| `question`      | String | The new question you want to check.                                                      | Yes      |
| `questions_url` | String | A URL that returns a JSON array of existing question objects. Each object must have a `Question` key. | Yes      |

**Example `curl` Request:**

```bash
curl -X POST http://localhost:5000/check-question \
-H "Content-Type: application/json" \
-d '{
    "questions_url": "https://beta.onlinetcsv5.meshilogic.co.in/website/ReadCourseQuestionDetails?PaperNameID=94",
    "question": "What is the difference between synchronic and diachronic linguistics?"
}'
```

### API Responses

#### 1. Success: Matches Found
**Status Code**: 200 OK

```json
{
  "response": "yes",
  "matched_questions": [
    {
      "QuestionID": 123,
      "Question": "What are the main distinctions between diachronic and synchronic approaches in linguistics?",
      "Answer": "..."
    }
  ]
}
```

#### 2. Success: No Matches Found
**Status Code**: 200 OK

```json
{
  "response": "no"
}
```

#### 3. Client Error: Bad Request
**Status Code**: 400 Bad Request

```json
{
  "error": "Request body must contain 'questions_url' and 'question'"
}
```

#### 4. Server Error: Could Not Fetch Questions
**Status Code**: 500 Internal Server Error

```json
{
  "error": "Could not retrieve questions from the provided URL: ..."
}
```

## Setup and Deployment

You can run this project locally for development or deploy it using Docker for production.

### A. Local Development Setup

Clone the repository and navigate to the project directory.

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create an environment file: Create a file named `.env` and add your Gemini API key:

```env
# .env
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
```

Run the Flask development server:

```bash
python app.py
```

The server will start on [http://localhost:5000](http://localhost:5000).

### B. Production Deployment with Docker

Ensure Docker is installed and running on your machine.

#### Project Structure

```
/your-project/
├── app.py
├── faiss_rag_utils.py
├── requirements.txt
├── Dockerfile
└── .env
```

#### Build the Docker Image

```bash
docker build -t question-checker .
```

#### Run the Docker Container

```bash
docker run -d -p 5000:5000 --env-file .env --name my-question-app question-checker
```

#### Verify and Test

Your API is now running and accessible at [http://localhost:5000](http://localhost:5000).

### Managing the Container

Check logs:

```bash
docker logs my-question-app
```

Stop the container:

```bash
docker stop my-question-app
```

Remove the container:

```bash
docker rm my-question-app
```