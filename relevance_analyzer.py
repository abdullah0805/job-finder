import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Any
import os
import json
import logging

# Load environment variables
load_dotenv()

# Initialize Gemini with API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

logger = logging.getLogger(__name__)

def test_gemini_api():
    """
    Test if Gemini API is working correctly
    Returns: (bool, str) - (is_working, message)
    """
    try:
        # Check if API key is set
        if not GEMINI_API_KEY:
            return False, "GEMINI_API_KEY not found in environment variables"
        
        print(f"API Key found: {GEMINI_API_KEY[:5]}...{GEMINI_API_KEY[-5:]}")  # Show first and last 5 chars
        
        # Create a simple test prompt
        test_prompt = "What is 2+2? Answer with just the number."
        
        # Initialize the model with the correct name
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Make a test API call
        response = model.generate_content(test_prompt)
        
        # Check if we got a valid response
        if response and response.text.strip() == "4":
            return True, "Gemini API is working correctly"
        else:
            return False, f"Unexpected response from Gemini API: {response.text}"
            
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg.lower():
            return False, "Invalid or missing API key. Please check your GEMINI_API_KEY in .env file"
        elif "model" in error_msg.lower():
            return False, "Model configuration error. Please check if 'gemini-2.0-flash' is available"
        else:
            return False, f"Error testing Gemini API: {error_msg}"

def analyze_job_relevance(jobs: List[Dict[str, Any]], criteria):
    """
    Analyze job listings for relevance to the user's criteria using LLM
    """
    print(f"Analyzing relevance for {len(jobs)} jobs")
    
    if not jobs:
        return []
    
    # Create user skills set for easier comparison
    user_skills = set(skill.strip().lower() for skill in criteria.skills.split(','))
    
    # Process each job
    relevant_jobs = []
    for job in jobs:
        try:
            # Extract and clean job description
            description = job.get("description", "").lower()
            if not description and "full_details" in job:
                description = job["full_details"].lower()
            
            # Basic relevance score calculation
            relevance_score = calculate_basic_relevance(job, criteria, user_skills)
            print(f"Basic relevance score for {job.get('job_title', 'Unknown')}: {relevance_score}")
            
            # For jobs with moderate to high basic relevance, use LLM for deeper analysis
            if relevance_score >= 0.3:  # Lowered threshold to include more jobs
                llm_relevance = analyze_with_llm(job, criteria)
                print(f"LLM relevance score for {job.get('job_title', 'Unknown')}: {llm_relevance}")
                # Combine basic and LLM relevance scores with more weight on LLM analysis
                final_relevance = (relevance_score * 0.3) + (llm_relevance * 0.7)
            else:
                final_relevance = relevance_score
            
            # Add relevance score to job
            job["relevance_score"] = round(final_relevance, 2)
            print(f"Final relevance score for {job.get('job_title', 'Unknown')}: {final_relevance}")
            
            # Filter out jobs with very low relevance
            if final_relevance >= 0.3:  # Lowered threshold to include more jobs
                # Standardize job format and fill missing fields using LLM
                standardized_job = standardize_job_format(job, criteria)
                relevant_jobs.append(standardized_job)
                print(f"Added job {standardized_job['job_title']} to relevant jobs")
            else:
                print(f"Job {job.get('job_title', 'Unknown')} filtered out due to low relevance")
                
        except Exception as e:
            print(f"Error analyzing job {job.get('job_title', 'Unknown')}: {str(e)}")
            continue
    
    print(f"Found {len(relevant_jobs)} relevant jobs")
    return relevant_jobs

def calculate_basic_relevance(job, criteria, user_skills):
    """
    Calculate basic relevance score based on keyword matching
    """
    score = 0.0
    
    # Job title relevance (highest weight)
    job_title = job.get("job_title", "").lower()
    if criteria.position.lower() in job_title:
        score += 0.3
        print(f"Title match for {job_title}")
    
    # Location match
    job_location = job.get("location", "").lower()
    criteria_location = criteria.location.lower()
    if criteria_location.split(',')[0].strip() in job_location:
        score += 0.1
        print(f"Location match for {job_location}")
    
    # Job nature match
    job_nature = job.get("jobNature", "").lower()
    if criteria.jobNature.lower() in job_nature:
        score += 0.1
        print(f"Job nature match for {job_nature}")
    
    # Experience match - convert to years for comparison
    job_exp = job.get("experience", "").lower()
    criteria_exp = criteria.experience.lower()
    
    # Extract numbers from experience strings
    import re
    job_exp_years = re.findall(r'\d+', job_exp)
    criteria_exp_years = re.findall(r'\d+', criteria_exp)
    
    if job_exp_years and criteria_exp_years:
        job_years = int(job_exp_years[0])
        criteria_years = int(criteria_exp_years[0])
        # If job experience is within 1 year of criteria
        if abs(job_years - criteria_years) <= 1:
            score += 0.1
            print(f"Experience match: {job_years} years")
    
    # Skills match from description
    description = job.get("description", "").lower()
    if not description and "full_details" in job:
        description = job["full_details"].lower()
    
    skill_matches = sum(1 for skill in user_skills if skill in description)
    skill_score = min(0.4, skill_matches * 0.05)  # Cap at 0.4
    score += skill_score
    if skill_matches > 0:
        print(f"Found {skill_matches} skill matches")
    
    return min(1.0, score)  # Cap at 1.0

