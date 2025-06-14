# app/core/linkedin_summary.py
"""
LinkedIn Summary Generator functionality.
"""
import logging
import json
import re
from typing import Dict, Any
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class LinkedInSummaryGenerator:
    """
    Generate professional LinkedIn summaries based on input parameters.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY",  "")
        self.logger = logging.getLogger(__name__)
        
    def generate_linkedin_summary(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a professional LinkedIn summary based on input parameters
        
        Args:
            summary_data: Dictionary containing summary parameters
                jobTitle: Current job title
                yearsOfExperience: Years of professional experience
                industry: Industry the person works in
                keySkills: Key professional skills
                achievements: Notable professional achievements
                careerGoals: Future career aspirations
                targetRole: Target role for career progression
                tone: Tone of the summary (professional, conversational, etc.)
                length: Target character length for summary
                
        Returns:
            Dictionary containing the generated LinkedIn summary
        """
        try:
            # Validate required fields
            required_fields = ['jobTitle', 'industry', 'keySkills']
            missing_fields = [field for field in required_fields if not summary_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            # Create the prompt for OpenAI
            prompt = self._create_linkedin_summary_prompt(summary_data)
            
            # Call OpenAI API to generate the summary
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating LinkedIn summary for {summary_data.get('jobTitle')} in {summary_data.get('industry')}")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert LinkedIn profile writer who crafts compelling, professional summaries that help professionals stand out and achieve their career goals."
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
                summary = json.loads(result)
                summary["success"] = True
                return summary
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    summary_str = json_match.group(0)
                    try:
                        summary = json.loads(summary_str)
                        summary["success"] = True
                        return summary
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error generating LinkedIn summary: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _create_linkedin_summary_prompt(self, summary_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the AI to generate a LinkedIn summary
        
        Args:
            summary_data: Dictionary containing summary parameters
            
        Returns:
            String containing the prompt
        """
        # Set default values if not provided
        tone = summary_data.get('tone', 'professional')
        length = summary_data.get('length', 150)
        years_experience = summary_data.get('yearsOfExperience', 'several years')
        
        prompt = f"""
        Generate a compelling LinkedIn summary in JSON format based on the following information:
        
        - Job Title: {summary_data.get('jobTitle', '')}
        - Years of Experience: {years_experience}
        - Industry: {summary_data.get('industry', '')}
        - Key Skills: {summary_data.get('keySkills', '')}
        - Achievements: {summary_data.get('achievements', '')}
        - Career Goals: {summary_data.get('careerGoals', '')}
        - Target Role: {summary_data.get('targetRole', '')}
        - Tone: {tone}
        - Target Length: Approximately {length} words
        
        Create a concise, impactful LinkedIn summary that:
        1. Starts with a strong hook about professional identity and value proposition
        2. Highlights key experience, skills, and achievements
        3. Demonstrates industry expertise
        4. Conveys career aspirations and goals
        5. Includes a subtle call-to-action for networking or opportunities
        
        Return the output as a valid JSON string with the following structure:
        {{
          "summary": "The complete LinkedIn summary",
          "wordCount": approximate word count,
          "keyThemes": ["Array of key themes/keywords included in the summary"]
        }}
        
        Make the summary {tone} in tone, focused on the {summary_data.get('industry', '')} industry, and highlighting the skills and achievements provided. The summary should be optimized for both human readers and LinkedIn's search algorithm.
        """
        
        return prompt