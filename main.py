# main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import json
import time
from datetime import datetime
import asyncio
import logging
from config import CACHE_EXPIRY, MAX_JOBS_PER_SOURCE
# Import job source modules
from job_sources.indeed import fetch_indeed_jobs
from job_sources.rozee import fetch_rozee_jobs
from job_sources.linkedin import fetch_linkedin_jobs
from relevance_analyzer import analyze_job_relevance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_finder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Job Finder API",
    description="API to fetch job listings from Indeed, Rozee.pk, and LinkedIn with AI-powered relevance analysis",
    version="1.0.0"
)

class JobSearchCriteria(BaseModel):
    position: str
    experience: str
    salary: str
    jobNature: str
    location: str
    skills: str

class JobListing(BaseModel):
    job_title: str
    company: str
    experience: str
    jobNature: str
    location: str
    salary: str
    apply_link: str
    relevance_score: Optional[float] = None

class JobSearchResponse(BaseModel):
    relevant_jobs: List[JobListing]
    total_jobs_found: int
    search_timestamp: str

# In-memory cache for job search results
job_cache = {}

@app.post("/search-jobs", response_model=JobSearchResponse)
async def search_jobs(criteria: JobSearchCriteria, background_tasks: BackgroundTasks):
    """
    Search for jobs based on the provided criteria across Indeed, Rozee.pk, and LinkedIn
    """
    try:
        # Create a cache key based on search criteria
        cache_key = f"{criteria.position}_{criteria.location}_{criteria.jobNature}"
        
        # Check cache
        current_time = time.time()
        if cache_key in job_cache and (current_time - job_cache[cache_key]['timestamp']) < CACHE_EXPIRY:
            logger.info(f"Returning cached results for {cache_key}")
            return job_cache[cache_key]['response']
        
        # Start job search process
        logger.info(f"Starting job search for position: {criteria.position} in {criteria.location}")
        
        # Fetch jobs from different sources concurrently
        indeed_task = fetch_indeed_jobs(criteria)
        rozee_task = fetch_rozee_jobs(criteria)
        linkedin_task = fetch_linkedin_jobs(criteria)
        
        # Wait for all tasks to complete
        indeed_jobs, rozee_jobs, linkedin_jobs = await asyncio.gather(
            indeed_task, 
            rozee_task,
            linkedin_task,
            return_exceptions=True
        )
        
        # Handle potential errors from job sources
        all_jobs = []
        if not isinstance(indeed_jobs, Exception):
            logger.info(f"Successfully fetched {len(indeed_jobs)} jobs from Indeed")
            all_jobs.extend(indeed_jobs)
        else:
            logger.error(f"Error fetching Indeed jobs: {str(indeed_jobs)}")
            
        if not isinstance(rozee_jobs, Exception):
            logger.info(f"Successfully fetched {len(rozee_jobs)} jobs from Rozee")
            all_jobs.extend(rozee_jobs)
        else:
            logger.error(f"Error fetching Rozee jobs: {str(rozee_jobs)}")
            
        if not isinstance(linkedin_jobs, Exception):
            logger.info(f"Successfully fetched {len(linkedin_jobs)} jobs from LinkedIn")
            all_jobs.extend(linkedin_jobs)
        else:
            logger.error(f"Error fetching LinkedIn jobs: {str(linkedin_jobs)}")
            
        if not all_jobs:
            logger.warning("No jobs found matching criteria")
            raise HTTPException(status_code=404, detail="No jobs found matching your criteria")
        
        # Analyze job relevance
        logger.info(f"Analyzing relevance for {len(all_jobs)} jobs")
        relevant_jobs = analyze_job_relevance(all_jobs, criteria)
        
        # Sort by relevance score (descending)
        relevant_jobs = sorted(relevant_jobs, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Create response
        response = JobSearchResponse(
            relevant_jobs=relevant_jobs,
            total_jobs_found=len(relevant_jobs),
            search_timestamp=datetime.now().isoformat()
        )
        
        # Cache the results
        job_cache[cache_key] = {
            'response': response,
            'timestamp': current_time
        }
        
        # Start background task to refresh cache
        background_tasks.add_task(refresh_job_cache, criteria)
        
        logger.info(f"Successfully completed job search. Found {len(relevant_jobs)} relevant jobs")
        return response
        
    except Exception as e:
        logger.error(f"Error in job search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching for jobs: {str(e)}")

async def refresh_job_cache(criteria: JobSearchCriteria):
    """Background task to refresh job cache periodically"""
    try:
        await asyncio.sleep(CACHE_EXPIRY)
        cache_key = f"{criteria.position}_{criteria.location}_{criteria.jobNature}"
        if cache_key in job_cache:
            del job_cache[cache_key]
            logger.info(f"Cache cleared for {cache_key}")
    except Exception as e:
        logger.error(f"Error in cache refresh: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cache_size": len(job_cache)
    }

if __name__ == "__main__":
    logger.info("Starting Job Finder API server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)