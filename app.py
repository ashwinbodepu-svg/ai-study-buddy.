import os
import shutil
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from extract_text import extract_text

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure uploads folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Gemini Client
# The SDK automatically uses GEMINI_API_KEY environment variable.
API_KEY = os.getenv("GEMINI_API_KEY")

def get_gemini_client():
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY is not set in the environment or .env file.")
    return genai.Client()

# Define Pydantic models for structured outputs
class QuizItem(BaseModel):
    question: str = Field(description="The question prompt for the student.")
    answer: str = Field(description="The detailed correct answer or explanation.")

class QuizResponse(BaseModel):
    quiz: list[QuizItem] = Field(description="A list of quiz questions generated from the text.")

class FlashcardItem(BaseModel):
    front: str = Field(description="The concept, question, or term on the front side.")
    back: str = Field(description="The definition, explanation, or answer on the back side.")

class FlashcardsResponse(BaseModel):
    flashcards: list[FlashcardItem] = Field(description="A list of flashcard front and back pairs.")

def validate_uploaded_file(request_files):
    """Validates the uploaded file from the request."""
    if 'file' not in request_files:
        raise ValueError("No file part in the request.")
    file = request_files['file']
    if file.filename == '':
        raise ValueError("No file selected for upload.")
    
    # Check extension
    filename = secure_filename(file.filename)
    _, ext = os.path.splitext(filename.lower())
    if ext not in ['.pdf', '.docx']:
        raise ValueError("Unsupported file format. Please upload a .pdf or .docx file.")
    
    return file

def save_and_extract_text(file) -> tuple[str, str]:
    """Saves the file to temp folder, extracts text, and returns (text, file_path)."""
    filename = secure_filename(file.filename)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(temp_path)
    try:
        text = extract_text(temp_path)
        return text, temp_path
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    temp_path = None
    try:
        # 1. Check API Key
        client = get_gemini_client()
        
        # 2. Validate and save file
        file = validate_uploaded_file(request.files)
        text, temp_path = save_and_extract_text(file)
        
        # 3. Call Gemini
        prompt = (
            "You are a professional educator. Based on the provided study notes below, "
            "generate a quiz containing 5 to 8 challenging questions with their respective answers. "
            "Ensure the questions test key concepts and definitions found in the notes.\n\n"
            f"STUDY NOTES:\n{text}"
        )
        
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QuizResponse,
                temperature=0.3
            )
        )
        
        # Clean up file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            
        # Parse output
        # In modern google-genai SDK, response.text contains the JSON string
        import json
        try:
            data = json.loads(response.text)
            return jsonify({"success": True, "quiz": data.get("quiz", [])})
        except Exception as json_err:
            return jsonify({"success": False, "error": f"Failed to parse Gemini JSON response: {str(json_err)}"}), 500
            
    except ValueError as val_err:
        return jsonify({"success": False, "error": str(val_err)}), 400
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"success": False, "error": f"An error occurred: {str(e)}"}), 500

@app.route('/generate-flashcards', methods=['POST'])
def generate_flashcards():
    temp_path = None
    try:
        # 1. Check API Key
        client = get_gemini_client()
        
        # 2. Validate and save file
        file = validate_uploaded_file(request.files)
        text, temp_path = save_and_extract_text(file)
        
        # 3. Call Gemini
        prompt = (
            "You are a study helper. Based on the provided study notes below, "
            "generate 6 to 10 flashcards (front and back pairs). "
            "The front side should contain a key term, concept, or quick question. "
            "The back side should contain a concise definition, answer, or explanation.\n\n"
            f"STUDY NOTES:\n{text}"
        )
        
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FlashcardsResponse,
                temperature=0.3
            )
        )
        
        # Clean up file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            
        # Parse output
        import json
        try:
            data = json.loads(response.text)
            return jsonify({"success": True, "flashcards": data.get("flashcards", [])})
        except Exception as json_err:
            return jsonify({"success": False, "error": f"Failed to parse Gemini JSON response: {str(json_err)}"}), 500
            
    except ValueError as val_err:
        return jsonify({"success": False, "error": str(val_err)}), 400
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"success": False, "error": f"An error occurred: {str(e)}"}), 500

@app.route('/ask-doubt', methods=['POST'])
def ask_doubt():
    temp_path = None
    try:
        # 1. Check API Key
        client = get_gemini_client()
        
        # 2. Validate question
        doubt_question = request.form.get('doubt', '').strip()
        if not doubt_question:
            return jsonify({"success": False, "error": "Please enter your doubt question."}), 400
            
        # 3. Validate and save file
        file = validate_uploaded_file(request.files)
        text, temp_path = save_and_extract_text(file)
        
        # 4. Call Gemini
        prompt = (
            "You are an AI Study Buddy helping a student with their notes.\n"
            "Using ONLY the provided study notes below, answer the student's question.\n"
            "If the answer is NOT covered or cannot be derived from the study notes, you MUST explicitly reply: "
            "\"I am sorry, but the answer to this question is not covered in your study notes.\"\n"
            "Do not use outside knowledge or hallucinate information that is not in the text.\n\n"
            f"STUDY NOTES:\n{text}\n\n"
            f"STUDENT QUESTION:\n{doubt_question}"
        )
        
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        
        # Clean up file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            
        return jsonify({"success": True, "answer": response.text})
            
    except ValueError as val_err:
        return jsonify({"success": False, "error": str(val_err)}), 400
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"success": False, "error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
