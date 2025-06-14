# app/core/resume_score.py
"""
Resume Scoring functionality.
"""
import logging
import json
import re
from typing import Dict, Any, List, Union
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class ResumeScorer:
    """
    Score and evaluate resumes based on best practices and industry standards.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.logger = logging.getLogger(__name__)
        
    def score_resume(self, resume_text: str, job_description: str = None) -> Dict[str, Any]:
        """
        Score and evaluate a resume based on best practices and optionally a job description
        
        Args:
            resume_text: Text content of the resume
            job_description: Optional job description to evaluate resume against
            
        Returns:
            Dictionary containing the evaluation results including overall score,
            section scores, improvements, and strengths
        """
        try:
            if not resume_text or len(resume_text.strip()) < 50:
                raise ValueError("Resume text is too short for meaningful analysis")
                
            # Create the prompt for OpenAI
            prompt = self._create_resume_scoring_prompt(resume_text, job_description)
            
            # Call OpenAI API to evaluate the resume
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Scoring resume of {len(resume_text)} characters" + 
                           (f" against job description" if job_description else ""))
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert ATS (Applicant Tracking System) and resume evaluation specialist. 
                        Your job is to analyze resumes objectively and provide detailed, actionable feedback to help job seekers 
                        improve their resumes and increase their chances of getting interviews."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            
            result = chat_completion.choices[0].message.content
            
            try:
                score_result = json.loads(result)
                score_result["success"] = True
                return score_result
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    score_result_str = json_match.group(0)
                    try:
                        score_result = json.loads(score_result_str)
                        score_result["success"] = True
                        return score_result
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error scoring resume: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _create_resume_scoring_prompt(self, resume_text: str, job_description: str = None) -> str:
        """
        Create a prompt for the AI to evaluate a resume
        
        Args:
            resume_text: Text content of the resume
            job_description: Optional job description to evaluate resume against
            
        Returns:
            String containing the prompt
        """
        job_specific_instructions = ""
        if job_description:
            job_specific_instructions = f"""
            Additionally, evaluate how well this resume matches the following job description:
            
            ```
            {job_description}
            ```
            
            For each section, also assess its relevance and alignment with the job description.
            Include job-specific keyword analysis and recommendations for better targeting this position.
            """
            
        prompt = f"""
        Analyze and score the following resume based on best practices, ATS compatibility, 
        and overall effectiveness{" for the provided job description" if job_description else ""}.
        
        RESUME TEXT:
        ```
        {resume_text}
        ```
        
        {job_specific_instructions}
        
        Provide a comprehensive evaluation with the following:
        
        1. Overall score from 0-100
        2. Section-by-section analysis with individual scores and specific feedback
        3. Key strengths of the resume
        4. Specific improvements that could be made
        
        Return your evaluation in the following JSON format:
        {{
          "overallScore": number (0-100),
          "sections": [
            {{
              "name": "section name (e.g., 'Contact Information', 'Experience', 'Education', etc.)",
              "score": number (0-100),
              "feedback": "specific feedback for this section",
              "status": "good" or "warning" or "bad"
            }}
            // Include entries for all major sections of the resume
          ],
          "improvements": [
            "specific suggestion 1",
            "specific suggestion 2",
            // Include 3-5 specific, actionable improvements
          ],
          "strengths": [
            "specific strength 1",
            "specific strength 2",
            // Include 2-4 notable strengths
          ]
        }}
        
        Ensure your feedback is specific, actionable, and tailored to this exact resume.
        For section status: 
        - "good" means no major issues (score 80-100)
        - "warning" means some issues to address (score 50-79)
        - "bad" means significant problems (score 0-49)
        """
        
        return prompt
        
    def generate_improved_resume(self, resume_text: str, job_description: str = None) -> Dict[str, Any]:
        """
        Generate an improved version of a resume based on best practices
        
        Args:
            resume_text: Text content of the resume
            job_description: Optional job description to target the resume toward
            
        Returns:
            Dictionary containing the improved resume and explanation of changes
        """
        try:
            if not resume_text or len(resume_text.strip()) < 50:
                raise ValueError("Resume text is too short for meaningful improvement")
                
            # Create the prompt for OpenAI
            prompt = self._create_resume_improvement_prompt(resume_text, job_description)
            
            # Call OpenAI API to improve the resume
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating improved resume version" + 
                           (f" targeted to job description" if job_description else ""))
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert resume writer and career coach who helps job seekers
                        create ATS-friendly, impactful resumes that land interviews. Your improvements maintain
                        the original information while enhancing presentation, language, and effectiveness."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                temperature=0.4,
                response_format={"type": "json_object"},
            )
            
            result = chat_completion.choices[0].message.content
            
            try:
                improved_result = json.loads(result)
                improved_result["success"] = True
                return improved_result
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    improved_result_str = json_match.group(0)
                    try:
                        improved_result = json.loads(improved_result_str)
                        improved_result["success"] = True
                        return improved_result
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error improving resume: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _create_resume_improvement_prompt(self, resume_text: str, job_description: str = None) -> str:
        """
        Create a prompt for the AI to improve a resume
        
        Args:
            resume_text: Text content of the resume
            job_description: Optional job description to target the resume toward
            
        Returns:
            String containing the prompt
        """
        job_targeting_instructions = ""
        if job_description:
            job_targeting_instructions = f"""
            Target the improved resume toward this specific job description:
            
            ```
            {job_description}
            ```
            
            Optimize for keywords and skills mentioned in the job description.
            Rephrase accomplishments to better align with the role requirements.
            """
            
        prompt = f"""
        Improve the following resume based on best practices, ATS compatibility, 
        and overall effectiveness{" for the provided job description" if job_description else ""}.
        
        ORIGINAL RESUME:
        ```
        {resume_text}
        ```
        
        {job_targeting_instructions}
        
        Create an improved version that:
        
        1. Enhances formatting and structure for better readability
        2. Strengthens bullet points with concrete achievements and metrics
        3. Uses action verbs and impactful language
        4. Removes filler words and unnecessary content
        5. Ensures proper keyword optimization for ATS systems
        6. Maintains all factual information (do not invent experience or qualifications)
        
        Return your response in the following JSON format:
        {{
          "improvedResume": "The complete improved resume text with proper formatting",
          "changesSummary": [
            "description of key change 1",
            "description of key change 2",
            // Include 3-5 key changes made
          ],
          "keywordsOptimized": [
            "keyword 1",
            "keyword 2",
            // Include relevant keywords that were added or strengthened
          ]
        }}
        
        Keep the same general structure and information as the original resume, 
        but enhance the presentation, wording, and impact.
        """
        
        return prompt