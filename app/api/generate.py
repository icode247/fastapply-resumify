"""
Resume generation API endpoints.
"""
from flask import Blueprint, request, jsonify, send_file
import io
import logging
from app.core.generator import generate_resume_pdf

# Create blueprint
bp = Blueprint('generate', __name__)
logger = logging.getLogger(__name__)

@bp.route('/generate-resume-pdf', methods=['POST'])
def api_generate_resume_pdf():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract user_data and resume_data
        user_data = data.get('user_data')
        resume_data = data.get('resume_data')
        
        if not user_data:
            return jsonify({"error": "Missing user_data"}), 400
        if not resume_data:
            return jsonify({"error": "Missing resume_data"}), 400
        
        # Extract fields from user_data with defaults
        author = user_data.get('author', 'Anonymous')
        email = user_data.get('email', 'abc@xyz.com')
        phone = user_data.get('phone', '00-0000000000')
        address = user_data.get('address', 'XXX')
        
        # Add contact info to resume_data
        resume_data['email'] = email
        resume_data['phone'] = phone
        resume_data['address'] = address
        
        # Generate PDF
        logger.info(f"Generating PDF resume for {author}")
        pdf_content = generate_resume_pdf(author, resume_data)
        
        if not pdf_content:
            return jsonify({"error": "Failed to generate PDF"}), 500
        
        # Return PDF as file response
        return send_file(
            io.BytesIO(pdf_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{author.lower().replace(' ', '_')}_resume.pdf"
        )
    
    except Exception as e:
        logger.error(f"Error generating resume: {str(e)}")
        return jsonify({
            "error": "Failed to generate resume",
            "details": str(e)
        }), 500