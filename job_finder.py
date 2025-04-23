"""
Job Finder Script - Takes JSON input and produces JSON output
"""
import asyncio
import json
import os
from datetime import datetime, date
from main import JobSearchCriteria
from job_sources.indeed import fetch_indeed_jobs
from job_sources.rozee import fetch_rozee_jobs
from job_sources.linkedin import fetch_linkedin_jobs
from relevance_analyzer import analyze_job_relevance
import logging
from typing import Dict, List, Any
import time

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.strftime('%Y-%m-%d')
        return super().default(obj)

def setup_logger(name: str, log_file: str) -> logging.Logger:
    """Setup a logger with the specified name and log file"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_json(logger: logging.Logger, data: Dict[str, Any], title: str):
    """Log JSON data with a title"""
    logger.info(f"\n{'='*50}")
    logger.info(f"{title}")
    logger.info(f"{'='*50}")
    logger.info(json.dumps(data, indent=2, cls=DateTimeEncoder))
    logger.info(f"{'='*50}\n")

async def fetch_jobs_with_retry(fetch_func, criteria, logger, max_retries=3, delay=5):
    """Fetch jobs with retry logic"""
    for attempt in range(max_retries):
        try:
            jobs = await fetch_func(criteria)
            if jobs:
                return jobs
            logger.warning(f"No jobs found on attempt {attempt + 1}")
        except Exception as e:
            logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error("Max retries reached, giving up")
                return []
    return []

async def find_jobs(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to find jobs based on input criteria"""
    # Setup loggers
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_logger = setup_logger('input', f'logs/input_{timestamp}.log')
    indeed_logger = setup_logger('indeed', f'logs/indeed_{timestamp}.log')
    rozee_logger = setup_logger('rozee', f'logs/rozee_{timestamp}.log')
    linkedin_logger = setup_logger('linkedin', f'logs/linkedin_{timestamp}.log')
    analysis_logger = setup_logger('analysis', f'logs/analysis_{timestamp}.log')
    output_logger = setup_logger('output', f'logs/output_{timestamp}.log')
    
    try:
        # Log input data
        log_json(input_logger, input_data, "Input Data")
        
        # Create search criteria
        if ',' not in input_data['location']:
            input_data['location'] = f"{input_data['location']}, Pakistan"
        
        criteria = JobSearchCriteria(**input_data)
        
        # Fetch jobs from all sources with retry logic
        indeed_logger.info("Fetching jobs from Indeed")
        indeed_jobs = await fetch_jobs_with_retry(fetch_indeed_jobs, criteria, indeed_logger)
        log_json(indeed_logger, {"jobs": indeed_jobs}, "Indeed Jobs")
        
        rozee_logger.info("Fetching jobs from Rozee")
        rozee_jobs = await fetch_jobs_with_retry(fetch_rozee_jobs, criteria, rozee_logger)
        log_json(rozee_logger, {"jobs": rozee_jobs}, "Rozee Jobs")
        
        linkedin_logger.info("Fetching jobs from LinkedIn")
        linkedin_jobs = await fetch_jobs_with_retry(fetch_linkedin_jobs, criteria, linkedin_logger)
        log_json(linkedin_logger, {"jobs": linkedin_jobs}, "LinkedIn Jobs")
        
        # Combine results
        all_jobs = indeed_jobs + rozee_jobs + linkedin_jobs
        print(f"Total jobs found: {len(all_jobs)}")
        
        if not all_jobs:
            output_logger.warning("No jobs found from any source")
            return {"relevant_jobs": []}
        
        # Analyze relevance
        analysis_logger.info("Analyzing job relevance")
        relevant_jobs = analyze_job_relevance(all_jobs, criteria)
        print(f"Relevant jobs found: {len(relevant_jobs)}")
        
        # Sort jobs by relevance score
        sorted_jobs = sorted(relevant_jobs, key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        # Create output structure with more details
        output = {
            "relevant_jobs": [
                {
                    "job_title": job["job_title"],
                    "company": job["company"],
                    "experience": job["experience"],
                    "jobNature": job["jobNature"],
                    "location": job["location"],
                    "salary": job["salary"],
                    "apply_link": job["apply_link"],
                    "relevance_score": job.get("relevance_score", 0),
                    "source": job.get("source", "Unknown"),
                    "posted_date": job.get("posted_date", "Not specified"),
                    "company_industry": job.get("company_industry", "Not specified"),
                    "skills": job.get("skills", []),
                    "description_snippet": job.get("description_snippet", "No description available")
                }
                for job in sorted_jobs
            ]
        }
        
        # Log the final output
        log_json(output_logger, output, "Final Output")
        
        # Save output to JSON file
        output_file = f'logs/output_{timestamp}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, cls=DateTimeEncoder)
        
        return output
        
    except Exception as e:
        output_logger.error(f"Error in job search: {str(e)}")
        raise

def main():
    """Main function to run the job finder"""
    # Sample input data
    input_data = {
        "position": "Full Stack Developer with AI Engineer",
        "experience": "2 years",
        "salary": "150,000 PKR to 170,000 PKR",
        "jobNature": "Fulltime",
        "location": "Lahore, Pakistan",  # Changed to Lahore for better results
        "skills": "full stack, MERN, Node.js, Express.js, React.js, Next.js, Firebase, TailwindCSS, CSS Frameworks, Tokens handling"
    }
    
    # Run the job finder
    try:
        output = asyncio.run(find_jobs(input_data))
        print("\nJob search completed successfully!")
        print(f"Found {len(output['relevant_jobs'])} relevant jobs")
        print(f"Results saved in logs/output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 