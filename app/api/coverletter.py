# app/api/coverletter.py
"""
Cover Letter API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
from app.utils.redis_cache import cache_response
from app.core.cover_letter import CoverLetterGenerator
from app.utils.validators import validate_request_json

# Create blueprint
bp = Blueprint('coverletter', __name__)
logger = logging.getLogger(__name__)

# Initialize generator
cover_letter_generator = CoverLetterGenerator()

@bp.route('/generate-cover-letter', methods=['POST'])
@cache_response(expiration=7200)  # Cache for 2 hours
@validate_request_json(['fullName', 'jobTitle', 'company'])
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