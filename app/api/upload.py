# app/api/upload.py
"""
File upload API endpoint for resume tracker.
"""

from flask import Blueprint, request, jsonify, current_app
import logging
import os
import uuid
import time
from werkzeug.utils import secure_filename
from app.services.firebase import parse_resume_from_firebase

# Create blueprint
bp = Blueprint('upload', __name__)
logger = logging.getLogger(__name__)

@bp.route('/upload-file', methods=['POST'])
def upload_file():
    """
    Upload a file (resume) and get back a URL to access it
    
    Returns:
        JSON response with success status and file URL
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file uploaded"
            }), 400
            
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
            
        # Check if file type is allowed
        allowed_extensions = {'pdf', 'doc', 'docx', 'txt'}
        if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({
                "success": False,
                "error": "File type not allowed. Please upload PDF, DOC, DOCX, or TXT files."
            }), 400
            
        # Generate a secure filename
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        original_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{unique_id}_{original_filename}"
        
        # Get upload directory
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'resumes')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        logger.info(f"File saved to {file_path}")
        
        # Generate URL (in production, this would be a properly secured URL)
        file_url = f"/uploads/resumes/{filename}"
        
        # Try to extract text from the file for convenience
        extracted_text = ""
        try:
            # For this example, we'll try to read as text and extract
            with open(file_path, 'rb') as f:
                file_content = f.read()
                
            # Detect file type and extract content
            if file_path.endswith('.pdf') or file_path.endswith('.docx') or file_path.endswith('.doc'):
                # Use mime type based on extension (simplified)
                if file_path.endswith('.pdf'):
                    mime_type = "application/pdf"
                else:
                    mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    
                # We're reusing our existing parsing functionality
                from app.services.firebase import extract_resume_content_server
                extracted_text = extract_resume_content_server(file_content, mime_type)
            elif file_path.endswith('.txt'):
                # For text files, just decode
                extracted_text = file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}")
            # We'll continue even if text extraction fails
        
        return jsonify({
            "success": True,
            "fileUrl": file_url,
            "fileName": original_filename,
            "extractedText": extracted_text if extracted_text else None
        })
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to upload file",
            "details": str(e)
        }), 500