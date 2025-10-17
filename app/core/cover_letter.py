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
        Generate a 100% HUMAN-SOUNDING, 2025 ATS-friendly cover letter that will pass ALL AI detection tools. This MUST sound like the candidate wrote it themselves.

        ANTI-AI DETECTION REQUIREMENTS (CRITICAL):
        - Write like a real person telling their story - natural, varied, authentic
        - Use contractions occasionally (I'm, I've, they're) to sound human
        - Vary sentence length dramatically (some 5 words, some 20+ words)
        - Show personality and genuine enthusiasm without sounding robotic
        - Use specific numbers, company names, and concrete examples
        - Write how people actually talk, not how AI writes
        - No formulaic openings like "I am writing to express my interest"
        - Start strong with something attention-grabbing and human
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

        INSTRUCTIONS:
        1. ANALYZE the job description to extract:
        - Company name (use the EXACT name)
        - Job title/position (use the EXACT title)
        - Key requirements and must-have skills
        - Company culture indicators

        2. CREATE a compelling cover letter that:
        - Opens with something memorable and human (NOT "I am writing to...")
        - Uses SPECIFIC examples from their actual work experience with real company names
        - Connects past achievements to job requirements naturally
        - Shows enthusiasm for THIS specific company and role
        - Mentions 2-3 concrete accomplishments with numbers
        - Demonstrates understanding of the role's challenges
        
        3. STRUCTURE (250-350 words TOTAL - keep it concise):
        - Date: {current_date}
        - Salutation: "Dear Hiring Manager," (or use hiring manager name if found in job description)
        - Opening (2-3 sentences): Hook them immediately - why you're excited about THIS role at THIS company
        - Body Paragraph 1 (3-4 sentences): Most relevant achievement with specific numbers and impact
        - Body Paragraph 2 (3-4 sentences): Another achievement that connects to their needs
        - Closing (2-3 sentences): Forward-looking statement about contribution + call to action
        - Signature: "Sincerely," or "Best regards," then name
        
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
        
        CRITICAL REQUIREMENTS:
        - Extract EXACT company name and job title from job description - use them multiple times
        - Reference their ACTUAL companies: {', '.join([pos.get('company', '') for pos in letter_data.get('fullPositions', [])[:3]])}
        - Include specific numbers and metrics from their experience
        - Write in a way that passes AI detection as 100% human
        - Keep total length 250-350 words (recruiters are busy!)
        - Use ONLY verified experience - NO fabrication
        - Sound genuinely excited about the opportunity
        - End with confidence, not desperation

        OPENING EXAMPLES (use similar natural style):
        ❌ BAD (robotic): "I am writing to express my interest in the Software Engineer position..."
        ✓ GOOD (human): "When I saw [Company]'s opening for a [Job Title], I knew I had to apply. Over the past [X] years at [Their Company], I've..."

        ❌ BAD (generic): "I believe I would be a great fit for this role..."
        ✓ GOOD (specific): "I've spent the last two years building scalable APIs that handle 10M+ requests daily. That's exactly what [Company] needs..."

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


        