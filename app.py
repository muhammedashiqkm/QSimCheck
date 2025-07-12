from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from faiss_rag_utils import build_faiss_index, embed_texts
import google.generativeai as genai
from bs4 import BeautifulSoup

# Load environment variables and configure Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
llm = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)

# Utility to remove HTML tags
def clean_html(text):
    return BeautifulSoup(text or "", "html.parser").get_text()

@app.route("/check-question", methods=["POST"])
def check_question():
    try:
        data = request.json
        questions_url = data.get("questions_url")
        new_question = data.get("question")

        if not questions_url or not new_question:
            return jsonify({"error": "Missing 'questions_url' or 'question'"}), 400

        # Fetch questions from the provided URL
        questions = []
        try:
            response = requests.get(questions_url, timeout=5)
            if response.status_code == 200:
                questions = response.json()
        except:
            pass

        if not questions:
            return jsonify({"error": "No questions available"}), 404

        # Clean questions and build FAISS index
        question_texts = [clean_html(q.get("Question")) for q in questions]
        index, all_questions, embeddings = build_faiss_index(question_texts)
        new_embedding = embed_texts([new_question])
        D, I = index.search(new_embedding, k=10)
        top_indices = I[0]

        # Prepare top matches for Gemini
        top_matches = [clean_html(questions[i].get("Question")) for i in top_indices]
        match_list = "\n".join(f"{i+1}. {q}" for i, q in enumerate(top_matches))

        # Gemini prompt for bulk semantic similarity check
        prompt = f"""
You are an expert in semantic question detection.

A new question has been added:
\"\"\"{new_question}\"\"\"

Below is a list of existing questions:

{match_list}

Identify which of the above questions are semantically the same or very similar to the new question.

Respond ONLY with a comma-separated list of matching numbers (e.g., "1, 3, 5"). Do NOT explain anything.
"""

        # Call Gemini
        response = llm.generate_content(prompt)
        match_numbers = response.text.strip()

        matched_questions = []
        if match_numbers:
            for num in match_numbers.split(","):
                try:
                    idx = int(num.strip()) - 1  # Convert 1-based index to 0-based
                    matched_questions.append(questions[top_indices[idx]])
                except:
                    continue

        # Final response formatting
        if matched_questions:
            return jsonify({
                "response": "yes",
                "matched_questions": matched_questions
            })
        else:
            return jsonify({
                "response": "no"
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run server in production mode
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
