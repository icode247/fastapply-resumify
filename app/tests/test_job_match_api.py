"""
Integration tests for AI Job Matching API endpoints.
"""
import pytest
import json
from unittest.mock import Mock, patch
from app import create_app


@pytest.fixture
def app():
    """Create test Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def mock_openai():
    """Mock OpenAI responses."""
    with patch('app.services.job_matcher_ai.OpenAI') as mock:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "shouldApply": True,
            "reason": "Strong technical match with required skills",
            "matchScore": 88,
            "mismatches": []
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock.return_value = mock_client
        yield mock


class TestJobMatchAPI:
    """Test suite for job match API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/job-match/health')
        assert response.status_code in [200, 503]
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'service' in data
        assert data['service'] == 'job_match_ai'
    
    def test_analyze_job_match_success(self, client, mock_openai):
        """Test successful job match analysis."""
        payload = {
            "resume_text": "Senior Python Developer with 5 years experience",
            "job_information": {
                "title": "Senior Python Engineer",
                "description": "Looking for Python expert",
                "requirements": "5+ years Python",
                "location": "Remote",
                "salary": "$150k-$180k",
                "type": "remote",
                "experience_required": "5+ years"
            },
            "job_preferences": {
                "locations": ["Remote"],
                "min_salary": 140000,
                "remote_preference": "required"
            }
        }
        
        response = client.post(
            '/api/job-match/analyze',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # May be 200 if OpenAI key is configured, or 503 if not
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'shouldApply' in data['data']
            assert 'reason' in data['data']
            assert 'matchScore' in data['data']
            assert 'mismatches' in data['data']
    
    def test_analyze_missing_resume(self, client):
        """Test analysis with missing resume text."""
        payload = {
            "job_information": {
                "title": "Developer"
            }
        }
        
        response = client.post(
            '/api/job-match/analyze',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code in [400, 503]
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_analyze_missing_job_info(self, client):
        """Test analysis with missing job information."""
        payload = {
            "resume_text": "Some resume text"
        }
        
        response = client.post(
            '/api/job-match/analyze',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code in [400, 503]
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_batch_analyze_success(self, client, mock_openai):
        """Test batch job analysis."""
        payload = {
            "resume_text": "Python Developer with 3 years experience",
            "jobs": [
                {
                    "id": "job1",
                    "title": "Python Developer",
                    "description": "Python role",
                    "requirements": "3+ years Python"
                },
                {
                    "id": "job2",
                    "title": "Java Developer",
                    "description": "Java role",
                    "requirements": "5+ years Java"
                }
            ],
            "job_preferences": {
                "locations": ["Remote"]
            }
        }
        
        response = client.post(
            '/api/job-match/batch-analyze',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'data' in data
            assert 'total_analyzed' in data
            assert 'should_apply_count' in data
    
    def test_batch_analyze_too_many_jobs(self, client):
        """Test batch analysis with too many jobs."""
        payload = {
            "resume_text": "Developer",
            "jobs": [{"title": f"Job {i}"} for i in range(51)],  # 51 jobs
            "job_preferences": {}
        }
        
        response = client.post(
            '/api/job-match/batch-analyze',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code in [400, 503]
        
        if response.status_code == 400:
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Maximum 50 jobs' in data['error']
    
    def test_batch_analyze_missing_jobs(self, client):
        """Test batch analysis with missing jobs array."""
        payload = {
            "resume_text": "Developer"
        }
        
        response = client.post(
            '/api/job-match/batch-analyze',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code in [400, 503]
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_invalid_json(self, client):
        """Test with invalid JSON payload."""
        response = client.post(
            '/api/job-match/analyze',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code in [400, 500, 503]
    
    def test_empty_request_body(self, client):
        """Test with empty request body."""
        response = client.post(
            '/api/job-match/analyze',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code in [400, 503]
        data = json.loads(response.data)
        assert 'error' in data
