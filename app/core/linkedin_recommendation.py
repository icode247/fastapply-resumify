# app/core/linkedin_recommendation.py
"""
LinkedIn Recommendation Generator functionality.
"""
import logging
import json
import re
from typing import Dict, Any
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class LinkedInRecommendationGenerator:
    """
    Generate personalized LinkedIn recommendations based on input parameters.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY",  "")
        self.logger = logging.getLogger(__name__)
        
    def generate_linkedin_recommendation(self, recommendation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a personalized LinkedIn recommendation based on input parameters
        
        Args:
            recommendation_data: Dictionary containing recommendation parameters
                yourName: Name of person giving the recommendation
                yourTitle: Job title of person giving the recommendation
                recipientName: Name of person receiving the recommendation
                recipientTitle: Job title of person receiving the recommendation
                relationship: Working relationship (colleague, manager, etc.)
                workDuration: Duration of working together
                keyStrengths: Key professional strengths to highlight
                specificExamples: Specific work examples or achievements
                personalQualities: Personal qualities to mention
                tone: Tone of the recommendation (professional, enthusiastic, etc.)
                length: Target word length
                
        Returns:
            Dictionary containing the generated LinkedIn recommendation
        """
        try:
            # Validate required fields
            required_fields = ['yourName', 'recipientName', 'recipientTitle', 'keyStrengths']
            missing_fields = [field for field in required_fields if not recommendation_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            # Create the prompt for OpenAI
            prompt = self._create_linkedin_recommendation_prompt(recommendation_data)
            
            # Call OpenAI API to generate the recommendation
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating LinkedIn recommendation for {recommendation_data.get('recipientName')} from {recommendation_data.get('yourName')}")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in professional networking who writes thoughtful, personalized LinkedIn recommendations that highlight a person's unique strengths and contributions."
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
                recommendation = json.loads(result)
                recommendation["success"] = True
                return recommendation
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    recommendation_str = json_match.group(0)
                    try:
                        recommendation = json.loads(recommendation_str)
                        recommendation["success"] = True
                        return recommendation
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error generating LinkedIn recommendation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _create_linkedin_recommendation_prompt(self, recommendation_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the AI to generate a LinkedIn recommendation
        
        Args:
            recommendation_data: Dictionary containing recommendation parameters
            
        Returns:
            String containing the prompt
        """
        # Set default values if not provided
        your_name = recommendation_data.get('yourName', '')
        your_title = recommendation_data.get('yourTitle', '')
        recipient_name = recommendation_data.get('recipientName', '')
        recipient_title = recommendation_data.get('recipientTitle', '')
        relationship = recommendation_data.get('relationship', 'colleague')
        work_duration = recommendation_data.get('workDuration', '')
        key_strengths = recommendation_data.get('keyStrengths', '')
        specific_examples = recommendation_data.get('specificExamples', '')
        personal_qualities = recommendation_data.get('personalQualities', '')
        tone = recommendation_data.get('tone', 'professional')
        length = recommendation_data.get('length', 150)
        
        # Map relationship to appropriate phrasing
        relationship_map = {
            'colleague': "worked alongside",
            'manager': "had the pleasure of managing",
            'direct_report': "reported to",
            'client': "worked with as a client",
            'vendor': "collaborated with as a vendor",
            'mentor': "mentored",
            'mentee': "was mentored by"
        }
        relationship_phrase = relationship_map.get(relationship, "worked with")
        
        prompt = f"""
        Generate a personalized LinkedIn recommendation in JSON format based on the following information:
        
        - Your Name: {your_name}
        - Your Title: {your_title}
        - Recipient's Name: {recipient_name}
        - Recipient's Title: {recipient_title}
        - Relationship: {relationship_phrase} {recipient_name}
        - Work Duration: {work_duration}
        - Key Strengths: {key_strengths}
        - Specific Examples: {specific_examples}
        - Personal Qualities: {personal_qualities}
        - Tone: {tone}
        - Target Length: Approximately {length} words
        
        Create a compelling LinkedIn recommendation that:
        1. Starts with a strong opening statement about the recipient
        2. Establishes your credibility and relationship to the recipient
        3. Highlights 2-3 specific strengths with concrete examples
        4. Includes a personal touch about working with them
        5. Ends with a strong endorsement or recommendation
        
        Return the output as a valid JSON string with the following structure:
        {{
          "recommendation": "The complete LinkedIn recommendation",
          "wordCount": approximate word count,
          "keyStrengthsHighlighted": ["Array of key strengths highlighted in the recommendation"]
        }}
        
        Make the recommendation {tone} in tone, authentic, and specific to the recipient's contributions and abilities. The recommendation should be credible and avoid generic praise without specific examples.

        FOLLOW THESE RULES

        SHOULD use clear, simple language.

        SHOULD be spartan and informative.

        SHOULD use short, impactful sentences.

        SHOULD use active voice; avoid passive voice.

        SHOULD focus on practical, actionable insights.

        SHOULD use bullet point lists in social media posts.

        SHOULD use data and examples to support claims when possible.

        SHOULD use “you” and “your” to directly address the reader.

        AVOID

        AVOID using em dashes (—) anywhere in your response. Use only commas, periods, or other standard punctuation. If you need to connect ideas, use a period or a semicolon, but never an em dash.

        AVOID constructions like "...not just this, but also this".

        AVOID metaphors and clichés.

        AVOID generalizations.

        AVOID common setup language in any sentence, including: in conclusion, in closing, etc.

        AVOID output warnings or notes, just the output requested.

        AVOID unnecessary adjectives and adverbs.

        AVOID hashtags.

        AVOID semicolons.

        AVOID markdown.

        AVOID asterisks.

        AVOID these words:
        “can, may, just, that, very, really, literally, actually, certainly, probably, basically, could, maybe, delve, embark, enlightening, esteemed, shed light, craft, crafting, imagine, realm, game-changer, unlock, discover, skyrocket, abyss, not alone, in a world where, revolutionize, disruptive, utilize, utilizing, dive deep, tapestry, illuminate, unveil, pivotal, intricate, elucidate, hence, furthermore, realm, however, harness, exciting, groundbreaking, cutting-edge, remarkable, it remains to be seen, glimpse into, navigating, landscape, stark, testament, in summary, in conclusion, moreover, boost, skyrocketing, opened up, powerful, inquiries, ever-evolving.”

        IMPORTANT:
        Review your response and ensure no em dashes!
        """
        
        return prompt