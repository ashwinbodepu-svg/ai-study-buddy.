import os
import pypdf
import docx

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file using pypdf."""
    text_content = []
    try:
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
    except Exception as e:
        raise ValueError(f"Failed to parse PDF file: {str(e)}")
    
    extracted_text = "\n".join(text_content).strip()
    if not extracted_text:
        raise ValueError("The PDF file appears to be empty or has no extractable text.")
    return extracted_text

def extract_text_from_docx(file_path: str) -> str:
    """Extracts text from a DOCX file using python-docx."""
    text_content = []
    try:
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            if paragraph.text:
                text_content.append(paragraph.text)
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX file: {str(e)}")
    
    extracted_text = "\n".join(text_content).strip()
    if not extracted_text:
        raise ValueError("The DOCX file appears to be empty or has no extractable text.")
    return extracted_text

def extract_text(file_path: str) -> str:
    """Detects file extension and extracts text accordingly."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    _, ext = os.path.splitext(file_path.lower())
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type '{ext}'. Only .pdf and .docx files are supported.")
