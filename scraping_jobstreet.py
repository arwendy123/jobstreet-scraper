from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import time
import re
import os

# ========== 🔧 SETUP FUNCTION ==========
def clean_text(text):
    if not isinstance(text, str):
        return text
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

def clean_description(text):
    if not isinstance(text, str):
        return text
    text = re.sub(r'(?i)\b(responsibilities|job descriptions?|requirements|qualifications)\s*[:\-–]*\s*', '', text)
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

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
MAX_DAYS_AGO = 30
MAX_PAGES = 1
roles = ["Research Analyst"]
results = []

# ========== 🔁 SCRAPING LOOP ==========
for role in roles:
    role_url = role.replace(" ", "-").lower()

    for page in range(1, MAX_PAGES + 1):
        url = f"https://id.jobstreet.com/id/{role_url}-jobs?page={page}&sortmode=ListedDate"
        print(f"\n📄 Scraping page {page} for role: {role}...")

        driver.get(url)
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        jobs = soup.find_all('article', {'data-automation': 'normalJob'})
        print(f"🔍 Found {len(jobs)} job cards.")

        for job in jobs:
            try:
                title_tag = job.find('a', {'data-automation': 'jobTitle'})
                title = title_tag.text.strip() if title_tag else 'NaN'
                job_url = 'https://id.jobstreet.com' + title_tag['href'] if title_tag else 'NaN'

                posted_tag = job.find('span', {'data-automation': 'jobListingDate'})
                posted_text = posted_tag.text.strip().lower() if posted_tag else 'tidak diketahui'

                if 'menit' in posted_text or 'jam' in posted_text:
                    posted_days_ago = 0
                elif 'hari' in posted_text:
                    try:
                        posted_days_ago = int(re.search(r'\d+', posted_text).group())
                    except:
                        posted_days_ago = 30
                else:
                    posted_days_ago = -1

                if MAX_DAYS_AGO and posted_days_ago > MAX_DAYS_AGO:
                    print(f"🛑 Skipping {title} karena sudah diposting lebih dari {MAX_DAYS_AGO} hari.")
                    continue

                posted_date = (datetime.today() - timedelta(days=posted_days_ago)).strftime('%Y-%m-%d') if posted_days_ago >= 0 else 'Unknown'

                # GET JOB DETAIL
                driver.get(job_url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1[data-automation="job-detail-title"]')))
                time.sleep(2)
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

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
                raw_desc = description_tag.get_text(separator='\n').strip() if description_tag else 'No description available'
                description_text = clean_description(clean_text(raw_desc))

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

            except Exception as e:
                print(f"❌ Failed to process a job: {e}")
                continue

# ========== 📦 SIMPAN HASIL ==========
df_job = pd.DataFrame(results)
df_job.drop_duplicates(subset=['title', 'company', 'location'], inplace=True)

save_folder = 'scraped_data'
os.makedirs(save_folder, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

csv_filename = os.path.join(save_folder, f'jobstreet_{role_url}_details_{timestamp}.csv')
excel_filename = os.path.join(save_folder, f'jobstreet_{role_url}_details_{timestamp}.xlsx')

df_job.to_csv(csv_filename, index=False)
df_job.to_excel(excel_filename, index=False)

print(f"\n📁 Saved to '{csv_filename}' and '{excel_filename}'.")
driver.quit()
print("✅ Selesai scraping semua role.")
