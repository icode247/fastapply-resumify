# app/api/resume_tracker.py
"""
API endpoints for the Resume Tracker feature.
"""
from flask import Blueprint, request, jsonify, current_app
import logging
# from app.utils.redis_cache import cache_response
from app.services.resume_tracker import ResumeTrackerService

# Create blueprint
bp = Blueprint('resume_tracker', __name__)
logger = logging.getLogger(__name__)

# Initialize service
tracker_service = ResumeTrackerService()

# Helper function to get user ID
def get_user_id():
    """
    Get user ID from request (simplified for now).
    In a real application, this would extract the user ID from authentication.
    """
    # This is a simplified approach - in production, extract from a JWT token or session
    user_id = request.headers.get('X-User-ID', 'default_user')
    return user_id

# Resume Version Endpoints

@bp.route('/resume-versions', methods=['GET'])
# @cache_response(expiration=300)  # Cache for 5 minutes
def get_resume_versions():
    """Get all resume versions for a user"""
    try:
        user_id = get_user_id()
        versions = tracker_service.get_resume_versions(user_id)
        
        return jsonify({
            "success": True,
            "data": versions
        })
    except Exception as e:
        logger.error(f"Error retrieving resume versions: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve resume versions",
            "details": str(e)
        }), 500

@bp.route('/resume-versions/<version_id>', methods=['GET'])
# @cache_response(expiration=300)  # Cache for 5 minutes
def get_resume_version(version_id):
    """Get a specific resume version"""
    try:
        user_id = get_user_id()
        version = tracker_service.get_resume_version(user_id, version_id)
        
        if not version:
            return jsonify({
                "success": False,
                "error": "Resume version not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": version
        })
    except Exception as e:
        logger.error(f"Error retrieving resume version: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve resume version",
            "details": str(e)
        }), 500

@bp.route('/resume-versions', methods=['POST'])
def create_resume_version():
    """Create a new resume version"""
    try:
        user_id = get_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({
                "success": False,
                "error": "Resume version name is required"
            }), 400
        
        # Create resume version
        version = tracker_service.create_resume_version(user_id, data)
        
        return jsonify({
            "success": True,
            "data": version
        }), 201
    except Exception as e:
        logger.error(f"Error creating resume version: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to create resume version",
            "details": str(e)
        }), 500

@bp.route('/resume-versions/<version_id>', methods=['PUT'])
def update_resume_version(version_id):
    """Update a resume version"""
    try:
        user_id = get_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # Update resume version
        version = tracker_service.update_resume_version(user_id, version_id, data)
        
        if not version:
            return jsonify({
                "success": False,
                "error": "Resume version not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": version
        })
    except Exception as e:
        logger.error(f"Error updating resume version: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to update resume version",
            "details": str(e)
        }), 500

@bp.route('/resume-versions/<version_id>', methods=['DELETE'])
def delete_resume_version(version_id):
    """Delete a resume version"""
    try:
        user_id = get_user_id()
        
        # Check if resume version is used by any job applications
        applications = tracker_service.get_resume_version_usage(user_id, version_id)
        if applications:
            return jsonify({
                "success": False,
                "error": "Cannot delete resume version that is in use by job applications",
                "applications": applications
            }), 400
        
        # Delete resume version
        success = tracker_service.delete_resume_version(user_id, version_id)
        
        if not success:
            return jsonify({
                "success": False,
                "error": "Resume version not found or could not be deleted"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Resume version deleted successfully"
        })
    except Exception as e:
        logger.error(f"Error deleting resume version: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to delete resume version",
            "details": str(e)
        }), 500

@bp.route('/resume-versions/<version_id>/usage', methods=['GET'])
# @cache_response(expiration=300)  # Cache for 5 minutes
def get_resume_version_usage(version_id):
    """Get job applications using a specific resume version"""
    try:
        user_id = get_user_id()
        applications = tracker_service.get_resume_version_usage(user_id, version_id)
        
        return jsonify({
            "success": True,
            "data": applications
        })
    except Exception as e:
        logger.error(f"Error retrieving resume version usage: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve resume version usage",
            "details": str(e)
        }), 500

# Job Application Endpoints

@bp.route('/job-applications', methods=['GET'])
# @cache_response(expiration=300)  # Cache for 5 minutes
def get_job_applications():
    """Get all job applications for a user"""
    try:
        user_id = get_user_id()
        applications = tracker_service.get_job_applications(user_id)
        
        return jsonify({
            "success": True,
            "data": applications
        })
    except Exception as e:
        logger.error(f"Error retrieving job applications: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve job applications",
            "details": str(e)
        }), 500

@bp.route('/job-applications/<job_id>', methods=['GET'])
# @cache_response(expiration=300)  # Cache for 5 minutes
def get_job_application(job_id):
    """Get a specific job application"""
    try:
        user_id = get_user_id()
        application = tracker_service.get_job_application(user_id, job_id)
        
        if not application:
            return jsonify({
                "success": False,
                "error": "Job application not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": application
        })
    except Exception as e:
        logger.error(f"Error retrieving job application: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve job application",
            "details": str(e)
        }), 500

@bp.route('/job-applications', methods=['POST'])
def create_job_application():
    """Create a new job application"""
    try:
        user_id = get_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # Validate required fields
        if not data.get('company') or not data.get('position'):
            return jsonify({
                "success": False,
                "error": "Company and position are required"
            }), 400
        
        # Create job application
        application = tracker_service.create_job_application(user_id, data)
        
        return jsonify({
            "success": True,
            "data": application
        }), 201
    except Exception as e:
        logger.error(f"Error creating job application: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to create job application",
            "details": str(e)
        }), 500


@bp.route('/job-applications/<job_id>', methods=['PUT'])
def update_job_application(job_id):
    """Update a job application"""
    try:
        user_id = get_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # Update job application
        application = tracker_service.update_job_application(user_id, job_id, data)
        
        if not application:
            return jsonify({
                "success": False,
                "error": "Job application not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": application
        })
    except Exception as e:
        logger.error(f"Error updating job application: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to update job application",
            "details": str(e)
        }), 500

@bp.route('/job-applications/<job_id>', methods=['DELETE'])
def delete_job_application(job_id):
    """Delete a job application"""
    try:
        user_id = get_user_id()
        
        # Delete job application
        success = tracker_service.delete_job_application(user_id, job_id)
        
        if not success:
            return jsonify({
                "success": False,
                "error": "Job application not found or could not be deleted"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Job application deleted successfully"
        })
    except Exception as e:
        logger.error(f"Error deleting job application: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to delete job application",
            "details": str(e)
        }), 500

# Analytics Endpoints

@bp.route('/analytics', methods=['GET'])
# @cache_response(expiration=600)  # Cache for 10 minutes
def get_analytics():
    """Get analytics for a user's job applications"""
    try:
        user_id = get_user_id()
        analytics = tracker_service.get_analytics(user_id)
        
        return jsonify({
            "success": True,
            "data": analytics
        })
    except Exception as e:
        logger.error(f"Error retrieving analytics: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve analytics",
            "details": str(e)
        }), 500

# Utility Endpoints

@bp.route('/job-statuses', methods=['GET'])
def get_job_statuses():
    """Get list of valid job application statuses"""
    statuses = ["applied", "interviewing", "rejected", "offer", "accepted", "withdrawn"]
    
    return jsonify({
        "success": True,
        "data": statuses
    })