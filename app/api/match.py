"""
Resume matching API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
from app.utils.redis_cache import cache_response
from app.core.matcher import EnhancedResumeJobMatcher
from app.utils.helpers import validate_input, process_for_json

# Create blueprint
bp = Blueprint('match', __name__)
logger = logging.getLogger(__name__)

# Initialize matcher
matcher = EnhancedResumeJobMatcher()

@bp.route('/match', methods=['POST'])
@cache_response(expiration=3600)  # Cache for 1 hour
def match_resumes():
    try:
        data = request.get_json()
        if not data or 'resume_urls' not in data:
            return jsonify({"error": "No resume URLs provided"}), 400
        
        resume_urls = data['resume_urls']
        
        # Check if job description is valid
        job_description_valid = False
        if 'job_description' in data:
            job_description = data['job_description']
            if validate_input(job_description):
                job_description_valid = True
        
        # If job description is invalid or not provided, return first resume as highest ranking
        if not job_description_valid:
            if resume_urls and len(resume_urls) > 0:
                return jsonify({
                    "success": True,
                    "highest_ranking_resume": resume_urls[0]
                })
            else:
                return jsonify({"error": "No resume URLs provided"}), 400
        
        # Normal matching process if job description is valid
        results = []
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