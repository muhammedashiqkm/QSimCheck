# app.py

from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from faiss_rag_utils import build_faiss_index, embed_texts
import google.generativeai as genai
from bs4 import BeautifulSoup
import logging

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO)
load_dotenv()

# --- Configure Gemini ---
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    llm = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    logging.error(f"Failed to configure Gemini: {e}")
    llm = None

app = Flask(__name__)

def clean_html(text):
    """Utility to remove HTML tags."""
    return BeautifulSoup(text or "", "html.parser").get_text()

@app.route("/check-question", methods=["POST"])
def check_question():
    if not llm:
        return jsonify({"error": "Gemini model not initialized. Check API Key."}), 503

    try:
        data = request.json
        questions_url = data.get("questions_url")
        new_question = data.get("question")

        if not questions_url or not new_question:
            return jsonify({"error": "Request body must contain 'questions_url' and 'question'"}), 400

        # --- Fetch questions from the provided URL for each request ---
        try:
            logging.info(f"Fetching questions from: {questions_url}")
            response = requests.get(questions_url, timeout=10)
            response.raise_for_status()  # This will raise an error for bad status codes (4xx or 5xx)
            questions = response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch or parse questions from URL: {e}")
            return jsonify({"error": f"Could not retrieve questions from the provided URL: {e}"}), 500

        if not questions:
            return jsonify({"error": "No questions were found at the provided URL"}), 404

        # --- Build FAISS index on-the-fly for each request ---
        logging.info(f"Building FAISS index for {len(questions)} questions...")
        question_texts = [clean_html(q.get("Question")) for q in questions]
        index, _, _ = build_faiss_index(question_texts)
        
        # Search for similar questions
        new_embedding = embed_texts([new_question])
        D, I = index.search(new_embedding, k=5)  # Find top 5 similar
        top_indices = I[0]

        # Prepare top matches for Gemini
        top_matches = [question_texts[i] for i in top_indices]
        match_list = "\n".join(f"{i+1}. {q}" for i, q in enumerate(top_matches))

        # --- Gemini prompt for bulk semantic similarity check ---
        prompt = f"""
You are an expert in semantic question detection.

A new question has been added:
\"\"\"{new_question}\"\"\"

Below is a list of existing questions:
{match_list}

Identify which of the above questions are semantically the same or very similar to the new question.

Respond ONLY with a comma-separated list of matching numbers (e.g., "1, 3, 5"). Do NOT explain anything.
"""

        # Call Gemini and parse response
        response = llm.generate_content(prompt)
        match_numbers = response.text.strip()

        matched_questions = []
        if match_numbers:
            for num_str in match_numbers.split(","):
                try:
                    # Convert 1-based index from Gemini to 0-based list index
                    match_idx_1_based = int(num_str.strip())
                    original_list_idx = top_indices[match_idx_1_based - 1]
                    matched_questions.append(questions[original_list_idx])
                except (ValueError, IndexError):
                    continue

        if matched_questions:
            return jsonify({
                "response": "yes",
                "matched_questions": matched_questions
            })
        else:
            return jsonify({"response": "no"})

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

# The __main__ block is kept for local testing but will not be used by Gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
