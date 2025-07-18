from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, JWTManager, verify_jwt_in_request
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS 
import logging
import os
from datetime import timedelta
from faiss_rag_utils import build_faiss_index, embed_texts

# --- Load environment variables and configure logging ---
load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app) 

# JWT and SQLAlchemy setup
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Configure Gemini
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    llm = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    logging.error(f"Failed to configure Gemini: {e}")
    llm = None

def clean_html(text):
    return BeautifulSoup(text or "", "html.parser").get_text()

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": f"User {username} created successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=username)
        refresh_token = create_refresh_token(identity=username)
        return jsonify(access_token=access_token, refresh_token=refresh_token)

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/refresh", methods=["POST"])
def refresh():
    try:
        verify_jwt_in_request(locations=['json'], refresh=True)
        current_user = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user)
        return jsonify(access_token=new_access_token)
    except Exception:
        return jsonify({"error": "Invalid, expired, or missing refresh token in JSON body"}), 401

@app.route("/check-question", methods=["POST"])
@jwt_required()
def check_question():
    if not llm:
        return jsonify({"error": "Gemini model not initialized. Check API Key."}), 503
    try:
        data = request.json
        questions_url = data.get("questions_url")
        new_question = data.get("question")

        if not questions_url or not new_question:
            return jsonify({"error": "Request body must contain 'questions_url' and 'question'"}), 400

        try:
            logging.info(f"Fetching questions from: {questions_url}")
            response = requests.get(questions_url, timeout=10)
            response.raise_for_status()
            questions = response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch or parse questions from URL: {e}")
            return jsonify({"error": f"Could not retrieve questions from the provided URL: {e}"}), 500

        if not questions:
            return jsonify({"error": "No questions were found at the provided URL"}), 404

        logging.info(f"Building FAISS index for {len(questions)} questions...")
        question_texts = [clean_html(q.get("Question")) for q in questions]
        index, _, _ = build_faiss_index(question_texts)

        new_embedding = embed_texts([new_question])
        D, I = index.search(new_embedding, k=5)
        top_indices = I[0]

        top_matches = [question_texts[i] for i in top_indices]
        match_list = "\n".join(f"{i+1}. {q}" for i, q in enumerate(top_matches))

        prompt = f"""
You are an expert semantic analysis AI. Your task is to compare a "New Question" against a list of "Candidate Questions" and identify which ones are semantically identical.

Definition of Semantically Identical: Two questions are semantically identical if they ask the exact same thing or test the same concept, even if the wording, names, or numbers are different.

*New Question:*
\"\"\"{new_question}\"\"\"

*Candidate Questions:*
{match_list}
Which of the numbered "Candidate Questions" are semantically identical to the "New Question"?

Return ONLY the numbers of the matching candidates, separated by commas (e.g., "1, 3").
Do not add any explanation or other text.
"""
        response = llm.generate_content(prompt)
        match_numbers = response.text.strip()
        matched_questions = []

        if match_numbers:
            for num_str in match_numbers.split(","):
                try:
                    match_idx_1_based = int(num_str.strip())
                    original_list_idx = top_indices[match_idx_1_based - 1]
                    matched_questions.append(questions[original_list_idx])
                except (ValueError, IndexError):
                    continue

        if matched_questions:
            return jsonify({"response": "yes", "matched_questions": matched_questions})
        else:
            return jsonify({"response": "no"})

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

@app.route("/group_similar_questions", methods=["POST"])
@jwt_required()
def group_similar_questions():
    if not llm:
        return jsonify({"error": "Gemini model not initialized. Check API Key."}), 503
    try:
        data = request.json
        questions_url = data.get("questions_url")

        if not questions_url:
            return jsonify({"error": "Missing 'questions_url' in request"}), 400

        try:
            logging.info(f"Fetching questions from: {questions_url}")
            response = requests.get(questions_url, timeout=10)
            response.raise_for_status()
            questions = response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch questions: {e}")
            return jsonify({"error": f"Could not fetch questions from the URL: {e}"}), 500

        if not questions:
            return jsonify({"response": "no", "message": "No questions found"}), 404

        question_texts = [clean_html(q.get("Question")) for q in questions]
        joined_questions = "\n".join([f"{i+1}. {q}" for i, q in enumerate(question_texts)])

        prompt = f"""
You are an expert question grouping AI. Your task is to review the provided list of academic questions and identify all groups of questions that are *semantically identical*.
*Definition of Semantically Identical:* Questions are semantically identical if they ask the exact same core question, test the exact same underlying concept/skill, or would require the exact same specific answer/problem-solving approach, regardless of variations in wording, specific numerical values, or names used. Focus strictly on the underlying meaning, not superficial phrasing or keywords.
Here is the list of questions:\n{joined_questions}
Return the result as groups of comma-separated numbers representing identical questions. 
Example output: 
Group 1: 1, 4, 7
Group 2: 2, 5
Only return groups with more than one question. Do not explain.
"""
        result = llm.generate_content(prompt)
        raw_output = result.text.strip()
        groups = []

        for line in raw_output.splitlines():
            if ":" in line:
                try:
                    _, indices = line.split(":")
                    ids = [int(x.strip()) - 1 for x in indices.strip().split(",") if x.strip().isdigit()]
                    if len(ids) > 1:
                        group = [questions[i] for i in ids if 0 <= i < len(questions)]
                        if group:
                            groups.append(group)
                except Exception as parse_error:
                    logging.warning(f"Error parsing group line: {line} - {parse_error}")
                    continue

        if groups:
            return jsonify({"response": "yes", "matched_groups": groups})
        else:
            return jsonify({"response": "no"})

    except Exception as e:
        logging.error(f"Internal error in /group-similar-questions: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
