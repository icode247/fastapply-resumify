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
                model="gpt-4.1",
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
        
        CRITICAL: You MUST extract EVERY work experience you find. This is extremely important.
        
        STEP 1 - SCAN FOR EXPERIENCE SECTIONS:
        Look for sections labeled: EXPERIENCE, WORK HISTORY, PROFESSIONAL EXPERIENCE, EMPLOYMENT, CAREER
        Extract EVERY entry from these sections - no exceptions.
        
        STEP 2 - SCAN ENTIRE RESUME FOR WORK PATTERNS:
        1. Look for patterns like "Job Title | Company Name" or "Job Title - Company Name"
        2. Look for any entry with job responsibilities and date ranges
        3. Look for freelance, consulting, contract, part-time, full-time work
        4. Look for internships with professional duties
        5. Look for any role where someone performed work duties for pay
        
        STEP 3 - EXTRACT ALL FINDINGS:
        If you find ANY indication of work experience, extract it. 
        Do not skip entries because they seem "minor" or "short-term".
        Do not skip freelance or consulting work.
        Do not skip internships or part-time work.
        
        YOUR GOAL: Extract EVERY SINGLE work experience mentioned in this resume.
        
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
          "education": [
            {{
              "school": "Institution name",
              "degree": "Degree type (bachelor, master, doctorate, etc.)",
              "major": "Field of study/major",
              "startDate": "Start date",
              "endDate": "End date",
              "location": "Location if available"
            }}
          ],
          "skills": [
            "List of technical and professional skills extracted from resume"
          ],
          "experience": [
            {{
              "title": "Job title",
              "company": "Company name",
              "startDate": "Start date",
              "endDate": "End date", 
              "description": "Job description/responsibilities",
              "location": "Work location if available"
            }}
          ],
          "projects": [
            {{
              "title": "Project name",
              "description": "Project description and technologies used",
              "url": "Project URL/link if available",
              "technologies": "Technologies/tools used"
            }}
          ],
          "certifications": [
            "List of certifications mentioned"
          ],
          "languages": [
            "List of languages mentioned"
          ]
        }}
        
        CRITICAL EXPERIENCE EXTRACTION RULES:
        1. SCAN THE ENTIRE RESUME for any work experience patterns
        2. Look for these work experience indicators:
           - Job titles with company names (e.g., "Developer at Company", "Manager | Company")
           - Employment periods with dates (e.g., "2020-2023", "Jan 2020 - Present")
           - Job descriptions with bullet points or responsibilities
           - Freelance, consulting, contract, part-time, full-time work
           - Internships, co-ops, volunteer positions with responsibilities
           - Any role where someone was performing work duties
        3. Extract experience from ANY section that contains work activities:
           - Traditional "Experience" or "Work History" sections
           - "Professional Experience" sections
           - Mixed sections that contain both projects AND work experience
           - Individual project descriptions that show ongoing work relationships
        4. For each experience found, extract:
           - Job title/role
           - Company/organization name
           - Start date (any format: MM/YYYY, Month Year, Year only)
           - End date (including "Present", "Current", "Ongoing")
           - Location if mentioned
           - Responsibilities/achievements
        5. If you find dates and responsibilities but unclear company, mark company as "Freelance" or "Various Clients"
        6. Extract ALL education entries (multiple schools/degrees should be separate entries)
        7. Extract ALL projects from technical/personal projects sections
        8. For skills, extract both technical and soft skills mentioned
        9. Do not hallucinate or guess information not in the resume
        10. Be AGGRESSIVE in finding work experiences - look for any indication of paid or professional work
        11. Focus on accuracy over completeness
        
        EXAMPLE PATTERNS TO RECOGNIZE AS WORK EXPERIENCE:
        - "Software Developer | ABC Company | 2020-2022"
        - "Freelance Web Developer | Various Clients | 2019-Present"  
        - "Freelancing Web Developer | Self-Employed, April 2025 - Present"
        - "Consultant | Self-Employed | June 2021 - Current"
        - "Marketing Intern | XYZ Corp | Summer 2020"
        - "Part-time Developer | Tech Startup | Jan 2019 - Dec 2020"
        - Any role with dates and responsibilities, even if in a "Projects" section
        
        SPECIFIC EXAMPLE - If you see this pattern in a resume:
        
        "EXPERIENCE
        
        Freelancing Web Developer | Self-Employed,  
        April 2025 - Present | Remote"
        
        You MUST extract it as:
        {{
          "title": "Freelancing Web Developer",
          "company": "Self-Employed", 
          "startDate": "April 2025",
          "endDate": "Present",
          "location": "Remote",
          "description": "[any bullet points or responsibilities that follow]"
        }}
        
        CRITICAL: If you see a section called "EXPERIENCE", extract EVERY entry from it - no exceptions!
        """
        
        return prompt
    
    def analyze_experience_patterns(self, resume_text: str) -> Dict[str, Any]:
        """
        Debug method to analyze what experience patterns are detected in resume text
        This helps identify why certain experiences might not be extracted
        """
        import re
        
        patterns = {
            "job_title_company_patterns": [],
            "date_range_patterns": [],
            "experience_section_found": False,
            "work_keywords_found": [],
            "potential_experiences": []
        }
        
        # Look for experience section headers
        experience_headers = re.findall(r'(EXPERIENCE|WORK HISTORY|PROFESSIONAL EXPERIENCE|EMPLOYMENT|CAREER)', 
                                       resume_text, re.IGNORECASE)
        patterns["experience_section_found"] = len(experience_headers) > 0
        
        # Look for job title patterns
        job_patterns = re.findall(r'([A-Za-z\s]+)\s*[\|\-]\s*([A-Za-z\s&]+)', resume_text)
        patterns["job_title_company_patterns"] = job_patterns[:10]  # First 10 matches
        
        # Look for date ranges
        date_patterns = re.findall(r'(\d{1,2}\/\d{4}|\w+\s+\d{4}|\d{4})\s*[-–]\s*(\d{1,2}\/\d{4}|\w+\s+\d{4}|\d{4}|Present|Current)', 
                                  resume_text, re.IGNORECASE)
        patterns["date_range_patterns"] = date_patterns[:10]  # First 10 matches
        
        # Look for work-related keywords
        work_keywords = ['developer', 'engineer', 'manager', 'analyst', 'consultant', 'intern', 
                        'freelance', 'contractor', 'specialist', 'coordinator', 'assistant']
        found_keywords = [kw for kw in work_keywords if kw.lower() in resume_text.lower()]
        patterns["work_keywords_found"] = found_keywords
        
        # Try to identify potential experience blocks
        lines = resume_text.split('\n')
        potential_exp = []
        for i, line in enumerate(lines):
            line = line.strip()
            # Look for lines with job titles and companies
            if any(kw in line.lower() for kw in work_keywords) and ('|' in line or '-' in line):
                context_lines = lines[max(0, i-2):min(len(lines), i+5)]  # Get surrounding context
                potential_exp.append({
                    "line_number": i,
                    "content": line,
                    "context": [l.strip() for l in context_lines if l.strip()]
                })
        
        patterns["potential_experiences"] = potential_exp[:5]  # First 5 potential matches
        
        return patterns

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
                "education": [],
                "skills": [],
                "experience": [],
                "projects": [],
                "certifications": [],
                "languages": []
            }
            
            # Merge with defaults to ensure structure
            for key, default_value in required_structure.items():
                if key not in result:
                    result[key] = default_value
            
            return result
            
        except Exception as e:
            self.logger.error(f"OpenAI resume parsing failed: {str(e)}")
            raise  # Re-raise so the parser can fall back to NLP methods