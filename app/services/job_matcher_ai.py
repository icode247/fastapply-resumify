"""
AI-powered job matching service using OpenAI.
Analyzes job preferences, job information, and resume to determine fit.
"""
import os
import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class JobMatcherAI:
    """
    Production-ready AI job matcher that analyzes whether a candidate
    should apply for a job based on their preferences, resume, and job details.
    """
    
    def __init__(self):
        """Initialize the OpenAI client."""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Fast and cost-effective for production
        
    def analyze_job_match(
        self,
        resume_text: str,
        job_information: Dict,
        job_preferences: Dict
    ) -> Dict:
        """
        Analyze if a candidate should apply for a job.
        
        Args:
            resume_text: The candidate's resume as plain text
            job_information: Dict containing job details (title, description, requirements, etc.)
            job_preferences: Dict containing candidate's preferences (location, salary, remote, etc.)
            
        Returns:
            Dict with:
                - shouldApply: bool
                - reason: str (max 20 words explaining mismatches)
                - matchScore: float (0-100)
                - mismatches: List[str] (specific items that don't match)
        """
        try:
            # Validate inputs
            if not resume_text or not resume_text.strip():
                raise ValueError("Resume text cannot be empty")
            
            if not job_information:
                raise ValueError("Job information is required")
            
            # Build the analysis prompt
            prompt = self._build_analysis_prompt(
                resume_text=resume_text,
                job_information=job_information,
                job_preferences=job_preferences or {}
            )
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Validate and format response
            return self._validate_and_format_response(result)
            
        except Exception as e:
            logger.error(f"Error in job match analysis: {str(e)}", exc_info=True)
            raise
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI."""
        return """You are an expert career advisor and job matching AI. Your role is to analyze whether a candidate should apply for a job based on their resume, job preferences, and the job requirements.

You must respond with a JSON object containing:
1. "shouldApply": boolean - true if they should apply, false otherwise
2. "reason": string - A concise explanation (MAX 20 words) of why they should or shouldn't apply. Focus on key mismatches if shouldApply is false.
3. "matchScore": number - A score from 0-100 indicating overall fit
4. "mismatches": array of strings - Specific items that don't match (e.g., "Required 5 years Python experience", "Location: Remote required but not offered")

Be strict but fair. Consider:
- Hard requirements (must-haves) vs nice-to-haves
- Years of experience requirements
- Technical skills match
- Location preferences
- Salary expectations
- Work arrangement (remote/hybrid/onsite)
- Career level alignment
- Language proficiency
- Industry alignment

Keep the reason concise, clear, and actionable. Don't truncate - use exactly the right words within 20 word limit."""

    def _build_analysis_prompt(
        self,
        resume_text: str,
        job_information: Dict,
        job_preferences: Dict
    ) -> str:
        """Build the analysis prompt from inputs."""
        
        # Extract job info
        job_title = job_information.get('title', 'Not specified')
        job_description = job_information.get('description', 'Not specified')
        job_requirements = job_information.get('requirements', 'Not specified')
        job_location = job_information.get('location', 'Not specified')
        job_salary = job_information.get('salary', 'Not specified')
        job_type = job_information.get('type', 'Not specified')  # remote/hybrid/onsite
        experience_required = job_information.get('experience_required', 'Not specified')
        
        # Extract preferences
        preferred_locations = job_preferences.get('locations', [])
        min_salary = job_preferences.get('min_salary', None)
        max_salary = job_preferences.get('max_salary', None)
        remote_preference = job_preferences.get('remote_preference', None)  # required/preferred/no_preference
        preferred_roles = job_preferences.get('roles', [])
        deal_breakers = job_preferences.get('deal_breakers', [])
        
        prompt = f"""Analyze this job match:

RESUME:
{resume_text[:3000]}  

JOB INFORMATION:
- Title: {job_title}
- Description: {job_description[:1000]}
- Requirements: {job_requirements[:1000]}
- Location: {job_location}
- Salary: {job_salary}
- Type: {job_type}
- Experience Required: {experience_required}

CANDIDATE PREFERENCES:
- Preferred Locations: {', '.join(preferred_locations) if preferred_locations else 'Any'}
- Salary Range: {f'${min_salary:,}' if min_salary else 'Not specified'} - {f'${max_salary:,}' if max_salary else 'Not specified'}
- Remote Preference: {remote_preference or 'No preference'}
- Preferred Roles: {', '.join(preferred_roles) if preferred_roles else 'Any'}
- Deal Breakers: {', '.join(deal_breakers) if deal_breakers else 'None'}

Analyze if the candidate should apply. Be thorough but concise in your reason (max 20 words)."""
        
        return prompt
    
    def _validate_and_format_response(self, result: Dict) -> Dict:
        """Validate and format the AI response."""
        # Ensure required fields exist
        if 'shouldApply' not in result:
            raise ValueError("AI response missing 'shouldApply' field")
        
        if 'reason' not in result:
            raise ValueError("AI response missing 'reason' field")
        
        # Validate reason length (20 words max)
        reason_words = result['reason'].split()
        if len(reason_words) > 20:
            # Truncate to 20 words if AI exceeded limit
            result['reason'] = ' '.join(reason_words[:20])
            logger.warning("AI response reason exceeded 20 words, truncated")
        
        # Ensure matchScore is present and valid
        match_score = result.get('matchScore', 0)
        if not isinstance(match_score, (int, float)) or match_score < 0 or match_score > 100:
            result['matchScore'] = 50  # Default to neutral if invalid
            logger.warning(f"Invalid matchScore: {match_score}, defaulting to 50")
        
        # Ensure mismatches is a list
        if 'mismatches' not in result or not isinstance(result['mismatches'], list):
            result['mismatches'] = []
        
        return {
            'shouldApply': bool(result['shouldApply']),
            'reason': str(result['reason']).strip(),
            'matchScore': float(result['matchScore']),
            'mismatches': [str(m).strip() for m in result['mismatches']]
        }
    
    def batch_analyze_jobs(
        self,
        resume_text: str,
        jobs: List[Dict],
        job_preferences: Dict
    ) -> List[Dict]:
        """
        Analyze multiple jobs at once.
        
        Args:
            resume_text: The candidate's resume
            jobs: List of job information dicts
            job_preferences: Candidate's preferences
            
        Returns:
            List of analysis results for each job
        """
        results = []
        
        for job in jobs:
            try:
                result = self.analyze_job_match(
                    resume_text=resume_text,
                    job_information=job,
                    job_preferences=job_preferences
                )
                result['job_id'] = job.get('id', None)
                result['job_title'] = job.get('title', 'Unknown')
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing job {job.get('id', 'unknown')}: {str(e)}")
                results.append({
                    'job_id': job.get('id', None),
                    'job_title': job.get('title', 'Unknown'),
                    'shouldApply': False,
                    'reason': 'Analysis failed',
                    'matchScore': 0,
                    'mismatches': ['Error during analysis'],
                    'error': str(e)
                })
        
        return results
