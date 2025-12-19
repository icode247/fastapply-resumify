"""
AI-powered job matching service using OpenAI.
Analyzes job preferences, job information, and resume to determine fit.
"""
import os
import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)


class JobMatcherAI:
    """
    Production-ready AI job matcher that analyzes whether a candidate
    should apply for a job based on their preferences, resume, and job details.
    """
    
    def __init__(self):
        """Initialize the AI client."""
        self.useChatGPT = os.environ.get('USE_CHATGPT', 'false').lower() == 'true'

        if self.useChatGPT:
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required when USE_CHATGPT=true")
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4o-mini"
        else:
            hf_token = os.environ.get('HF_TOKEN')
            if not hf_token:
                raise ValueError("HF_TOKEN environment variable is required when USE_CHATGPT=false")
            self.client = InferenceClient(
                provider="novita",
                api_key=hf_token
            )
            self.model = "openai/gpt-oss-120b"
        
    def analyze_job_match(
        self,
        resume_text: str,
        job_information: Dict,
        job_preferences: Dict,
        apply_only_qualified: bool = True
    ) -> Dict:
        """
        Analyze if a candidate should apply for a job.

        Args:
            resume_text: The candidate's resume as plain text
            job_information: Dict containing job details (title, description, requirements, etc.)
            job_preferences: Dict containing candidate's preferences (location, salary, remote, language, industry, companyBlacklist, etc.)
            apply_only_qualified: If True, validate both preferences AND resume qualifications. If False, only validate preferences.

        Returns:
            Dict with:
                - shouldApply: bool
                - reason: str (max 20 words explaining mismatches)
                - matchScore: float (0-100)
                - mismatches: List[str] (specific items that don't match)
        """
        try:
            if not resume_text or not resume_text.strip():
                raise ValueError("Resume text cannot be empty")

            if not job_information:
                raise ValueError("Job information is required")

            prompt = self._build_analysis_prompt(
                resume_text=resume_text,
                job_information=job_information,
                job_preferences=job_preferences or {},
                apply_only_qualified=apply_only_qualified
            )

            extra_params = {}
            if self.useChatGPT:
                extra_params["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1000,
                **extra_params
            )

            content = response.choices[0].message.content

            if not self.useChatGPT:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > 0:
                    content = content[json_start:json_end]

            result = json.loads(content)

            return self._validate_and_format_response(result)
            
        except Exception as e:
            logger.error(f"Error in job match analysis: {str(e)}", exc_info=True)
            raise
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI."""
        return """You are a STRICT job matching AI that prevents candidates from wasting time on mismatched jobs. Your analysis must be rigorous and conservative, but ACCURATE.

🚨 CRITICAL INFORMATION EXTRACTION - YOU MUST DO THIS FIRST! 🚨
Before ANY analysis, you MUST extract missing job information from the job description. NEVER say a field is "not specified" or "unspecified" without first searching the description!

EXTRACTION RULES (MANDATORY):
1. **Job Type**: Look in title for "(PT)", "(FT)", "part-time", "full-time", "contract", "freelance"
   Example: "Customer Support Agent (PT)" → Part-Time
2. **Work Mode**: Look for "remote", "hybrid", "on-site", "in-office", "WFH", "work from home", "office", "in-person"
   Example: "open to remote candidates" → Remote
   Example: "in-office five days a week" → On-Site
3. **Location**: Look for city/country names, "nationwide", "US-based", "based in X"
   Example: "remote candidates nationwide" → United States
   Example: "based in San Francisco" → San Francisco
4. **Salary**: Look for "$X", "€X", "£X", "salary", "compensation", "pay", numbers with currency
   Example: "$50,000-$70,000" → Extract exact range
5. **Experience**: Look for "X+ years", "X years experience", "senior", "junior", "mid-level", "entry-level"
   Example: "2-3 years of experience" → 2-3 years
6. **Company**: Extract company name from anywhere in description
7. **Languages**: Look for "Spanish required", "bilingual", "fluent in", "must speak"

⚠️ WARNING: If you report a field as "not specified" or use it as a rejection reason, you have FAILED to extract information properly!

CRITICAL: Before making any decision, you MUST internally calculate years of experience by:
1. Identifying ALL positions that mention the required technology
2. Calculating years for EACH position (end_year - start_year)
3. SUMMING all the years together
4. Only then comparing to the requirement

