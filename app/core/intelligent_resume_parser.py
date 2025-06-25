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
        4. For experience years, calculate based on work history if not explicitly stated
        5. Do not hallucinate or guess information not in the resume
        6. Ensure all JSON keys are present even if values are empty
        """
        
        return prompt
        
    def merge_with_linkedin_data(self, resume_data: Dict[str, Any], linkedin_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge resume data with LinkedIn data, prioritizing more complete information
        LinkedIn data is completely optional - if not provided, returns resume data as-is
        
        Args:
            resume_data: Data extracted from resume
            linkedin_data: Data from LinkedIn (optional)
            
        Returns:
            Merged data with best information from both sources
        """
        try:
            # If no LinkedIn data provided, return resume data with metadata
            if not linkedin_data:
                merged_data = resume_data.copy()
                merged_data['dataSource'] = {
                    'resume': resume_data.get('success', False),
                    'linkedin': False,
                    'mergedAt': self._get_current_timestamp()
                }
                merged_data['success'] = True
                return merged_data
            
            merged_data = {}
            
            # Helper function to choose best value
            def choose_best_value(resume_val, linkedin_val, field_name=""):
                # If one is empty and other isn't, choose the non-empty one
                if not resume_val and linkedin_val:
                    return linkedin_val
                if resume_val and not linkedin_val:
                    return resume_val
                
                # If both have values, prefer resume for contact info, LinkedIn for professional info
                if field_name in ['firstName', 'lastName', 'phoneNumber', 'streetAddress', 'education']:
                    return resume_val if resume_val else linkedin_val
                elif field_name in ['headline', 'summary', 'currentCity']:
                    return linkedin_val if linkedin_val else resume_val
                else:
                    # Default: prefer resume data (more recent)
                    return resume_val if resume_val else linkedin_val
            
            # Helper function to safely merge lists (handles both strings and dicts)
            def safe_merge_lists(list1, list2):
                """Safely merge two lists, handling both string and dict elements"""
                if not list1 and not list2:
                    return []
                if not list1:
                    return list2.copy() if list2 else []
                if not list2:
                    return list1.copy() if list1 else []
                
                merged = []
                
                # Add all items from list1
                for item in list1:
                    if item and item not in merged:
                        merged.append(item)
                
                # Add items from list2 that aren't already in merged
                for item in list2:
                    if item and item not in merged:
                        merged.append(item)
                
                return merged
            
            # Merge basic fields
            basic_fields = [
                'firstName', 'lastName', 'phoneNumber', 'phoneCountryCode', 
                'headline', 'summary', 'streetAddress', 'currentCity', 'state', 
                'country', 'zipcode', 'githubURL', 'website', 'yearsOfExperience', 
                'desiredSalary'
            ]
            
            for field in basic_fields:
                resume_val = resume_data.get(field, "")
                linkedin_val = linkedin_data.get(field, "")
                merged_data[field] = choose_best_value(resume_val, linkedin_val, field)
            
            # Merge education (prefer resume, fallback to LinkedIn)
            if resume_data.get('education') and any(resume_data['education'].values()):
                merged_data['education'] = resume_data['education']
                merged_data['educationStartMonth'] = resume_data.get('educationStartMonth', "")
                merged_data['educationStartYear'] = resume_data.get('educationStartYear', "")
                merged_data['educationEndMonth'] = resume_data.get('educationEndMonth', "")
                merged_data['educationEndYear'] = resume_data.get('educationEndYear', "")
            else:
                merged_data['education'] = linkedin_data.get('education', {"school": "", "degree": "", "major": ""})
                merged_data['educationStartMonth'] = linkedin_data.get('educationStartMonth', "")
                merged_data['educationStartYear'] = linkedin_data.get('educationStartYear', "")
                merged_data['educationEndMonth'] = linkedin_data.get('educationEndMonth', "")
                merged_data['educationEndYear'] = linkedin_data.get('educationEndYear', "")
            
            # Merge arrays safely (handles both strings and dicts)
            resume_skills = resume_data.get('skills', [])
            linkedin_skills = linkedin_data.get('skills', [])
            merged_data['skills'] = safe_merge_lists(resume_skills, linkedin_skills)
            
            resume_certs = resume_data.get('certifications', [])
            linkedin_certs = linkedin_data.get('certifications', [])
            merged_data['certifications'] = safe_merge_lists(resume_certs, linkedin_certs)
            
            resume_langs = resume_data.get('languages', [])
            linkedin_langs = linkedin_data.get('languages', [])
            merged_data['languages'] = safe_merge_lists(resume_langs, linkedin_langs)
            
            # For experience, prefer resume but keep LinkedIn as backup
            merged_data['experience'] = resume_data.get('experience', linkedin_data.get('experience', []))
            
            # Add metadata
            merged_data['dataSource'] = {
                'resume': resume_data.get('success', False),
                'linkedin': bool(linkedin_data),
                'mergedAt': self._get_current_timestamp()
            }
            
            merged_data['success'] = True
            return merged_data
            
        except Exception as e:
            self.logger.error(f"Error merging resume and LinkedIn data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_data": resume_data if resume_data.get('success') else linkedin_data
            }
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
        
    def parse_and_merge(self, resume_text: str, linkedin_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parse resume and merge with LinkedIn data in one step
        LinkedIn data is completely optional
        
        Args:
            resume_text: Raw resume text
            linkedin_data: Optional LinkedIn data to merge with
            
        Returns:
            Merged structured data or resume data only if no LinkedIn data
        """
        # Parse resume
        resume_data = self.parse_resume_to_structured_data(resume_text)
        
        if not resume_data.get('success'):
            return resume_data
        
        # If no LinkedIn data, return resume data with proper metadata
        if not linkedin_data:
            resume_data['dataSource'] = {
                'resume': True,
                'linkedin': False,
                'mergedAt': self._get_current_timestamp()
            }
            return resume_data
        
        # Merge with LinkedIn data
        return self.merge_with_linkedin_data(resume_data, linkedin_data)