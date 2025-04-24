# job_sources/linkedin.py
import asyncio
import logging
from typing import List, Dict, Any
from pydantic import BaseModel
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime
from config import JOBS_PER_SOURCE
import json

# Configure LinkedIn-specific logging
linkedin_logger = logging.getLogger('linkedin')
linkedin_logger.setLevel(logging.INFO)
linkedin_handler = logging.FileHandler('linkedin_raw.log')
linkedin_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
linkedin_logger.addHandler(linkedin_handler)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        return super().default(obj)

class JobSearchCriteria(BaseModel):
    position: str
    experience: str
    salary: str
    jobNature: str
    location: str
    skills: str

async def fetch_linkedin_jobs(criteria: JobSearchCriteria) -> List[Dict[str, Any]]:
    """
    Fetch job listings from LinkedIn based on search criteria
    
    Args:
        criteria: Job search criteria including position, location, etc.
        
    Returns:
        List of job listings from LinkedIn
    """
    linkedin_logger.info(f"Fetching LinkedIn jobs for position: {criteria.position} in {criteria.location}")
    
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
        
        linkedin_logger.info(f"LinkedIn search parameters: job_type={job_type}, is_remote={is_remote}")
        
        # Execute in a separate thread pool to not block the async event loop
        loop = asyncio.get_event_loop()
        linkedin_jobs = await loop.run_in_executor(
            None,
            lambda: scrape_jobs(
                site_name=["linkedin"],
                search_term=criteria.position,
                location=criteria.location,
                results_wanted=JOBS_PER_SOURCE,  # Limit to configured number of jobs
                hours_old=72,       # Recent jobs only
                job_type=job_type,
                is_remote=is_remote,
                linkedin_fetch_description=True,  # Get full description
                enforce_annual_salary=True,  # Convert all salaries to annual
                verbose=0
            )
        )
        
        # Log raw LinkedIn response
        linkedin_logger.info("Raw LinkedIn Response:")
        linkedin_logger.info(json.dumps(linkedin_jobs.to_dict(orient='records'), indent=2, cls=DateTimeEncoder))
        
        # Convert to list of dictionaries
        if isinstance(linkedin_jobs, pd.DataFrame):
            # Process the job listings into a standardized format
            jobs_list = []
            for _, job in linkedin_jobs.iterrows():
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
                    "experience": job.get('job_level', criteria.experience),  # LinkedIn often provides job level
                    "jobNature": job_nature,
                    "location": job.get('location', criteria.location),
                    "salary": salary,
                    "apply_link": job.get('job_url', ''),
                    "source": "LinkedIn",
                    "description": job.get('description', 'No description available'),
                    "company_industry": job.get('company_industry', ''),
                    "job_function": job.get('job_function', ''),
                    "employment_type": job.get('employment_type', ''),
                    "seniority_level": job.get('job_level', ''),
                    "posted_date": posted_date
                }
                jobs_list.append(job_obj)
                
            linkedin_logger.info(f"Successfully processed {len(jobs_list)} jobs from LinkedIn")
            return jobs_list
        
        linkedin_logger.warning("LinkedIn returned no jobs or invalid format")
        return []
        
    except Exception as e:
        linkedin_logger.error(f"Error fetching LinkedIn jobs: {str(e)}")
        return []  # Return empty list on error