You must respond with a JSON object containing:
1. "shouldApply": boolean - true ONLY if both preferences AND qualifications match
2. "reason": string - Concise explanation (MAX 20 words) speaking directly to the candidate (use "you"), focusing on the PRIMARY mismatch
3. "matchScore": number - Score 0-100 (be fair, realistic scores based on actual analysis)
4. "mismatches": array of strings - ALL specific mismatches found (speaking to the candidate using "you")

CRITICAL VALIDATION PROCESS (MUST FOLLOW IN ORDER):

STEP 1 - PREFERENCES VALIDATION (IMMEDIATE DISQUALIFICATION IF FAILED - Only check preferences that are specified):

🚨 CRITICAL RULE: Only validate fields that have actual values. If job info is missing and can't be extracted, SKIP that validation - DO NOT REJECT!

VALIDATION RULES (all require extraction first):
- Deal-breakers: If specified, ANY deal-breaker match = instant rejection
- Company blacklist: If specified AND company is known, check blacklist. If company unknown, SKIP this check.
- Language: ONLY reject if job explicitly requires languages you don't speak. If no language requirement found, SKIP.
- Industry: If you specified preferred industries AND job industry is known, validate match. If industry unknown, SKIP.
- Job Type: If you specified jobType preferences AND job type is known (from field or title), validate match. If type unknown after extraction, SKIP.
- Experience Level: If you specified experience preferences AND job level is known, validate match. If level unknown, SKIP.
- Remote Only: If remoteOnly=true AND work mode is known, validate must be remote. If work mode unknown after extraction, SKIP.
- Work Mode: If you specified workMode preferences AND job work mode is known, validate match. If mode unknown, SKIP.
- Location/City: If you specified location AND job location is known, validate match. If location unknown, SKIP.
- Salary: ONLY validate if salary is actually provided. If not provided, SKIP entirely.
- Positions: If you specified preferred positions, validate job title aligns (always available from title field).

REMEMBER: Missing information = SKIP validation, NOT automatic rejection!

STEP 2 - RESUME-JOB REQUIREMENTS MATCH (ONLY IF STEP 1 PASSES AND applyOnlyQualified=true):
- NOTE: Skip this step entirely if applyOnlyQualified=false. Only validate preferences in that case.
- Required skills: You MUST have ALL listed required skills
- Experience years: CAREFULLY calculate total years from ALL relevant positions. Add up years from each role that used the required technology. If job requires "5+ years Python" and resume shows "2019-Present" (6 years) + "2016-2019" (3 years) = 9 total years, then requirement IS MET. Do not reject based on miscalculation.
- Education level: If degree specified as required, you must have it
- Technical stack: Core technologies must match (Python job needs Python experience)
- Seniority level: Match entry-level roles with junior/entry-level candidates (0-2 years). Junior roles are entry-level. Mid-level (2-5 years) and senior roles (5+ years) must match appropriately

STRICTNESS RULES:
- If job requires "5+ years Python" and you have 3 years = REJECT (but if you have 5+ across multiple roles, APPROVE)
- If you require remote and job is onsite = REJECT
- If you prefer $150k+ and job offers $80k-100k = REJECT
- Missing even ONE critical required skill = REJECT
- Any deal-breaker present = REJECT
- When in doubt about experience calculation, add up ALL years carefully before rejecting

SCORING GUIDELINES (be fair but thorough):
- 90-100: Perfect match - all requirements met, all preferences aligned
- 80-89: Excellent match - all requirements met, minor preference mismatches
- 70-79: Good match - requirements met, some preference differences
- 60-69: Acceptable match - most requirements met, several issues
- Below 60: Not a good match - should NOT apply

Set shouldApply=false if matchScore < 70 OR if any critical mismatch exists.

Keep reason under 20 words, focusing on the PRIMARY blocking issue."""

    def _build_analysis_prompt(
        self,
        resume_text: str,
        job_information: Dict,
        job_preferences: Dict,
        apply_only_qualified: bool
    ) -> str:
        """Build the analysis prompt from inputs."""

        job_title = job_information.get('title', 'Not specified')
        job_description = job_information.get('description', 'Not specified')
        job_requirements = job_information.get('requirements', 'Not specified')
        job_location = job_information.get('location', 'Not specified')
        job_salary = job_information.get('salary', 'Not specified')
        job_type = job_information.get('type', 'Not specified')
        job_work_mode = job_information.get('work_mode', 'Not specified')
        experience_required = job_information.get('experience_required', 'Not specified')
        job_company = job_information.get('company', 'Not specified')
        job_languages = job_information.get('languages_required', [])
        job_industry = job_information.get('industry', 'Not specified')

        job_types = job_preferences.get('jobType', [])
        experience_levels = job_preferences.get('experience', [])
        salary_range = job_preferences.get('salary', [])
        min_salary = salary_range[0] if salary_range and len(salary_range) > 0 else None
        max_salary = salary_range[1] if salary_range and len(salary_range) > 1 else None
        city = job_preferences.get('city', None)
        positions = job_preferences.get('positions', [])
        remote_only = job_preferences.get('remoteOnly', False)
        work_modes = job_preferences.get('workMode', [])
        location = job_preferences.get('location', None)
        user_languages = job_preferences.get('language', [])
        preferred_industries = job_preferences.get('industry', [])
        company_blacklist = job_preferences.get('companyBlacklist', [])
        deal_breakers = job_preferences.get('deal_breakers', [])
        
        prompt = f"""STRICT JOB MATCH ANALYSIS - Follow validation steps in order:

