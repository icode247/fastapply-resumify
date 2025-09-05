# app/api/intelligent_parse.py
"""
Intelligent Resume Parsing API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
from app.utils.redis_cache import cache_response
from app.core.intelligent_resume_parser import IntelligentResumeParser
from app.services.firebase import parse_resume_from_firebase
from app.utils.validators import validate_input
import requests

# Create blueprint
bp = Blueprint('intelligent_parse', __name__)
logger = logging.getLogger(__name__)

# Initialize parser
intelligent_parser = IntelligentResumeParser()

@bp.route('/intelligent-parse-resume', methods=['POST'])
@cache_response(expiration=3600)  # Cache for 1 hour
def intelligent_parse_resume():
    """
    Intelligently parse resume from file
    
    Expected payload:
    {
        "file_url": "Firebase URL to resume file"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'file_url' not in data:
            return jsonify({"error": "No file URL provided"}), 400
                
        file_url = data['file_url']
        
        # Step 1: Extract text from resume file
        logger.info(f"Extracting text from resume: {file_url[:50]}...")
        parse_result = parse_resume_from_firebase(file_url)
        print(parse_result)
        
        if not parse_result.get('success'):
            logger.error(f"Failed to extract text from resume: {parse_result.get('error')}")
            return jsonify({
                "success": False,
                "error": f"Failed to extract text from resume: {parse_result.get('error')}"
            }), 400
        
        resume_text = parse_result.get('text', '')
        
        if not resume_text:
            return jsonify({
                "success": False,
                "error": "No valid text could be extracted from the resume"
            }), 400
        
        # Step 2: Parse resume into structured data
        logger.info("Parsing resume into structured data...")
        result = intelligent_parser.parse_resume_to_structured_data(resume_text)
        
        if result.get('success'):
            logger.info("Successfully parsed resume data")
            return jsonify({
                "success": True,
                "data": result,
                "extracted_text_length": len(resume_text)
            })
        else:
            logger.error(f"Failed to parse resume: {result.get('error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to parse resume'),
                "fallback_data": result.get('fallback_data')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to process resume",
            "details": str(e)
        }), 500

@bp.route('/parse-resume-text', methods=['POST'])
@cache_response(expiration=3600)  # Cache for 1 hour
def parse_resume_text():
    """
    Parse resume from direct text input (no file upload needed)
    
    Expected payload:
    {
        "resume_text": "Raw resume text"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'resume_text' not in data:
            return jsonify({"error": "No resume text provided"}), 400
                
        resume_text = data['resume_text']
        
        if not resume_text or not validate_input(resume_text):
            return jsonify({
                "success": False,
                "error": "Resume text is too short or invalid"
            }), 400
        
        # Parse resume into structured data
        logger.info("Parsing resume text into structured data...")
        result = intelligent_parser.parse_resume_to_structured_data(resume_text)
        
        if result.get('success'):
            logger.info("Successfully parsed resume text")
            return jsonify({
                "success": True,
                "data": result
            })
        else:
            logger.error(f"Failed to parse resume text: {result.get('error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to parse resume text'),
                "fallback_data": result.get('fallback_data')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to process resume text",
            "details": str(e)
        }), 500

@bp.route('/merge-data', methods=['POST'])
def merge_resume_linkedin_data():
    """
    Merge already parsed resume data with LinkedIn data
    
    Expected payload:
    {
        "resume_data": {...},
        "linkedin_data": {...} // Optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        resume_data = data.get('resume_data', {})
        linkedin_data = data.get('linkedin_data', {})
        
        if not resume_data:
            return jsonify({"error": "resume_data is required"}), 400
        
        # Parse the resume data (no merging needed)
        logger.info("Processing resume data...")
        result = intelligent_parser.parse_resume_to_structured_data(str(resume_data))
        
        if result.get('success'):
            logger.info("Successfully merged data")
            return jsonify({
                "success": True,
                "data": result
            })
        else:
            logger.error(f"Failed to merge data: {result.get('error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to merge data'),
                "fallback_data": result.get('fallback_data')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to merge data",
            "details": str(e)
        }), 500