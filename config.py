"""
Configuration settings for the job finder application
"""

# Job Search Settings
MAX_JOBS_PER_SOURCE = 15
JOB_AGE_HOURS = 72
DEFAULT_LOCATION = "Pakistan"

# API Keys and Credentials
GEMINI_API_KEY = None  # Set via environment variable

# Scraping Settings
SELENIUM_WAIT_TIME = 20
SELENIUM_IMPLICIT_WAIT = 10
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30

# Cache Settings
CACHE_EXPIRY = 3600  # 1 hour in seconds

# Relevance Analysis Settings
MIN_RELEVANCE_SCORE = 0.4
LLM_WEIGHT = 0.7
BASIC_WEIGHT = 0.3

# Testing Settings
TEST_MODE = False
TEST_SEARCH_CRITERIA = {
    "position": "Software Engineer",
    "experience": "3+ years",
    "salary": "Competitive",
    "jobNature": "Full Time",
    "location": "Pakistan",
    "skills": "Python, JavaScript, API"
} 