def analyze_with_llm(job, criteria):
    """
    Use Gemini to analyze job relevance in greater depth using complete job details
    Handles different job source formats (Indeed, Rozee, LinkedIn)
    """
    try:
        # Extract and normalize job information based on source
        source = job.get('source', '').lower()
        
        # Common fields that should be present in all sources
        job_details = {
            "title": job.get('job_title', ''),
            "company": job.get('company', ''),
            "location": job.get('location', ''),
            "salary": job.get('salary', ''),
            "description": job.get('description', ''),
            "experience": job.get('experience', ''),
            "job_nature": job.get('jobNature', ''),
            "source": source
        }

        # Source-specific fields
        if source == 'rozee.pk':
            job_details.update({
                "full_details": job.get('full_details', ''),
                "industry": job.get('industry', ''),
                "functional_area": job.get('functional_area', ''),
                "total_positions": job.get('total_positions', ''),
                "job_shift": job.get('job_shift', ''),
                "job_type": job.get('job_type', ''),
                "gender": job.get('gender', ''),
                "minimum_education": job.get('minimum_education', ''),
                "career_level": job.get('career_level', ''),
                "experience": job.get('experience', ''),
                "apply_before": job.get('apply_before', ''),
                "posting_date": job.get('posting_date', '')
            })
        elif source == 'indeed':
            # Indeed specific fields
            job_details.update({
                "job_type": job.get('job_type', ''),
                "posted_date": job.get('posted_date', ''),
                "company_rating": job.get('company_rating', ''),
                "company_reviews": job.get('company_reviews', ''),
                "benefits": job.get('benefits', []),
                "qualifications": job.get('qualifications', ''),
                "responsibilities": job.get('responsibilities', '')
            })
        elif source == 'linkedin':
            # LinkedIn specific fields
            job_details.update({
                "employment_type": job.get('employment_type', ''),
                "seniority_level": job.get('seniority_level', ''),
                "industry": job.get('industry', ''),
                "job_function": job.get('job_function', ''),
                "posted_date": job.get('posted_date', ''),
                "applicants": job.get('applicants', ''),
                "company_size": job.get('company_size', ''),
                "company_industry": job.get('company_industry', '')
            })

        # Build a comprehensive prompt for the LLM
        prompt = f"""
        Analyze how relevant this job is to the candidate's criteria. Consider all aspects of the job and candidate's requirements.
        Score from 0.0 (not relevant) to 1.0 (perfect match).

        CANDIDATE CRITERIA:
        - Position: {criteria.position}
        - Experience: {criteria.experience}
        - Salary: {criteria.salary}
        - Job Nature: {criteria.jobNature}
        - Location: {criteria.location}
        - Skills: {criteria.skills}

        JOB DETAILS:
        - Title: {job_details['title']}
        - Company: {job_details['company']}
        - Location: {job_details['location']}
        - Salary: {job_details['salary']}
        - Experience Required: {job_details['experience']}
        - Job Nature: {job_details['job_nature']}
        - Source: {job_details['source']}
        """

        # Add source-specific details to the prompt
        if source == 'rozee.pk':
            prompt += f"""
            ADDITIONAL DETAILS (Rozee):
            - Industry: {job_details['industry']}
            - Functional Area: {job_details['functional_area']}
            - Total Positions: {job_details['total_positions']}
            - Job Shift: {job_details['job_shift']}
            - Job Type: {job_details['job_type']}
            - Gender: {job_details['gender']}
            - Minimum Education: {job_details['minimum_education']}
            - Career Level: {job_details['career_level']}
            - Experience: {job_details['experience']}
            - Apply Before: {job_details['apply_before']}
            - Posted Date: {job_details['posting_date']}
            - Full Details: {job_details['full_details']}
            """
        elif source == 'indeed':
            prompt += f"""
            ADDITIONAL DETAILS (Indeed):
            - Job Type: {job_details['job_type']}
            - Posted Date: {job_details['posted_date']}
            - Company Rating: {job_details['company_rating']}
            - Company Reviews: {job_details['company_reviews']}
            - Benefits: {', '.join(job_details['benefits']) if isinstance(job_details['benefits'], list) else job_details['benefits']}
            - Qualifications: {job_details['qualifications']}
            - Responsibilities: {job_details['responsibilities']}
            """
        elif source == 'linkedin':
            prompt += f"""
            ADDITIONAL DETAILS (LinkedIn):
            - Employment Type: {job_details['employment_type']}
            - Seniority Level: {job_details['seniority_level']}
            - Industry: {job_details['industry']}
            - Job Function: {job_details['job_function']}
            - Posted Date: {job_details['posted_date']}
            - Applicants: {job_details['applicants']}
            - Company Size: {job_details['company_size']}
            - Company Industry: {job_details['company_industry']}
            """

        prompt += """
        Please analyze the following aspects:
        1. Position match (title and responsibilities)
        2. Experience level compatibility
        3. Location match
        4. Skills match
        5. Job nature alignment
        6. Salary expectations
        7. Education and career level fit
        8. Overall suitability

        Output only a number between 0.0 and 1.0 representing the overall relevance score.
        """

        # Call Gemini API with the correct model
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        result = response.text.strip()

        try:
            relevance_score = float(result)
            return max(0.0, min(1.0, relevance_score))
        except ValueError:
            logger.error(f"Failed to parse Gemini relevance score: {result}")
            return 0.5

    except Exception as e:
        logger.error(f"Error in Gemini relevance analysis: {str(e)}")
        return 0.5

