# Job Finder API Documentation

## Overview

The Job Finder API provides a powerful interface for searching and matching jobs across multiple sources (Indeed, LinkedIn, and Rozee.pk) with AI-powered relevance analysis.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. However, you need to provide a valid Google Gemini API key in the `.env` file for the AI-powered relevance analysis to work.

## Endpoints

### 1. Search Jobs

Search for jobs across multiple sources with AI-powered relevance analysis.

**Endpoint:** `POST /search-jobs`

**Request Body:**
```json
{
    "position": "Full Stack Developer",
    "experience": "2 years",
    "salary": "100000",
    "jobNature": "Full Time",
    "location": "Lahore, Pakistan",
    "skills": "Python, JavaScript, React, Node.js"
}
```

**Parameters:**
- `position` (string, required): The job title or position to search for
- `experience` (string, required): Required experience level
- `salary` (string, required): Expected salary range
- `jobNature` (string, required): Type of employment (Full Time, Part Time, Contract, etc.)
- `location` (string, required): Job location
- `skills` (string, required): Comma-separated list of required skills

**Response:**
```json
{
    "relevant_jobs": [
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
    ],
    "total_jobs_found": 1,
    "search_timestamp": "2024-03-21T12:00:00Z"
}
```

### 2. Health Check

Check the health status of the API.

**Endpoint:** `GET /health`

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-03-21T12:00:00Z",
    "cache_size": 5
}
```

## Job Matching Process

### 1. Job Collection

The API collects jobs from multiple sources:

1. **Indeed**
   - Uses JobSpy library for scraping
   - Configurable number of jobs per search
   - Handles date serialization automatically

2. **LinkedIn**
   - Uses JobSpy library for scraping
   - Respects rate limits
   - Requires proper configuration

3. **Rozee.pk**
   - Custom scraper using Selenium
   - Handles dynamic content
   - Extracts detailed job information

### 2. Relevance Analysis

Jobs are analyzed for relevance using Google's Gemini API:

1. **Basic Relevance Score**
   - Title match (30% weight)
   - Location match (10% weight)
   - Job nature match (10% weight)
   - Experience match (10% weight)
   - Skills match (40% weight)

2. **AI-Powered Analysis**
   - Analyzes job description
   - Considers company information
   - Evaluates overall suitability
   - Provides detailed relevance score

### 3. Job Standardization

All jobs are standardized to a common format:

```json
{
    "job_title": "string",
    "company": "string",
    "experience": "string",
    "jobNature": "string",
    "location": "string",
    "salary": "string",
    "apply_link": "string",
    "relevance_score": "float"
}
```

### 4. Caching

The API implements caching to improve performance:

- Cache duration: 1 hour (configurable)
- Cache key: Combination of search parameters
- Automatic cache invalidation

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid input parameters
- `404 Not Found`: No jobs found matching criteria
- `500 Internal Server Error`: Server-side error

## Rate Limiting

The API implements rate limiting based on the Gemini API quota:

- Maximum 15 requests per minute
- 5 jobs per source
- Total of 15 jobs per search

## Example Usage

### Python
```python
import requests

def search_jobs():
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
    if response.status_code == 200:
        jobs = response.json()
        print(f"Found {jobs['total_jobs_found']} jobs")
        for job in jobs['relevant_jobs']:
            print(f"Job: {job['job_title']} at {job['company']}")
    else:
        print(f"Error: {response.status_code}")

search_jobs()
```

### cURL
```bash
curl -X POST http://localhost:8000/search-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "position": "Full Stack Developer",
    "experience": "2 years",
    "salary": "100000",
    "jobNature": "Full Time",
    "location": "Lahore, Pakistan",
    "skills": "Python, JavaScript, React, Node.js"
  }'
```

## Best Practices

1. **Search Parameters**
   - Use specific job titles
   - Include relevant skills
   - Specify location accurately

2. **Error Handling**
   - Implement proper error handling
   - Check response status codes
   - Handle rate limiting

3. **Caching**
   - Cache results when possible
   - Respect cache expiration
   - Handle cache misses gracefully

4. **Performance**
   - Limit concurrent requests
   - Use appropriate timeouts
   - Monitor API usage

## Troubleshooting

Common issues and solutions:

1. **No Jobs Found**
   - Check search parameters
   - Verify location format
   - Ensure skills are relevant

2. **Rate Limiting**
   - Reduce request frequency
   - Implement exponential backoff
   - Use caching

3. **Scraping Issues**
   - Check internet connection
   - Verify Chrome installation
   - Monitor log files

## Support

For issues and support:
1. Check the log files
2. Review the documentation
3. Open an issue on GitHub 