# app/core/resignation_letter.py
"""
Resignation Letter Generator functionality.
"""
import logging
import json
import re
from typing import Dict, Any
from openai import OpenAI
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ResignationLetterGenerator:
    """
    Generate professional resignation letters based on input parameters.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY",  "")
        self.logger = logging.getLogger(__name__)
        
    def generate_resignation_letter(self, letter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a professional resignation letter based on input parameters
        
        Args:
            letter_data: Dictionary containing letter parameters
                fullName: Employee's full name
                currentPosition: Current job title
                company: Company name
                managerName: Manager's name
                lastDay: Last day of employment
                reasonForLeaving: Reason for resignation
                positiveExperiences: Positive experiences at the company
                transitionDetails: Details about transition plan
                tone: Tone of the letter (professional, grateful, etc.)
                format: Format of the letter (formal, standard, brief)
                
        Returns:
            Dictionary containing the generated resignation letter
        """
        try:
            # Validate required fields
            required_fields = ['fullName', 'currentPosition', 'company', 'lastDay']
            missing_fields = [field for field in required_fields if not letter_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            # Create the prompt for OpenAI
            prompt = self._create_resignation_letter_prompt(letter_data)
            
            # Call OpenAI API to generate the letter
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating resignation letter for {letter_data.get('fullName')} at {letter_data.get('company')}")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in professional business communication who drafts clear, respectful resignation letters that maintain positive relationships."
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
                letter = json.loads(result)
                letter["success"] = True
                return letter
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    letter_str = json_match.group(0)
                    try:
                        letter = json.loads(letter_str)
                        letter["success"] = True
                        return letter
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error generating resignation letter: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _create_resignation_letter_prompt(self, letter_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the AI to generate a resignation letter
        
        Args:
            letter_data: Dictionary containing letter parameters
            
        Returns:
            String containing the prompt
        """
        # Get current date for the letter
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Set tone and format based on input or defaults
        tone = letter_data.get('tone', 'professional')
        format_type = letter_data.get('format', 'formal')
        
        # Get manager salutation
        manager_name = letter_data.get('managerName', '')
        if manager_name:
            salutation = f"Dear {manager_name},"
        else:
            salutation = "Dear Manager,"
            
        prompt = f"""
        Generate a professional resignation letter in JSON format based on the following information:
        
        - Full Name: {letter_data.get('fullName', '')}
        - Current Position: {letter_data.get('currentPosition', '')}
        - Company: {letter_data.get('company', '')}
        - Manager Name: {manager_name}
        - Last Day of Employment: {letter_data.get('lastDay', '')}
        - Reason for Leaving: {letter_data.get('reasonForLeaving', '')}
        - Positive Experiences: {letter_data.get('positiveExperiences', '')}
        - Transition Details: {letter_data.get('transitionDetails', '')}
        - Tone: {tone}
        - Format: {format_type}
        - Current Date: {current_date}
        
        Create a clear, professional resignation letter with the following structure:
        1. Header - Employee's contact details and date
        2. Recipient - Manager's name and company address
        3. Greeting - Formal salutation to the manager
        4. First paragraph - Clear statement of resignation and last day
        5. Second paragraph - Gratitude and positive experiences
        6. Third paragraph - Transition plan and offer to help
        7. Closing - Professional sign-off
        
        Return the output as a valid JSON string with the following structure:
        {{
          "header": "The formatted header with contact info and date",
          "recipient": "The recipient information",
          "salutation": "The salutation line",
          "firstParagraph": "The resignation statement paragraph",
          "secondParagraph": "The gratitude paragraph",
          "thirdParagraph": "The transition plan paragraph",
          "closing": "The closing and signature",
          "fullLetter": "The complete formatted resignation letter with all components"
        }}
        
        Make the letter {tone} in tone and {format_type} in format. If the format is 'brief', make the letter concise and direct. If 'formal', use more formal business language. The letter should be approximately 250-350 words and follow standard business letter format.
        """
        
        return prompt