def standardize_job_format(job: Dict[str, Any], criteria) -> Dict[str, Any]:
    """
    Standardize job format and fill missing fields using LLM
    """
    # Initialize standardized job with required fields
    standardized_job = {
        "job_title": job.get("job_title", ""),
        "company": job.get("company", ""),
        "experience": job.get("experience", ""),
        "jobNature": job.get("jobNature", ""),
        "location": job.get("location", ""),
        "salary": job.get("salary", ""),
        "apply_link": job.get("apply_link", ""),
        "relevance_score": job.get("relevance_score", 0.0)
    }
    
    # Check for missing or unspecified fields
    missing_fields = [field for field, value in standardized_job.items() 
                     if not value or value == "Not specified" or value == "N/A" or value == "Not Specified"]
    
    if missing_fields:
        logger.info(f"Missing fields for job {job.get('job_title', 'Unknown')}: {missing_fields}")
        # Use LLM to fill missing fields
        filled_fields = fill_missing_fields_with_llm(job, missing_fields)
        standardized_job.update(filled_fields)
        logger.info(f"Filled missing fields: {filled_fields}")
    
    return standardized_job

def fill_missing_fields_with_llm(job: Dict[str, Any], missing_fields: List[str]) -> Dict[str, Any]:
    """
    Use LLM to fill missing fields based on job description and details
    """
    try:
        # Prepare job details for LLM
        job_details = {
            "title": job.get("job_title", ""),
            "company": job.get("company", ""),
            "description": job.get("description", ""),
            "full_details": job.get("full_details", ""),
            "source": job.get("source", ""),
            "job_type": job.get("job_type", ""),
            "employment_type": job.get("employment_type", ""),
            "seniority_level": job.get("seniority_level", ""),
            "location": job.get("location", ""),
            "salary": job.get("salary", ""),
            "experience": job.get("experience", ""),
            "skills": job.get("skills", []),
            "posted_date": job.get("posted_date", ""),
            # Add Rozee-specific fields
            "industry": job.get("industry", ""),
            "functional_area": job.get("functional_area", ""),
            "total_positions": job.get("total_positions", ""),
            "job_shift": job.get("job_shift", ""),
            "gender": job.get("gender", ""),
            "minimum_education": job.get("minimum_education", ""),
            "career_level": job.get("career_level", ""),
            "apply_before": job.get("apply_before", "")
        }
        
        # Build prompt for LLM
        prompt = f"""
        Based on the following job details, fill in the missing fields: {', '.join(missing_fields)}.
        Only output the missing fields in JSON format.
        
        Job Details:
        {json.dumps(job_details, indent=2)}
        
        For each missing field, provide the most accurate information based on the available details.
        If information cannot be determined, use "Not specified".
        
        Guidelines for each field:
        - job_title: Extract from title or description if missing
        - company: Extract from company name or description
        - experience: Look for phrases like "X years experience" or "entry level"
        - jobNature: Look for terms like "onsite", "remote", "hybrid"
        - location: Extract from location field or description
        - salary: Look for salary ranges or compensation information
        - apply_link: Use the job URL if available
        
        Output format should be a JSON object with only the missing fields.
        Do not include any markdown formatting or code blocks.
        """
        
        # Call Gemini API
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Clean the response to remove any markdown formatting
        result = result.replace("```json", "").replace("```", "").strip()
        
        # Parse LLM response
        try:
            filled_fields = json.loads(result)
            logger.info(f"Successfully filled fields: {filled_fields}")
            return filled_fields
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {result}")
            logger.error(f"JSON decode error: {str(e)}")
            return {field: "Not specified" for field in missing_fields}
            
    except Exception as e:
        logger.error(f"Error filling missing fields with LLM: {str(e)}")
        return {field: "Not specified" for field in missing_fields}
