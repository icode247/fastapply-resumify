"""
AI-powered job matching API endpoints.
Provides intelligent job-candidate matching analysis.
"""
from flask import Blueprint, request, jsonify
import logging
from app.services.job_matcher_ai import JobMatcherAI
from app.utils.redis_cache import cache_response
from functools import wraps

bp = Blueprint('job_match_ai', __name__)
logger = logging.getLogger(__name__)

# Initialize the AI matcher
try:
    matcher = JobMatcherAI()
except Exception as e:
    logger.error(f"Failed to initialize JobMatcherAI: {str(e)}")
    matcher = None


def require_matcher(f):
    """Decorator to ensure matcher is initialized."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if matcher is None:
            return jsonify({
                "error": "Job matcher service unavailable. Please check OPENAI_API_KEY configuration."
            }), 503
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/job-match/analyze', methods=['POST'])
@require_matcher
def analyze_job_match():
    """
    STRICT AI job matching analysis - prevents wasting time on mismatched jobs.

    Validation Process:
    1. First validates ALL candidate preferences against job information (language, location, salary, company blacklist, industry, etc.)
    2. If apply_only_qualified=true, also validates resume against job requirements
    3. If apply_only_qualified=false, only checks preferences (allows applying even if not fully qualified)
    4. Returns shouldApply=false if matchScore < 70 OR any critical mismatch exists
    
    Request body:
    {
        "resume_text": "string (required)",
        "job_information": {
            "title": "string",
            "company": "string (optional - can be extracted from description)",
            "industry": "string (optional - can be inferred from description/title)",
            "description": "string",
            "requirements": "string",
            "location": "string",
            "salary": "string",
            "type": "remote|hybrid|onsite",
            "experience_required": "string",
            "languages_required": ["string"] (optional - can be extracted from description)
        },
        "job_preferences": {
            "jobType": ["Full-time", "Part-time", "Contract"] (optional),
            "experience": ["Entry level", "Internship", "Associate", "Mid-Senior level"] (optional),
            "salary": [min, max] (optional - array of two numbers),
            "city": "string" (optional),
            "location": "string" (optional - country),
            "positions": ["Software Engineer", "..."] (optional),
            "remoteOnly": boolean (optional - default false),
            "workMode": ["Remote", "Hybrid", "On-Site"] (optional),
            "language": ["English", "Spanish", "..."] (optional),
            "industry": ["Technology", "Healthcare", "..."] (optional),
            "companyBlacklist": ["string"] (optional),
            "deal_breakers": ["string"] (optional)
        },
        "apply_only_qualified": boolean (optional - default: true)
    }
    
    Response:
    {
        "success": true,
        "data": {
            "shouldApply": boolean,
            "reason": "string (max 20 words)",
            "matchScore": number (0-100),
            "mismatches": ["string"]
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                "error": "Request body is required"
            }), 400
        
        resume_text = data.get('resume_text')
        if not resume_text:
            return jsonify({
                "error": "resume_text is required"
            }), 400
        
        job_information = data.get('job_information')
        if not job_information:
            return jsonify({
                "error": "job_information is required"
            }), 400
        
        job_preferences = data.get('job_preferences', {})
        apply_only_qualified = data.get('apply_only_qualified', True)  # Default to True for backward compatibility

        # Perform analysis
        result = matcher.analyze_job_match(
            resume_text=resume_text,
            job_information=job_information,
            job_preferences=job_preferences,
            apply_only_qualified=apply_only_qualified
        )
        
        return jsonify({
            "success": True,
            "data": result
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error in job match analysis: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to analyze job match. Please try again."
        }), 500


@bp.route('/job-match/batch-analyze', methods=['POST'])
@require_matcher
def batch_analyze_jobs():
    """
    Analyze multiple jobs at once for a candidate.
    
    Request body:
    {
        "resume_text": "string (required)",
        "jobs": [
            {
                "id": "string (optional)",
                "title": "string",
                "description": "string",
                ...
            }
        ],
        "job_preferences": {
            "locations": ["string"],
            ...
        }
    }
    
    Response:
    {
        "success": true,
        "data": [
            {
                "job_id": "string",
                "job_title": "string",
                "shouldApply": boolean,
                "reason": "string",
                "matchScore": number,
                "mismatches": ["string"]
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                "error": "Request body is required"
            }), 400
        
        resume_text = data.get('resume_text')
        if not resume_text:
            return jsonify({
                "error": "resume_text is required"
            }), 400
        
        jobs = data.get('jobs')
        if not jobs or not isinstance(jobs, list):
            return jsonify({
                "error": "jobs must be a non-empty array"
            }), 400
        
        if len(jobs) > 50:
            return jsonify({
                "error": "Maximum 50 jobs can be analyzed at once"
            }), 400
        
        job_preferences = data.get('job_preferences', {})
        
        # Perform batch analysis
        results = matcher.batch_analyze_jobs(
            resume_text=resume_text,
            jobs=jobs,
            job_preferences=job_preferences
        )
        
        return jsonify({
            "success": True,
            "data": results,
            "total_analyzed": len(results),
            "should_apply_count": sum(1 for r in results if r.get('shouldApply', False))
        }), 200
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error in batch job analysis: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to analyze jobs. Please try again."
        }), 500


@bp.route('/job-match/health', methods=['GET'])
def health_check():
    """
    Check if the job matcher service is available.
    
    Response:
    {
        "status": "healthy|unavailable",
        "service": "job_match_ai",
        "matcher_initialized": boolean
    }
    """
    return jsonify({
        "status": "healthy" if matcher is not None else "unavailable",
        "service": "job_match_ai",
        "matcher_initialized": matcher is not None
    }), 200 if matcher is not None else 503
