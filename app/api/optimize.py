"""
Resume optimization API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
from app.utils.redis_cache import cache_response
from app.services.resume_processor import ATSResumeProcessor
import os
# Create blueprint
bp = Blueprint('optimize', __name__)
logger = logging.getLogger(__name__)
api_token = os.environ.get("OPENAI_API_KEY", "")
# Initialize resume processor
resume_processor = ATSResumeProcessor(api_token)

@bp.route('/optimize-resume', methods=['POST'])
@cache_response(expiration=7200)  
def optimize_resume():
    """
    Endpoint to optimize a resume for ATS based on a job description
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Check for required fields
        resume_text = data.get('resume_text')
        job_description = data.get('job_description')
        user_data = data.get('user_data')
        
        if not resume_text:
            return jsonify({"error": "No resume text provided"}), 400
        
        if not user_data:
            return jsonify({"error": "user data provided"}), 400
            
        if not job_description:
            return jsonify({"error": "No job description provided"}), 400
            
        # Process the resume
        try:
            logger.info("Processing resume for optimization")
            optimized_resume = resume_processor.process_resume_pdf(resume_text, job_description, user_data)
            return jsonify({
                "success": True,
                "data": optimized_resume
            })
            
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            return jsonify({"error": f"Error processing resume: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "error": "Failed to optimize resume",
            "details": str(e)
        }), 500

@bp.route('/generate-resume', methods=['POST'])
@cache_response(expiration=7200)  
def generate_resume():
    try:
        job_description = request.json.get('job_description')
        resume_text = request.json.get('resume_text', '')
        user_data = request.json.get('user_data')

        if not job_description or not resume_text:
            return jsonify({"error": "Missing required fields"}), 400

        if not user_data:
            return jsonify({"error": "User data is required"}), 400

        optimized_data = resume_processor.process_resume(resume_text, job_description, user_data)
        return jsonify({
            "success": True,
            "data": optimized_data
        })

    except Exception as error:
        logger.error(f"API Error: {str(error)}")
        return jsonify({
            "error": "Failed to generate resume",
            "details": str(error)
        }), 500
