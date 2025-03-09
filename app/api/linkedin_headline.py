# app/api/linkedin_headline.py
"""
LinkedIn Headline API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
# from app.utils.redis_cache import cache_response
from app.core.linkedin_headline import LinkedInHeadlineGenerator
from app.utils.validators import validate_request_json

# Create blueprint
bp = Blueprint('linkedin_headline', __name__)
logger = logging.getLogger(__name__)

# Initialize generator
headline_generator = LinkedInHeadlineGenerator()

@bp.route('/generate-linkedin-headline', methods=['POST'])
# @cache_response(expiration=7200)  # Cache for 2 hours
@validate_request_json(['currentRole', 'industry'])
def generate_linkedin_headline():
    """
    Generate a professional LinkedIn headline
    """
    try:
        data = request.get_json()
        
        # Generate LinkedIn headline
        logger.info(f"Generating LinkedIn headline for {data.get('currentRole')} in {data.get('industry')}")
        result = headline_generator.generate_linkedin_headline(data)
        
        if result.get('success', False):
            return jsonify({
                "success": True,
                "data": result
            })
        else:
            logger.error(f"Error generating LinkedIn headline: {result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to generate LinkedIn headline')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate LinkedIn headline",
            "details": str(e)
        }), 500