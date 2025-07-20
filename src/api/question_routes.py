import uuid
import urllib.parse
import requests
import os
from flask import request, jsonify, g, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.utils import clean_html, build_vector_index, embed_texts

def register_question_routes(app, limiter):
    allowed_domains_str = os.getenv('ALLOWED_DOMAINS', '') if os.getenv('ALLOWED_DOMAINS', '') else 'all'
    allowed_domains = [domain.strip() for domain in allowed_domains_str.split(',')]
    
    @app.route("/check-question", methods=["POST"])
    @jwt_required()
    @limiter.limit("20 per minute")
    def check_question():
        request_id = getattr(g, 'request_id', str(uuid.uuid4()))
        current_user = get_jwt_identity()
        app.logger.info("Processing check-question request", 
                    extra={'user_id': current_user, 'request_id': request_id})
        
        llm = current_app.config.get('llm')
        if not llm:
            app.logger.error("Gemini model not initialized", 
                            extra={'user_id': current_user, 'request_id': request_id})
            return jsonify({"error": "Gemini model not initialized. Check API Key."}), 503
        try:
            data = request.json
            questions_url = data.get("questions_url")
            new_question = data.get("question")

            if not questions_url or not new_question:
                app.logger.warning("Missing required parameters", 
                                extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"error": "Request body must contain 'questions_url' and 'question'"}), 400
                
            parsed_url = urllib.parse.urlparse(questions_url)
            
            if not any(domain in parsed_url.netloc for domain in allowed_domains) and allowed_domains_str != 'all':
                app.logger.warning(f"URL not allowed: {questions_url}", 
                                extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"error": "URL not allowed. Please use an approved API endpoint."}), 403
                
            try:
                app.logger.info(f"Fetching questions from: {questions_url}", 
                            extra={'user_id': current_user, 'request_id': request_id})
                response = requests.get(questions_url, timeout=5, 
                                    headers={'User-Agent': 'Flask-App/1.0'})
                response.raise_for_status()
                questions = response.json()
            except requests.exceptions.RequestException as e:
                app.logger.error(f"Failed to fetch questions: {str(e)}", 
                                extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"error": "Could not retrieve questions from the provided URL"}), 500

            if not questions:
                app.logger.warning("No questions found at URL", 
                                extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"error": "No questions were found at the provided URL"}), 404

            app.logger.info(f"Building vector index for {len(questions)} questions", 
                        extra={'user_id': current_user, 'request_id': request_id})
            question_texts = [clean_html(q.get("Question")) for q in questions]

            index, _, _ = build_vector_index(question_texts)

            app.logger.info("Generating embeddings for new question", 
                        extra={'user_id': current_user, 'request_id': request_id})

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
            app.logger.info("Sending prompt to Gemini API", 
                        extra={'user_id': current_user, 'request_id': request_id})
            response = llm.generate_content(prompt)
            match_numbers = response.text.strip()
            matched_questions = []

            if match_numbers:
                app.logger.info(f"Gemini identified matches: {match_numbers}", 
                            extra={'user_id': current_user, 'request_id': request_id})
                for num_str in match_numbers.split(","):
                    try:
                        match_idx_1_based = int(num_str.strip())
                        original_list_idx = top_indices[match_idx_1_based - 1]
                        matched_questions.append(questions[original_list_idx])
                    except (ValueError, IndexError) as e:
                        app.logger.warning(f"Error parsing match index: {str(e)}", 
                                        extra={'user_id': current_user, 'request_id': request_id})
                        continue

            if matched_questions:
                app.logger.info(f"Found {len(matched_questions)} matching questions", 
                            extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"response": "yes", "matched_questions": matched_questions})
            else:
                app.logger.info("No matching questions found", 
                            extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"response": "no"})

        except Exception as e:
            app.logger.error(f"Error in check-question: {str(e)}", 
                            extra={'user_id': current_user, 'request_id': request_id})
            return jsonify({"error": "An internal server error occurred"}), 500

    @app.route("/group_similar_questions", methods=["POST"])
    @jwt_required()
    def group_similar_questions():
        request_id = getattr(g, 'request_id', str(uuid.uuid4()))
        current_user = get_jwt_identity()
        app.logger.info("Processing group_similar_questions request", 
                    extra={'user_id': current_user, 'request_id': request_id})
        
        llm = current_app.config.get('llm')
        if not llm:
            app.logger.error("Gemini model not initialized", 
                            extra={'user_id': current_user, 'request_id': request_id})
            return jsonify({"error": "Gemini model not initialized. Check API Key."}), 503
        try:
            data = request.json
            questions_url = data.get("questions_url")

            if not questions_url:
                app.logger.warning("Missing questions_url parameter", 
                                extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"error": "Missing 'questions_url' in request"}), 400
                
            parsed_url = urllib.parse.urlparse(questions_url)
            
            if not any(domain in parsed_url.netloc for domain in allowed_domains):
                app.logger.warning(f"URL not allowed: {questions_url}", 
                                extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"error": "URL not allowed. Please use an approved API endpoint."}), 403

            try:
                app.logger.info(f"Fetching questions from: {questions_url}", 
                            extra={'user_id': current_user, 'request_id': request_id})
                response = requests.get(questions_url, timeout=5,
                                    headers={'User-Agent': 'Flask-App/1.0'})
                response.raise_for_status()
                questions = response.json()
            except requests.exceptions.RequestException as e:
                app.logger.error(f"Failed to fetch questions: {str(e)}", 
                                extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"error": "Could not fetch questions from the URL"}), 500

            if not questions:
                app.logger.warning("No questions found at URL", 
                                extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"response": "no", "message": "No questions found"}), 404

            app.logger.info(f"Processing {len(questions)} questions for grouping", 
                        extra={'user_id': current_user, 'request_id': request_id})
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
            app.logger.info("Sending grouping prompt to Gemini API", 
                        extra={'user_id': current_user, 'request_id': request_id})
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
                        app.logger.warning(f"Error parsing group line: {line} - {str(parse_error)}", 
                                        extra={'user_id': current_user, 'request_id': request_id})
                        continue

            if groups:
                app.logger.info(f"Found {len(groups)} question groups", 
                            extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"response": "yes", "matched_groups": groups})
            else:
                app.logger.info("No question groups found", 
                            extra={'user_id': current_user, 'request_id': request_id})
                return jsonify({"response": "no"})

        except Exception as e:
            app.logger.error(f"Error in group_similar_questions: {str(e)}", 
                            extra={'user_id': current_user, 'request_id': request_id})
            return jsonify({"error": "An internal server error occurred"}), 500