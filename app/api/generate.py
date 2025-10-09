"""
Resume generation API endpoints.
"""
from flask import Blueprint, request, jsonify, send_file
import io
import logging
from app.core.generator import generate_resume_pdf
from app.core.docx_generator import generate_resume_docx

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

@bp.route('/generate-resume-docx', methods=['POST'])
def api_generate_resume_docx():
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
        
        # Generate DOCX
        logger.info(f"Generating DOCX resume for {author}")
        docx_content = generate_resume_docx(author, resume_data)
        
        if not docx_content:
            return jsonify({"error": "Failed to generate DOCX"}), 500
        
        # Return DOCX as file response
        return send_file(
            io.BytesIO(docx_content),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f"{author.lower().replace(' ', '_')}_resume.docx"
        )
    
    except Exception as e:
        logger.error(f"Error generating DOCX resume: {str(e)}")
        return jsonify({
            "error": "Failed to generate resume",
            "details": str(e)
        }), 500

@bp.route('/generate-resume', methods=['POST'])
def api_generate_resume():
    """Generate resume in specified format (PDF or DOCX)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract user_data and resume_data
        user_data = data.get('user_data')
        resume_data = data.get('resume_data')
        format_type = data.get('format', 'docx').lower()  # Default to DOCX for ATS compatibility
        
        if not user_data:
            return jsonify({"error": "Missing user_data"}), 400
        if not resume_data:
            return jsonify({"error": "Missing resume_data"}), 400
        if format_type not in ['pdf', 'docx']:
            return jsonify({"error": "Format must be 'pdf' or 'docx'"}), 400
            
        # Extract fields from user_data with defaults
        author = user_data.get('author', 'Anonymous')
        email = user_data.get('email', 'abc@xyz.com')
        phone = user_data.get('phone', '00-0000000000')
        address = user_data.get('address', 'XXX')

        # Add contact info to resume_data
        resume_data['email'] = email
        resume_data['phone'] = phone
        resume_data['address'] = address
        
        if format_type == 'docx':
            # Generate DOCX (ATS-friendly)
            logger.info(f"Generating ATS-optimized DOCX resume for {author}")
            content = generate_resume_docx(author, resume_data)
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            filename = f"{author.lower().replace(' ', '_')}_resume.docx"
        else:
            # Generate PDF
            logger.info(f"Generating PDF resume for {author}")
            content = generate_resume_pdf(author, resume_data)
            mimetype = 'application/pdf'
            filename = f"{author.lower().replace(' ', '_')}_resume.pdf"
        
        if not content:
            return jsonify({"error": f"Failed to generate {format_type.upper()}"}), 500
        
        # Return file response
        return send_file(
            io.BytesIO(content),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Error generating resume: {str(e)}")
        return jsonify({
            "error": "Failed to generate resume",
            "details": str(e)
        }), 500