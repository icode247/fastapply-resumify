# app/api/resume_score.py
"""
Resume Scoring API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
from app.utils.redis_cache import cache_response
from app.core.resume_score import ResumeScorer
from app.services.firebase import parse_resume_from_firebase
from app.utils.validators import validate_input

# Create blueprint
bp = Blueprint('resume_score', __name__)
logger = logging.getLogger(__name__)

# Initialize scorer
resume_scorer = ResumeScorer()

@bp.route('/score-resume', methods=['POST'])
@cache_response(expiration=7200)  # Cache for 2 hours
def score_resume():
    """
    Score a resume based on best practices and optionally a job description
    
    Request can include:
    - resume_text: Direct text of the resume to score
    - file_url: Firebase URL to a resume file (PDF, DOCX)
    - job_description: Optional job description to evaluate against
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get job description if provided
        job_description = data.get('job_description', '')
        
        # Determine the source of resume text
        resume_text = None
        
        # Option 1: Direct resume text input
        if 'resume_text' in data and data['resume_text']:
            resume_text = data['resume_text']
            logger.info(f"Using provided resume text of length: {len(resume_text)}")
            
        # Option 2: File URL (parse it first)
        elif 'file_url' in data and data['file_url']:
            file_url = data['file_url']
            logger.info(f"Parsing resume from URL: {file_url[:50]}...")
            
            # Use the existing parsing functionality
            parse_result = parse_resume_from_firebase(file_url)
            
            if not parse_result.get('success', False):
                return jsonify({
                    "success": False,
                    "error": f"Failed to parse resume: {parse_result.get('error', 'Unknown error')}"
                }), 400
                
            resume_text = parse_result.get('text', '')
            logger.info(f"Successfully parsed resume: {len(resume_text)} characters")
        
        # Validate we have resume text to analyze
        if not resume_text or not validate_input(resume_text):
            return jsonify({"error": "No valid resume text provided"}), 400
            
        # Score the resume
        score_result = resume_scorer.score_resume(resume_text, job_description if job_description else None)
        
        if score_result.get('success', False):
            return jsonify({
                "success": True,
                "data": score_result
            })
        else:
            logger.error(f"Error scoring resume: {score_result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": score_result.get('error', 'Failed to score resume')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to score resume",
            "details": str(e)
        }), 500

@bp.route('/improve-resume', methods=['POST'])
@cache_response(expiration=7200)  # Cache for 2 hours
def improve_resume():
    """
    Generate an improved version of a resume
    
    Request can include:
    - resume_text: Direct text of the resume to improve
    - file_url: Firebase URL to a resume file (PDF, DOCX)
    - job_description: Optional job description to target the resume toward
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get job description if provided
        job_description = data.get('job_description', '')
        
        # Determine the source of resume text
        resume_text = None
        
        # Option 1: Direct resume text input
        if 'resume_text' in data and data['resume_text']:
            resume_text = data['resume_text']
            logger.info(f"Using provided resume text of length: {len(resume_text)}")
            
        # Option 2: File URL (parse it first)
        elif 'file_url' in data and data['file_url']:
            file_url = data['file_url']
            logger.info(f"Parsing resume from URL: {file_url[:50]}...")
            
            # Use the existing parsing functionality
            parse_result = parse_resume_from_firebase(file_url)
            
            if not parse_result.get('success', False):
                return jsonify({
                    "success": False,
                    "error": f"Failed to parse resume: {parse_result.get('error', 'Unknown error')}"
                }), 400
                
            resume_text = parse_result.get('text', '')
            logger.info(f"Successfully parsed resume: {len(resume_text)} characters")
        
        # Validate we have resume text to analyze
        if not resume_text or not validate_input(resume_text):
            return jsonify({"error": "No valid resume text provided"}), 400
            
        # Generate improved resume
        improved_result = resume_scorer.generate_improved_resume(resume_text, job_description if job_description else None)
        
        if improved_result.get('success', False):
            return jsonify({
                "success": True,
                "data": improved_result
            })
        else:
            logger.error(f"Error improving resume: {improved_result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": improved_result.get('error', 'Failed to improve resume')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to improve resume",
            "details": str(e)
        }), 500