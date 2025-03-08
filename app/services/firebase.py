# app/services/firebase.py
"""
Firebase integration for resume parsing.
"""
import io
import os
import requests
from typing import Dict, Any, Optional, Tuple, Union
import fitz  # PyMuPDF for PDF processing
import docx  # python-docx for DOCX processing
import logging

logger = logging.getLogger(__name__)

def parse_resume_from_firebase(file_url: str) -> Dict[str, Any]:
    """
    Fetch and extract text from a resume file stored in Firebase.
    
    Args:
        file_url: The publicly accessible Firebase Storage URL of the file.
        
    Returns:
        Dict containing extraction results or error information.
    """
    try:
        if not file_url:
            raise ValueError("Resume file URL is required.")

        # Validate the URL format
        try:
            # This will raise ValueError if URL is invalid
            _ = requests.utils.urlparse(file_url)
        except Exception:
            raise ValueError("Invalid URL format.")

        # Fetch the file from Firebase Storage
        response = requests.get(
            file_url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; ResumeParser/1.0)",
                "Accept": "application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/octet-stream,*/*",
            },
            allow_redirects=True,
        )
        
        # Handle errors if the file is not accessible
        if not response.ok:
            if response.status_code == 404:
                raise ValueError("File not found. The Firebase download URL may have expired.")
            raise ValueError(f"Failed to fetch file: {response.reason}")

        # Get file content as bytes
        file_content = response.content

        if len(file_content) == 0:
            raise ValueError("Downloaded file is empty.")

        logger.info(f"File downloaded: {len(file_content)} bytes")

        # Determine file type
        content_type = response.headers.get("content-type", "")
        file_type = ""

        if "pdf" in content_type or file_url.lower().endswith(".pdf"):
            file_type = "application/pdf"
        elif ("openxmlformats-officedocument.wordprocessingml.document" in content_type 
              or "msword" in content_type 
              or file_url.lower().endswith(".docx") 
              or file_url.lower().endswith(".doc")):
            file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif "octet-stream" in content_type:
            # Try detecting the file type using its signature
            file_signature = file_content[:4].hex().upper()
            if file_signature == "25504446":
                file_type = "application/pdf"  # PDF
            elif file_signature == "504B0304":
                file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # DOCX (ZIP)
            else:
                raise ValueError("Could not determine file type. Ensure it's a PDF or DOCX.")
        else:
            raise ValueError(f"Unsupported file type: {content_type}. Please upload a PDF or DOCX.")

        # Extract text from the file
        extracted_text = extract_resume_content_server(file_content, file_type)

        if extracted_text and extracted_text.strip():
            return {"success": True, "text": extracted_text, "fileType": file_type}
        else:
            return {
                "success": True,
                "text": "No text could be extracted. The file may be scanned or contain only images.",
                "isEmptyText": True,
            }
            
    except Exception as e:
        logger.error(f"Error in file processing: {str(e)}")
        return {"success": False, "error": str(e)}


def extract_resume_content_server(file_content: bytes, file_type: str) -> str:
    """
    Server-side function to extract content from a resume file (PDF or DOCX).
    
    Args:
        file_content: The file content as bytes
        file_type: MIME type of the file
        
    Returns:
        Extracted text from the resume
    """
    try:
        if file_type == "application/pdf":
            text = extract_text_from_pdf_server(file_content)
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = extract_text_from_docx_server(file_content)
        else:
            raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")

        return text
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        raise ValueError(f"Failed to parse resume: {str(e)}")


def extract_text_from_pdf_server(file_content: bytes) -> str:
    """
    Extracts text from a PDF file using PyMuPDF
    
    Args:
        file_content: The PDF file content as bytes
        
    Returns:
        The extracted text
    """
    try:
        # Create a file-like object from bytes
        file_stream = io.BytesIO(file_content)
        
        # Open the PDF document
        pdf_document = fitz.open(stream=file_stream, filetype="pdf")
        full_text = ""
        
        # Extract text from each page
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            page_text = page.get_text()
            full_text += page_text + "\n"
            
        return full_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise e


def extract_text_from_docx_server(file_content: bytes) -> str:
    """
    Extracts text from a DOCX file using python-docx
    
    Args:
        file_content: The DOCX file content as bytes
        
    Returns:
        The extracted text
    """
    try:
        # Create a file-like object from bytes
        file_stream = io.BytesIO(file_content)
        
        # Open the DOCX document
        doc = docx.Document(file_stream)
        
        # Extract text from paragraphs
        paragraphs = [paragraph.text for paragraph in doc.paragraphs]
        full_text = '\n'.join(paragraphs)
        
        return full_text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        raise e
