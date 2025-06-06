# app/api/job_tracking.py
"""
Job Tracking API endpoints.
"""
from flask import Blueprint, request, jsonify
import logging
import requests
import os
from datetime import datetime, timedelta
from functools import wraps
from app.utils.redis_cache import cache_response
from app.utils.validators import validate_input
from app.services.job_status_checker import JobStatusChecker

# Create blueprint
bp = Blueprint('job_tracking', __name__)
logger = logging.getLogger(__name__)

# Firebase API configuration
FIREBASE_API_URL = os.environ.get('FIREBASE_API_URL', 'https://your-api-domain.com')
FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', 'your-firebase-api-key')

# Authentication decorator
# def authenticate(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         auth_header = request.headers.get('Authorization')
#         if not auth_header or not auth_header.startswith('Bearer '):
#             return jsonify({"success": False, "error": "Unauthorized"}), 401
        
#         token = auth_header.split(' ')[1]
        
#         # Verify token with Firebase
#         try:
#             response = requests.post(
#                 f"{FIREBASE_API_URL}/api/auth/verify",
#                 json={"token": token, "api_key": FIREBASE_API_KEY}
#             )
            
#             if response.status_code != 200:
#                 return jsonify({"success": False, "error": "Invalid token"}), 401
            
#             auth_data = response.json().get("data", {})
#             request.user = auth_data.get("user", {})
            
#             return f(*args, **kwargs)
            
#         except Exception as e:
#             logger.error(f"Authentication error: {str(e)}")
#             return jsonify({"success": False, "error": "Authentication failed"}), 401
            
#     return decorated_function

@bp.route('/track', methods=['POST'])
# @authenticate
@validate_input(['url'])
def track_job():
    """
    Track a new job application
    """
    try:
        data = request.get_json()
        user_id = request.user.get("uid")
        
        url = data.get('url')
        job_title = data.get('jobTitle')
        company_name = data.get('companyName')
        
        if not url or not url.startswith('https://www.linkedin.com/jobs'):
            return jsonify({
                "success": False,
                "error": "Invalid LinkedIn job URL"
            }), 400
        
        # Add job to Firebase via API
        response = requests.post(
            f"{FIREBASE_API_URL}/api/job-tracking",
            json={
                "api_key": FIREBASE_API_KEY,
                "userId": user_id,
                "url": url,
                "jobTitle": job_title,
                "companyName": company_name,
            }
        )
        
        if response.status_code != 201:
            return jsonify({
                "success": False,
                "error": f"Failed to track job: {response.text}"
            }), response.status_code
        
        data = response.json()
        
        # Check job status immediately if requested
        if request.args.get('checkNow') == 'true':
            job_id = data.get("data", {}).get("id")
            
            if job_id:
                # Initialize checker and check job status
                checker = JobStatusChecker(FIREBASE_API_URL, FIREBASE_API_KEY)
                status = checker.check_job_status(url)
                
                # Update job status in Firebase
                checker.update_job_status_in_firebase(job_id, status)
                
                # Include status in response
                data["data"]["initialStatus"] = status
        
        return jsonify(data), 201
        
    except Exception as e:
        logger.error(f"Error tracking job: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to track job application"
        }), 500

@bp.route('/list', methods=['GET'])
# @authenticate
@cache_response(expiration=300)  # Cache for 5 minutes
def list_jobs():
    """
    Get all tracked job applications for a user
    """
    try:
        user_id = request.user.get("uid")
        status = request.args.get('status')
        page = request.args.get('page', '1')
        limit = request.args.get('limit', '20')
        
        # Get jobs from Firebase via API
        params = {
            "api_key": FIREBASE_API_KEY,
            "userId": user_id,
            "page": page,
            "limit": limit
        }
        
        if status:
            params["status"] = status
        
        response = requests.get(
            f"{FIREBASE_API_URL}/api/job-tracking",
            params=params
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": f"Failed to fetch jobs: {response.text}"
            }), response.status_code
        
        return jsonify(response.json()), 200
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to list job applications"
        }), 500

@bp.route('/<job_id>', methods=['GET'])
# @authenticate
@cache_response(expiration=300)  # Cache for 5 minutes
def get_job(job_id):
    """
    Get a specific job application
    """
    try:
        user_id = request.user.get("uid")
        
        # Get job from Firebase via API
        response = requests.get(
            f"{FIREBASE_API_URL}/api/job-tracking/{job_id}",
            params={
                "api_key": FIREBASE_API_KEY,
                "userId": user_id
            }
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": f"Failed to fetch job: {response.text}"
            }), response.status_code
        
        return jsonify(response.json()), 200
        
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get job application"
        }), 500

