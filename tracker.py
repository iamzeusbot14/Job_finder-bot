import yaml
import os
import requests
import pandas as pd
from jobspy import scrape_jobs

# 1. Load Sent History
HISTORY_FILE = "sent_jobs.txt"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        sent_ids = set(f.read().splitlines())
else:
    sent_ids = set()

def send_telegram(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, data=payload)

# 2. Load Config
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)["search"]

# 3. Scrape for Each Company
all_new_jobs = []

for company in config["companies"]:
    print(f"Searching for jobs at {company}...")
    for kw in config["keywords"]:
        try:
            jobs = scrape_jobs(
                site_name=["linkedin"],
                search_term=f"{company} {kw}",
                location=config["location"],
                results_wanted=10,
                hours_old=config["past_hours"]
            )
            
            if not jobs.empty:
                # Filter out already sent jobs
                new_jobs = jobs[~jobs['job_url'].astype(str).isin(sent_ids)]
                if not new_jobs.empty:
                    all_new_jobs.append(new_jobs)
        except Exception as e:
            print(f"Error searching for {company} {kw}: {e}")

# 4. Process and Save History
if all_new_jobs:
    df = pd.concat(all_new_jobs).drop_duplicates(subset=['job_url'])
    
    # Sort by company for a cleaner report
    df = df.sort_values(by='company')
    
    report = f"🚀 **MAANG/Big Tech Hiring Report ({len(df)})**\n"
    report += "---" + "\n"
    
    new_history = []
    for _, row in df.iterrows():
        # Format: Company | Title | Link
        line = f"• **{row['company']}**: [{row['title']}]({row['job_url']})\n"
        
        if len(report) + len(line) > 4000:
            send_telegram(report)
            report = ""
        report += line
        new_history.append(row['job_url'])

    if report:
        send_telegram(report)

    # Update history file
    with open(HISTORY_FILE, "a") as f:
        for job_id in new_history:
            f.write(f"{job_id}\n")
else:
    print("No new unique jobs found for Google, Microsoft, or Apple.")
