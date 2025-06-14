
"""
Resume processing and optimization using external AI services.
"""
import json
import re
import requests
from typing import Dict, Any
import logging
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

class ATSResumeProcessor:
    """
    Process and generate ATS-optimized resumes based on user data and job descriptions.
    """
    
    def __init__(self, api_token):
        self.api_key = os.environ.get("OPENAI_API_KEY",  "")
        self.logger = logging.getLogger(__name__)
        
    def extract_resume_sections(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract sections from plain text resume into structured format
        """
        # Define common resume section patterns
        section_patterns = {
            "contact": r"(?:CONTACT|PERSONAL)(?:\s+INFORMATION)?",
            "summary": r"(?:PROFESSIONAL\s+)?SUMMARY|PROFILE|OBJECTIVE",
            "skills": r"(?:TECHNICAL\s+)?SKILLS|TECHNOLOGIES|EXPERTISE",
            "experience": r"(?:WORK|PROFESSIONAL)\s+EXPERIENCE|EMPLOYMENT|WORK HISTORY",
            "education": r"EDUCATION(?:\s+(?:AND|&)\s+TRAINING)?",
            "certifications": r"CERTIFICATIONS|CERTIFICATES|ACCREDITATIONS"
        }
        
        # Initialize result dictionary
        result = {
            "name": "",
            "contact": {
                "email": "",
                "phone": "",
                "website": "",
                "github": ""
            },
            "skills": {
                "languages": [],
                "frameworks/libraries": [],
                "technologies": [],
                "others": []
            },
            "experience": [],
            "education": [],
            "certifications": []
        }
        
        # Extract name (assuming it's at the top of the resume)
        lines = resume_text.split('\n')
        if lines and lines[0].strip():
            result["name"] = lines[0].strip()
        
        # Extract email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text)
        if email_match:
            result["contact"]["email"] = email_match.group(0)
        
        # Extract phone
        phone_match = re.search(r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', resume_text)
        if phone_match:
            result["contact"]["phone"] = phone_match.group(0)
        
        # Extract website and github
        website_match = re.search(r'(?:https?://)?(?:www\.)?([A-Za-z0-9-]+\.[A-Za-z0-9-.]+)(?:/\S*)?', resume_text)
        if website_match and "github" not in website_match.group(0).lower():
            result["contact"]["website"] = website_match.group(0)
        
        github_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_-]+)', resume_text)
        if github_match:
            result["contact"]["github"] = github_match.group(0)
        
        # Extract skills - simplified approach, would need refinement in production
        skills_pattern = re.compile(r'(?:' + section_patterns["skills"] + r')(.*?)(?:' + '|'.join(section_patterns.values()) + r')', re.DOTALL | re.IGNORECASE)
        skills_match = skills_pattern.search(resume_text)
        
        if skills_match:
            skills_text = skills_match.group(1).strip()
            # Extract common programming languages
            languages = re.findall(r'\b(?:Python|Java(?:Script)?|TypeScript|C\+\+|C#|Ruby|Go|PHP|Swift|Kotlin|Rust|SQL|HTML|CSS|Bash|Shell)\b', skills_text, re.IGNORECASE)
            if languages:
                result["skills"]["languages"] = [lang.strip() for lang in languages]
            
            # Extract common frameworks/libraries
            frameworks = re.findall(r'\b(?:React|Angular|Vue|Django|Flask|Express|Spring|Laravel|Rails|Node\.js|Next\.js|Svelte|Bootstrap|Tailwind|jQuery|Jest|Mocha|Selenium|Cypress)\b', skills_text, re.IGNORECASE)
            if frameworks:
                result["skills"]["frameworks/libraries"] = [framework.strip() for framework in frameworks]
            
            # Extract common technologies
            technologies = re.findall(r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Git|CI/CD|Jenkins|GitHub Actions|MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch|Kafka|RabbitMQ|Firebase|Heroku|Vercel|Netlify)\b', skills_text, re.IGNORECASE)
            if technologies:
                result["skills"]["technologies"] = [tech.strip() for tech in technologies]
        
        # Extract experience
        experience_pattern = re.compile(r'(?:' + section_patterns["experience"] + r')(.*?)(?:' + '|'.join(section_patterns.values()) + r'|$)', re.DOTALL | re.IGNORECASE)
        experience_match = experience_pattern.search(resume_text)
        
        if experience_match:
            experience_text = experience_match.group(1).strip()
            # Extract job entries (simplified)
            job_entries = re.split(r'\n\s*\n', experience_text)
            
            for entry in job_entries:
                if entry.strip():
                    # Attempt to extract job title, company, and period
                    title_match = re.search(r'^(.+?)(?:at|@|\n|\|)', entry, re.IGNORECASE)
                    company_match = re.search(r'(?:at|@)\s+(.+?)(?:\n|\|)', entry, re.IGNORECASE)
                    period_match = re.search(r'(?:\d{4}\s*-\s*(?:Present|\d{4})|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*(?:-|–|to)\s*(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}))', entry, re.IGNORECASE)
                    
                    # Extract bullet points
                    description_lines = re.findall(r'(?:•|\*|-|\d+\.)\s+(.+)', entry)
                    
                    job = {
                        "title": title_match.group(1).strip() if title_match else "",
                        "company": company_match.group(1).strip() if company_match else "",
                        "period": period_match.group(0) if period_match else "",
                        "description": [line.strip() for line in description_lines]
                    }
                    
                    if job["title"] or job["company"]:
                        result["experience"].append(job)
        
        # Extract education (simplified)
        education_pattern = re.compile(r'(?:' + section_patterns["education"] + r')(.*?)(?:' + '|'.join(section_patterns.values()) + r'|$)', re.DOTALL | re.IGNORECASE)
        education_match = education_pattern.search(resume_text)
        
        if education_match:
            education_text = education_match.group(1).strip()
            # Look for degree patterns
            degree_matches = re.findall(r'((?:Bachelor|Master|Ph\.?D|B\.S\.|M\.S\.|M\.B\.A|Associate)(?:\s+(?:of|in|degree))?\s+(?:[^,\n]+))', education_text, re.IGNORECASE)
            
            for degree in degree_matches:
                # Try to find associated institution
                institution_match = re.search(r'' + re.escape(degree) + r'.*?((?:University|College|Institute|School)\s+of\s+[^,\n]+|[^,\n]+(?:University|College|Institute|School))', education_text, re.IGNORECASE)
                
                # Try to find year
                year_match = re.search(r'' + re.escape(degree) + r'.*?(\d{4})', education_text)
                
                education_entry = {
                    "degree": degree.strip(),
                    "institution": institution_match.group(1).strip() if institution_match else "",
                    "year": year_match.group(1) if year_match else ""
                }
                
                result["education"].append(education_entry)
        
        return result
    
    def optimize_resume_for_ats_pdf(self, resume_text, job_description: str, user_data: Any) -> Dict[str, Any]:
        """
        Optimize resume data for ATS based on job description using HuggingFace API
        """
        try:
            # Solution 1: Escape all curly braces in the JSON template
            prompt = f"""
        Generate a 100% ATS-friendly resume data optimized for this exact job description below. Follow these instructions strictly to avoid hallucination:
        - You must not hallucinate.

        - Extract all details (e.g., experience, skills, education, certifications) from the provided resume text: 
          ```
          {resume_text}
          ```
        - Optimize the resume to match the job description: 
          ```
          {job_description}
          ```
        
        - Get more projects, other fullPositions, education etc from this data to enrich resume: 
          ```
          {user_data}
          ```
        - Reword experience descriptions to incoporate all relevant keywords from job description.                    
        - Title field must match the job title in job description
        - All the fields here are important to render the resume. So we must not miss any of them in the output.
        - Structure the output this JSON format:
          ```
          {{
            "title": "Backend Developer & API Specialist",
            "education": [
                {{
                "course": "M.S. in Computer Science, GPA - 3.91",
                "institution": "Stanford University",
                "location": "Palo Alto, California, USA",
                "start_date": "September 2018",
                "end_date": "June 2020"
                }}
            ],
            "experience": [
                {{
                "title": "Senior Software Engineer",
                "company": "Cloudflare, Inc.",
                "location": "San Francisco, California, USA",
                "start_date": "January 2023",
                "end_date": "Present",
                "description": [
                    "Led the redesign of the edge computing platform, resulting in a 70% reduction in cold start latency and 40% improvement in resource utilization across 250+ global data centers.",
                    "Architected and implemented a distributed tracing system using OpenTelemetry, enabling engineers to troubleshoot complex performance issues 5x faster.",
                    "Optimized data ingestion pipeline handling 30TB daily, reducing processing time by 65% and cutting cloud infrastructure costs by $450K annually.",
                    "Mentored 8 junior engineers through technical development plans, with 3 successfully advancing to mid-level positions within 12 months."
                ]
                }}
            ],
            "skills": [
                {{
                "title": "Programming Languages",
                "elements": ["Rust", "Go", "TypeScript", "Python", "C++"]
                }},
                {{
                "title": "Cloud & Infrastructure",
                "elements": ["AWS", "Kubernetes", "Terraform", "Docker", "Istio"]
                }},
                {{
                "title": "Frameworks & Libraries",
                "elements": ["React", "Next.js", "gRPC", "GraphQL", "PyTorch", "TensorFlow", "Spark"]
                }},
                {{
                "title": "Data & Analytics",
                "elements": ["PostgreSQL", "Elasticsearch", "Kafka", "Prometheus", "Grafana"]
                }},
                {{
                "title": "Tools & Practices",
                "elements": ["Distributed Systems", "Microservices", "CI/CD", "TDD", "Performance Optimization", "System Design"]
                }}
            ],
            "projects": [
                {{
                "title": "Distributed Tracing Framework",
                "description": "Developed an open-source distributed tracing framework that combines sampling techniques with intelligent context propagation, reducing overhead by 75% while maintaining 99% trace fidelity. The project has been adopted by 12 companies and has 800+ GitHub stars.",
                "link": "https://github.com/example/tracing-framework"
                }}
            ]
            }}
          ```
        - Enhance the resume by incorporating relevant keywords from the job description (e.g., "customer support," "communication skills," "handle pressure," "interpersonal skills," "client education") into the skills and experience sections where applicable.
        - Do not invent new experiences, certifications, or details—use only the information provided in the resume text.
        - Return the enhanced resume data as a JSON string matching the exact structure of the template above.
        - Calculate the ATS match score and include it as matchScore.
        - If you do not find any detail is better to leave empty than N/A.
        - Add as many expriences, projects,
        Provide the output as a valid JSON string without additional text or comments.
        """
            client = OpenAI(
                api_key=self.api_token,
            )

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are the best in creating 100% ATS friendly resumes. You understand how ATS systems works and the keywords any resume needs from the job description to standout.",
                    },
                     {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                temperature= 0.4,
            )
            result= chat_completion.choices[0].message.content
            try:
                optimized_data = json.loads(result)
                
              
                return optimized_data

            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    optimized_data_str = json_match.group(0)
                    try:
                        optimized_data = json.loads(optimized_data_str)
                        
                        
                        return optimized_data
                    except json.JSONDecodeError:
                        raise ValueError("Extracted content is not valid JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
        except Exception as e:
                        raise ValueError(f"Error generatiin ${e}")
    
    def optimize_resume_for_ats(self, resume_text, job_description: str) -> Dict[str, Any]:
        """
        Optimize resume data for ATS based on job description using HuggingFace API
        """
        try:
            prompt = f"""
                    Generate a 100% ATS-friendly resume data optimized for the job description below. Follow these instructions strictly to avoid hallucination:

                    - Extract all details (e.g., experience, skills, education, certifications) from the provided resume text: 
                    ```
                    {resume_text}
                    ```
                    - Optimize the resume to match the job description: 
                    ```
                    {job_description}
                    ```
                    - Reword experience descriptions to incorporate all relevant keywords from job description.
                    - Title should match the job title in job description
                    - All the fields here are important to render the resume. So we must not miss any of them in the output.
                    - Structure the output in this JSON format:
                    {{

                        "name": "Ekekenta Odonyenfe Clinton",
                        "title": "Backend Developer & API Specialist",
                        "contact": {{
                            "email": "zionekekenta@gmail.com",
                            "phone": "",
                            "location": "",
                            "github": "http://github.com/icode247",
                            "website": "https://my-resume-icode247.vercel.app/"
                        }},
                        "summary": "",
                        "skills": {{
                            "languages": ["JavaScript", "TypeScript", "Python", "Hausa"],
                            "frameworks": ["Express.js", "NestJS", "Strapi", "Next.js"],
                            "tools": [
                                "Node.js",
                                "REST APIs",
                                "GraphQL",
                                "Postman",
                                "Docker",
                                "Redis",
                                "AWS",
                                "CircleCI",
                                "Git",
                                "PostgreSQL",
                                "MongoDB"
                            ]
                        }},
                        "relevantSkills": [
                            "Customer Support",
                            "Communication Skills",
                            "Problem Solving",
                            "Interpersonal Skills",
                            "Client Education",
                            "Handle Pressure"
                        ],
                        "experience": [
                            {{
                                "title": "Backend Developer & API Specialist (Freelance)",
                                "company": "(Remote)",
                                "period": "January 2023 – Present",
                                "description": [
                                    "Developed a YouTube clone using Strapi and Node.js, ensuring excellent customer support through real-time chat functionality and seamless user experience.",
                                    "Created and optimized REST APIs with Express.js, enhancing performance and reliability to meet client needs under pressure.",
                                    "Built multi-language applications with Strapi and Next.js, showcasing strong interpersonal skills by collaborating with diverse teams.",
                                    "Improved backend efficiency by 25% through API caching and load balancing, demonstrating ability to work independently and solve problems."
                                ]
                            }}
                        ],
                        "education": [
                            {{
                                "degree": "Higher National Diploma (HND) - Computer Science",
                                "institution": "",
                                "year": "September 2023"
                            }}
                        ],
                        "certifications": [
                            "Awarded Writer of the Month by Medusa.js for exceptional backend development content"
                        ],
                        "matchScore": 85
                    }}

                    - Every object, attribute, and key in the JSON output structure is important and should be there.
                    - Enhance the resume by incorporating relevant keywords from the job description (e.g., "customer support," "communication skills," "handle pressure," "interpersonal skills," "client education") into the skills and experience sections where applicable.
                    - Do not invent new experiences, certifications, or details—use only the information provided in the resume text.
                    - Return the enhanced resume data as a JSON string matching the exact structure of the template above.
                    - Calculate the ATS match score and include it as matchScore.
                    Provide the output as a valid JSON string without additional text or comments.
                    """
            
            client = OpenAI(
                api_key=self.api_token,
            )

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are the best in creating 100% ATS friendly resumes. You understand how ATS systems works and the keywords any resume needs from the job description to standout.",
                    },
                     {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                temperature= 0.7,
            )
            result= chat_completion.choices[0].message.content
            try:
                optimized_data = json.loads(result)
                
                
                return optimized_data

            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    optimized_data_str = json_match.group(0)
                    try:
                        optimized_data = json.loads(optimized_data_str)
                        
                        return optimized_data
                    except json.JSONDecodeError:
                        raise ValueError("Extracted content is not valid JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
        except Exception as e:
                        raise ValueError(f"Error generatiin ${e}")
   
    def process_resume(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """
        Process a resume text and optimize it for ATS based on a job description
        """
        # Optimize resume for ATS
        optimized_data = self.optimize_resume_for_ats(resume_text, job_description)
        
        return optimized_data

    def process_resume_pdf(self, resume_text: str, job_description: str, user_data: Any) -> Dict[str, Any]:
        """
        Process a resume text and optimize it for ATS based on a job description
        """
        # Optimize resume for ATS
        optimized_data = self.optimize_resume_for_ats_pdf(resume_text, job_description, user_data)
        
        return optimized_data