@bp.route('/<job_id>/refresh', methods=['POST'])
# @authenticate
def refresh_job(job_id):
    """
    Manually refresh job status
    """
    try:
        user_id = request.user.get("uid")
        
        # Get job details to verify ownership and get URL
        response = requests.get(
            f"{FIREBASE_API_URL}/api/job-tracking/{job_id}",
            params={
                "api_key": FIREBASE_API_KEY,
                "userId": user_id
            }
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": "Job not found or access denied"
            }), 404
        
        job_data = response.json().get("data", {})
        job_url = job_data.get("url")
        
        if not job_url:
            return jsonify({
                "success": False,
                "error": "Job URL not found"
            }), 400
        
        # Check job status
        checker = JobStatusChecker(FIREBASE_API_URL, FIREBASE_API_KEY)
        status = checker.check_job_status(job_url)
        
        # Update job status in Firebase
        success = checker.update_job_status_in_firebase(job_id, status)
        
        if not success:
            return jsonify({
                "success": False,
                "error": "Failed to update job status"
            }), 500
        
        # Calculate next check date
        next_check_days = 14 if status.get("status") == "CLOSED" else 3
        next_check_at = datetime.now() + timedelta(days=next_check_days)
        
        return jsonify({
            "success": True,
            "data": {
                **status,
                "nextCheckAt": next_check_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error refreshing job {job_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to refresh job status"
        }), 500

@bp.route('/<job_id>', methods=['DELETE'])
# @authenticate
def delete_job(job_id):
    """
    Delete a job application
    """
    try:
        user_id = request.user.get("uid")
        
        # Delete job from Firebase via API
        response = requests.delete(
            f"{FIREBASE_API_URL}/api/job-tracking/{job_id}",
            params={
                "api_key": FIREBASE_API_KEY,
                "userId": user_id
            }
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": f"Failed to delete job: {response.text}"
            }), response.status_code
        
        return jsonify({
            "success": True,
            "message": "Job tracking removed successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to delete job application"
        }), 500

@bp.route('/status/summary', methods=['GET'])
# @authenticate
@cache_response(expiration=3600)  # Cache for 1 hour
def job_status_summary():
    """
    Get a summary of job application statuses for a user
    """
    try:
        user_id = request.user.get("uid")
        
        # Get status summary from Firebase via API
        response = requests.get(
            f"{FIREBASE_API_URL}/api/job-tracking/summary",
            params={
                "api_key": FIREBASE_API_KEY,
                "userId": user_id
            }
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": f"Failed to fetch status summary: {response.text}"
            }), response.status_code
        
        return jsonify(response.json()), 200
        
    except Exception as e:
        logger.error(f"Error getting status summary: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get status summary"
        }), 500

@bp.route('/pending/count', methods=['GET'])
def get_pending_count():
    """
    Get count of jobs pending status check (for worker/scheduler)
    Requires API key authentication
    """
    try:
        api_key = request.args.get('api_key')
        
        if not api_key or api_key != FIREBASE_API_KEY:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 401
        
        # Get count of pending jobs from Firebase via API
        response = requests.get(
            f"{FIREBASE_API_URL}/api/job-tracking/pending-count",
            params={"api_key": FIREBASE_API_KEY}
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": f"Failed to fetch pending count: {response.text}"
            }), response.status_code
        
        return jsonify(response.json()), 200
        
    except Exception as e:
        logger.error(f"Error getting pending count: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get pending count"
        }), 500

@bp.route('/pending', methods=['GET'])
def get_pending_jobs():
    """
    Get jobs pending status check (for worker/scheduler)
    Requires API key authentication
    """
    try:
        api_key = request.args.get('api_key')
        limit = request.args.get('limit', '50')
        
        if not api_key or api_key != FIREBASE_API_KEY:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 401
        
        # Get pending jobs from Firebase via API
        response = requests.get(
            f"{FIREBASE_API_URL}/api/job-tracking/pending",
            params={
                "api_key": FIREBASE_API_KEY,
                "limit": limit
            }
        )
        
        if response.status_code != 200:
            return jsonify({
                "success": False,
                "error": f"Failed to fetch pending jobs: {response.text}"
            }), response.status_code
        
        return jsonify(response.json()), 200
        
    except Exception as e:
        logger.error(f"Error getting pending jobs: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get pending jobs"
        }), 500

@bp.route('/batch-process', methods=['POST'])
def batch_process_jobs():
    """
    Process a batch of jobs (for worker/scheduler)
    Requires API key authentication
    """
    try:
        # Verify API key
        data = request.get_json()
        api_key = data.get('api_key')
        
        if not api_key or api_key != FIREBASE_API_KEY:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 401
        
        # Get job URLs to process
        job_data = data.get('jobs', [])
        if not job_data:
            return jsonify({
                "success": False,
                "error": "No jobs provided"
            }), 400
        
        # Extract URLs and IDs
        job_urls = [job.get('url') for job in job_data if job.get('url')]
        job_id_map = {job.get('url'): job.get('id') for job in job_data if job.get('url') and job.get('id')}
        
        if not job_urls:
            return jsonify({
                "success": False,
                "error": "No valid job URLs provided"
            }), 400
        
        # Process the job batch
        checker = JobStatusChecker(FIREBASE_API_URL, FIREBASE_API_KEY)
        results = checker.process_batch(job_urls)
        
        # Update jobs in Firebase
        updated_count = 0
        updated_jobs = []
        
        for result in results:
            job_url = result.get('url')
            job_id = job_id_map.get(job_url)
            
            if not job_id:
                continue
            
            success = checker.update_job_status_in_firebase(job_id, result)
            if success:
                updated_count += 1
                updated_jobs.append({
                    'id': job_id,
                    'status': result.get('status'),
                    'isActive': result.get('is_active')
                })
        
        return jsonify({
            "success": True,
            "data": {
                "processed": len(results),
                "updated": updated_count,
                "jobs": updated_jobs
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error batch processing jobs: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to process job batch"
        }), 500