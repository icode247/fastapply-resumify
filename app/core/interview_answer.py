# app/core/interview_answer.py
"""
Interview Answer Generator functionality.
"""
import logging
import json
import re
from typing import Dict, Any, List
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class InterviewAnswerGenerator:
    """
    Generate professional interview answers based on input parameters and company context.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "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")
        self.logger = logging.getLogger(__name__)
        
        # Top companies data for contextual answers
        self.company_data = {
            "google": {
                "culture": "innovation-focused, data-driven, user-centric, collaborative",
                "values": "Focus on the user, freedom to pursue innovation, flat hierarchy, technical excellence",
                "interview_style": "Problem-solving focused, behavioral questions about teamwork, leadership principles",
                "key_traits": "Analytical thinking, bias for action, technical depth, innovation mindset"
            },
            "amazon": {
                "culture": "customer-obsessed, frugal, high bar for talent, bias for action",
                "values": "Customer Obsession, Ownership, Invent & Simplify, Learn & Be Curious, Hire the Best",
                "interview_style": "Leadership Principles-based, behavioral questions, technical problem-solving",
                "key_traits": "Ownership mentality, customer focus, data-driven decision making, deliver results"
            },
            "apple": {
                "culture": "design-focused, perfection-oriented, secretive, innovative",
                "values": "Design excellence, user experience, quality, innovation, privacy",
                "interview_style": "Creative problem-solving, attention to detail, passion for products",
                "key_traits": "Perfectionism, creativity, attention to detail, passion for technology"
            },
            "microsoft": {
                "culture": "growth mindset, collaborative, inclusive, innovation-driven",
                "values": "Growth mindset, diversity & inclusion, customer success, innovation",
                "interview_style": "Problem-solving, collaborative approach, coding challenges for technical roles",
                "key_traits": "Adaptability, continual learning, collaborative spirit, technology passion"
            },
            "meta": {
                "culture": "move fast, open communication, impact-focused, builder's mentality",
                "values": "Move Fast, Be Bold, Focus on Impact, Be Open, Build Social Value",
                "interview_style": "Technical skills, cultural fit, problem-solving ability",
                "key_traits": "Building mindset, willingness to take risks, focus on impact"
            },
            "netflix": {
                "culture": "freedom & responsibility, high performance, context not control",
                "values": "Judgment, communication, impact, curiosity, courage, passion",
                "interview_style": "Experience-based, focus on past actions, cultural alignment",
                "key_traits": "Self-discipline, ownership, excellence, direct communication"
            }
        }
        
        # Common interview questions with required skills
        self.common_questions = {
            "tell_me_about_yourself": {
                "question": "Tell me about yourself",
                "category": "introduction",
                "skills_to_highlight": ["communication", "self-awareness", "relevance"],
                "tips": ["Start with present", "Touch on relevant past", "End with future goals", "Keep under 2 minutes"]
            },
            "why_this_company": {
                "question": "Why do you want to work for this company?",
                "category": "motivation",
                "skills_to_highlight": ["research", "alignment", "enthusiasm"],
                "tips": ["Show company research", "Connect to personal values", "Mention specific initiatives"]
            },
            "why_this_role": {
                "question": "Why this role?",
                "category": "motivation",
                "skills_to_highlight": ["role understanding", "career clarity", "alignment"],
                "tips": ["Connect to career path", "Highlight relevant skills", "Show enthusiasm"]
            },
            "greatest_strengths": {
                "question": "What are your greatest strengths?",
                "category": "self-assessment",
                "skills_to_highlight": ["self-awareness", "relevance", "evidence"],
                "tips": ["Choose relevant strengths", "Provide examples", "Quantify impact"]
            },
            "greatest_weakness": {
                "question": "What is your greatest weakness?",
                "category": "self-assessment",
                "skills_to_highlight": ["self-awareness", "growth mindset", "honesty"],
                "tips": ["Be honest", "Show improvement efforts", "Choose non-critical weakness"]
            },
            "challenging_situation": {
                "question": "Tell me about a challenging situation and how you handled it",
                "category": "behavioral",
                "skills_to_highlight": ["problem-solving", "resilience", "adaptability"],
                "tips": ["Use STAR method", "Focus on actions", "Highlight positive outcome"]
            },
            "biggest_achievement": {
                "question": "What is your biggest professional achievement?",
                "category": "behavioral",
                "skills_to_highlight": ["impact", "initiative", "results"],
                "tips": ["Choose relevant achievement", "Quantify results", "Show your specific contribution"]
            },
            "handle_failure": {
                "question": "Describe a time you failed and what you learned",
                "category": "behavioral",
                "skills_to_highlight": ["learning agility", "resilience", "self-reflection"],
                "tips": ["Be honest", "Focus on the learning", "Explain how you've improved"]
            },
            "work_under_pressure": {
                "question": "How do you work under pressure?",
                "category": "behavioral",
                "skills_to_highlight": ["stress management", "prioritization", "focus"],
                "tips": ["Provide specific examples", "Highlight coping strategies", "Show positive outcomes"]
            },
            "conflict_resolution": {
                "question": "How do you handle conflict with colleagues?",
                "category": "interpersonal",
                "skills_to_highlight": ["communication", "empathy", "problem-solving"],
                "tips": ["Focus on constructive resolution", "Show respect for others", "Emphasize communication"]
            },
            "leadership_style": {
                "question": "Describe your leadership style",
                "category": "leadership",
                "skills_to_highlight": ["self-awareness", "adaptability", "team development"],
                "tips": ["Be authentic", "Provide examples", "Connect to results"]
            },
            "five_year_plan": {
                "question": "Where do you see yourself in 5 years?",
                "category": "career goals",
                "skills_to_highlight": ["ambition", "stability", "growth mindset"],
                "tips": ["Be realistic", "Show commitment", "Connect to company growth"]
            },
            "salary_expectations": {
                "question": "What are your salary expectations?",
                "category": "practical",
                "skills_to_highlight": ["research", "confidence", "value communication"],
                "tips": ["Research market rates", "Provide a range", "Consider total compensation"]
            },
            "questions_for_interviewer": {
                "question": "Do you have any questions for me?",
                "category": "engagement",
                "skills_to_highlight": ["curiosity", "engagement", "preparation"],
                "tips": ["Prepare 3-5 thoughtful questions", "Focus on role, team, and culture", "Avoid basic information"]
            }
        }
        
        # Response frameworks for different question types
        self.answer_frameworks = {
            "introduction": {
                "structure": ["Present role/situation", "Relevant past experience", "Future goals aligned with role"],
                "template": "Currently, I {current_situation}. Before this, I {past_experience} where I gained valuable skills in {relevant_skills}. I'm now looking to {future_goal} which aligns perfectly with this {role} at {company}."
            },
            "motivation": {
                "structure": ["Company-specific appeal", "Personal alignment", "Enthusiastic conclusion"],
                "template": "I'm particularly drawn to {company}'s {company_trait} and commitment to {company_value}. This resonates with my personal focus on {personal_value}. I'm excited about the opportunity to contribute to {specific_initiative} and grow with the company."
            },
            "self-assessment": {
                "structure": ["Clear statement", "Supporting evidence", "Relevance to role"],
                "template": "One of my greatest {assessment_type} is {trait}. For example, at {previous_company}, I {specific_example} which resulted in {measurable_outcome}. This {trait} would be valuable in this role because {relevance}."
            },
            "behavioral": {
                "structure": ["Situation", "Task", "Action", "Result", "Learning"],
                "template": "I faced a situation where {situation}. I needed to {task}. I approached this by {action}. As a result, {result}. From this experience, I learned {learning} which I believe will help me in similar situations at {company}."
            },
            "interpersonal": {
                "structure": ["Communication approach", "Empathy demonstration", "Resolution process"],
                "template": "When facing {interpersonal_situation}, I first {communication_approach}. I make sure to {empathy_demonstration} to understand different perspectives. Then I work toward {resolution_process} that benefits the team and organization."
            },
            "leadership": {
                "structure": ["Philosophy statement", "Adaptability approach", "Example of success"],
                "template": "My leadership philosophy centers on {leadership_philosophy}. I adapt my approach based on {adaptation_factors}. For instance, when leading {specific_project}, I {leadership_action} which resulted in {team_outcome}."
            },
            "career goals": {
                "structure": ["Short-term goals", "Long-term vision", "Development plan"],
                "template": "In the next few years, I aim to {short_term_goal} and develop expertise in {expertise_area}. Long-term, I aspire to {long_term_vision}. I have a development plan that includes {development_actions} to help me achieve these goals."
            },
            "practical": {
                "structure": ["Research basis", "Range statement", "Value proposition"],
                "template": "Based on my research and experience level, I'm looking for a range of {salary_range}. However, I value the total compensation package including {benefits_of_interest}. Most importantly, I'm excited about the value I can bring to {company} through {key_contributions}."
            },
            "engagement": {
                "structure": ["Role-specific questions", "Team questions", "Culture questions"],
                "template": "I'd like to know more about {role_curiosity}. I'm also curious about {team_question}. Finally, I'd love to hear your perspective on {culture_question}."
            }
        }
        
    def generate_interview_answer(self, answer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a professional interview answer based on input parameters
        
        Args:
            answer_data: Dictionary containing answer parameters
                company: Company name
                jobTitle: Job title/role
                question: Interview question
                yearsOfExperience: Years of experience
                keySkills: Key skills relevant to the position
                achievements: Notable achievements
                industry: Industry
                tone: Tone of the answer
                
        Returns:
            Dictionary containing the generated answer
        """
        try:
            # Validate required fields
            required_fields = ['company', 'jobTitle', 'question']
            missing_fields = [field for field in required_fields if not answer_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            # Create the prompt for OpenAI
            prompt = self._create_interview_answer_prompt(answer_data)
            
            # Call OpenAI API to generate the answer
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating interview answer for {answer_data.get('jobTitle')} at {answer_data.get('company')}")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert interview coach who helps professionals craft compelling, authentic interview answers that showcase their value while respecting company culture."
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
                answer = json.loads(result)
                answer["success"] = True
                return answer
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    answer_str = json_match.group(0)
                    try:
                        answer = json.loads(answer_str)
                        answer["success"] = True
                        return answer
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error generating interview answer: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_company_data(self, company_name: str) -> Dict[str, Any]:
        """Get company-specific data for contextualizing answers"""
        company_name = company_name.lower()
        
        # Try exact match
        if company_name in self.company_data:
            return self.company_data[company_name]
            
        # Try partial match
        for company, data in self.company_data.items():
            if company in company_name or company_name in company:
                return data
                
        # Return generic data if no match
        return {
            "culture": "professional, results-oriented, collaborative",
            "values": "Quality, teamwork, innovation, customer focus",
            "interview_style": "Mix of behavioral and technical questions",
            "key_traits": "Problem-solving, teamwork, communication, expertise"
        }
    
    def get_question_data(self, question: str) -> Dict[str, Any]:
        """Get question-specific data for structuring answers"""
        # Try exact match
        for q_id, data in self.common_questions.items():
            if data["question"].lower() == question.lower():
                return data
                
        # Try fuzzy match
        for q_id, data in self.common_questions.items():
            if any(keyword in question.lower() for keyword in q_id.split('_')):
                return data
                
        # Categorize by keywords
        if any(word in question.lower() for word in ["yourself", "background", "introduce"]):
            return self.common_questions["tell_me_about_yourself"]
        elif any(word in question.lower() for word in ["why", "interest", "join"]) and "company" in question.lower():
            return self.common_questions["why_this_company"]
        elif any(word in question.lower() for word in ["strength", "good at", "excel"]):
            return self.common_questions["greatest_strengths"]
        elif any(word in question.lower() for word in ["weakness", "improve", "development"]):
            return self.common_questions["greatest_weakness"]
        elif any(word in question.lower() for word in ["challenge", "difficult", "obstacle"]):
            return self.common_questions["challenging_situation"]
        elif any(word in question.lower() for word in ["achievement", "proud", "accomplish"]):
            return self.common_questions["biggest_achievement"]
        elif any(word in question.lower() for word in ["fail", "mistake", "wrong"]):
            return self.common_questions["handle_failure"]
        elif any(word in question.lower() for word in ["pressure", "stress", "deadline"]):
            return self.common_questions["work_under_pressure"]
        elif any(word in question.lower() for word in ["conflict", "disagree", "difficult person"]):
            return self.common_questions["conflict_resolution"]
        elif any(word in question.lower() for word in ["lead", "leadership", "team"]):
            return self.common_questions["leadership_style"]
        elif any(word in question.lower() for word in ["year", "future", "plan"]):
            return self.common_questions["five_year_plan"]
        elif any(word in question.lower() for word in ["salary", "compensation", "pay"]):
            return self.common_questions["salary_expectations"]
        
        # Default to a general behavioral question framework
        return {
            "question": question,
            "category": "behavioral",
            "skills_to_highlight": ["problem-solving", "communication", "adaptability"],
            "tips": ["Use STAR method", "Be specific", "Show impact"]
        }
            
    def _create_interview_answer_prompt(self, answer_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the AI to generate an interview answer
        
        Args:
            answer_data: Dictionary containing answer parameters
            
        Returns:
            String containing the prompt
        """
        # Extract and process data
        company = answer_data.get('company', '').strip()
        job_title = answer_data.get('jobTitle', '').strip()
        question = answer_data.get('question', '').strip()
        years_experience = answer_data.get('yearsOfExperience', '').strip()
        key_skills = answer_data.get('keySkills', '').strip()
        achievements = answer_data.get('achievements', '').strip()
        industry = answer_data.get('industry', '').strip()
        tone = answer_data.get('tone', 'professional').strip()
        
        # Get company and question context
        company_context = self.get_company_data(company)
        question_data = self.get_question_data(question)
        question_category = question_data.get("category", "behavioral")
        
        # Get answer framework
        framework = self.answer_frameworks.get(question_category, self.answer_frameworks["behavioral"])
        
        # Prepare specific guidelines based on question type
        skills_to_highlight = ", ".join(question_data.get("skills_to_highlight", ["communication", "problem-solving"]))
        answer_tips = "\n".join([f"- {tip}" for tip in question_data.get("tips", ["Be specific", "Show impact"])])
        
        prompt = f"""
        Generate a professional interview answer in JSON format for a {job_title} position at {company} based on the following information:
        
        CANDIDATE INFORMATION:
        - Job Title: {job_title}
        - Years of Experience: {years_experience}
        - Key Skills: {key_skills}
        - Notable Achievements: {achievements}
        - Industry: {industry}
        
        QUESTION: "{question}"
        
        COMPANY CONTEXT:
        - Company: {company}
        - Company Culture: {company_context.get('culture')}
        - Company Values: {company_context.get('values')}
        - Interview Style: {company_context.get('interview_style')}
        - Key Traits Valued: {company_context.get('key_traits')}
        
        ANSWER FRAMEWORK:
        - Question Category: {question_category}
        - Structure: {', '.join(framework.get('structure', []))}
        - Skills to Highlight: {skills_to_highlight}
        
        TIPS FOR THIS QUESTION:
        {answer_tips}
        
        Create a compelling, authentic interview answer that:
        1. Follows the appropriate structure for this question type
        2. Demonstrates relevant skills and experience
        3. Aligns with the company culture and values
        4. Includes specific examples and achievements where appropriate
        5. Maintains a {tone} tone throughout
        6. Is concise but comprehensive (200-300 words)
        
        Return the output as a valid JSON string with the following structure:
        {{
          "answer": "The complete interview answer",
          "keyPoints": ["Array of 3-4 key points made in the answer"],
          "skillsHighlighted": ["Array of key skills demonstrated"],
          "improvementTips": ["Array of 2-3 tips to strengthen the answer further"],
          "followUpQuestions": ["Array of 2-3 likely follow-up questions"]
        }}
        
        The answer should be authentic, specific to the candidate's background, and tailored to {company}'s culture. Avoid generic responses that could apply to any company or role.
        """
        
        return prompt