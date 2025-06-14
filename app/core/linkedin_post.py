# app/core/linkedin_post.py
"""
LinkedIn Post Generator functionality.
"""
import logging
import json
import re
from typing import Dict, Any, List
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class LinkedInPostGenerator:
    """
    Generate engaging LinkedIn posts based on input parameters.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.logger = logging.getLogger(__name__)
        
    def generate_linkedin_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an engaging LinkedIn post based on input parameters
        
        Args:
            post_data: Dictionary containing post parameters
                topic: Main topic of the post
                purpose: Purpose of the post (share_knowledge, announce_news, etc.)
                industry: Related industry
                keyPoints: Key points to include
                tone: Tone of the post (professional, conversational, etc.)
                includeHashtags: Whether to include hashtags (yes/no)
                includeCallToAction: Whether to include call to action (yes/no)
                postLength: Target length (short, medium, long)
                
        Returns:
            Dictionary containing the generated LinkedIn post
        """
        try:
            # Validate required fields
            required_fields = ['topic', 'purpose']
            missing_fields = [field for field in required_fields if not post_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            # Create the prompt for OpenAI
            prompt = self._create_linkedin_post_prompt(post_data)
            
            # Call OpenAI API to generate the post
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating LinkedIn post about {post_data.get('topic')} for purpose: {post_data.get('purpose')}")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert LinkedIn content creator who crafts engaging, professional posts that drive engagement and establish thought leadership."
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
                post = json.loads(result)
                post["success"] = True
                return post
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    post_str = json_match.group(0)
                    try:
                        post = json.loads(post_str)
                        post["success"] = True
                        return post
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error generating LinkedIn post: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _create_linkedin_post_prompt(self, post_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the AI to generate a LinkedIn post
        
        Args:
            post_data: Dictionary containing post parameters
            
        Returns:
            String containing the prompt
        """
        # Set default values if not provided
        topic = post_data.get('topic', '')
        purpose = post_data.get('purpose', 'share_knowledge')
        industry = post_data.get('industry', '')
        key_points = post_data.get('keyPoints', '')
        tone = post_data.get('tone', 'professional')
        include_hashtags = post_data.get('includeHashtags', 'yes').lower() == 'yes'
        include_cta = post_data.get('includeCallToAction', 'yes').lower() == 'yes'
        post_length = post_data.get('postLength', 'medium').lower()
        
        # Map post length to word count
        length_map = {
            'short': "100-150 words",
            'medium': "200-250 words",
            'long': "300-400 words"
        }
        word_count = length_map.get(post_length, "200-250 words")
        
        # Map purpose to content strategy
        purpose_map = {
            'share_knowledge': "Share valuable insights and expertise on the topic",
            'announce_news': "Announce news or updates in an engaging way",
            'share_achievement': "Share a professional achievement with humility and impact",
            'industry_trend': "Discuss an industry trend with insight and perspective",
            'ask_question': "Ask a thought-provoking question to encourage engagement",
            'share_story': "Tell a compelling professional story with a lesson or takeaway"
        }
        purpose_guidance = purpose_map.get(purpose, purpose_map['share_knowledge'])
        
        prompt = f"""
        Generate an engaging LinkedIn post in JSON format based on the following information:
        
        - Topic: {topic}
        - Purpose: {purpose_guidance}
        - Industry: {industry}
        - Key Points: {key_points}
        - Tone: {tone}
        - Include Hashtags: {"Yes" if include_hashtags else "No"}
        - Include Call to Action: {"Yes" if include_cta else "No"}
        - Post Length: {word_count}
        
        Create a LinkedIn post that:
        1. Starts with a strong hook or attention-grabbing opening
        2. Delivers valuable content related to the topic
        3. Incorporates the key points provided
        4. Uses appropriate formatting for readability (emojis, line breaks, etc.)
        5. {"Includes relevant industry hashtags" if include_hashtags else "Does not include hashtags"}
        6. {"Ends with a clear call to action" if include_cta else "Ends with a thoughtful conclusion"}
        
        Return the output as a valid JSON string with the following structure:
        {{
          "post": "The complete LinkedIn post with formatting",
          "wordCount": approximate word count,
          "estimatedReadTime": estimated read time in minutes,
          "hashtags": ["Array of hashtags used"] (empty if no hashtags requested)
        }}
        
        Make the post {tone} in tone, focused on the specified topic, and optimized for LinkedIn's algorithm and readability on mobile devices.
        """
        
        return prompt