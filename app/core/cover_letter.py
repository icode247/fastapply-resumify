# app/core/cover_letter.py
"""
Cover Letter Generator functionality.
"""
import io
import logging
import json
import re
from typing import Dict, Any
from openai import OpenAI
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class CoverLetterGenerator:
    """
    Generate professional cover letters based on input parameters.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.logger = logging.getLogger(__name__)
        
    def generate_cover_letter(self, letter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a professional cover letter based on input parameters
        
        Args:
            letter_data: Dictionary containing cover letter parameters
                fullName: Applicant's full name (required)
                jobDescription: Full job description text (required)
                skills: Relevant skills for the position (optional)
                education: Education background (optional)
                fullPositions: Array of work experience objects (optional but recommended)
                tone: Tone of the letter (Professional, Enthusiastic, etc.) (optional)
                
        Returns:
            Dictionary containing the generated cover letter
        """
        try:
            # Validate required fields
            required_fields = ['fullName', 'jobDescription']
            missing_fields = [field for field in required_fields if not letter_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
            # Create the prompt for GPT
            prompt = self._create_cover_letter_prompt(letter_data)
            
            # Call OpenAI API to generate the cover letter
            client = OpenAI(api_key=self.api_key)

            self.logger.info(f"Generating cover letter for {letter_data.get('fullName')} based on job description")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert career coach who writes compelling, authentic cover letters that sound 100% human-written. Your cover letters:
- Pass ALL AI detection tools (GPTZero, Originality.ai, etc.) as 100% human-written
- Sound like the candidate wrote it themselves - natural, confident, direct
- Use varied sentence structures and authentic human phrasing
- Show genuine enthusiasm without sounding desperate or robotic
- Connect real experiences to job requirements in a natural way
- Avoid all AI-generated phrases and clichés
- Write brief, punchy, impactful sentences
- Focus on specific achievements and concrete examples
- Sound professional but conversational, not stiff or formulaic
Your goal: Create cover letters that hiring managers believe the candidate wrote themselves."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                temperature=0.85,
                response_format={"type": "json_object"},
            )
            
            result = chat_completion.choices[0].message.content
            
            try:
                cover_letter = json.loads(result)
                cover_letter["success"] = True
                return cover_letter
                
            except json.JSONDecodeError:
                # Try to extract JSON if the response isn't properly formatted
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    cover_letter_str = json_match.group(0)
                    try:
                        cover_letter = json.loads(cover_letter_str)
                        cover_letter["success"] = True
                        return cover_letter
                    except json.JSONDecodeError:
                        raise ValueError("Failed to parse response as JSON")
                else:
                    raise ValueError("No valid JSON found in the API response")
                    
        except Exception as e:
            self.logger.error(f"Error generating cover letter: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }   
        
    def _create_cover_letter_prompt(self, letter_data: Dict[str, Any]) -> str:
        """
        Create a prompt for the AI to generate a cover letter
        
        Args:
            letter_data: Dictionary containing cover letter parameters
            
        Returns:
            String containing the prompt
        """
        # Get current date for the letter
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Set tone based on input or default to Professional
        tone = letter_data.get('tone', 'Professional')
        
        # Process work experience data
        work_experience = ""
        if letter_data.get('fullPositions'):
            work_experience = "CANDIDATE'S ACTUAL WORK EXPERIENCE:\n"
            for position in letter_data.get('fullPositions', []):
                work_experience += f"- {position.get('role', 'N/A')} at {position.get('company', 'N/A')} ({position.get('type', 'N/A')}) - {position.get('duration', 'N/A')} in {position.get('location', 'N/A')}\n"
        
        # Process skills and education if provided
        skills_section = f"SKILLS: {letter_data.get('skills', '')}" if letter_data.get('skills') else ""
        education_section = f"EDUCATION: {letter_data.get('education', '')}" if letter_data.get('education') else ""
        
        # Get job description
        job_description = letter_data.get('jobDescription', '')
        
        prompt = f"""
        Generate a 100% HUMAN-SOUNDING, highly personalized cover letter that passes ALL AI detection tools and connects directly to the company's mission and culture.

        ANTI-AI DETECTION REQUIREMENTS (CRITICAL):
        - Write like a real person telling their story, natural and authentic
        - Use contractions occasionally (I'm, I've, they're) to sound human
        - Vary sentence length dramatically (some 5 words, some 20+ words)
        - Show personality and genuine enthusiasm without sounding robotic
        - Use specific numbers, company names, and concrete examples
        - Write how people talk, not how AI writes
        - NO formulaic openings like "I am writing to express my interest" or "When I came across"
        - Start with WHY the company excites you (their products, mission, engineering culture)
        - Sound confident but not arrogant, enthusiastic but not desperate

        APPLICANT INFORMATION:
        - Full Name: {letter_data.get('fullName', '')}
        - Desired Tone: {tone} (but keep it genuinely human)

        JOB DESCRIPTION TO ANALYZE:
        ```
        {job_description}
        ```

        {work_experience}

        {skills_section}
        {education_section}

        STEP 1 - DEEP ANALYSIS (Do this first, don't include in output):
        Extract from job description:
        - EXACT company name
        - EXACT job title
        - Company mission, products, or engineering culture clues
        - Key technical requirements
        - Scale indicators (users, requests, data volume)
        - Values they emphasize (collaboration, innovation, impact, etc.)

        STEP 2 - CRAFT THE COVER LETTER:
        
        OPENING PARAGRAPH (2-3 sentences):
        ✅ DO: Start with why THIS company specifically excites you
        - Reference their products, mission, scale, or engineering culture
        - Show you understand what makes them unique
        - Connect your passion to their values
        ❌ AVOID: Generic excitement, "I came across this role", template phrases
        
        EXAMPLES:
        ✓ "As a developer passionate about building scalable systems, I've admired how [Company] engineers design products that seamlessly serve billions of users. The [Job Title] role aligns perfectly with my drive to build solutions that perform at massive scale."
        ✓ "I've spent the last three years building distributed systems that handle millions of transactions daily. [Company]'s focus on [specific tech/mission] is exactly the kind of challenge I want to tackle next."
        
        BODY PARAGRAPHS (2 paragraphs, 3-4 sentences each):
        ✅ DO: Connect achievements to VALUE for the company
        - Lead with specific, quantified achievements
        - Explicitly state how this experience benefits THEM
        - Tie accomplishments to their scale, tech stack, or challenges
        - Use language like "I'm excited to bring this experience to..."
        ❌ AVOID: Just listing what you did without connecting to their needs
        
        EXAMPLE STRUCTURE:
        "At [Their Company], I led a team that built [specific system] supporting [X million] users. This reduced downtime by [X%] and increased deployment frequency, directly improving user satisfaction. This experience mirrors [Company]'s focus on [their value], and I'm excited to bring this background to enhance [their product/system]."
        
        CLOSING PARAGRAPH (2-3 sentences):
        ✅ DO: Reaffirm enthusiasm with confidence
        - Reference their mission or impact
        - Show excitement about contributing to their goals
        - End with forward momentum, not desperation
        ❌ AVOID: "I look forward to the possibility" or weak, vague statements
        
        EXAMPLES:
        ✓ "I'd be thrilled to bring my experience building scalable, user-focused systems to [Company]'s mission of [their mission], and I'm excited about contributing to projects that touch billions of lives."
        ✓ "I'm eager to apply my background in [tech] to help [Company] continue building products that [their impact]."
        
        OUTPUT STRUCTURE (250-350 words):
        - NO DATE (omit for modern applications)
        - Salutation: "Dear Hiring Manager," (or name if found)
        - Opening: Why THIS company excites you
        - Body 1: Achievement + value to company
        - Body 2: Achievement + connection to their needs  
        - Closing: Confident enthusiasm about their mission
        - Signature: "Sincerely," or "Best regards," then name
        
        Return valid JSON:
        {{
        "header": "",
        "salutation": "Dear Hiring Manager,",
        "introductionParagraph": "Opening showing specific excitement about THIS company's mission/products/culture",
        "bodyParagraphs": [
            "Achievement with numbers + how this benefits the company specifically",
            "Another achievement + direct connection to their technical challenges or scale"
        ],
        "closingParagraph": "Confident, enthusiastic statement about contributing to their mission or impact",
        "signature": "Sincerely,\\n\\n{letter_data.get('fullName', '')}",
        "fullLetter": "Complete formatted cover letter"
        }}
        
        CRITICAL REQUIREMENTS:
        - Use EXACT company name from job description
        - Reference their ACTUAL work experience: {', '.join([pos.get('company', '') for pos in letter_data.get('fullPositions', [])[:3]])}
        - Include specific numbers and metrics
        - Every achievement MUST connect to value for the company
        - Tailor to company culture/mission from job description
        - 250-350 words total
        - NO fabrication of experience
        - Pass AI detection as 100% human

        OPENING COMPARISON:
        ❌ "When I came across [Company]'s opening for [Job Title], I felt a rush of excitement."
        ✓ "As a developer passionate about building scalable systems, I've always admired how [Company] engineers design products that seamlessly serve billions of users."

        VALUE-FOCUSED LANGUAGE:
        ❌ "At Tech Solutions, I led the design of a distributed microservices system."
        ✓ "At Tech Solutions, I led the design of a distributed microservices system that supported millions of users. This experience mirrors [Company]'s focus on reliability and scalability in products like [their products], and I'm excited to bring this background to enhance [Company]'s infrastructure."

        CLOSING COMPARISON:
        ❌ "I look forward to the possibility of discussing how my background can support your team's goals."
        ✓ "I'd be thrilled to bring my experience building resilient systems to [Company]'s mission of [mission], and I'm excited to contribute to projects that touch billions of lives."

        WRITING RULES:
        SHOULD use clear, simple language
        SHOULD be spartan and informative
        SHOULD use short, impactful sentences
        SHOULD use active voice
        SHOULD focus on practical examples
        SHOULD use data and numbers

        AVOID em dashes, semicolons, markdown, asterisks
        AVOID constructions like "not just this, but also this"
        AVOID metaphors and clichés
        AVOID generalizations
        AVOID setup language like "in conclusion"
        AVOID unnecessary adjectives and adverbs
        AVOID these words: "can, may, just, that, very, really, literally, actually, certainly, probably, basically, could, maybe, delve, embark, enlightening, esteemed, shed light, craft, crafting, imagine, realm, game-changer, unlock, discover, skyrocket, abyss, not alone, in a world where, revolutionize, disruptive, utilize, utilizing, dive deep, tapestry, illuminate, unveil, pivotal, intricate, elucidate, hence, furthermore, realm, however, harness, exciting, groundbreaking, cutting-edge, remarkable, it remains to be seen, glimpse into, navigating, landscape, stark, testament, in summary, in conclusion, moreover, boost, skyrocketing, opened up, powerful, inquiries, ever-evolving"
        """
        
        return prompt

    def generate_cover_letter_pdf(self, letter_data: Dict[str, Any]) -> bytes:
        """
        Generate a PDF cover letter from the provided letter data
        
        Args:
            letter_data: Dictionary containing cover letter parameters
            
        Returns:
            bytes: The generated PDF content as bytes
        """
        try:
            # First generate the cover letter content
            cover_letter_result = self.generate_cover_letter(letter_data)
            
            if not cover_letter_result.get('success', False):
                raise ValueError(f"Failed to generate cover letter content: {cover_letter_result.get('error', 'Unknown error')}")
            
            # Extract the cover letter components
            header = cover_letter_result.get('header', '')
            salutation = cover_letter_result.get('salutation', '')
            intro_paragraph = cover_letter_result.get('introductionParagraph', '')
            body_paragraphs = cover_letter_result.get('bodyParagraphs', [])
            closing_paragraph = cover_letter_result.get('closingParagraph', '')
            signature = cover_letter_result.get('signature', '')
            
            # Create a BytesIO buffer to hold the PDF content
            buffer = io.BytesIO()
            
            # Generate the cover letter PDF
            self._generate_cover_letter_to_buffer(
                buffer, header, salutation, intro_paragraph, 
                body_paragraphs, closing_paragraph, signature
            )
            
            # Get the PDF content from the buffer
            buffer.seek(0)
            pdf_content = buffer.getvalue()
            
            return pdf_content
            
        except Exception as e:
            self.logger.error(f"Error generating cover letter PDF: {str(e)}")
            raise


    def _generate_cover_letter_to_buffer(self, buffer, header, salutation, intro_paragraph, 
                                   body_paragraphs, closing_paragraph, signature):
        """
        Generate a cover letter PDF and write it to a buffer
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
        from app.constants import GARAMOND_REGULAR, GARAMOND_SEMIBOLD
        from reportlab.lib.styles import ParagraphStyle

        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=1 * inch,
            leftMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch
        )
        
        # Define paragraph styles for cover letter
        header_style = ParagraphStyle(
            'HeaderStyle',
            fontName=GARAMOND_REGULAR,
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=24  # More space after date
        )
        
        salutation_style = ParagraphStyle(
            'SalutationStyle',
            fontName=GARAMOND_REGULAR,
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=12
        )
        
        body_style = ParagraphStyle(
            'BodyStyle',
            fontName=GARAMOND_REGULAR,
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14
        )
        
        signature_style = ParagraphStyle(
            'SignatureStyle',
            fontName=GARAMOND_REGULAR,
            fontSize=11,
            alignment=TA_LEFT,
            spaceAfter=6
        )
        
        # Build the document content
        story = []
        
        # Add simple date header (no contact info)
        if header:
            story.append(Paragraph(header, header_style))
        
        # Add salutation
        if salutation:
            story.append(Paragraph(salutation, salutation_style))
        
        # Add introduction paragraph
        if intro_paragraph:
            story.append(Paragraph(intro_paragraph, body_style))
        
        # Add body paragraphs
        for paragraph in body_paragraphs:
            if paragraph:
                story.append(Paragraph(paragraph, body_style))
        
        # Add closing paragraph
        if closing_paragraph:
            story.append(Paragraph(closing_paragraph, body_style))
        
        if signature:
            story.append(Spacer(1, 0.3 * inch))
            formatted_signature = signature.replace('\n', '<br/>') 
            signature_style = ParagraphStyle(
                name='Signature',
                leading=14,  
                spaceBefore=6
            )
            story.append(Paragraph(formatted_signature, signature_style))
        # Build the document
        doc.build(story)


        