"""
Tests for AI-powered job matching service.
"""
import pytest
import json
from unittest.mock import Mock, patch
from app.services.job_matcher_ai import JobMatcherAI


class TestJobMatcherAI:
    """Test suite for JobMatcherAI service."""
    
    @pytest.fixture
    def matcher(self):
        """Create a JobMatcherAI instance with mocked OpenAI."""
        with patch('app.services.job_matcher_ai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            matcher = JobMatcherAI()
            matcher.client = mock_client
            yield matcher
    
    @pytest.fixture
    def sample_resume(self):
        """Sample resume text."""
        return """
        John Doe
        Senior Software Engineer
        
        Experience:
        - 5 years of Python development
        - 3 years of React and TypeScript
        - Experience with AWS, Docker, Kubernetes
        - Built microservices with Django and Flask
        
        Education:
        - BS Computer Science, MIT
        
        Skills: Python, JavaScript, React, Django, Flask, AWS, Docker, Kubernetes, PostgreSQL
        """
    
    @pytest.fixture
    def sample_job(self):
        """Sample job information."""
        return {
            "title": "Senior Python Developer",
            "description": "We're looking for a senior Python developer to join our team.",
            "requirements": "5+ years Python, Django/Flask, AWS experience required",
            "location": "San Francisco, CA",
            "salary": "$150,000 - $180,000",
            "type": "hybrid",
            "experience_required": "5+ years"
        }
    
    @pytest.fixture
    def sample_preferences(self):
        """Sample job preferences."""
        return {
            "locations": ["San Francisco", "Remote"],
            "min_salary": 140000,
            "max_salary": 200000,
            "remote_preference": "preferred",
            "roles": ["Software Engineer", "Backend Developer"],
            "deal_breakers": ["No relocation"]
        }
    
    def test_analyze_job_match_success(self, matcher, sample_resume, sample_job, sample_preferences):
        """Test successful job match analysis."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "shouldApply": True,
            "reason": "Strong Python and AWS experience matches requirements perfectly",
            "matchScore": 92,
            "mismatches": []
        })
        matcher.client.chat.completions.create.return_value = mock_response
        
        result = matcher.analyze_job_match(
            resume_text=sample_resume,
            job_information=sample_job,
            job_preferences=sample_preferences
        )
        
        assert result['shouldApply'] is True
        assert isinstance(result['reason'], str)
        assert len(result['reason'].split()) <= 20
        assert 0 <= result['matchScore'] <= 100
        assert isinstance(result['mismatches'], list)
    
    def test_analyze_job_match_should_not_apply(self, matcher, sample_resume, sample_preferences):
        """Test when candidate should not apply."""
        job = {
            "title": "Junior Java Developer",
            "description": "Entry level Java position",
            "requirements": "0-2 years Java experience",
            "location": "New York, NY",
            "salary": "$60,000 - $80,000",
            "type": "onsite",
            "experience_required": "0-2 years"
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "shouldApply": False,
            "reason": "Overqualified senior engineer for junior role, salary below expectations",
            "matchScore": 35,
            "mismatches": [
                "Experience level: Senior vs Junior required",
                "Salary: $60k-80k vs $140k+ expected",
                "Primary skill: Python vs Java required"
            ]
        })
        matcher.client.chat.completions.create.return_value = mock_response
        
        result = matcher.analyze_job_match(
            resume_text=sample_resume,
            job_information=job,
            job_preferences=sample_preferences
        )
        
        assert result['shouldApply'] is False
        assert len(result['mismatches']) > 0
        assert result['matchScore'] < 50
    
    def test_validate_empty_resume(self, matcher, sample_job, sample_preferences):
        """Test validation with empty resume."""
        with pytest.raises(ValueError, match="Resume text cannot be empty"):
            matcher.analyze_job_match(
                resume_text="",
                job_information=sample_job,
                job_preferences=sample_preferences
            )
    
    def test_validate_missing_job_info(self, matcher, sample_resume, sample_preferences):
        """Test validation with missing job information."""
        with pytest.raises(ValueError, match="Job information is required"):
            matcher.analyze_job_match(
                resume_text=sample_resume,
                job_information=None,
                job_preferences=sample_preferences
            )
    
    def test_reason_truncation(self, matcher, sample_resume, sample_job, sample_preferences):
        """Test that reasons exceeding 20 words are truncated."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        # Create a reason with more than 20 words
        long_reason = " ".join(["word"] * 25)
        mock_response.choices[0].message.content = json.dumps({
            "shouldApply": True,
            "reason": long_reason,
            "matchScore": 85,
            "mismatches": []
        })
        matcher.client.chat.completions.create.return_value = mock_response
        
        result = matcher.analyze_job_match(
            resume_text=sample_resume,
            job_information=sample_job,
            job_preferences=sample_preferences
        )
        
        assert len(result['reason'].split()) <= 20
    
    def test_batch_analyze_jobs(self, matcher, sample_resume, sample_preferences):
        """Test batch job analysis."""
        jobs = [
            {
                "id": "job1",
                "title": "Senior Python Developer",
                "description": "Python role",
                "requirements": "5+ years Python"
            },
            {
                "id": "job2",
                "title": "Frontend Developer",
                "description": "React role",
                "requirements": "3+ years React"
            }
        ]
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "shouldApply": True,
            "reason": "Good match",
            "matchScore": 85,
            "mismatches": []
        })
        matcher.client.chat.completions.create.return_value = mock_response
        
        results = matcher.batch_analyze_jobs(
            resume_text=sample_resume,
            jobs=jobs,
            job_preferences=sample_preferences
        )
        
        assert len(results) == 2
        assert all('job_id' in r for r in results)
        assert all('job_title' in r for r in results)
        assert all('shouldApply' in r for r in results)
    
    def test_invalid_match_score(self, matcher, sample_resume, sample_job, sample_preferences):
        """Test handling of invalid match scores."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "shouldApply": True,
            "reason": "Good match",
            "matchScore": 150,  # Invalid: > 100
            "mismatches": []
        })
        matcher.client.chat.completions.create.return_value = mock_response
        
        result = matcher.analyze_job_match(
            resume_text=sample_resume,
            job_information=sample_job,
            job_preferences=sample_preferences
        )
        
        # Should default to 50 for invalid scores
        assert result['matchScore'] == 50
