# app/api/jobdesc.py
"""
Job Description API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
# from app.utils.redis_cache import cache_response
from app.core.job_description import JobDescriptionGenerator
from app.utils.validators import validate_request_json

# Create blueprint
bp = Blueprint('job_description', __name__)
logger = logging.getLogger(__name__)

# Initialize generator
job_desc_generator = JobDescriptionGenerator()

@bp.route('/generate-job-description', methods=['POST'])
# @cache_response(expiration=7200)  # Cache for 2 hours
@validate_request_json(['jobTitle', 'company', 'industry', 'experienceLevel'])
def generate_job_description():
    """
    Generate a professional job description
    """
    try:
        data = request.get_json()
        
        # Generate job description
        logger.info(f"Generating job description for {data.get('jobTitle')} at {data.get('company')}")
        result = job_desc_generator.generate_job_description(data)
        
        if result.get('success', False):
            return jsonify({
                "success": True,
                "data": result
            })
        else:
            logger.error(f"Error generating job description: {result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to generate job description')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate job description",
            "details": str(e)
        }), 500

