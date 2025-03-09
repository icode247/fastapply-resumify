# app/api/interview.py
"""
Interview Answer API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
from app.utils.redis_cache import cache_response
from app.core.interview_answer import InterviewAnswerGenerator
from app.utils.validators import validate_request_json

# Create blueprint
bp = Blueprint('interview', __name__)
logger = logging.getLogger(__name__)

# Initialize generator
interview_answer_generator = InterviewAnswerGenerator()

@bp.route('/generate-interview-answer', methods=['POST'], endpoint='generate_interview_answer')
@cache_response(expiration=7200)  # Cache for 2 hours
@validate_request_json(['company', 'jobTitle', 'question'])
def generate_interview_answer():
    """
    Generate a professional interview answer
    """
    try:
        data = request.get_json()
        
        # Generate interview answer
        logger.info(f"Generating interview answer for {data.get('jobTitle')} at {data.get('company')}")
        result = interview_answer_generator.generate_interview_answer(data)
        
        if result.get('success', False):
            return jsonify({
                "success": True,
                "data": result
            })
        else:
            logger.error(f"Error generating interview answer: {result.get('error', 'Unknown error')}")
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to generate interview answer')
            }), 400
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to generate interview answer",
            "details": str(e)
        }), 500

@bp.route('/common-questions', methods=['GET'], endpoint='common_questions')
@cache_response(expiration=86400)  # Cache for 24 hours
def get_common_questions():
    """
    Get a list of common interview questions by company and/or category
    """
    try:
        company = request.args.get('company', '').lower()
        category = request.args.get('category', '').lower()
        role_type = request.args.get('roleType', '').lower()
        
        # Get questions from the generator
        questions = list(interview_answer_generator.common_questions.values())
        
        # Filter by category if provided
        if category:
            questions = [q for q in questions if q.get('category', '').lower() == category]
            
        # Format response data
        question_data = [{
            'id': i,
            'question': q['question'],
            'category': q['category'],
            'tips': q.get('tips', [])
        } for i, q in enumerate(questions)]
        
        return jsonify({
            "success": True,
            "data": {
                "questions": question_data
            }
        })
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve common questions",
            "details": str(e)
        }), 500

@bp.route('/company-data', methods=['GET'], endpoint='company_data')
@cache_response(expiration=86400)  # Cache for 24 hours
def get_company_data():
    """
    Get data about top companies for interview preparation
    """
    try:
        company_name = request.args.get('company', '').lower()
        
        if company_name:
            # Return data for specific company
            company_data = interview_answer_generator.get_company_data(company_name)
            return jsonify({
                "success": True,
                "data": {
                    "company": company_name,
                    "details": company_data
                }
            })
        else:
            # Return list of all companies
            companies = []
            for company, data in interview_answer_generator.company_data.items():
                companies.append({
                    "name": company,
                    "culture": data.get("culture", "").split(", ")[0],
                    "keyTraits": data.get("key_traits", "").split(", ")[:2]
                })
                
            return jsonify({
                "success": True,
                "data": {
                    "companies": companies
                }
            })
            
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve company data",
            "details": str(e)
        }), 500