# app/services/resume_tracker.py
"""
Service for managing resume tracker data.
"""
import logging
import json
import os
from typing import Dict, List, Optional, Any, Union, Tuple
from app.models.resume_tracker import ResumeVersion, JobApplication, TrackerUser
from app.services.firebase import parse_resume_from_firebase

logger = logging.getLogger(__name__)

class ResumeTrackerService:
    """
    Service for managing resume versions and job applications.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the service with a data directory.
        
        Args:
            data_dir: Directory to store data files. Defaults to 'data' in the current directory.
        """
        self.data_dir = data_dir or os.path.join(os.getcwd(), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        logger.info(f"Resume Tracker Service initialized with data directory: {self.data_dir}")
        
    def _get_user_data_path(self, user_id: str) -> str:
        """Get path to user's data file"""
        return os.path.join(self.data_dir, f"user_{user_id}.json")
        
    def _load_user_data(self, user_id: str) -> TrackerUser:
        """
        Load user data from file.
        
        Args:
            user_id: ID of the user to load data for
            
        Returns:
            TrackerUser object with the user's data
        """
        file_path = self._get_user_data_path(user_id)
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return TrackerUser.from_dict(data)
            else:
                # Create new user if file doesn't exist
                return TrackerUser(user_id=user_id)
        except Exception as e:
            logger.error(f"Error loading user data for {user_id}: {str(e)}")
            # Return empty user data on error
            return TrackerUser(user_id=user_id)
            
    def _save_user_data(self, user: TrackerUser) -> bool:
        """
        Save user data to file.
        
        Args:
            user: TrackerUser object to save
            
        Returns:
            True if successful, False otherwise
        """
        file_path = self._get_user_data_path(user.user_id)
        
        try:
            with open(file_path, 'w') as f:
                json.dump(user.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving user data for {user.user_id}: {str(e)}")
            return False
            
    def get_resume_versions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all resume versions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of resume version dictionaries
        """
        user = self._load_user_data(user_id)
        return [rv.to_dict() for rv in user.resume_versions]
        
    def get_resume_version(self, user_id: str, version_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific resume version.
        
        Args:
            user_id: ID of the user
            version_id: ID of the resume version
            
        Returns:
            Resume version dictionary or None if not found
        """
        user = self._load_user_data(user_id)
        
        for rv in user.resume_versions:
            if rv.id == version_id:
                return rv.to_dict()
                
        return None
        
    def create_resume_version(self, user_id: str, version_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new resume version.
        
        Args:
            user_id: ID of the user
            version_data: Data for the new resume version
            
        Returns:
            The created resume version dictionary
        """
        user = self._load_user_data(user_id)
        
        # Create new resume version
        resume_version = ResumeVersion.from_dict(version_data)
        
        # If there's a file URL, try to extract content
        if resume_version.file_url and not resume_version.content:
            try:
                parse_result = parse_resume_from_firebase(resume_version.file_url)
                if parse_result.get('success', False):
                    resume_version.content = parse_result.get('text', '')
                    logger.info(f"Extracted content from resume file: {len(resume_version.content)} characters")
            except Exception as e:
                logger.error(f"Error extracting content from resume file: {str(e)}")
        
        # Add to user's resume versions
        user.resume_versions.append(resume_version)
        
        # Save user data
        self._save_user_data(user)
        
        return resume_version.to_dict()
        
    def update_resume_version(self, user_id: str, version_id: str, version_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a resume version.
        
        Args:
            user_id: ID of the user
            version_id: ID of the resume version to update
            version_data: Updated data for the resume version
            
        Returns:
            Updated resume version dictionary or None if not found
        """
        user = self._load_user_data(user_id)
        
        # Find the resume version to update
        for i, rv in enumerate(user.resume_versions):
            if rv.id == version_id:
                # Update fields
                rv.name = version_data.get('name', rv.name)
                rv.date = version_data.get('date', rv.date)
                rv.notes = version_data.get('notes', rv.notes)
                
                # Update content if provided
                if 'content' in version_data:
                    rv.content = version_data['content']
                    
                # Update file URL if provided
                if 'file_url' in version_data:
                    rv.file_url = version_data['file_url']
                    
                    # If file URL updated and no content provided, try to extract content
                    if rv.file_url and not rv.content:
                        try:
                            parse_result = parse_resume_from_firebase(rv.file_url)
                            if parse_result.get('success', False):
                                rv.content = parse_result.get('text', '')
                                logger.info(f"Extracted content from updated resume file: {len(rv.content)} characters")
                        except Exception as e:
                            logger.error(f"Error extracting content from updated resume file: {str(e)}")
                
                # Save user data
                self._save_user_data(user)
                
                return rv.to_dict()
        
        return None
        
    def delete_resume_version(self, user_id: str, version_id: str) -> bool:
        """
        Delete a resume version.
        
        Args:
            user_id: ID of the user
            version_id: ID of the resume version to delete
            
        Returns:
            True if deleted, False otherwise
        """
        user = self._load_user_data(user_id)
        
        # Check if any job applications use this resume version
        for job in user.job_applications:
            if job.resumeVersion == version_id:
                return False  # Can't delete if it's in use
        
        # Find and remove the resume version
        original_length = len(user.resume_versions)
        user.resume_versions = [rv for rv in user.resume_versions if rv.id != version_id]
        
        if len(user.resume_versions) < original_length:
            # Save user data
            self._save_user_data(user)
            return True
            
        return False
        
    def get_job_applications(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all job applications for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of job application dictionaries
        """
        user = self._load_user_data(user_id)
        return [ja.to_dict() for ja in user.job_applications]
        
    def get_job_application(self, user_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific job application.
        
        Args:
            user_id: ID of the user
            job_id: ID of the job application
            
        Returns:
            Job application dictionary or None if not found
        """
        user = self._load_user_data(user_id)
        
        for ja in user.job_applications:
            if ja.id == job_id:
                return ja.to_dict()
                
        return None
        
    def create_job_application(self, user_id: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new job application.
        
        Args:
            user_id: ID of the user
            job_data: Data for the new job application
            
        Returns:
            The created job application dictionary
        """
        user = self._load_user_data(user_id)
        
        # Check if resume version exists if provided
        resume_version_id = job_data.get('resumeVersion')
        if resume_version_id:
            resume_version_exists = any(rv.id == resume_version_id for rv in user.resume_versions)
            if not resume_version_exists:
                job_data['resumeVersion'] = ""  # Clear invalid resume version
        
        # Create new job application
        job_application = JobApplication.from_dict(job_data)
        
        # Add to user's job applications
        user.job_applications.append(job_application)
        
        # Save user data
        self._save_user_data(user)
        
        return job_application.to_dict()
        
    def update_job_application(self, user_id: str, job_id: str, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a job application.
        
        Args:
            user_id: ID of the user
            job_id: ID of the job application to update
            job_data: Updated data for the job application
            
        Returns:
            Updated job application dictionary or None if not found
        """
        user = self._load_user_data(user_id)
        
        # Check if resume version exists if provided
        resume_version_id = job_data.get('resumeVersion')
        if resume_version_id:
            resume_version_exists = any(rv.id == resume_version_id for rv in user.resume_versions)
            if not resume_version_exists:
                job_data['resumeVersion'] = ""  # Clear invalid resume version
        
        # Find the job application to update
        for i, ja in enumerate(user.job_applications):
            if ja.id == job_id:
                # Update fields
                ja.company = job_data.get('company', ja.company)
                ja.position = job_data.get('position', ja.position)
                ja.dateApplied = job_data.get('dateApplied', ja.dateApplied)
                ja.status = job_data.get('status', ja.status)
                ja.resumeVersion = job_data.get('resumeVersion', ja.resumeVersion)
                ja.notes = job_data.get('notes', ja.notes)
                ja.jobDescription = job_data.get('jobDescription', ja.jobDescription)
                ja.contactInfo = job_data.get('contactInfo', ja.contactInfo)
                
                # Update interview dates if provided
                if 'interviewDates' in job_data:
                    ja.interviewDates = job_data['interviewDates']
                
                # Save user data
                self._save_user_data(user)
                
                return ja.to_dict()
        
        return None
        
    def delete_job_application(self, user_id: str, job_id: str) -> bool:
        """
        Delete a job application.
        
        Args:
            user_id: ID of the user
            job_id: ID of the job application to delete
            
        Returns:
            True if deleted, False otherwise
        """
        user = self._load_user_data(user_id)
        
        # Find and remove the job application
        original_length = len(user.job_applications)
        user.job_applications = [ja for ja in user.job_applications if ja.id != job_id]
        
        if len(user.job_applications) < original_length:
            # Save user data
            self._save_user_data(user)
            return True
            
        return False
        
    def get_resume_version_usage(self, user_id: str, version_id: str) -> List[Dict[str, Any]]:
        """
        Get all job applications using a specific resume version.
        
        Args:
            user_id: ID of the user
            version_id: ID of the resume version
            
        Returns:
            List of job application dictionaries using the specified resume version
        """
        user = self._load_user_data(user_id)
        
        # Find all job applications using this resume version
        applications = [ja.to_dict() for ja in user.job_applications if ja.resumeVersion == version_id]
        
        return applications
        
    def get_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Get analytics and statistics for a user's job applications.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with analytics data
        """
        user = self._load_user_data(user_id)
        
        # Calculate statistics
        total_applications = len(user.job_applications)
        status_counts = {}
        applications_by_month = {}
        resume_usage = {}
        
        for ja in user.job_applications:
            # Count by status
            status = ja.status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by month
            try:
                month = ja.dateApplied[:7]  # Format: YYYY-MM
                applications_by_month[month] = applications_by_month.get(month, 0) + 1
            except:
                pass
            
            # Count by resume version
            if ja.resumeVersion:
                resume_usage[ja.resumeVersion] = resume_usage.get(ja.resumeVersion, 0) + 1
        
        # Calculate response rate
        responses = status_counts.get('interviewing', 0) + status_counts.get('offer', 0) + status_counts.get('accepted', 0)
        response_rate = (responses / total_applications) * 100 if total_applications > 0 else 0
        
        # Add resume version names to usage stats
        resume_usage_with_names = {}
        for rv_id, count in resume_usage.items():
            name = "Unknown"
            for rv in user.resume_versions:
                if rv.id == rv_id:
                    name = rv.name
                    break
            resume_usage_with_names[name] = count
        
        return {
            "totalApplications": total_applications,
            "statusCounts": status_counts,
            "applicationsByMonth": applications_by_month,
            "resumeUsage": resume_usage_with_names,
            "responseRate": response_rate
        }