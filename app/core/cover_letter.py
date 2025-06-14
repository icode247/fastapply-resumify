# app/core/cover_letter.py
"""
Cover Letter Generator functionality.
"""
import logging
import json
import re
from typing import Dict, Any
from openai import OpenAI
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class CoverLetterGenerator:
    """
    Generate professional cover letters based on input parameters.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.logger = logging.getLogger(__name__)
        
    def generate_cover_letter(self, letter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a professional cover letter based on input parameters
        
        Args:
            letter_data: Dictionary containing cover letter parameters
                fullName: Applicant's full name
                jobTitle: Job title being applied for
                company: Company name
                hiringManager: Hiring manager's name (optional)
                skills: Relevant skills for the position
                roleType: Type of role (General, Technical, Creative, etc.)
                location: Job location (optional)
                tone: Tone of the letter (Professional, Enthusiastic, etc.)
                
        Returns:
            Dictionary containing the generated cover letter
        """
        try:
            # Validate required fields
            required_fields = ['fullName', 'jobTitle', 'company']
            missing_fields = [field for field in required_fields if not letter_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            # Create the prompt for GPT
            prompt = self._create_cover_letter_prompt(letter_data)
            
            # Call OpenAI API to generate the cover letter
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating cover letter for {letter_data.get('fullName')} applying for {letter_data.get('jobTitle')} at {letter_data.get('company')}")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert career coach who writes compelling, personalized, and professional cover letters that help candidates stand out."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                temperature=0.6,
                response_format={"type": "json_object"},
            )
            
            result = chat_completion.choices[0].message.content
            
            try:
                cover_letter = json.loads(result)
                cover_letter["success"] = True
                return cover_letter
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    cover_letter_str = json_match.group(0)
                    try:
                        cover_letter = json.loads(cover_letter_str)
                        cover_letter["success"] = True
                        return cover_letter
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error generating cover letter: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _create_cover_letter_prompt(self, letter_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the AI to generate a cover letter
        
        Args:
            letter_data: Dictionary containing cover letter parameters
            
        Returns:
            String containing the prompt
        """
        # Get current date for the letter
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Get hiring manager salutation
        if letter_data.get('hiringManager'):
            salutation = f"Dear {letter_data.get('hiringManager')},"
        else:
            salutation = "Dear Hiring Manager,"
            
        # Set tone based on input or default to Professional
        tone = letter_data.get('tone', 'Professional')
        
        # Set role type based on input or default to General
        role_type = letter_data.get('roleType', 'General')
        
        prompt = f"""
        Generate a professional cover letter in JSON format based on the following information:
        
        - Applicant Name: {letter_data.get('fullName', '')}
        - Job Title: {letter_data.get('jobTitle', '')}
        - Company: {letter_data.get('company', '')}
        - Hiring Manager: {letter_data.get('hiringManager', 'Hiring Manager')}
        - Relevant Skills: {letter_data.get('skills', '')}
        - Role Type: {role_type}
        - Location: {letter_data.get('location', '')}
        - Tone: {tone}
        - Current Date: {current_date}
        
        Create a compelling cover letter with the following structure:
        1. Header - Applicant's contact details and date
        2. Greeting - Personalized salutation to the hiring manager
        3. Introduction - Engaging opening paragraph expressing interest in the position
        4. Body - 1-2 paragraphs highlighting relevant skills and experience
        5. Closing - Brief paragraph expressing enthusiasm and requesting an interview
        6. Signature - Professional sign-off
        
        Return the output as a valid JSON string with the following structure:
        {{
          "header": "The formatted header with contact info and date",
          "salutation": "The salutation line",
          "introductionParagraph": "The opening paragraph",
          "bodyParagraphs": ["Array of body paragraphs"],
          "closingParagraph": "The closing paragraph",
          "signature": "The signature line",
          "fullLetter": "The complete formatted cover letter with all components"
        }}
        
        Make the cover letter {tone.lower()} in tone, tailored to a {role_type.lower()} position, and focused on the specific job and company. The letter should be 1 page in length (approximately 300-400 words) and follow standard business letter format.
        """
        
        return prompt