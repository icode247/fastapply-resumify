# app/core/linkedin_hashtags.py
"""
LinkedIn Hashtags Generator functionality.
"""
import logging
import json
import re
from typing import Dict, Any, List
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class LinkedInHashtagsGenerator:
    """
    Generate relevant hashtags for LinkedIn posts based on input parameters.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "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")
        self.logger = logging.getLogger(__name__)
        
    def generate_linkedin_hashtags(self, hashtag_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate relevant LinkedIn hashtags based on input parameters
        
        Args:
            hashtag_data: Dictionary containing hashtag parameters
                industry: Industry related to the post
                topic: Main topic of the post
                postContent: Content of the post
                targetAudience: Target audience for the post
                hashtagCount: Number of hashtags to generate
                popularityLevel: Popularity level of hashtags (trending, niche, mixed)
                
        Returns:
            Dictionary containing the generated LinkedIn hashtags
        """
        try:
            # Validate required fields
            required_fields = ['topic']
            missing_fields = [field for field in required_fields if not hashtag_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            # Create the prompt for OpenAI
            prompt = self._create_linkedin_hashtags_prompt(hashtag_data)
            
            # Call OpenAI API to generate the hashtags
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating LinkedIn hashtags for topic: {hashtag_data.get('topic')}")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert social media strategist who specializes in creating optimized hashtag sets for LinkedIn that increase post visibility and engagement."
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
                hashtags = json.loads(result)
                hashtags["success"] = True
                return hashtags
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    hashtags_str = json_match.group(0)
                    try:
                        hashtags = json.loads(hashtags_str)
                        hashtags["success"] = True
                        return hashtags
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error generating LinkedIn hashtags: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _create_linkedin_hashtags_prompt(self, hashtag_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the AI to generate LinkedIn hashtags
        
        Args:
            hashtag_data: Dictionary containing hashtag parameters
            
        Returns:
            String containing the prompt
        """
        # Set default values if not provided
        industry = hashtag_data.get('industry', '')
        topic = hashtag_data.get('topic', '')
        post_content = hashtag_data.get('postContent', '')
        target_audience = hashtag_data.get('targetAudience', '')
        hashtag_count = int(hashtag_data.get('hashtagCount', 10))
        popularity_level = hashtag_data.get('popularityLevel', 'mixed')
        
        # Map popularity level to strategy
        popularity_map = {
            'trending': "Focus on popular and trending hashtags with high visibility",
            'niche': "Focus on specific niche hashtags with targeted but smaller audiences",
            'mixed': "Provide a balanced mix of popular, industry-specific, and niche hashtags"
        }
        popularity_strategy = popularity_map.get(popularity_level, popularity_map['mixed'])
        
        prompt = f"""
        Generate relevant LinkedIn hashtags in JSON format based on the following information:
        
        - Industry: {industry}
        - Topic: {topic}
        - Post Content: {post_content}
        - Target Audience: {target_audience}
        - Number of Hashtags: {hashtag_count}
        - Popularity Strategy: {popularity_strategy}
        
        Create a set of LinkedIn hashtags that:
        1. Are relevant to the topic and industry
        2. Follow the specified popularity strategy
        3. Include a mix of general, industry-specific, and topic-specific hashtags
        4. Follow LinkedIn best practices (no spaces, appropriate length)
        5. Will help increase post visibility and engagement
        6. Are targeted to the specified audience
        
        Return the output as a valid JSON string with the following structure:
        {{
          "hashtags": ["Array of hashtags without the # symbol"],
          "formattedHashtags": "All hashtags in a single string with # symbols ready to copy-paste",
          "categories": {{
            "trending": ["Trending hashtags"],
            "industry": ["Industry-specific hashtags"],
            "niche": ["More specific niche hashtags"]
          }},
          "tips": ["Array of 2-3 tips for using these hashtags effectively"]
        }}
        
        Ensure all hashtags follow LinkedIn best practices: no spaces, no special characters (except underscore), and avoid excessively long hashtags that are unlikely to be searched.
        """
        
        return prompt