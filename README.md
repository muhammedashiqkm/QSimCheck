# Flask FAISS Semantic Question Matcher API

This project provides a secure, production-ready API to:
- Register and authenticate users using JWT.
- Check if a new question is semantically similar to existing ones.
- Group semantically identical questions using FAISS + Gemini LLM.

---

## 🚀 Deployment (Docker + Gunicorn)

### 1. Clone the Repository

```bash
git clone https://your-repo-url
cd your-repo-folder
```

### 2. Add `.env` File

Create a `.env` file with:

```env
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=your_strong_jwt_secret
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_NAME=college_db
```

### 3. Build Docker Image

```bash
docker build -t flask-rag-app .
```

### 4. Run Docker Container

```bash
docker run -p 5000:5000 --env-file .env flask-rag-app
```

---

## 🔐 API Endpoints

### 1. Register a New User

`POST /register`

```json
{
  "username": "yourusername",
  "password": "yourpassword"
}
```

---

### 2. Login

`POST /login`

```json
{
  "username": "yourusername",
  "password": "yourpassword"
}
```

**Returns:**

```json
{
  "access_token": "JWT access token",
  "refresh_token": "JWT refresh token"
}
```

---

### 3. Refresh Token

`POST /refresh`

```json
{
  "refresh_token": "your_refresh_token"
}
```

---

### 4. Check Semantically Similar Question

`POST /check-question`  
**JWT Required**

```json
{
  "questions_url": "https://example.com/api/questions",
  "question": "Explain the role of loops in Python."
}
```

**Returns:**

```json
{
  "response": "yes",
  "matched_questions": [ ... ]
}
```

---

### 5. Group Similar Questions

`POST /group_similar_questions`  
**JWT Required**

```json
{
  "questions_url": "https://example.com/api/questions"
}
```

**Returns:**

```json
{
  "response": "yes",
  "matched_groups": [ [ ... ], [ ... ] ]
}
```

---

## 📦 Requirements

- Python 3.11+
- Docker
- MySQL (configured separately)

---

## 🧠 Powered by

- FAISS (for semantic search)
- Gemini LLM (Google Generative AI)
- Sentence Transformers (MiniLM)