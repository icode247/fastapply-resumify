# app/models/resume_tracker.py
"""
Models for the Resume Tracker feature.
"""
from typing import Dict, List, Optional, Literal, Any, Union
from datetime import datetime
import uuid

# Define job application status options
JobStatus = Literal["applied", "interviewing", "rejected", "offer", "accepted", "withdrawn"]

class ResumeVersion:
    """
    Model for a resume version.
    """
    def __init__(
        self,
        name: str,
        date: str,
        notes: str = "",
        content: str = "",
        file_url: str = "",
        id: Optional[str] = None
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.date = date
        self.notes = notes
        self.content = content
        self.file_url = file_url
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert ResumeVersion to a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date,
            "notes": self.notes,
            "content": self.content,
            "file_url": self.file_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResumeVersion':
        """Create ResumeVersion from a dictionary"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            date=data.get("date", ""),
            notes=data.get("notes", ""),
            content=data.get("content", ""),
            file_url=data.get("file_url", "")
        )

class JobApplication:
    """
    Model for a job application.
    """
    def __init__(
        self,
        company: str,
        position: str,
        dateApplied: str,
        status: JobStatus = "applied",
        resumeVersion: str = "",
        notes: str = "",
        jobDescription: str = "",
        contactInfo: str = "",
        interviewDates: List[str] = None,
        id: Optional[str] = None
    ):
        self.id = id or str(uuid.uuid4())
        self.company = company
        self.position = position
        self.dateApplied = dateApplied
        self.status = status
        self.resumeVersion = resumeVersion
        self.notes = notes
        self.jobDescription = jobDescription
        self.contactInfo = contactInfo
        self.interviewDates = interviewDates or []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert JobApplication to a dictionary"""
        return {
            "id": self.id,
            "company": self.company,
            "position": self.position,
            "dateApplied": self.dateApplied,
            "status": self.status,
            "resumeVersion": self.resumeVersion,
            "notes": self.notes,
            "jobDescription": self.jobDescription,
            "contactInfo": self.contactInfo,
            "interviewDates": self.interviewDates
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobApplication':
        """Create JobApplication from a dictionary"""
        return cls(
            id=data.get("id"),
            company=data.get("company", ""),
            position=data.get("position", ""),
            dateApplied=data.get("dateApplied", ""),
            status=data.get("status", "applied"),
            resumeVersion=data.get("resumeVersion", ""),
            notes=data.get("notes", ""),
            jobDescription=data.get("jobDescription", ""),
            contactInfo=data.get("contactInfo", ""),
            interviewDates=data.get("interviewDates", [])
        )

class TrackerUser:
    """
    Model for a user in the resume tracker system.
    """
    def __init__(
        self,
        user_id: str,
        resume_versions: List[ResumeVersion] = None,
        job_applications: List[JobApplication] = None
    ):
        self.user_id = user_id
        self.resume_versions = resume_versions or []
        self.job_applications = job_applications or []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert TrackerUser to a dictionary"""
        return {
            "user_id": self.user_id,
            "resume_versions": [rv.to_dict() for rv in self.resume_versions],
            "job_applications": [ja.to_dict() for ja in self.job_applications]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrackerUser':
        """Create TrackerUser from a dictionary"""
        resume_versions = [
            ResumeVersion.from_dict(rv_data) 
            for rv_data in data.get("resume_versions", [])
        ]
        job_applications = [
            JobApplication.from_dict(ja_data) 
            for ja_data in data.get("job_applications", [])
        ]
        
        return cls(
            user_id=data.get("user_id", ""),
            resume_versions=resume_versions,
            job_applications=job_applications
        )