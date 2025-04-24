# Job Finder

A powerful job search application that aggregates job listings from multiple sources (Indeed, LinkedIn, and Rozee.pk) with AI-powered relevance analysis.

## Features

- Multi-source job search (Indeed, LinkedIn, Rozee.pk)
- AI-powered relevance analysis using Google's Gemini API
- Standardized job listing format
- Configurable job limits per source
- Detailed logging for debugging
- FastAPI backend with async support
- Caching for improved performance

## Prerequisites

- Python 3.10 or higher
- Chrome browser (for web scraping)
- Google Gemini API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/job-finder.git
cd job-finder
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Configuration

The `config.py` file contains important configuration settings:

```python
# API Limits
GEMINI_API_LIMIT_PER_MINUTE = 15  # Free tier limit
JOBS_PER_SOURCE = 5  # Number of jobs to fetch per source

# Cache Settings
CACHE_EXPIRY = 3600  # Cache expiry in seconds (1 hour)

# Scraping Settings
SCRAPING_TIMEOUT = 30  # Timeout for web scraping in seconds
```

## Usage

1. Start the FastAPI server:
```bash
python main.py
```

2. The server will start at `http://localhost:8000`

3. API Endpoints:
   - `POST /search-jobs`: Search for jobs
   - `GET /health`: Health check endpoint

4. Example job search request:
```python
import requests

url = "http://localhost:8000/search-jobs"
data = {
    "position": "Full Stack Developer",
    "experience": "2 years",
    "salary": "100000",
    "jobNature": "Full Time",
    "location": "Lahore, Pakistan",
    "skills": "Python, JavaScript, React, Node.js"
}

response = requests.post(url, json=data)
jobs = response.json()
```

## Project Structure

```
job-finder/
├── main.py                 # FastAPI application
├── config.py              # Configuration settings
├── relevance_analyzer.py  # AI-powered relevance analysis
├── api_client.py         # API client for job search
├── job_sources/          # Job source scrapers
│   ├── indeed.py
│   ├── linkedin.py
│   └── rozee.py
├── requirements.txt      # Project dependencies
└── README.md            # This file
```

## Logging

The application generates several log files:
- `job_finder.log`: Main application logs
- `indeed_raw.log`: Raw Indeed job data
- `linkedin_raw.log`: Raw LinkedIn job data
- `rozee_raw.log`: Raw Rozee job data

## Output Format

Job listings are returned in a standardized format:
```json
{
    "job_title": "Full Stack Developer",
    "company": "Example Corp",
    "experience": "2 years",
    "jobNature": "Full Time",
    "location": "Lahore, Pakistan",
    "salary": "PKR 100,000 - 150,000",
    "apply_link": "https://example.com/job",
    "relevance_score": 0.85
}
```
- Sample output is present in output.json, which comes through the result of the json input in api_client

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [JobSpy](https://github.com/Radicalpiotr/jobspy) for job scraping functionality
- [Google Gemini](https://ai.google.dev/) for AI-powered relevance analysis
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework 