"""
HuggingFace API integration for NLP tasks.
"""
import json
import requests
import re
import logging
import os
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def enhance_with_huggingface(user_data: dict, job_description: str, max_retries: int = 3) -> Optional[dict]:
    """
    Enhanced version with retry logic and better error handling
    """
    # Get API token from environment or use default
    api_token = os.environ.get("HUGGINGFACE_API_TOKEN", "")
    logger = logging.getLogger(__name__)
    
    for attempt in range(max_retries):
        try:
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            # Use different models based on availability
            api_urls = [
                "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-32B-Instruct",
                "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-14B-Instruct",
                "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
            ]
            
            # Try each model in sequence
            for api_url in api_urls:
                try:
                    prompt = f"""Enhance this resume data for the following job description. 
                    Maintain the same structure but optimize content and keywords.
                    
                    Job Description: {job_description}
                    
                    User Data: {json.dumps(user_data, indent=2)}
                    
                    Return only the enhanced data in JSON format matching the original structure."""

                    payload = {
                        "inputs": prompt,
                        "parameters": {
                            "temperature": 0.7,
                            "max_new_tokens": 2048,
                            "return_full_text": False
                        }
                    }
                    
                    # Set a timeout to avoid hanging
                    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    if isinstance(result, list) and len(result) > 0:
                        response_text = result[0].get("generated_text", "{}")
                        
                        # Try to extract JSON from the response text
                        json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                        if json_match:
                            response_text = json_match.group(1)
                        
                        try:
                            enhanced_data = json.loads(response_text)
                            return enhanced_data
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON from API response, trying next model")
                            continue
                    
                    # If we got a response but couldn't process it, try next model
                    logger.warning(f"Unexpected response format from {api_url}, trying next model")
                    
                except requests.RequestException as req_err:
                    logger.warning(f"Request failed for {api_url}: {str(req_err)}, trying next model")
                    continue
            
            # If all models failed, wait before retry
            logger.warning(f"All models failed, retrying in {2**attempt} seconds (attempt {attempt+1}/{max_retries})")
            time.sleep(2**attempt)  # Exponential backoff
            
        except Exception as e:
            logger.error(f"Error enhancing resume: {str(e)}")
            # On the last attempt, give up and return None
            if attempt == max_retries - 1:
                return None
            
            # Otherwise wait and retry
            time.sleep(2**attempt)
    
    # If we exhausted all retries, return None
    return None