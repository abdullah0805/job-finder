# Job Finder API

A FastAPI-based service that aggregates job listings from multiple sources (Indeed and Rozee.pk) with AI-powered relevance analysis.

## Features

- Multi-source job aggregation (Indeed, Rozee.pk)
- AI-powered relevance scoring using Google's Gemini
- Caching for improved performance
- Asynchronous job fetching
- Comprehensive test suite

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd job-finder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export GEMINI_API_KEY=your_api_key_here
```

4. Run the application:
```bash
uvicorn main:app --reload
```

## API Endpoints

### POST /search-jobs

Search for jobs across multiple sources.

Request body:
```json
{
    "position": "Software Engineer",
    "experience": "3+ years",
    "salary": "Competitive",
    "jobNature": "Full Time",
    "location": "Pakistan",
    "skills": "Python, JavaScript, API"
}
```

Response:
```json
{
    "relevant_jobs": [
        {
            "job_title": "Senior Software Engineer",
            "company": "Example Corp",
            "experience": "3+ years",
            "jobNature": "Full Time",
            "location": "Lahore, Pakistan",
            "salary": "Competitive",
            "apply_link": "https://example.com/job",
            "source": "Indeed",
            "relevance_score": 0.85
        }
    ],
    "total_jobs_found": 1,
    "search_timestamp": "2024-03-21T12:00:00Z"
}
```

### GET /health

Health check endpoint.

Response:
```json
{
    "status": "healthy",
    "timestamp": "2024-03-21T12:00:00Z",
    "cache_size": 5
}
```

## Configuration

Key settings can be modified in `config.py`:

- `MAX_JOBS_PER_SOURCE`: Maximum jobs to fetch from each source
- `JOB_AGE_HOURS`: Maximum age of jobs to fetch
- `CACHE_EXPIRY`: Cache expiration time in seconds
- `MIN_RELEVANCE_SCORE`: Minimum score for jobs to be included in results

## Testing

Run the test suite:
```bash
pytest tests/test_job_finder.py -v
```

For tests requiring network access:
```bash
pytest tests/test_job_finder.py -v -m network
```

## Project Structure

```
job-finder/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── requirements.txt     # Dependencies
├── job_sources/        # Job source implementations
│   ├── __init__.py
│   ├── indeed.py
│   └── rozee.py
├── tests/             # Test suite
│   └── test_job_finder.py
└── relevance_analyzer.py  # AI-powered relevance analysis
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License 