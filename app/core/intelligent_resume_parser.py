# app/core/intelligent_resume_parser.py
"""
Intelligent Resume Parser - Extracts structured data from resumes using OpenAI
"""
import logging
import json
import re
from typing import Dict, Any, Optional
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class IntelligentResumeParser:
    """
    Extract structured data from resume text using AI
    """
    
    def __init__(self):
        try:
            from app.core.config import get_settings
            settings = get_settings()
            self.api_key = settings.openai_api_key or ""
        except (ImportError, AttributeError):
            # Fallback to environment variable if config module not available
            self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.logger = logging.getLogger(__name__)
        
    def parse_resume_to_structured_data(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume text and extract structured data for onboarding
        
        Args:
            resume_text: Raw text extracted from resume
            
        Returns:
            Dictionary with structured resume data
        """
        try:
            if not resume_text or len(resume_text.strip()) < 50:
                raise ValueError("Resume text is too short for meaningful parsing")
                
            prompt = self._create_parsing_prompt(resume_text)
            
            client = OpenAI(api_key=self.api_key)
            
            self.logger.info(f"Parsing resume with {len(resume_text)} characters")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert resume parser that extracts structured data from resumes. 
                        Extract information accurately without hallucinating. If information is not available, 
                        leave the field empty rather than guessing."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                temperature=0.2,
                response_format={"type": "json_object"},
                timeout=50,  # Set timeout to 50 seconds (less than Gunicorn's 60s)
            )
            
            result = chat_completion.choices[0].message.content
            
            try:
                parsed_data = json.loads(result)
                parsed_data["success"] = True
                parsed_data["source"] = "resume_parsing"
                return parsed_data
                
            except json.JSONDecodeError:
                # Try to extract JSON if response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    parsed_data = json.loads(json_match.group(0))
                    parsed_data["success"] = True
                    parsed_data["source"] = "resume_parsing"
                    return parsed_data
                else:
                    raise ValueError("Could not parse AI response as JSON")
                    
        except Exception as e:
            self.logger.error(f"Error parsing resume: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "source": "resume_parsing"
            }
            
    def _create_parsing_prompt(self, resume_text: str) -> str:
        """Create prompt for AI to parse resume into structured data"""
        
        prompt = f"""
        Extract structured data from the following resume text. Return ONLY a JSON object with the exact structure below.
        Do not add any additional text or comments outside the JSON.
        
        RESUME TEXT:
        ```
        {resume_text}
        ```
        
        Extract the following information and return as JSON:
        
        {{
          "firstName": "First name only",
          "lastName": "Last name only", 
          "phoneNumber": "Phone number without country code",
          "phoneCountryCode": "Country code (e.g., '+1', '+44') or empty if not clear",
          "headline": "Professional title/headline",
          "summary": "Professional summary or objective",
          "streetAddress": "Full address",
          "currentCity": "City name only",
          "state": "State/Province name",
          "country": "Country name",
          "zipcode": "Postal/ZIP code",
          "githubURL": "GitHub profile URL",
          "website": "Personal website URL",
          "yearsOfExperience": "Total years of experience as number",
          "desiredSalary": "Expected/desired salary if mentioned",
          "education": {{
            "school": "Institution name",
            "degree": "Degree type (bachelor, master, doctorate, etc.)",
            "major": "Field of study/major"
          }},
          "educationStartMonth": "Start month of education",
          "educationStartYear": "Start year of education", 
          "educationEndMonth": "End month of education",
          "educationEndYear": "End year of education",
          "skills": [
            "List of technical and professional skills extracted from resume"
          ],
          "experience": [
            {{
              "title": "Job title",
              "company": "Company name",
              "startDate": "Start date",
              "endDate": "End date", 
              "description": "Job description/responsibilities"
            }}
          ],
          "certifications": [
            "List of certifications mentioned"
          ],
          "languages": [
            "List of languages mentioned"
          ]
        }}
        
        Rules:
        1. Extract only information that is clearly present in the resume
        2. If information is not available, use empty string "" or empty array []
        3. For dates, extract in any format found (MM/YYYY, Month Year, etc.)
        4. For experience years, calculate based of work history if not explicitly stated
        5. Do not hallucinate or guess information not in the resume
        6. Ensure all JSON keys are present even if values are empty
        7. Focus on accuracy over completeness
        """
        
        return prompt

    def parse_resume_to_required_format(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume and return data in the exact required format.
        This is the main method that should be used by the parsers.
        """
        try:
            if not self.api_key:
                raise ValueError("OpenAI API key not configured")
                
            openai_result = self.parse_resume_to_structured_data(resume_text)
            
            if not openai_result.get("success", False):
                raise ValueError(f"OpenAI parsing failed: {openai_result.get('error', 'Unknown error')}")
            
            # The OpenAI response should already be in the required format
            # Remove the success/source metadata
            result = {k: v for k, v in openai_result.items() if k not in ['success', 'source', 'error']}
            
            # Ensure all required keys exist with default values
            required_structure = {
                "firstName": "",
                "lastName": "",
                "phoneNumber": "",
                "phoneCountryCode": "",
                "headline": "",
                "summary": "",
                "streetAddress": "",
                "currentCity": "",
                "state": "",
                "country": "",
                "zipcode": "",
                "githubURL": "",
                "website": "",
                "yearsOfExperience": 0,
                "desiredSalary": "",
                "education": {"school": "", "degree": "", "major": ""},
                "educationStartMonth": "",
                "educationStartYear": "",
                "educationEndMonth": "",
                "educationEndYear": "",
                "skills": [],
                "experience": [],
                "certifications": [],
                "languages": []
            }
            
            # Merge with defaults to ensure structure
            for key, default_value in required_structure.items():
                if key not in result:
                    result[key] = default_value
                elif key == "education" and isinstance(result[key], dict):
                    # Ensure education has all required subfields
                    for subkey, subdefault in default_value.items():
                        if subkey not in result[key]:
                            result[key][subkey] = subdefault
            
            return result
            
        except Exception as e:
            self.logger.error(f"OpenAI resume parsing failed: {str(e)}")
            raise  # Re-raise so the parser can fall back to NLP methods