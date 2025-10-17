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
    
    def __init__(self, api_token=None):
        # Fix: Use consistent attribute naming and handle both parameter and environment variable
        self.api_key = api_token or os.environ.get("OPENAI_API_KEY", "")
        self.logger = logging.getLogger(__name__)
        # Validate API key
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Provide it as parameter or set OPENAI_API_KEY environment variable.")
        
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
        Optimize resume data for ATS based on job description using OpenAI API
        """
        try:
            # Solution 1: Escape all curly braces in the JSON template
            prompt = f"""
        Generate a COMPLETE, 100% ATS-friendly resume for 2025 that reads naturally and authentically human. This resume MUST pass AI detection tools and feel completely human-written. Follow these critical instructions:

        ANTI-AI DETECTION REQUIREMENTS (2025):
        - Write in a natural, conversational professional tone with varied sentence structures
        - Use authentic human phrasing - avoid robotic patterns like "leveraged", "spearheaded" repeatedly
        - Include specific, concrete details and numbers that feel real and contextual
        - Vary bullet point lengths and structures naturally (some short, some detailed)
        - Use natural transitions and flow - not formulaic templates
        - Add personality through word choice while maintaining professionalism
        - NO generic corporate buzzwords unless genuinely necessary
        - Write like a real person describing their actual work experience

        FORBIDDEN WORDS (NEVER USE THESE - they sound AI-generated):
        can, may, just, that, very, really, literally, actually, certainly, probably, basically, could, maybe, delve, embark, enlightening, esteemed, shed light, craft, crafting, imagine, realm, game-changer, unlock, discover, skyrocket, abyss, not alone, in a world where, revolutionize, disruptive, utilize, utilizing, dive deep, tapestry, illuminate, unveil, pivotal, intricate, elucidate, hence, furthermore, realm, however, harness, exciting, groundbreaking, cutting-edge, remarkable, it remains to be seen, glimpse into, navigating, landscape, stark, testament, in summary, in conclusion, moreover, boost, skyrocketing, opened up, powerful, inquiries, ever-evolving, dedicated, passionate, results-driven, leverage, solid foundation

        SOURCE DATA - MUST NOT HALLUCINATE:
        - Extract ALL details from the provided resume text:
          ```
          {resume_text}
          ```
        - Optimize to match this job description (use its keywords naturally):
          ```
          {job_description}
          ```
        - Enrich with additional verified information from user data:
          ```
          {user_data}
          ```

        PROFESSIONAL SUMMARY REQUIREMENTS:
        - Generate a COMPLETE professional summary (3-4 sentences, 70-90 words)
        - MUST include these 4 elements in order:
          1. Job title + years of experience + what you do/achieve
          2. Core expertise and specializations
          3. Tools/technologies + quantifiable results/impact
          4. Soft skills + additional capabilities (leadership, budgets, teams, etc.)
        - Make it 100% ATS-optimized with keywords from job description
        - Write like a real person would describe themselves - direct and straightforward
        - Avoid flowery language - be direct and confident
        - NEVER use the forbidden words listed above

        SUMMARY FORMAT EXAMPLE (FOLLOW THIS STRUCTURE EXACTLY):
        "Digital Marketing Manager with 7 years of experience developing and executing data-driven marketing campaigns that increase brand awareness and drive revenue growth. Proven expertise in SEO, SEM, content marketing, and social media strategy. Skilled in Google Analytics, HubSpot, and Salesforce with a track record of improving conversion rates by 45% and reducing customer acquisition costs by 30%. Strong analytical and leadership abilities with experience managing cross-functional teams and million-dollar budgets."

        Notice the 4-part structure:
        1. Title + years + what you accomplish
        2. Core expertise areas
        3. Tools + quantifiable impact/results
        4. Soft skills + management/leadership experience

        CONTENT OPTIMIZATION:
        - Reword experience descriptions with job description keywords (naturally integrated)
        - Title field MUST match the job title in job description exactly
        - Every field in the JSON is critical - include ALL of them
        - NO truncation of any content - provide COMPLETE descriptions

        EXPERIENCE SECTION FORMATTING (CRITICAL):
        - Include ALL work experiences from the source data - DO NOT omit any
        - Each experience MUST have 4-6 bullet points (not just 1-2)
        - Start each bullet with strong action verbs (Built, Created, Designed, Improved, Reduced, Increased, Led, Managed, Developed, Analyzed, Led, Conducted, etc.)
        - Include quantifiable results in bullets (percentages, dollar amounts, time saved, number of users, etc.)
        - Format: "Action verb + what you did + quantifiable result"
        - Make bullets achievement-focused, not just task lists
        - Vary bullet length - some short (10-15 words), some detailed (20-30 words)
        - NO generic statements like "Responsible for" or "Worked on"

        EXPERIENCE BULLET EXAMPLES (follow this style):
        ✓ "Developed comprehensive digital marketing strategies that increased organic website traffic by 125% and generated 2,500+ qualified leads annually"
        ✓ "Managed annual marketing budget of $800,000 and optimized spend allocation across channels including paid search, social media, and email marketing"
        ✓ "Led team of 5 marketing specialists and coordinated with sales, product, and design teams to ensure alignment on campaign objectives"
        ✓ "Conducted A/B testing on landing pages and email campaigns, resulting in 35% improvement in conversion rates and 28% increase in click-through rates"

        Notice: Action verb starts, specific metrics, no fluff, concrete achievements.

        Structure the output in this JSON format:
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

        FINAL OUTPUT REQUIREMENTS:
        - Incorporate job description keywords NATURALLY throughout (e.g., specific technologies, methodologies, soft skills)
        - Use ONLY verified information from resume text and user data - NO fabrication
        - Return COMPLETE JSON with all fields filled - no truncation anywhere
        - Calculate realistic ATS match score (60-95%) and include as matchScore
        - Leave fields empty rather than using "N/A" if no information exists
        - Include ALL experiences from source data (if source has 3 jobs, output must have 3 jobs)
        - Include ALL education entries from source data
        - Include ALL projects from source data
        - Each experience MUST have 4-6 achievement-focused bullet points with metrics
        - Make every sentence sound authentically human - vary structure and tone
        - Ensure the output would pass GPTZero, Originality.ai, and other AI detectors as human-written

        OUTPUT FORMAT: Return ONLY valid JSON matching the template structure above. No markdown, no comments, no additional text.
        """
            client = OpenAI(
                api_key=self.api_key,  # Fix: Use self.api_key instead of self.api_key
            )

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert resume writer specializing in 2025 ATS-optimized resumes that are completely undetectable as AI-generated. Your resumes:
- Pass ALL AI detection tools (GPTZero, Originality.ai, etc.) as 100% human-written
- Are fully optimized for 2025 ATS systems with strategic keyword placement
- Sound authentically human with natural language variations and personality
- Include complete, detailed content with NO truncation
- Use varied sentence structures and avoid repetitive AI patterns
- Blend professional expertise with genuine human expression
- Never use generic templates or formulaic corporate jargon unless contextually appropriate
- NEVER use flowery, overly descriptive, or "purple prose" language
- Write brief, punchy, direct statements - like how real people talk
- Avoid the forbidden words list provided in the prompt
- Summaries must follow the 4-part structure: years/title, expertise, tools/results, soft skills
Your goal: Create resumes that hiring managers believe were written by the candidate themselves.""",
                    },
                     {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                temperature=0.7,
            )
            result = chat_completion.choices[0].message.content
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
            raise ValueError(f"Error generating resume: {e}")
    
    def optimize_resume_for_ats(self, resume_text, job_description: str) -> Dict[str, Any]:
        """
        Optimize resume data for ATS based on job description using OpenAI API
        """
        try:
            prompt = f"""
                    Generate a COMPLETE, 100% ATS-friendly resume for 2025 that reads naturally and authentically human. This resume MUST pass AI detection tools and feel completely human-written.

                    ANTI-AI DETECTION REQUIREMENTS (2025):
                    - Write in a natural, conversational professional tone with varied sentence structures
                    - Use authentic human phrasing - avoid robotic patterns like "leveraged", "spearheaded" repeatedly
                    - Include specific, concrete details and numbers that feel real and contextual
                    - Vary bullet point lengths and structures naturally (some short, some detailed)
                    - Use natural transitions and flow - not formulaic templates
                    - Add personality through word choice while maintaining professionalism
                    - NO generic corporate buzzwords unless genuinely necessary
                    - Write like a real person describing their actual work experience

                    FORBIDDEN WORDS (NEVER USE THESE - they sound AI-generated):
                    can, may, just, that, very, really, literally, actually, certainly, probably, basically, could, maybe, delve, embark, enlightening, esteemed, shed light, craft, crafting, imagine, realm, game-changer, unlock, discover, skyrocket, abyss, not alone, in a world where, revolutionize, disruptive, utilize, utilizing, dive deep, tapestry, illuminate, unveil, pivotal, intricate, elucidate, hence, furthermore, realm, however, harness, exciting, groundbreaking, cutting-edge, remarkable, it remains to be seen, glimpse into, navigating, landscape, stark, testament, in summary, in conclusion, moreover, boost, skyrocketing, opened up, powerful, inquiries, ever-evolving, dedicated, passionate, results-driven, leverage, solid foundation

                    SOURCE DATA - MUST NOT HALLUCINATE:
                    - Extract ALL details from the provided resume text:
                    ```
                    {resume_text}
                    ```
                    - Optimize to match this job description (use its keywords naturally):
                    ```
                    {job_description}
                    ```

                    PROFESSIONAL SUMMARY REQUIREMENTS:
                    - Generate a COMPLETE professional summary (3-4 sentences, 70-90 words)
                    - MUST include these 4 elements in order:
                      1. Job title + years of experience + what you do/achieve
                      2. Core expertise and specializations
                      3. Tools/technologies + quantifiable results/impact
                      4. Soft skills + additional capabilities (leadership, budgets, teams, etc.)
                    - Make it 100% ATS-optimized with keywords from job description
                    - Write like a real person would describe themselves - direct and straightforward
                    - Avoid flowery language - be direct and confident
                    - NEVER use the forbidden words listed above

                    SUMMARY FORMAT EXAMPLE (FOLLOW THIS STRUCTURE EXACTLY):
                    "Digital Marketing Manager with 7 years of experience developing and executing data-driven marketing campaigns that increase brand awareness and drive revenue growth. Proven expertise in SEO, SEM, content marketing, and social media strategy. Skilled in Google Analytics, HubSpot, and Salesforce with a track record of improving conversion rates by 45% and reducing customer acquisition costs by 30%. Strong analytical and leadership abilities with experience managing cross-functional teams and million-dollar budgets."

                    Notice the 4-part structure:
                    1. Title + years + what you accomplish
                    2. Core expertise areas
                    3. Tools + quantifiable impact/results
                    4. Soft skills + management/leadership experience

                    CONTENT OPTIMIZATION:
                    - Reword experience descriptions with job description keywords (naturally integrated)
                    - Title MUST match the job title in job description exactly
                    - Every field in the JSON is critical - include ALL of them
                    - NO truncation of any content - provide COMPLETE descriptions

                    EXPERIENCE SECTION FORMATTING (CRITICAL):
                    - Include ALL work experiences from the source data - DO NOT omit any
                    - Each experience MUST have 4-6 bullet points (not just 1-2)
                    - Start each bullet with strong action verbs (Built, Created, Designed, Improved, Reduced, Increased, Led, Managed, Developed, Analyzed, Conducted, etc.)
                    - Include quantifiable results in bullets (percentages, dollar amounts, time saved, number of users, etc.)
                    - Format: "Action verb + what you did + quantifiable result"
                    - Make bullets achievement-focused, not just task lists
                    - Vary bullet length - some short (10-15 words), some detailed (20-30 words)
                    - NO generic statements like "Responsible for" or "Worked on"

                    EXPERIENCE BULLET EXAMPLES (follow this style):
                    ✓ "Developed comprehensive digital marketing strategies that increased organic website traffic by 125% and generated 2,500+ qualified leads annually"
                    ✓ "Managed annual marketing budget of $800,000 and optimized spend allocation across channels including paid search, social media, and email marketing"
                    ✓ "Led team of 5 marketing specialists and coordinated with sales, product, and design teams to ensure alignment on campaign objectives"
                    ✓ "Conducted A/B testing on landing pages and email campaigns, resulting in 35% improvement in conversion rates and 28% increase in click-through rates"

                    Notice: Action verb starts, specific metrics, no fluff, concrete achievements.

                    Structure the output in this JSON format:
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
                        "summary": "GENERATE THE 4-PART SUMMARY HERE following the exact structure shown above",
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

                    FINAL OUTPUT REQUIREMENTS:
                    - Every object, attribute, and key in the JSON output structure is REQUIRED
                    - THE "summary" FIELD IS MANDATORY - Generate the full 4-part ATS summary as described above
                    - Incorporate job description keywords NATURALLY throughout the resume
                    - Use ONLY verified information from resume text - NO fabrication
                    - Return COMPLETE JSON with all fields filled - no truncation anywhere
                    - Calculate realistic ATS match score (60-95%) and include as matchScore
                    - Include ALL experiences from source data (if source has 3 jobs, output must have 3 jobs)
                    - Include ALL education entries from source data
                    - Include ALL projects from source data
                    - Each experience MUST have 4-6 achievement-focused bullet points with metrics
                    - Make every sentence sound authentically human - vary structure and tone
                    - Ensure the output would pass GPTZero, Originality.ai, and other AI detectors as human-written

                    OUTPUT FORMAT: Return ONLY valid JSON matching the template structure above. No markdown, no comments, no additional text.
                    """
            
            client = OpenAI(
                api_key=self.api_key,
            )

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert resume writer specializing in 2025 ATS-optimized resumes that are completely undetectable as AI-generated. Your resumes:
- Pass ALL AI detection tools (GPTZero, Originality.ai, etc.) as 100% human-written
- Are fully optimized for 2025 ATS systems with strategic keyword placement
- Sound authentically human with natural language variations and personality
- Include complete, detailed content with NO truncation
- Use varied sentence structures and avoid repetitive AI patterns
- Blend professional expertise with genuine human expression
- Never use generic templates or formulaic corporate jargon unless contextually appropriate
- NEVER use flowery, overly descriptive, or "purple prose" language
- Write brief, punchy, direct statements - like how real people talk
- Avoid the forbidden words list provided in the prompt
- Summaries must follow the 4-part structure: years/title, expertise, tools/results, soft skills
Your goal: Create resumes that hiring managers believe were written by the candidate themselves.""",
                    },
                     {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                temperature=0.8,
            )
            result = chat_completion.choices[0].message.content
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
            raise ValueError(f"Error generating resume: {e}")
   
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