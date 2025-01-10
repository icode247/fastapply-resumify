# api/index.py
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from .matcher import EnhancedResumeJobMatcher
from .utils import  validate_input
import re
from .utils import LATEX_TEMPLATE

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = '/tmp'

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "10 per hour"]
)

matcher = EnhancedResumeJobMatcher()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

def process_for_json(result):
    """Convert sets to lists for JSON serialization"""
    if isinstance(result, dict):
        return {k: process_for_json(v) for k, v in result.items()}
    if isinstance(result, set):
        return list(result)
    return result

@app.route('/api/match', methods=['POST'])
@limiter.limit("10 per minute")
def match_resumes():
    try:
        # Check for resume URLs in JSON body
        data = request.get_json()
        if not data or 'resume_urls' not in data:
            return jsonify({"error": "No resume URLs provided"}), 400
        
        if 'job_description' not in data:
            return jsonify({"error": "No job description provided"}), 400

        job_description = data['job_description']
        if not validate_input(job_description):
            return jsonify({"error": "Invalid job description"}), 400

        results = []
        resume_urls = data['resume_urls']
        
        for url in resume_urls:
            try:
                # Process URL directly with the matcher
                result = matcher.process_resume(url, job_description)
                results.append(process_for_json(result))
            except Exception as e:
                app.logger.error(f"Error processing resume URL {url}: {str(e)}")
                # Continue processing other URLs even if one fails
                continue

        return jsonify({
            "success": True,
            "matches": results
        })

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/generate-resume', methods=['POST'])
def generate_resume():
    try:
        job_description = request.json.get('job_description')
        user_data = request.json.get('user_data')
        if not job_description or not user_data:
            return jsonify({"error": "Missing required fields"}), 400


        token = "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"
        enhanced_content = enhance_with_huggingface(
            user_data,
            job_description,
            LATEX_TEMPLATE,
            token
        )
        
        if not enhanced_content:
            return jsonify({"error": "Failed to generate resume"}), 500
            
        return enhanced_content, 200, {'Content-Type': 'text/html'}

    except Exception as error:
        print(f"API Error: {str(error)}")
        return jsonify({
            "error": "Failed to generate resume",
            "details": str(error)
        }), 500
def enhance_with_huggingface(user_data: str, job_description: str, template: str, api_token: str) -> str:
    """Enhance resume content using Qwen 2.5 Coder API with exact template matching."""
    try:
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-32B-Instruct"

        # More detailed and structured prompt
        prompt = f"""You are an expert ATS optimization specialist and resume formatter. Your task is to create an HTML resume that exactly matches the structure and format of the provided LaTeX template while optimizing content for ATS compatibility.

Template Analysis:
The provided LaTeX template has the following structure:
1. Header section with name, title, and contact details
2. Professional Summary section
3. Skills section with specific categories
4. Experience section with multiple roles
5. Education section

Task Requirements:
1. First analyze the job description: {job_description}
   - Extract all key requirements and skills
   - Note important industry-specific keywords
   - Identify required years of experience and qualifications

2. Then analyze the user data: {user_data}
   - Match skills and experiences with job requirements
   - Identify relevant accomplishments
   - Extract education and certification details

3. Create an HTML resume that:
   - Follows the EXACT same section order as the template: {template}
   - Maintains all sections: Professional Summary, Skills, Experience, Education
   - Uses consistent heading levels (h1, h2, etc.)
   - Includes proper spacing between sections
   - Uses professional fonts and styling
   - Optimizes content with keywords from job description
   - Maintains the same bullet point structure for experiences

4. Output Requirements:
   - Return ONLY the HTML code
   - Include all CSS styling in a <style> tag
   - Ensure the HTML structure mirrors the LaTeX template sections exactly
   - No explanations or comments needed, just the HTML code

Important: The output must be valid HTML that maintains the exact same structure, sections, and formatting as the provided LaTeX template."""

        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": 0.7,
                "max_new_tokens": 2048,
                "return_full_text": False
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload)
        print(f"API Response Status: {response.status_code}")
        print(f"API Response: {response.text}")
        response.raise_for_status()
        
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            enhanced_content = result[0]
            if isinstance(enhanced_content, str):
                content = enhanced_content
            else:
                content = enhanced_content.get("generated_text", "")
        else:
            content = ""
            
        # Clean up any markdown code block indicators
        content = re.sub(r'^```html\n', '', content)
        content = re.sub(r'\n```$', '', content)
        
        return content.strip()
        
    except Exception as e:
        print(f"Qwen API error: {str(e)}")
        return ""

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large"}), 413

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded"}), 429
