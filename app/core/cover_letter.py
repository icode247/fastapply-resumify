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
                        "content": "You are an expert career coach who writes compelling, personalized, and professional cover letters that help candidates stand out."
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
        Generate a highly personalized and professional cover letter in JSON format based on the following information:
        
        APPLICANT INFORMATION:
        - Full Name: {letter_data.get('fullName', '')}
        - Tone: {tone}
        
        JOB DESCRIPTION TO ANALYZE:
        ```
        {job_description}
        ```
        
        {work_experience}
        
        {skills_section}
        {education_section}
        
        INSTRUCTIONS:
        1. ANALYZE the job description to extract:
        - Company name
        - Job title/position
        - Key requirements and responsibilities
        - Required skills and technologies
        
        2. CREATE a compelling, personalized cover letter that:
        - Uses SPECIFIC examples from the candidate's actual work experience
        - Connects their past roles and companies to the job requirements
        - Mentions relevant skills that match the job description
        - Shows how their progression (internships to full-time) aligns with the role
        - Addresses the specific company and position from the job description
        
        3. STRUCTURE:
        - Date: {current_date}
        - Salutation: "Dear Hiring Manager,"
        - Opening: Strong introduction mentioning the specific position and company from job description
        - Body Paragraph 1: Highlight most relevant work experience with specific examples
        - Body Paragraph 2: Connect additional experience/skills to the job requirements
        - Closing: Express enthusiasm and request interview
        - Signature: Professional closing
        
        Return the output as a valid JSON string with this exact structure:
        {{
        "header": "{current_date}",
        "salutation": "Dear Hiring Manager,",
        "introductionParagraph": "Strong opening paragraph mentioning the specific position and company extracted from job description",
        "bodyParagraphs": [
            "First body paragraph highlighting most relevant experience from their actual work history",
            "Second body paragraph connecting their skills and experience to the specific job requirements"
        ],
        "closingParagraph": "Professional closing expressing enthusiasm for the specific role and company",
        "signature": "Sincerely,\\n\\n{letter_data.get('fullName', '')}",
        "fullLetter": "Complete formatted cover letter combining all sections"
        }}
        
        IMPORTANT: 
        - Extract the EXACT company name and job title from the job description
        - Use REAL company names from their experience (like {', '.join([pos.get('company', '') for pos in letter_data.get('fullPositions', [])[:3]])})
        - Be specific about what they accomplished at each role
        - Match their skills to the job requirements
        - Keep it {tone.lower()} in tone
        - Keep it focused and concise (300-400 words total)
        - Don't make up experience they don't have

        FOLLOW THESE RULES
        SHOULD

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


        