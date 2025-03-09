"""
Resume parsing API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
# from app.utils.redis_cache import cache_response, invalidate_cache
from app.services.firebase import parse_resume_from_firebase

# Create blueprint
bp = Blueprint('parse', __name__)
logger = logging.getLogger(__name__)

@bp.route('/parse-resume', methods=['POST'])
# @cache_response(expiration=3600)  # Cache for 1 hour as parsing is expensive
def parse_resume():
    """
    Parse resume from a Firebase storage URL
    """
    try:
        data = request.get_json()
        
        if not data or 'file_url' not in data:
            return jsonify({"error": "No file URL provided"}), 400
                
        file_url = data['file_url']
        
        # Check if request has a force_refresh parameter
        force_refresh = data.get('force_refresh', False)
        # if force_refresh:
        #     # Invalidate the cache for this specific request
        #     invalidate_cache('/api/parse-resume', data)
        
        # Call the resume parser function
        logger.info(f"Parsing resume from URL: {file_url[:50]}...")
        result = parse_resume_from_firebase(file_url)
        
        # If parsing was successful
        if result.get('success'):
            logger.info(f"Successfully parsed resume, extracted {len(result.get('text', ''))} characters")
            return jsonify(result)
        else:
            # Return error with 400 status
            logger.error(f"Failed to parse resume: {result.get('error', 'Unknown error')}")
            return jsonify(result), 400
                
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        return jsonify({
            "success": False, 
            "error": "Failed to parse resume",
            "details": str(e)
        }), 500
