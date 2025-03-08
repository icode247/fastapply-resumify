# app/api/linkedin.py
"""
LinkedIn feature API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
from app.utils.redis_cache import cache_response
from app.core.linkedin_summary import LinkedInSummaryGenerator
from app.core.linkedin_post import LinkedInPostGenerator
from app.core.linkedin_recommendation import LinkedInRecommendationGenerator
from app.utils.validators import validate_request_json

# Create blueprint
bp = Blueprint('linkedin_features', __name__)
logger = logging.getLogger(__name__)

# Initialize generators
summary_generator = LinkedInSummaryGenerator()
post_generator = LinkedInPostGenerator()
recommendation_generator = LinkedInRecommendationGenerator()

@bp.route('/generate-linkedin-summary', methods=['POST'], endpoint='generate_linkedin_summary')
@cache_response(expiration=7200)  # Cache for 2 hours
@validate_request_json(['jobTitle', 'industry', 'keySkills'])
def generate_linkedin_summary():
    """
    Generate a professional LinkedIn summary
    """
    try:
        data = request.get_json()
        
        # Generate LinkedIn summary
        logger.info(f"Generating LinkedIn summary for {data.get('jobTitle')} in {data.get('industry')}")
        result = summary_generator.generate_linkedin_summary(data)
        
        if result.get('success', False):
            return jsonify({
                "success": True,
                "data": result
            })
        else:
            logger.error(f"Error generating LinkedIn summary: {result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to generate LinkedIn summary')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate LinkedIn summary",
            "details": str(e)
        }), 500

@bp.route('/generate-linkedin-post', methods=['POST'], endpoint='generate_linkedin-post')
@cache_response(expiration=7200)  # Cache for 2 hours
@validate_request_json(['topic', 'purpose'])
def generate_linkedin_post():
    """
    Generate an engaging LinkedIn post
    """
    try:
        data = request.get_json()
        
        # Generate LinkedIn post
        logger.info(f"Generating LinkedIn post about {data.get('topic')}")
        result = post_generator.generate_linkedin_post(data)
        
        if result.get('success', False):
            return jsonify({
                "success": True,
                "data": result
            })
        else:
            logger.error(f"Error generating LinkedIn post: {result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to generate LinkedIn post')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate LinkedIn post",
            "details": str(e)
        }), 500

@bp.route('/generate-linkedin-recommendation', methods=['POST'], endpoint='generate-linkedin-recommendation')
@cache_response(expiration=7200)  # Cache for 2 hours
@validate_request_json(['yourName', 'recipientName', 'recipientTitle', 'keyStrengths'])
def generate_linkedin_recommendation():
    """
    Generate a personalized LinkedIn recommendation
    """
    try:
        data = request.get_json()
        
        # Generate LinkedIn recommendation
        logger.info(f"Generating LinkedIn recommendation for {data.get('recipientName')}")
        result = recommendation_generator.generate_linkedin_recommendation(data)
        
        if result.get('success', False):
            return jsonify({
                "success": True,
                "data": result
            })
        else:
            logger.error(f"Error generating LinkedIn recommendation: {result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to generate LinkedIn recommendation')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate LinkedIn recommendation",
            "details": str(e)
        }), 500