"""
Resume matching API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
# from app.utils.redis_cache import cache_response
from app.core.matcher import EnhancedResumeJobMatcher
from app.utils.helpers import validate_input, process_for_json

# Create blueprint
bp = Blueprint('match', __name__)
logger = logging.getLogger(__name__)

# Initialize matcher
matcher = EnhancedResumeJobMatcher()

@bp.route('/match', methods=['POST'])
# @cache_response(expiration=3600)  # Cache for 1 hour
def match_resumes():
    try:
        data = request.get_json()
        if not data or 'resume_urls' not in data:
            return jsonify({"error": "No resume URLs provided"}), 400
        
        if 'job_description' not in data:
            return jsonify({"error": "No job description provided"}), 400

        job_description = data['job_description']
        if not validate_input(job_description):
            return jsonify({"error": "Invalid job description"}), 400

        results = []
        resume_urls = data['resume_urls']
        
        highest_score = -1
        best_match = None
        
        for url in resume_urls:
            try:
                result = matcher.process_resume(url, job_description)
                processed_result = process_for_json(result)
                results.append(processed_result)
                
                if processed_result['total_score'] > highest_score:
                    highest_score = processed_result['total_score']
                    best_match = processed_result['resume']
                    
            except Exception as e:
                logger.error(f"Error processing resume URL {url}: {str(e)}")
                continue

        return jsonify({
            "success": True,
            "highest_ranking_resume": best_match
        })

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