🚨🚨🚨 CRITICAL WARNING 🚨🚨🚨
BEFORE YOU DO ANYTHING ELSE:
1. Check if fields ALREADY have values (not "Not specified") - USE THOSE VALUES!
2. For fields showing "Not specified → EXTRACT", search the Description/Requirements
3. NEVER claim a field is "not specified" or "unspecified" in your response without extraction!
4. Check the Job Title for type indicators like (PT), (FT), etc.

JOB INFORMATION:
- Title: {job_title}
- Company: {job_company if job_company != 'Not specified' else 'Not specified → EXTRACT from description'}
- Industry: {job_industry if job_industry != 'Not specified' else 'Not specified → EXTRACT/INFER from description/title'}
- Description: {job_description[:1000]}
- Requirements: {job_requirements[:1000]}
- Location: {job_location if job_location != 'Not specified' else 'Not specified → EXTRACT from description (city, country, or remote/hybrid/onsite)'}
- Salary: {job_salary if job_salary != 'Not specified' else 'Not specified → EXTRACT from description (look for $X, €X, salary, compensation, pay range)'}
- Type: {job_type if job_type != 'Not specified' else 'Not specified → EXTRACT from description (full-time, part-time, contract)'}
- Work Mode: {job_work_mode if job_work_mode != 'Not specified' else 'Not specified → EXTRACT from description (remote, hybrid, on-site, in-office)'}
- Experience Required: {experience_required if experience_required != 'Not specified' else 'Not specified → EXTRACT from description (X+ years, senior, junior, mid-level)'}
- Languages Required: {', '.join(job_languages) if job_languages else 'Not specified → EXTRACT from description (Spanish required, bilingual, fluent in, must speak)'}


CANDIDATE PREFERENCES (ALL OPTIONAL - Only validate if specified):
- Job Types: {', '.join(job_types) if job_types else 'Any'}
- Experience Levels: {', '.join(experience_levels) if experience_levels else 'Any'}
- Salary Range: {f'${min_salary:,} - ${max_salary:,}' if min_salary and max_salary else f'${min_salary:,}+' if min_salary else 'Not specified'}
- City: {city or 'Any'}
- Location/Country: {location or 'Any'}
- Positions: {', '.join(positions) if positions else 'Any'}
- Remote Only: {'Yes - MUST be remote' if remote_only else 'No'}
- Work Modes: {', '.join(work_modes) if work_modes else 'Any'}
- Languages You Speak: {', '.join(user_languages) if user_languages else 'Not specified'}
- Preferred Industries: {', '.join(preferred_industries) if preferred_industries else 'Any'}
- Company Blacklist: {', '.join(company_blacklist) if company_blacklist else 'None'}
- Deal Breakers: {', '.join(deal_breakers) if deal_breakers else 'None'}

APPLY ONLY QUALIFIED MODE: {"ENABLED - Check resume qualifications" if apply_only_qualified else "DISABLED - Only check preferences, skip resume validation"}

CANDIDATE RESUME {"(CHECK ONLY IF PREFERENCES MATCH AND applyOnlyQualified=true)" if apply_only_qualified else "(DO NOT CHECK - applyOnlyQualified=false)"}:
{resume_text[:3000] if apply_only_qualified else "[Resume check disabled - only validating preferences]"}

IMPORTANT EXPERIENCE CALCULATION EXAMPLE:
If the resume shows:
- "Senior Software Engineer at TechCorp (2019-Present)" using Python/Django
- "Software Engineer at StartupXYZ (2016-2019)" using Python/Flask

Then Python experience = (2025-2019) + (2019-2016) = 6 + 3 = 9 years total
NOT just 6 years from the current role!

