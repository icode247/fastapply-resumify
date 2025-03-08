# app/api/resignation.py
"""
Resignation Letter API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
from app.utils.redis_cache import cache_response
from app.core.resignation_letter import ResignationLetterGenerator
from app.utils.validators import validate_request_json

# Create blueprint
bp = Blueprint('resignation', __name__)
logger = logging.getLogger(__name__)

# Initialize generator
resignation_letter_generator = ResignationLetterGenerator()

@bp.route('/generate-resignation-letter', methods=['POST'])
@cache_response(expiration=7200)  # Cache for 2 hours
@validate_request_json(['fullName', 'currentPosition', 'company', 'lastDay'])
def generate_resignation_letter():
    """
    Generate a professional resignation letter
    """
    try:
        data = request.get_json()
        
        # Generate resignation letter
        logger.info(f"Generating resignation letter for {data.get('fullName')} at {data.get('company')}")
        result = resignation_letter_generator.generate_resignation_letter(data)
        
        if result.get('success', False):
            return jsonify({
                "success": True,
                "data": result
            })
        else:
            logger.error(f"Error generating resignation letter: {result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to generate resignation letter')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate resignation letter",
            "details": str(e)
        }), 500