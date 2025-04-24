import requests
import json
from typing import Dict, Any, List
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JobFinderAPI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def search_jobs(self, 
                   position: str,
                   experience: str,
                   salary: str,
                   job_nature: str,
                   location: str,
                   skills: str) -> Dict[str, Any]:
        """
        Search for jobs using the API
        """
        endpoint = f"{self.base_url}/search-jobs"
        
        payload = {
            "position": position,
            "experience": experience,
            "salary": salary,
            "jobNature": job_nature,
            "location": location,
            "skills": skills
        }
        
        try:
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching jobs: {str(e)}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health
        """
        endpoint = f"{self.base_url}/health"
        
        try:
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking health: {str(e)}")
            return None

def format_job_output(jobs: List[Dict[str, Any]]) -> str:
    """
    Format job listings for display
    """
    output = []
    for i, job in enumerate(jobs, 1):
        output.append(f"\nJob {i}:")
        output.append(f"Title: {job['job_title']}")
        output.append(f"Company: {job['company']}")
        output.append(f"Experience: {job['experience']}")
        output.append(f"Job Nature: {job['jobNature']}")
        output.append(f"Location: {job['location']}")
        output.append(f"Salary: {job['salary']}")
        output.append(f"Apply Link: {job['apply_link']}")
        output.append(f"Relevance Score: {job.get('relevance_score', 'N/A')}")
        output.append("-" * 50)
    
    return "\n".join(output)

def save_results_to_json(results: Dict[str, Any], filename: str = "output.json"):
    """
    Save job results to a JSON file in the specified format
    """
    try:
        # Extract only the required fields for each job
        formatted_jobs = []
        for job in results['relevant_jobs']:
            formatted_job = {
                "job_title": job['job_title'],
                "company": job['company'],
                "experience": job['experience'],
                "jobNature": job['jobNature'],
                "location": job['location'],
                "salary": job['salary'],
                "apply_link": job['apply_link']
            }
            formatted_jobs.append(formatted_job)
        
        # Create the final output structure
        output_data = {
            "relevant_jobs": formatted_jobs
        }
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving results to JSON: {str(e)}")

def main():
    # Initialize API client
    api = JobFinderAPI(base_url="http://localhost:8000")
    
    # Define search criteria
    search_criteria = {
        "position": "Full Stack Developer",
        "experience": "2+ years",
        "salary": "100,000 PKR",
        "job_nature": "onsite",
        "location": "Lahore, Pakistan",
        "skills": "Python,JavaScript,React,Node.js"
    }
    
    logger.info("Starting job search with criteria:")
    for key, value in search_criteria.items():
        logger.info(f"{key}: {value}")
    
    # Check API health
    health = api.health_check()
    if health:
        logger.info(f"API Status: {health['status']}")
        logger.info(f"Cache Size: {health['cache_size']}")
        logger.info(f"Timestamp: {health['timestamp']}")
        logger.info("-" * 50)
    
    # Search for jobs
    logger.info("\nSearching for jobs...")
    results = api.search_jobs(
        position=search_criteria["position"],
        experience=search_criteria["experience"],
        salary=search_criteria["salary"],
        job_nature=search_criteria["job_nature"],
        location=search_criteria["location"],
        skills=search_criteria["skills"]
    )
    
    if results:
        logger.info(f"\nFound {results['total_jobs_found']} relevant jobs")
        logger.info(f"Search timestamp: {results['search_timestamp']}")
        print(format_job_output(results['relevant_jobs']))
        
        # Save results to JSON file
        save_results_to_json(results)
    else:
        logger.error("No jobs found or error occurred")

if __name__ == "__main__":
    main() 