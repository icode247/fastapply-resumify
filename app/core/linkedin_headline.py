# app/core/linkedin_headline.py
"""
LinkedIn Headline Generator functionality.
"""
import logging
import json
import re
from typing import Dict, Any
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class LinkedInHeadlineGenerator:
    """
    Generate professional LinkedIn headlines based on input parameters.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        
    def generate_linkedin_headline(self, headline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a professional LinkedIn headline based on input parameters
        
        Args:
            headline_data: Dictionary containing headline parameters
                currentRole: Current job title or role
                industry: Industry the person works in
                yearsOfExperience: Years of professional experience
                keySkills: Key professional skills to highlight
                achievements: Notable professional achievements 
                targetAudience: Target audience for the headline
                style: Style of headline (professional, creative, etc.)
                includeEmoji: Whether to include emojis (yes/no)
                length: Maximum character length for headline
                
        Returns:
            Dictionary containing the generated LinkedIn headline
        """
        try:
            # Validate required fields
            required_fields = ['currentRole', 'industry']
            missing_fields = [field for field in required_fields if not headline_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            # Create the prompt for OpenAI
            prompt = self._create_linkedin_headline_prompt(headline_data)
            
            # Call OpenAI API to generate the headline
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating LinkedIn headline for {headline_data.get('currentRole')} in {headline_data.get('industry')}")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert LinkedIn profile writer who crafts compelling, professional headlines that help professionals stand out and attract opportunities."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            
            result = chat_completion.choices[0].message.content
            
            try:
                headline = json.loads(result)
                headline["success"] = True
                return headline
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    headline_str = json_match.group(0)
                    try:
                        headline = json.loads(headline_str)
                        headline["success"] = True
                        return headline
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error generating LinkedIn headline: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _create_linkedin_headline_prompt(self, headline_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the AI to generate a LinkedIn headline
        
        Args:
            headline_data: Dictionary containing headline parameters
            
        Returns:
            String containing the prompt
        """
        # Set default values if not provided
        current_role = headline_data.get('currentRole', '')
        industry = headline_data.get('industry', '')
        years_experience = headline_data.get('yearsOfExperience', '')
        key_skills = headline_data.get('keySkills', '')
        achievements = headline_data.get('achievements', '')
        target_audience = headline_data.get('targetAudience', '')
        style = headline_data.get('style', 'professional')
        include_emoji = headline_data.get('includeEmoji', 'no').lower() == 'yes'
        length = int(headline_data.get('length', 100))
        
        prompt = f"""
        Generate a compelling LinkedIn headline in JSON format based on the following information:
        
        - Current Role: {current_role}
        - Industry: {industry}
        - Years of Experience: {years_experience}
        - Key Skills: {key_skills}
        - Achievements: {achievements}
        - Target Audience: {target_audience}
        - Style: {style}
        - Include Emoji: {"Yes" if include_emoji else "No"}
        - Maximum Length: {length} characters
        
        Create a LinkedIn headline that:
        1. Clearly communicates professional identity and value proposition
        2. Highlights expertise and key skills
        3. Is optimized for LinkedIn search algorithms
        4. Maintains professionalism while being memorable
        5. Stays within the character limit
        6. {"Incorporates relevant emojis" if include_emoji else "Does not use emojis"}
        
        Return the output as a valid JSON string with the following structure:
        {{
          "headline": "The complete LinkedIn headline",
          "characterCount": approximate character count,
          "keywords": ["Array of key search terms included in the headline"]
        }}
        
        Make the headline {style} in style, focused on the {industry} industry, and highlighting the skills and achievements provided. The headline should be optimized for both human readers and LinkedIn's search algorithm.
        """
        
        return prompt