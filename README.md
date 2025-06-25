# Jobstreet Scraper

The JobStreet Job Scraper project focuses on automating the process of gathering job listings from JobStreet Indonesia. By utilizing web scraping techniques, the project aims to collect detailed information about job vacancies, including job titles, companies, locations, salaries, descriptions, and more. This information can be further analyzed to understand trends in job markets or for building a dataset of job opportunities in specific roles.

The project leverages Selenium and BeautifulSoup to scrape job listings dynamically, handling various challenges such as loading pages, scrolling, and parsing JavaScript-rendered content. It is capable of scraping multiple pages of job listings for specific roles, such as "Data Analyst" and "System Analyst," and saving the results into CSV files for easy data manipulation and analysis.

Key Features:
* Scrapes detailed job listings including:
  * Job title
  * Company name
  * Location
  * Salary (if available)
  * Job description and requirements
  * Link to the job posting
  * Additional sections like job-related questions (if available)
* Supports scraping for multiple roles (configurable in the script).
* Configurable scraping depth (number of pages).
* Outputs results in CSV format for easy analysis.
