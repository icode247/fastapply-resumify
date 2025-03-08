# app/core/job_description.py
"""
Job Description Generator functionality.
"""
import logging
import json
import re
from typing import Dict, Any
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class JobDescriptionGenerator:
    """
    Generate professional job descriptions based on input parameters.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "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")
        self.logger = logging.getLogger(__name__)
        
    def generate_job_description(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a professional job description based on input parameters
        
        Args:
            job_data: Dictionary containing job parameters
                jobTitle: Job title
                company: Company name
                industry: Industry type
                experienceLevel: Required experience level
                location: Job location
                jobType: Type of employment (full-time, part-time, etc.)
                keyResponsibilities: Primary job responsibilities
                requiredSkills: Required skills and qualifications
                additionalRequirements: Any additional requirements
                
        Returns:
            Dictionary containing the generated job description
        """
        try:
            # Validate required fields
            required_fields = ['jobTitle', 'company', 'industry', 'experienceLevel']
            missing_fields = [field for field in required_fields if not job_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            # Create the prompt for GPT
            prompt = self._create_job_description_prompt(job_data)
            
            # Call OpenAI API to generate the job description
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating job description for {job_data.get('jobTitle')} at {job_data.get('company')}")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR professional who writes clear, engaging, and professional job descriptions that attract qualified candidates."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                temperature=0.5,
                response_format={"type": "json_object"},
            )
            
            result = chat_completion.choices[0].message.content
            
            try:
                job_description = json.loads(result)
                job_description["success"] = True
                return job_description
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    job_description_str = json_match.group(0)
                    try:
                        job_description = json.loads(job_description_str)
                        job_description["success"] = True
                        return job_description
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error generating job description: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _create_job_description_prompt(self, job_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the AI to generate a job description
        
        Args:
            job_data: Dictionary containing job parameters
            
        Returns:
            String containing the prompt
        """
        prompt = f"""
        Generate a professional job description in JSON format based on the following information:
        
        - Job Title: {job_data.get('jobTitle', '')}
        - Company: {job_data.get('company', '')}
        - Industry: {job_data.get('industry', '')}
        - Experience Level: {job_data.get('experienceLevel', '')}
        - Location: {job_data.get('location', '')}
        - Job Type: {job_data.get('jobType', 'Full-time')}
        
        Additional information:
        - Key Responsibilities: {job_data.get('keyResponsibilities', '')}
        - Required Skills: {job_data.get('requiredSkills', '')}
        - Additional Requirements: {job_data.get('additionalRequirements', '')}
        
        Create a comprehensive job description with the following sections:
        1. Job Overview - A short paragraph that summarizes the role
        2. About the Company - Brief description of the company
        3. Key Responsibilities - Detailed bullet-point list of responsibilities
        4. Qualifications - Bullet-point list of required skills and experience
        5. Benefits - Standard benefits appropriate for this industry/role
        6. How to Apply - Instructions for application
        
        Return the output as a valid JSON string with the following structure:
        {{
          "jobTitle": "The formatted job title",
          "companyName": "The company name",
          "location": "The job location",
          "jobType": "The employment type",
          "jobOverview": "A paragraph overview of the position",
          "aboutCompany": "A paragraph about the company",
          "responsibilities": ["Array of responsibility bullet points"],
          "qualifications": ["Array of qualification bullet points"],
          "benefits": ["Array of benefit bullet points"],
          "applicationProcess": "Instructions on how to apply"
        }}
        
        Make the job description professional, engaging, and inclusive. Do not invent specific details that weren't provided, but craft a complete and compelling job description based on the information given.
        """
        
        return prompt