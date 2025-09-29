from datetime import datetime, timedelta
import re
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random

# ========== 🔧 SETUP FUNCTION ========== 
def clean_text(text):
    if not isinstance(text, str):
        return text
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

# ========== 🚀 SETUP SELENIUM ========== 
option = webdriver.ChromeOptions()
option.add_argument('--incognito')
option.add_argument('--start-maximized')
option.add_argument('--disable-gpu')
option.add_argument('--no-sandbox')
option.add_argument('--headless')  # Set False jika ingin lihat browser

driver = webdriver.Chrome(options=option)
driver.implicitly_wait(10)

# ========== ⚙️ KONFIGURASI ========== 
FILTER_BY = 'pages'  # Pilih 'date', 'days_ago', atau 'pages'
START_DATE = datetime(2025, 1, 1)  # Opsi jika FILTER_BY = 'date'
MAX_DAYS_AGO = 30  # Opsi jika FILTER_BY = 'days_ago'
MAX_PAGES = 1  # Opsi jika FILTER_BY = 'pages'
roles = ["Data Analyst", "Data Engineer"]
results = []

# Retry logic helper function
def safe_get_page(url, retries=3, delay=5):
    """
    Attempts to fetch the page multiple times with a delay between retries.
    If it fails after the retries, it will raise the last encountered exception.
    """
    attempt = 0
    while attempt < retries:
        try:
            driver.get(url)
            time.sleep(5)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            return driver.page_source
        except Exception as e:
            attempt += 1
            print(f"⚠️ Error on attempt {attempt} for {url}: {e}")
            if attempt < retries:
                print(f"⏳ Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise  # Raise the exception if retries are exhausted

# ========== 🔁 SCRAPING LOOP ========== 
for role in roles:
    role_url = role.replace(" ", "-").lower()

    # Handle pages filter
    if FILTER_BY == 'pages':
        page_limit = MAX_PAGES  # Limit pages based on MAX_PAGES
    else:
        page_limit = 100  # We will fetch up to 100 pages by default for date or days_ago

    page = 1
    while page <= page_limit:  # Continue until we reach the condition to stop
        url = f"https://id.jobstreet.com/id/{role_url}-jobs?page={page}&sortmode=ListedDate"
        print(f"\n📄 Scraping page {page} for role: {role}...")

        try:
            page_source = safe_get_page(url)  # Try to get the page with retry logic
        except Exception as e:
            print(f"🛑 Failed to retrieve page {page} for {role} after multiple attempts. Skipping this page.")
            break  # Stop scraping this page and move to the next one

        soup = BeautifulSoup(page_source, 'html.parser')
        jobs = soup.find_all('article', {'data-automation': 'normalJob'})
        print(f"🔍 Found {len(jobs)} job cards on page {page}.")

        # If no jobs found, break out of the loop
        if not jobs:
            print(f"🛑 No jobs found on page {page}. Stopping scraping.")
            break

        page_has_valid_jobs = False  # Flag to check if any valid job exists on this page

        for job in jobs:
            try:
                title_tag = job.find('a', {'data-automation': 'jobTitle'})
                title = title_tag.text.strip() if title_tag else 'NaN'
                job_url = 'https://id.jobstreet.com' + title_tag['href'] if title_tag else 'NaN'

                posted_tag = job.find('span', {'data-automation': 'jobListingDate'})
                posted_text = posted_tag.text.strip().lower() if posted_tag else 'tidak diketahui'

                # ========== Handle cases like "30+ hari yang lalu" ========== 
                if 'hari' in posted_text:
                    match = re.search(r'(\d+)\+?', posted_text)
                    if match:
                        posted_days_ago = int(match.group(1))  # Extract the number of days
                        if '+' in match.group(0):  # If there's a "+" we treat it as more than 30 days
                            posted_days_ago = 31  # Set to 31 because it's beyond the 30-day limit
                    else:
                        posted_days_ago = -1
                elif 'menit' in posted_text or 'jam' in posted_text:
                    posted_days_ago = 0
                else:
                    posted_days_ago = -1

                # ========== Handle FILTER_BY = 'days_ago' ========== 
                if FILTER_BY == 'days_ago' and MAX_DAYS_AGO and posted_days_ago > MAX_DAYS_AGO:
                    print(f"🛑 Skipping {title} karena sudah diposting lebih dari {MAX_DAYS_AGO} hari.")
                    continue

                # ========== Handle FILTER_BY = 'date' ========== 
                if FILTER_BY == 'date':
                    if posted_days_ago == 31:  # If it's more than 30 days, still keep it
                        print(f"✅ Keeping {title} (posted more than 30 days).")
                    else:
                        posted_date = (datetime.today() - timedelta(days=posted_days_ago)).strftime('%Y-%m-%d') if posted_days_ago >= 0 else 'Unknown'

                        try:
                            posted_date_obj = datetime.strptime(posted_date, '%Y-%m-%d')
                        except ValueError:
                            posted_date_obj = None  # If can't parse the date, set it to None

                        if posted_date_obj and posted_date_obj < START_DATE:
                            print(f"🛑 Skipping {title} karena diposting sebelum {START_DATE.strftime('%Y-%m-%d')}.")
                            continue

                posted_date = (datetime.today() - timedelta(days=posted_days_ago)).strftime('%Y-%m-%d') if posted_days_ago >= 0 else 'Unknown'

                # GET JOB DETAIL
                try:
                    driver.get(job_url)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1[data-automation="job-detail-title"]')))
                    time.sleep(2)
                    detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                except Exception as e:
                    print(f"❌ Failed to load job details for {title}: {e}")
                    continue

                title = detail_soup.select_one('h1[data-automation="job-detail-title"]').get_text(strip=True)
                company_tag = detail_soup.select_one('span[data-automation="advertiser-name"]')
                company = company_tag.get_text(strip=True) if company_tag else 'NaN'

                location_tag = detail_soup.select_one('span[data-automation="job-detail-location"]')
                location = location_tag.get_text(strip=True) if location_tag else 'NaN'

                salary_tag = detail_soup.select_one('span[data-automation="job-detail-salary"]')
                salary = salary_tag.get_text(strip=True) if salary_tag else 'NaN'

                job_type_tag = detail_soup.select_one('span[data-automation="job-detail-work-type"]')
                job_type = job_type_tag.get_text(strip=True) if job_type_tag else 'NaN'

                description_tag = detail_soup.select_one('div[data-automation="jobAdDetails"]')
                description_text = description_tag.get_text(separator='\n').strip() if description_tag else 'No description available'

                job_info = {
                    'role': role,
                    'title': title,
                    'company': company,
                    'location': location,
                    'salary': salary,
                    'link': job_url,
                    'description': description_text,
                    'job_type': job_type,
                    'posted_date': posted_date
                }

                results.append(job_info)
                print(f"✅ Scraped: {title} | {company} | {posted_days_ago} hari lalu")

                page_has_valid_jobs = True  # Mark that we found at least one valid job on this page

            except Exception as e:
                print(f"❌ Failed to process a job: {e}")
                continue

        # If no valid jobs were found on this page, stop the loop
        if not page_has_valid_jobs:
            print(f"🛑 No valid jobs found on page {page}. Stopping scraping.")
            break

        page += 1  # Move to the next page if valid jobs were found

    # ========== 📦 SIMPAN HASIL PER ROLE ========== 
    df_role = pd.DataFrame([job for job in results if job['role'] == role])

    # Remove duplicate rows (completely identical rows)
    df_role.drop_duplicates(subset=df_role.columns, keep='first', inplace=True)

    if not df_role.empty:
        # Save the data for each role
        save_folder = 'scraped_data'
        os.makedirs(save_folder, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        csv_filename = os.path.join(save_folder, f'jobstreet_{role_url}_details_{timestamp}.csv')
        excel_filename = os.path.join(save_folder, f'jobstreet_{role_url}_details_{timestamp}.xlsx')

        df_role.to_csv(csv_filename, index=False)
        df_role.to_excel(excel_filename, index=False)

        print(f"\n📁 Saved {len(df_role)} jobs for '{role}' to '{csv_filename}' and '{excel_filename}'.")
    else:
        print(f"🚫 No jobs found for role '{role}'.")

# Finish up the driver
driver.quit()
print("✅ Selesai scraping semua role.")
