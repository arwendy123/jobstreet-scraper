from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import time

# Setup Selenium Chrome driver
option = webdriver.ChromeOptions()
option.add_argument("--start-maximized")
option.add_argument("--disable-gpu")
option.add_argument("--no-sandbox")
# option.add_argument("--headless")  # Gunakan ini jika tidak ingin browser terbuka

driver = webdriver.Chrome(options=option)

MAX_PAGES = 3
roles = ["Data Science"]
sorted_once = False

for role in roles:
    role_url = role.replace(" ", "-").lower()
    results = []

    for page in range(1, MAX_PAGES + 1):
        url = f"https://id.jobstreet.com/id/{role_url}-jobs?page={page}"
        print(f"📄 Scraping page {page} for role: {role}...")
        driver.get(url)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ube6hn0")))
        time.sleep(2)

        if not sorted_once:
            try:
                sort_button = driver.find_element(By.ID, 'sorted-by')
                sort_button.click()
                time.sleep(1)
                tanggal_button = driver.find_element(By.XPATH, "//span[text()='Tanggal']")
                tanggal_button.click()
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'czgzl04')))
                time.sleep(2)
                sorted_once = True
                print("✅ Sorted by date.")
            except Exception as e:
                print(f"❌ Sorting error: {e}")

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

                company_tag = job.find('a', {'data-automation': 'jobCompany'})
                company = company_tag.text.strip() if company_tag else 'NaN'

                location_tag = job.find('span', {'data-automation': 'jobLocation'})
                location = location_tag.text.strip() if location_tag else 'NaN'

                salary_tag = job.find('span', {'data-automation': 'jobSalary'})
                salary = salary_tag.text.strip() if salary_tag else 'NaN'

                # Ambil info tanggal posting
                posted_tag = job.find('span', {'data-automation': 'jobListingDate'})
                posted_text = posted_tag.text.strip().lower() if posted_tag else 'tidak diketahui'

                if 'menit' in posted_text or 'jam' in posted_text:
                    posted_days_ago = 0
                elif 'hari' in posted_text:
                    try:
                        posted_days_ago = int(posted_text.split()[0])
                    except:
                        posted_days_ago = 30  # default untuk "30+ hari"
                else:
                    posted_days_ago = -1  # tidak diketahui

                # Optionally konversi ke tanggal
                try:
                    posted_date = (datetime.today() - timedelta(days=posted_days_ago)).strftime('%Y-%m-%d')
                except:
                    posted_date = 'Unknown'

                # Buka halaman detail
                driver.get(job_url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1[data-automation="job-detail-title"]')))
                time.sleep(2)

                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

                description_tag = detail_soup.select_one('div[data-automation="jobAdDetails"]')
                description_text = description_tag.get_text(separator='\n').strip() if description_tag else 'No description available'

                company_profile_tag = detail_soup.select_one('div[data-automation="company-profile"]')
                company_profile_text = company_profile_tag.get_text(separator='\n').strip() if company_profile_tag else 'No company profile available'

                job_type_tag = detail_soup.select_one('span[data-automation="job-detail-work-type"]')
                job_type = job_type_tag.text.strip() if job_type_tag else 'NaN'

                job_info = {
                    'role': role,
                    'title': title,
                    'company': company,
                    'location': location,
                    'salary': salary,
                    'link': job_url,
                    'description': description_text,
                    'company_profile': company_profile_text,
                    'job_type': job_type,
                    'posted_days_ago': posted_days_ago,
                    'posted_date': posted_date,
                }

                results.append(job_info)
                print(f"✅ Scraped: {title} | {company} | {posted_days_ago} hari lalu")

            except Exception as e:
                print(f"❌ Failed to process a job: {e}")
                continue

    # Simpan hasil ke CSV dan Excel
    df_job = pd.DataFrame(results)
    csv_filename = f'jobstreet_{role_url}_details.csv'
    excel_filename = f'jobstreet_{role_url}_details.xlsx'

    df_job.to_csv(csv_filename, index=False)
    df_job.to_excel(excel_filename, index=False)

    print(f"📁 Saved to '{csv_filename}' and '{excel_filename}'.")


driver.quit()
print("\n✅ Selesai scraping semua role.")
