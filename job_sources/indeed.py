# job_sources/indeed.py
import asyncio
import logging
from typing import List, Dict, Any
from pydantic import BaseModel
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class JobSearchCriteria(BaseModel):
    position: str
    experience: str
    salary: str
    jobNature: str
    location: str
    skills: str

async def fetch_indeed_jobs(criteria: JobSearchCriteria) -> List[Dict[str, Any]]:
    """
    Fetch job listings from Indeed based on search criteria
    
    Args:
        criteria: Job search criteria including position, location, etc.
        
    Returns:
        List of job listings from Indeed
    """
    logger.info(f"Fetching Indeed jobs for position: {criteria.position} in {criteria.location}")
    
    try:
        # Create job type filter based on criteria
        job_type = "fulltime"
        if criteria.jobNature.lower() == "part time":
            job_type = "parttime"
        elif criteria.jobNature.lower() == "contract":
            job_type = "contract"
        elif criteria.jobNature.lower() == "internship":
            job_type = "internship"
            
        # Remote flag logic
        is_remote = "remote" in criteria.jobNature.lower()
        
        # Execute in a separate thread pool to not block the async event loop
        loop = asyncio.get_event_loop()
        indeed_jobs = await loop.run_in_executor(
            None,
            lambda: scrape_jobs(
                site_name=["indeed"],
                search_term=criteria.position,
                location=criteria.location,
                results_wanted=15,  # Fetch 15 results
                hours_old=72,       # Recent jobs only
                job_type=job_type,
                is_remote=is_remote,
                country_indeed=criteria.location.split(',')[-1].strip() if ',' in criteria.location else criteria.location,
                enforce_annual_salary=True,  # Convert all salaries to annual
                verbose=0
            )
        )
        
        # Convert to list of dictionaries
        if isinstance(indeed_jobs, pd.DataFrame):
            # Process the job listings into a standardized format
            jobs_list = []
            for _, job in indeed_jobs.iterrows():
                # Format salary information
                salary = "Not specified"
                if job.get('min_amount') is not None and job.get('max_amount') is not None:
                    min_amount = job.get('min_amount')
                    max_amount = job.get('max_amount')
                    interval = job.get('interval', 'yearly')
                    currency = job.get('currency', 'USD')
                    
                    if min_amount == max_amount:
                        salary = f"{currency} {min_amount:,} per {interval}"
                    else:
                        salary = f"{currency} {min_amount:,} - {max_amount:,} per {interval}"
                
                # Extract job type information
                job_nature = job.get('job_type', criteria.jobNature)
                if job_nature and str(job_nature) != 'nan':
                    job_nature = str(job_nature).title()
                
                # Format date to string
                posted_date = job.get('date_posted', '')
                if isinstance(posted_date, (pd.Timestamp, datetime)):
                    posted_date = posted_date.strftime('%Y-%m-%d')
                
                # Create standardized job object
                job_obj = {
                    "job_title": job.get('title', 'Unknown Title'),
                    "company": job.get('company', 'Unknown Company'),
                    "experience": extract_experience_from_description(job.get('description', '')),
                    "jobNature": job_nature,
                    "location": job.get('location', criteria.location),
                    "salary": salary,
                    "apply_link": job.get('job_url', ''),
                    "source": "Indeed",
                    "description": job.get('description', 'No description available'),
                    "company_industry": job.get('company_industry', ''),
                    "company_description": job.get('company_description', ''),
                    "company_rating": job.get('company_rating', ''),
                    "company_reviews": job.get('company_reviews', ''),
                    "posted_date": posted_date
                }
                jobs_list.append(job_obj)
                
            logger.info(f"Successfully fetched {len(jobs_list)} jobs from Indeed")
            return jobs_list
        
        logger.warning("Indeed returned no jobs or invalid format")
        return []
        
    except Exception as e:
        logger.error(f"Error fetching Indeed jobs: {str(e)}")
        return []  # Return empty list on error

def extract_experience_from_description(description: str) -> str:
    """Helper function to extract experience requirements from job description"""
    description = description.lower()
    
    # Common experience phrases
    experience_phrases = [
        "years of experience", "years experience", "year experience",
        "yrs experience", "year of experience", "yrs of experience"
    ]
    
    for phrase in experience_phrases:
        if phrase in description:
            # Find the position of the phrase
            pos = description.find(phrase)
            # Look for numbers before the phrase
            start = max(0, pos - 20)
            segment = description[start:pos].strip()
            words = segment.split()
            
            # Check the last few words for numbers
            for word in reversed(words):
                if word.isdigit() or word in ["one", "two", "three", "four", "five", 
                                              "six", "seven", "eight", "nine", "ten"]:
                    return f"{word} {phrase}"
    
    return "Not specified"