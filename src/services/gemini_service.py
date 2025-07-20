import os
import google.generativeai as genai

def setup_gemini(app):
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        llm = genai.GenerativeModel("gemini-1.5-flash")
        app.logger.info("Gemini API initialized successfully")
        app.config['llm'] = llm
        return llm
    except Exception as e:
        app.logger.error(f"Failed to configure Gemini API: {str(e)}")
        return None