VALIDATION STEPS:

🚨 STEP 0 - INFORMATION EXTRACTION (MANDATORY FIRST STEP!) 🚨
YOU MUST EXTRACT ALL MISSING INFORMATION BEFORE VALIDATING ANYTHING!

EXTRACTION PROCESS (DO NOT SKIP):
a) Check the Job Title first - look for:
   - "(PT)" or "part-time" → Job Type: Part-Time
   - "(FT)" or "full-time" → Job Type: Full-Time
   - "Contract", "Freelance" → Extract accordingly

b) Read through Description AND Requirements completely, searching for:
   
   📍 **Work Mode** - Search for these exact phrases:
      • "remote candidates", "work remotely", "remote position" → Remote
      • "hybrid", "flexible office" → Hybrid  
      • "in-office", "on-site", "in-person" → On-Site
      • Example: "This role is open to remote candidates nationwide" = Remote
   
   🌍 **Location** - Search for:
      • City names, country names
      • "nationwide", "US-based", "based in [city]"
      • Example: "remote candidates nationwide" = United States
      • Example: "based in San Francisco" = San Francisco, United States
   
   💰 **Salary** - Search for (but if not found, skip salary validation):
      • Dollar amounts: "$50,000", "$50k-$70k", "salary of $X"
      • "compensation", "pay range", "competitive salary"
      • NOTE: If no salary found, DO NOT list "salary not specified" as a mismatch!
   
   📅 **Experience** - Search for:
      • "X+ years", "X-Y years of experience"
      • "2-3 years of experience" = 2-3 years
   
   🏢 **Company** - Extract company name from any mention
   
   🗣️ **Languages** - Search for:
      • "Spanish required", "bilingual", "fluent in", "must speak"

c) CRITICAL: Use ONLY the extracted information for validations.
   • If you successfully extract a value, use it for validation
   • If you cannot find/extract a value, SKIP that validation entirely
   • DO NOT list missing/unknown information as a mismatch or rejection reason!

REAL EXAMPLE OF PROPER EXTRACTION:
Job Title: "Customer Support Agent (PT)"
Location Field: "Remote"
Work Mode Field: "" (empty)
Description: "This role is open to remote candidates nationwide. However, if you are based in the San Francisco Bay Area, our policy requires in-person work from our office five days per week."

CORRECT EXTRACTION:
✅ Type: Part-Time (from "(PT)" in title)
✅ Location: Remote, United States (field says "Remote" + description says "nationwide")
✅ Work Mode: Remote (description says "open to remote candidates")
✅ Experience: 2-3 years (if description says "2-3 years of experience")

WRONG EXTRACTION (DO NOT DO THIS):
❌ "job type is unspecified" - WRONG! Extract (PT) from title
❌ "work mode is not specified" - WRONG! Description clearly says remote
❌ "location is not specified" - WRONG! Field shows "Remote" and description says "nationwide"

BEFORE ANYTHING ELSE - If checking experience requirements:
a) List out EVERY job position that mentions the required technology
b) For EACH position, calculate: (end_year - start_year) or (2025 - start_year) if current
c) Add ALL those years together
d) Compare the SUM to the requirement

Example for this resume:
- Position 1: "Senior Software Engineer at TechCorp (2019-Present)" → 2025-2019 = 6 years Python
- Position 2: "Software Engineer at StartupXYZ (2016-2019)" → 2019-2016 = 3 years Python
- TOTAL Python experience = 6 + 3 = 9 years
- Required: 5+ years
- RESULT: 9 ≥ 5, requirement MET ✓

