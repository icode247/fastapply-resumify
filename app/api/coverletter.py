# app/api/coverletter.py
"""
Cover Letter API endpoints.
"""
from flask import Blueprint, Response, request, jsonify, send_file
import io
import logging
from app.utils.redis_cache import cache_response
from app.core.cover_letter import CoverLetterGenerator
from app.utils.validators import validate_request_json

# Create blueprint
bp = Blueprint('coverletter', __name__)
logger = logging.getLogger(__name__)

# Initialize generator
cover_letter_generator = CoverLetterGenerator()

@bp.route('/generate-cover-letter', methods=['POST'], endpoint='generate_cover_letter')
@cache_response(expiration=7200)  # Cache for 2 hours
# @validate_request_json(['fullName', 'jobTitle', 'company'])
def generate_cover_letter():
    """
    Generate a professional cover letter
    """
    try:
        data = request.get_json()
        
        # Generate cover letter
        logger.info(f"Generating cover letter for {data.get('fullName')} applying to {data.get('company')}")
        result = cover_letter_generator.generate_cover_letter(data)
        
        if result.get('success', False):
            return jsonify({
                "success": True,
                "data": result
            })
        else:
            logger.error(f"Error generating cover letter: {result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to generate cover letter')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate cover letter",
            "details": str(e)
        }), 500

@bp.route('/generate-cover-letter-pdf', methods=['POST'], endpoint='generate_cover_letter_pdf')
def generate_cover_letter_pdf():
    """
    Generate a professional cover letter PDF
    
    Required fields: fullName, jobDescription
    Optional fields: skills, education, fullPositions, tone
    
    fullPositions format: [
        {
            "company": "Company Name",
            "role": "Job Title",
            "type": "Full-time/Internship/etc", 
            "duration": "X months/years",
            "location": "City, State, Country"
        }
    ]
    """
    try:
        # Validate request JSON manually
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Check required fields - only fullName and jobDescription are required now
        required_fields = ['fullName', 'jobDescription']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        # Generate cover letter PDF
        logger.info(f"Generating cover letter PDF for {data.get('fullName')} based on job description")
        
        try:
            pdf_content = cover_letter_generator.generate_cover_letter_pdf(data)
            
            if not pdf_content:
                return jsonify({
                    "success": False,
                    "error": "Failed to generate cover letter PDF"
                }), 500
            
            # Create the response with proper filename
            filename = f"{data.get('fullName', 'cover_letter').lower().replace(' ', '_')}_cover_letter.pdf"
            
            # Return PDF as file response
            response = send_file(
                io.BytesIO(pdf_content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            
            return response
            
        except Exception as pdf_error:
            logger.error(f"PDF Generation Error: {str(pdf_error)}")
            return jsonify({
                "success": False,
                "error": "Failed to generate PDF",
                "details": str(pdf_error)
            }), 500
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate cover letter PDF",
            "details": str(e)
        }), 500
    

@bp.route('/download-cover-letter', methods=['POST'], endpoint='download-cover-letter')
def generate_cover_letter_pdf_endpoint():
    """
    Generate and return a cover letter PDF
    """
    try:
        # Get the letter data from request
        letter_data = request.get_json()
        
        # Validate required fields
        if not letter_data:
            return jsonify({"error": "No data provided"}), 400
            
        required_fields = ['fullName', 'jobDescription']
        missing_fields = [field for field in required_fields if not letter_data.get(field)]
        
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        # Generate the PDF
        generator = CoverLetterGenerator()
        pdf_bytes = generator.generate_cover_letter_pdf(letter_data)
        
        # Return PDF as response
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': 'attachment; filename=cover-letter.pdf',
                'Content-Type': 'application/pdf',
                'Content-Length': str(len(pdf_bytes))
            }
        )
        
    except ValueError as e:
        logging.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        logging.error(f"Error generating cover letter PDF: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500