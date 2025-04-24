# job_sources/rozee.py
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
from urllib.parse import quote
import traceback
import re
from concurrent.futures import ThreadPoolExecutor
import logging
from config import JOBS_PER_SOURCE
import json

# Configure Rozee-specific logging
rozee_logger = logging.getLogger('rozee')
rozee_logger.setLevel(logging.INFO)
rozee_handler = logging.FileHandler('rozee_raw.log')
rozee_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
rozee_logger.addHandler(rozee_handler)

async def fetch_rozee_jobs(criteria):
    """
    Fetch jobs from Rozee.pk using Selenium for web scraping, including details.
    """
    rozee_logger.info(f"Fetching Rozee.pk jobs for {criteria.position} in {criteria.location}")
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_rozee_jobs_sync, criteria)

def _fetch_rozee_jobs_sync(criteria):
    """
    Synchronous function to fetch Rozee.pk jobs using Selenium, clicking for details.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")

    # Performance optimizations
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.images": 2,  # Disable images
        "profile.managed_default_content_settings.javascript": 1,  # Enable JavaScript
        "profile.managed_default_content_settings.cookies": 1,  # Enable cookies
        "profile.managed_default_content_settings.plugins": 2,  # Disable plugins
        "profile.managed_default_content_settings.popups": 2,  # Disable popups
        "profile.managed_default_content_settings.geolocation": 2,  # Disable geolocation
        "profile.managed_default_content_settings.media_stream": 2,  # Disable media stream
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)  # Set page load timeout
    driver.implicitly_wait(5)  # Reduced implicit wait
    wait = WebDriverWait(driver, 10)  # Reduced explicit wait

    try:
        # Navigation and City Selection
        city = criteria.location.split(',')[0].strip()
        position_query = quote(criteria.position)
        rozee_url = f"https://www.rozee.pk/job/jsearch/q/{position_query}"
        rozee_logger.info(f"Navigating to Rozee.pk URL: {rozee_url}")
        driver.get(rozee_url)

        try:
            select_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-control.w-100")))
            select = Select(select_element)
            rozee_logger.info(f"Selecting city: {city}")
            select.select_by_visible_text(city)
        except Exception as city_select_error:
            rozee_logger.warning(f"Could not select city '{city}'. Error: {city_select_error}. Proceeding without city filter.")

        # Wait for job list to load
        wait_selector = "div#jobs > div.job div.jhead div.jobt h3.s-18 a"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector)))

        # Find job cards
        card_selector = "div#jobs > div.job"
        job_cards = driver.find_elements(By.CSS_SELECTOR, card_selector)
        rozee_logger.info(f"Found {len(job_cards)} potential job cards.")

        jobs = []
        processed_urls = set()

        # Process only the configured number of cards
        for i in range(min(len(job_cards), JOBS_PER_SOURCE)):
            try:
                job = process_job_card(driver, job_cards[i], i, criteria, processed_urls)
                if job:
                    jobs.append(job)
            except Exception as e:
                rozee_logger.error(f"Error processing job card {i + 1}: {str(e)}")
                continue

        # Log raw Rozee jobs
        rozee_logger.info("Raw Rozee Jobs:")
        rozee_logger.info(json.dumps(jobs, indent=2))

        rozee_logger.info(f"Finished processing. Found {len(jobs)} valid Rozee.pk jobs with details.")
        return jobs

    except Exception as e:
        rozee_logger.error(f"MAJOR ERROR during Rozee.pk job fetch: {str(e)}")
        rozee_logger.error("Full Traceback:", exc_info=True)
        return []

    finally:
        rozee_logger.info("Closing Rozee.pk WebDriver.")
        if 'driver' in locals() and driver:
            driver.quit()

def process_job_card(driver, card, index, criteria, processed_urls):
    """Process a single job card and extract its details"""
    try:
        # Extract basic info
        job_title_elem = card.find_element(By.CSS_SELECTOR, "div.jhead div.jobt h3.s-18")
        job_title = job_title_elem.get_attribute("title") or job_title_elem.text.strip()

        job_link_elem = job_title_elem.find_element(By.CSS_SELECTOR, "a")
        job_link = job_link_elem.get_attribute("href")

        if job_link in processed_urls:
            return None

        company_location_container = card.find_element(By.CSS_SELECTOR, "div.jhead div.cname bdi")
        company_location_parts = [a.text.strip() for a in company_location_container.find_elements(By.TAG_NAME, "a")]
        company = company_location_parts[0].rstrip(',') if company_location_parts else "N/A"
        location = " ".join(company_location_parts[1:]).lstrip(', ') if len(company_location_parts) > 1 else criteria.location

        # Get salary if available
        salary = "Not Specified"
        try:
            # First try to get salary from the job header
            salary_div = driver.find_element(By.CSS_SELECTOR, "div.mrsl.float-left.mt5.ofa.nrs-18")
            if salary_div:
                salary = salary_div.text.strip()
        except NoSuchElementException:
            try:
                # Try to get salary from the job card
                salary_div = card.find_element(By.CSS_SELECTOR, "div.mrsl")
                if salary_div:
                    salary = salary_div.text.strip()
            except NoSuchElementException:
                pass

        # Click to view details
        click_target = card.find_element(By.CSS_SELECTOR, "div.jhead div.jobt h3.s-18 a")
        click_target.click()
        processed_urls.add(job_link)

        # Wait for job details to load
        wait = WebDriverWait(driver, 5)
        detail_container = wait.until(EC.visibility_of_element_located((By.ID, "job-content")))
        
        # Get full job description and details
        full_details = ""
        try:
            # Get job description
            desc_section = detail_container.find_element(By.XPATH, ".//h3[text()='Job Description']/following-sibling::div[1]")
            if desc_section:
                full_details += "Job Description:\n" + desc_section.text.strip() + "\n\n"
        except NoSuchElementException:
            pass

        try:
            # Get job skills
            skills_section = detail_container.find_element(By.XPATH, ".//h4[text()='Job Skills']/following-sibling::div[1]")
            if skills_section:
                full_details += "Job Skills:\n" + skills_section.text.strip() + "\n\n"
        except NoSuchElementException:
            pass

        # Extract structured job details
        job_details = {}
        try:
            # Find the job details section using the correct class
            details_section = detail_container.find_element(By.CSS_SELECTOR, "div.jblk h4.nrs-18 + div.jcnt.jobd")
            if details_section:
                # Find all rows in the details section
                rows = details_section.find_elements(By.CSS_SELECTOR, "div.row")
                for row in rows:
                    try:
                        # Get the label (first column)
                        label_elem = row.find_element(By.CSS_SELECTOR, "div.col-lg-3")
                        label = label_elem.text.strip().rstrip(':')
                        
                        # Get the value (second column)
                        value_elem = row.find_element(By.CSS_SELECTOR, "div.col-lg-7")
                        # Get text from all elements in the value column
                        value_parts = []
                        for elem in value_elem.find_elements(By.CSS_SELECTOR, "*"):
                            if elem.tag_name == "a":
                                value_parts.append(elem.text.strip())
                            else:
                                value_parts.append(elem.text.strip())
                        value = " ".join(filter(None, value_parts))
                        
                        # Store in job_details
                        job_details[label] = value
                    except NoSuchElementException:
                        continue
        except NoSuchElementException:
            pass

        # Check if apply button exists
        apply_button_found = False
        try:
            apply_button = driver.find_element(By.CSS_SELECTOR, "a.btn-applyJb")
            apply_button_found = apply_button.is_displayed()
        except NoSuchElementException:
            pass

        # Create simplified job object with complete details
        job = {
            "job_title": job_title,
            "company": company,
            "location": location,
            "salary": salary,
            "apply_link": job_link if job_link else "N/A",
            "apply_button_present": apply_button_found,
            "source": "Rozee.pk",
            "description_snippet": card.find_element(By.CSS_SELECTOR, "div.jbody bdi").text.strip(),
            "full_details": full_details,
            # Add structured job details
            "industry": job_details.get("Industry", "Not specified"),
            "functional_area": job_details.get("Functional Area", "Not specified"),
            "total_positions": job_details.get("Total Positions", "Not specified"),
            "job_shift": job_details.get("Job Shift", "Not specified"),
            "job_type": job_details.get("Job Type", "Not specified"),
            "gender": job_details.get("Gender", "Not specified"),
            "minimum_education": job_details.get("Minimum Education", "Not specified"),
            "career_level": job_details.get("Career Level", "Not specified"),
            "experience": job_details.get("Experience", "Not specified"),
            "apply_before": job_details.get("Apply Before", "Not specified"),
            "posting_date": job_details.get("Posting Date", "Not specified")
        }

        rozee_logger.info(f"Successfully processed job card {index + 1}: {job_title}")
        return job

    except Exception as e:
        rozee_logger.error(f"Error processing card {index + 1}: {str(e)}")
        return None