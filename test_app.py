import os
import sys

def test_imports():
    print("Testing imports...")
    try:
        import flask
        import google.genai
        import docx
        import pypdf
        import dotenv
        import pydantic
        print("✅ All packages imported successfully!")
    except ImportError as e:
        print(f"❌ Import failed: {str(e)}")
        sys.exit(1)

def test_env():
    print("Checking for environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        # Mask API key for safety
        masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "..."
        print(f"✅ GEMINI_API_KEY found: {masked}")
    else:
        print("⚠️ GEMINI_API_KEY not found in environment or .env. Please configure it for AI features to work.")

if __name__ == "__main__":
    test_imports()
    test_env()
