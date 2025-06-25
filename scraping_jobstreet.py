from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

# Setting up the Chrome Driver
option = webdriver.ChromeOptions()
option.add_argument("--start-maximized")
option.add_argument("--headless")  # Uncomment if you want headless mode
option.add_argument("--disable-gpu")
option.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=option)

# List to store the results
MAX_PAGES = 5  # Maximal pages to scrape

# List of roles to scrape (with spaces for flexibility)
roles = ["Data Analyst", "System Analyst"]

for role in roles:
    # Convert the role with spaces to URL-friendly format by replacing spaces with dashes
    role_url = role.replace(" ", "-").lower()  # Convert spaces to dashes for the URL
    
    results = []  # List to store the result for this role

    for page in range(1, MAX_PAGES + 1):
        url = f"https://id.jobstreet.com/id/{role_url}-jobs?page={page}"  # URL with dynamic role
        print(f"📄 Scraping page {page} for role: {role}...")

        driver.get(url)
        
        # Wait for the page to load and become ready
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "xhgj00")))
        
        # Scroll to End Content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait a bit after scrolling
        
        # Parse page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        jobs = soup.find_all('article', class_="xhgj00")

        for job in jobs:
            # Extract job title
            title_tag = job.find('a', {'data-automation': 'jobTitle'})
            title = title_tag.text.strip() if title_tag else 'NaN'
            print(title)
            
            # Extract company
            company_tag = job.find('a', {'data-automation': 'jobCompany'})
            company = company_tag.text.strip() if company_tag else 'NaN'
            
            # Extract location
            location_tag = job.find('span', {'data-automation': 'jobCardLocation'})
            location = location_tag.text.strip() if location_tag else 'NaN'
            
            # Extract salary
            salary_tag = job.find('span', {'data-automation': 'jobSalary'})
            salary = salary_tag.text.strip() if salary_tag else 'NaN'
            
            # Extract job link
            link_tag = job.find('a', {'data-automation': 'job-list-view-job-link'})
            job_url = 'https://id.jobstreet.com' + link_tag['href'] if link_tag and link_tag.has_attr('href') else 'NaN'
            
            # Visit job details page
            driver.get(job_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "xhgj00")))

            # Parse the job detail page
            detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract job description, requirements, etc.
            description = detail_soup.find('section', {'data-automation': 'jobAdDetails'})
            description_text = description.get_text(strip=True) if description else 'No description available'
            
            # Extract questions (if any)
            questions_section = detail_soup.find('section', {'class': 'xhgj00 xhgj01'})
            questions_text = questions_section.get_text(strip=True) if questions_section else 'No questions available'
            
            # Store job information with the role information
            job_info = {
                'role': role,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'link': job_url,
                'description': description_text,
                'questions': questions_text
            }
            results.append(job_info)
    
    # After collecting all pages for this role, save to CSV
    df_job = pd.DataFrame(results)
    df_job.to_csv(f'jobstreet_{role_url}_details.csv', index=False)  # Save as CSV per role
    print(f"✅ Data for role {role} saved to 'jobstreet_{role_url}_details.csv'.")

driver.quit()

print("\n✅ Scraping completed for all roles.")