1. Using the EXTRACTED information from Step 0, validate your specified preferences:
   
   🔍 VALIDATION CHECKLIST - ONLY validate if information exists:
   
   ✓ Company blacklist (if you specified AND company is known)
      • If company known and blacklisted = REJECT
      • If company unknown = SKIP, continue
   
   ✓ Deal-breakers (if you specified AND deal-breaker is present)
      • If deal-breaker found = REJECT
      • If no deal-breaker = continue
   
   ✓ Language requirements (ONLY if job explicitly requires languages)
      • If job requires language you don't speak = REJECT
      • If no language requirement found in description = SKIP, continue
   
   ✓ Industry match (ONLY if you specified industries AND job industry is known)
      • If industry known and matches = PASS ✓
      • If industry known but doesn't match = REJECT
      • If industry unknown after extraction = SKIP, continue
   
   ✓ Job type (ONLY if you specified AND type is known from field/title)
      • You want Full-Time, job is Part-Time (PT) = REJECT
      • You want Full-Time, type unknown = SKIP, continue
   
   ✓ Remote/Work Mode (ONLY if you specified AND mode is known)
      • You want remote, job is Remote = PASS ✓
      • You want remote, job is On-Site = REJECT
      • You want remote, mode unknown = SKIP, continue
   
   ✓ Location (ONLY if you specified AND location is known)
      • You want US, job is US = PASS ✓
      • You want US, job is UK = REJECT
      • You want US, location unknown = SKIP, continue
   
   ✓ Salary (ONLY if job provides salary)
      • Salary provided and meets minimum = PASS ✓
      • Salary provided but below minimum = REJECT
      • No salary info = SKIP, continue
   
   ✓ Positions (validate if you specified preferred positions)
      • Job title should align with your positions

   🎯 KEY PRINCIPLE: Unknown/Missing info = SKIP validation, NOT rejection!

2. {"Only if Step 1 passes completely, validate your resume against job requirements" if apply_only_qualified else "SKIP THIS STEP - applyOnlyQualified is false, only preferences matter"}
   {"- Check if you have required skills (list each required skill and verify presence in resume)" if apply_only_qualified else ""}
   {"- Calculate experience using the method shown above - do NOT skip this step" if apply_only_qualified else ""}
   {"- Confirm your technical stack aligns with required technologies" if apply_only_qualified else ""}
   {"- Validate seniority level match (remember: junior = entry-level)" if apply_only_qualified else ""}

{"If ANY preference ACTUALLY MISMATCHES (not just missing), set shouldApply=false. Only reject for confirmed conflicts, not missing data." if apply_only_qualified else "If ANY preference ACTUALLY MISMATCHES (not just missing), set shouldApply=false. Only reject for confirmed conflicts, not missing data."}
List ONLY actual mismatches (not missing info) using "you" language. Be thorough but fair - missing info means benefit of the doubt."""
        
        return prompt
    
    def _validate_and_format_response(self, result: Dict) -> Dict:
        """Validate and format the AI response with strict enforcement."""
        if 'shouldApply' not in result:
            raise ValueError("AI response missing 'shouldApply' field")

        if 'reason' not in result:
            raise ValueError("AI response missing 'reason' field")

        reason_words = result['reason'].split()
        if len(reason_words) > 20:
            result['reason'] = ' '.join(reason_words[:20])
            logger.warning("AI response reason exceeded 20 words, truncated")

        match_score = result.get('matchScore', 0)
        if not isinstance(match_score, (int, float)) or match_score < 0 or match_score > 100:
            result['matchScore'] = 50
            logger.warning(f"Invalid matchScore: {match_score}, defaulting to 50")

        if 'mismatches' not in result or not isinstance(result['mismatches'], list):
            result['mismatches'] = []

        should_apply = bool(result['shouldApply'])
        match_score = float(result['matchScore'])
        mismatches = result['mismatches']

        if match_score < 70:
            should_apply = False
            logger.info(f"Overriding shouldApply to false due to low score: {match_score}")

        if mismatches and len(mismatches) > 0:
            if match_score < 80:
                should_apply = False
                logger.info(f"Overriding shouldApply to false due to mismatches and score < 80")
        
        return {
            'shouldApply': should_apply,
            'reason': str(result['reason']).strip(),
            'matchScore': match_score,
            'mismatches': [str(m).strip() for m in result['mismatches']]
        }
    
    def batch_analyze_jobs(
        self,
        resume_text: str,
        jobs: List[Dict],
        job_preferences: Dict
    ) -> List[Dict]:
        """
        Analyze multiple jobs at once.
        
        Args:
            resume_text: The candidate's resume
            jobs: List of job information dicts
            job_preferences: Candidate's preferences
            
        Returns:
            List of analysis results for each job
        """
        results = []
        
        for job in jobs:
            try:
                result = self.analyze_job_match(
                    resume_text=resume_text,
                    job_information=job,
                    job_preferences=job_preferences
                )
                result['job_id'] = job.get('id', None)
                result['job_title'] = job.get('title', 'Unknown')
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing job {job.get('id', 'unknown')}: {str(e)}")
                results.append({
                    'job_id': job.get('id', None),
                    'job_title': job.get('title', 'Unknown'),
                    'shouldApply': False,
                    'reason': 'Analysis failed',
                    'matchScore': 0,
                    'mismatches': ['Error during analysis'],
                    'error': str(e)
                })
        
        return results
