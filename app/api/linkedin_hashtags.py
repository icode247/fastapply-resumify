# app/api/linkedin_hashtags.py
"""
LinkedIn Hashtags API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
# from app.utils.redis_cache import cache_response
from app.core.linkedin_hashtags import LinkedInHashtagsGenerator
from app.utils.validators import validate_request_json

# Create blueprint
bp = Blueprint('linkedin_hashtags', __name__)
logger = logging.getLogger(__name__)

# Initialize generator
hashtags_generator = LinkedInHashtagsGenerator()

@bp.route('/generate-linkedin-hashtags', methods=['POST'])
# @cache_response(expiration=7200)  # Cache for 2 hours
@validate_request_json(['topic'])
def generate_linkedin_hashtags():
    """
    Generate relevant hashtags for LinkedIn posts
    """
    try:
        data = request.get_json()
        
        # Generate LinkedIn hashtags
        logger.info(f"Generating LinkedIn hashtags for topic: {data.get('topic')}")
        result = hashtags_generator.generate_linkedin_hashtags(data)
        
        if result.get('success', False):
            return jsonify({
                "success": True,
                "data": result
            })
        else:
            logger.error(f"Error generating LinkedIn hashtags: {result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to generate LinkedIn hashtags')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate LinkedIn hashtags",
            "details": str(e)
        }), 500